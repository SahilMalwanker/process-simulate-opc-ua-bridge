"""Desktop controller app for OPC UA server + sequencer.

Features:
- Build server
- Start/Stop server
- Start/Stop sequencer
- Toggle First/Second/Thrid/Fourth operations
- Show active operation
- Parse server logs to show client connection status
"""
from __future__ import annotations

import asyncio
import queue
import re
import subprocess
import sys
import threading
import time
import os
from pathlib import Path
import shutil
from typing import Dict, Optional

import tkinter as tk
from tkinter import ttk

from asyncua import Client


def _is_repo_root(p: Path) -> bool:
    """Return True if *p* looks like the TestOPC repo root."""
    return (p / "Working_OPC" / "build.ps1").exists() and (p / "open62541").exists()


def _find_project_root() -> Optional[Path]:
    # 1. Explicit env-var override
    env_root = os.environ.get("TESTOPC_ROOT")
    if env_root:
        root = Path(env_root).resolve()
        if _is_repo_root(root):
            return root

    # 2. Walk upward from the *real* EXE location (not the _MEI temp dir)
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
    else:
        exe_dir = Path(__file__).resolve().parent

    for parent in [exe_dir] + list(exe_dir.parents):
        if _is_repo_root(parent):
            return parent

    # 3. If this script lives directly in Working_OPC
    if (exe_dir / "build.ps1").exists() and (exe_dir.parent / "open62541").exists():
        return exe_dir.parent

    # 4. Ask the user via a folder-picker dialog (GUI fallback)
    try:
        from tkinter import filedialog, messagebox
        messagebox.showinfo(
            "OPC UA Control",
            "Could not auto-detect the project folder.\n\n"
            "Please select the TestOPC repo root\n"
            "(the folder that contains Working_OPC and open62541).",
        )
        chosen = filedialog.askdirectory(title="Select TestOPC repo root")
        if chosen:
            chosen_path = Path(chosen).resolve()
            if _is_repo_root(chosen_path):
                return chosen_path
    except Exception:
        pass

    return None


PROJECT_ROOT = _find_project_root()
APP_DIR = (PROJECT_ROOT / "Working_OPC") if PROJECT_ROOT else Path(__file__).resolve().parent
BUILD_SCRIPT = APP_DIR / "build.ps1"
SERVER_EXE = APP_DIR / "server_json_config.exe"
SERVER_CONFIG = APP_DIR / "ps_server.json5"
SEQUENCER_SCRIPT = APP_DIR / "opcua_sequencer.py"
SEQUENCER_EXE = APP_DIR / "opcua_sequencer.exe"

DEFAULT_OPC_URL = "opc.tcp://192.168.174.1:4841"

CONTROL_TRIGGERS = {
    "FirstOp": "Trigger.FirstOp",
    "SecondOp": "Trigger.SecondOp",
    "ThridOp": "Trigger.ThridOp",
    "FourthOp": "Trigger.FourthOp",
}


class OpcUaWorker:
    """Background OPC UA client for control triggers."""

    def __init__(self, log_queue: queue.Queue, status_queue: queue.Queue) -> None:
        self.log_queue = log_queue
        self.status_queue = status_queue
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.client: Optional[Client] = None
        self.control_nodes: Dict[str, object] = {}
        self.connected = False
        self.polling_task: Optional[asyncio.Task] = None

    def start(self) -> None:
        self.thread.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect(self, url: str) -> None:
        fut = asyncio.run_coroutine_threadsafe(self._connect(url), self.loop)
        fut.result(timeout=10)

    async def _connect(self, url: str) -> None:
        if self.connected:
            return
        try:
            self.client = Client(url=url)
            await self.client.connect()
            self.control_nodes = {}
            for name, node_str in CONTROL_TRIGGERS.items():
                node = self.client.get_node(f"ns=1;s={node_str}")
                await node.read_value()
                self.control_nodes[name] = node
            self.connected = True
            self.status_queue.put(("opc_connected", True))
            self.polling_task = asyncio.create_task(self._poll_controls())
            self.log_queue.put("[OPC] Connected")
        except Exception as exc:  # noqa: BLE001
            self.status_queue.put(("opc_connected", False))
            self.log_queue.put(f"[OPC] Connect failed: {exc}")
            raise

    def disconnect(self) -> None:
        fut = asyncio.run_coroutine_threadsafe(self._disconnect(), self.loop)
        fut.result(timeout=10)

    async def _disconnect(self) -> None:
        if not self.connected:
            return
        self.connected = False
        if self.polling_task:
            self.polling_task.cancel()
            self.polling_task = None
        if self.client:
            await self.client.disconnect()
            self.client = None
        self.control_nodes = {}
        self.status_queue.put(("opc_connected", False))
        self.log_queue.put("[OPC] Disconnected")

    def set_active_control(self, url: str, active: str) -> None:
        fut = asyncio.run_coroutine_threadsafe(
            self._set_active_control(url, active), self.loop
        )
        fut.result(timeout=10)

    async def _set_active_control(self, url: str, active: str) -> None:
        if not self.connected:
            await self._connect(url)
        for name, node in self.control_nodes.items():
            await node.write_value(name == active)
        self.log_queue.put(f"[OPC] Active control set: {active}")

    def clear_controls(self, url: str) -> None:
        fut = asyncio.run_coroutine_threadsafe(self._clear_controls(url), self.loop)
        fut.result(timeout=10)

    async def _clear_controls(self, url: str) -> None:
        if not self.connected:
            await self._connect(url)
        for node in self.control_nodes.values():
            await node.write_value(False)
        self.log_queue.put("[OPC] All controls set to FALSE")

    async def _poll_controls(self) -> None:
        while self.connected:
            data: Dict[str, bool] = {}
            for name, node in self.control_nodes.items():
                try:
                    value = await node.read_value()
                    data[name] = bool(value)
                except Exception:
                    data[name] = False
            self.status_queue.put(("controls", data))
            await asyncio.sleep(0.2)


class OpcUaControlApp:
    """Tkinter GUI for controlling the OPC UA server and sequencer."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OPC UA Control Panel")
        self.root.geometry("900x600")

        self.log_queue: queue.Queue = queue.Queue()
        self.status_queue: queue.Queue = queue.Queue()

        self.server_process: Optional[subprocess.Popen[str]] = None
        self.sequencer_process: Optional[subprocess.Popen[str]] = None

        self.server_status = tk.StringVar(value="Stopped")
        self.client_status = tk.StringVar(value="Unknown")
        self.sequencer_status = tk.StringVar(value="Stopped")
        self.active_operation = tk.StringVar(value="None")
        self.opc_connected = tk.StringVar(value="Disconnected")

        self.opc_worker = OpcUaWorker(self.log_queue, self.status_queue)
        self.opc_worker.start()

        self._build_ui()
        self._poll_queues()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="OPC URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(top, width=40)
        self.url_entry.insert(0, DEFAULT_OPC_URL)
        self.url_entry.grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(top, text="Server:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(top, textvariable=self.server_status).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(top, text="Client:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0))
        ttk.Label(top, textvariable=self.client_status).grid(row=1, column=3, sticky=tk.W)

        ttk.Label(top, text="OPC Client:").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(top, textvariable=self.opc_connected).grid(row=2, column=1, sticky=tk.W)

        ttk.Label(top, text="Sequencer:").grid(row=2, column=2, sticky=tk.W, padx=(20, 0))
        ttk.Label(top, textvariable=self.sequencer_status).grid(row=2, column=3, sticky=tk.W)

        ttk.Label(top, text="Active Operation:").grid(row=3, column=0, sticky=tk.W)
        ttk.Label(top, textvariable=self.active_operation).grid(row=3, column=1, sticky=tk.W)

        if not PROJECT_ROOT:
            ttk.Label(
                top,
                text="Project root not found. Set TESTOPC_ROOT to repo root.",
                foreground="red",
            ).grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))

        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Build Server", command=self._build_server).grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.server_btn = ttk.Button(
            button_frame, text="Start Server", command=self._toggle_server
        )
        self.server_btn.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        self.seq_btn = ttk.Button(
            button_frame, text="Start Sequencer", command=self._toggle_sequencer
        )
        self.seq_btn.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        ttk.Button(button_frame, text="Stop All Ops", command=self._clear_controls).grid(
            row=0, column=3, padx=5, pady=5, sticky=tk.W
        )

        ops = ttk.LabelFrame(self.root, text="Operations", padding=10)
        ops.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(ops, text="FirstOp", command=lambda: self._set_operation("FirstOp")).grid(
            row=0, column=0, padx=5, pady=5
        )
        ttk.Button(ops, text="SecondOp", command=lambda: self._set_operation("SecondOp")).grid(
            row=0, column=1, padx=5, pady=5
        )
        ttk.Button(ops, text="ThridOp", command=lambda: self._set_operation("ThridOp")).grid(
            row=0, column=2, padx=5, pady=5
        )
        ttk.Button(ops, text="FourthOp", command=lambda: self._set_operation("FourthOp")).grid(
            row=0, column=3, padx=5, pady=5
        )

        log_frame = ttk.LabelFrame(self.root, text="Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_text = tk.Text(log_frame, height=15, wrap=tk.NONE)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _log(self, line: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"{timestamp} {line}\n")
        self.log_text.see(tk.END)

    def _poll_queues(self) -> None:
        while not self.log_queue.empty():
            self._log(self.log_queue.get())

        while not self.status_queue.empty():
            key, value = self.status_queue.get()
            if key == "controls":
                self._update_active_operation(value)
            elif key == "opc_connected":
                self.opc_connected.set("Connected" if value else "Disconnected")

        self.root.after(100, self._poll_queues)

    def _update_active_operation(self, controls: Dict[str, bool]) -> None:
        active = "None"
        for name in ["FourthOp", "ThridOp", "SecondOp", "FirstOp"]:
            if controls.get(name):
                active = name
                break
        self.active_operation.set(active)

    def _build_server(self) -> None:
        def runner() -> None:
            self.log_queue.put("[BUILD] Starting build.ps1")
            try:
                subprocess.run(
                    [
                        "powershell.exe",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(BUILD_SCRIPT),
                    ],
                    cwd=str(APP_DIR),
                    check=True,
                    text=True,
                )
                self.log_queue.put("[BUILD] Build complete")
            except Exception as exc:  # noqa: BLE001
                self.log_queue.put(f"[BUILD] Failed: {exc}")

        threading.Thread(target=runner, daemon=True).start()

    def _get_python_exe(self) -> Optional[str]:
        """Find a real Python interpreter (never this frozen EXE)."""
        # 1. Explicit env-var
        env_python = os.environ.get("OPCUA_PYTHON_EXE")
        if env_python and Path(env_python).exists():
            self.log_queue.put(f"[SEQ] Using OPCUA_PYTHON_EXE: {env_python}")
            return env_python

        # 2. If we are NOT frozen, sys.executable is the real Python
        if not getattr(sys, "frozen", False):
            return sys.executable

        # 3. Known install location (per-user Python 3.13)
        known = Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python313" / "python.exe"
        if known.exists():
            self.log_queue.put(f"[SEQ] Using known Python: {known}")
            return str(known)

        # 4. Search PATH for python/py but skip our own EXE
        my_exe = Path(sys.executable).resolve()
        for candidate in ("python", "py", "python3"):
            resolved = shutil.which(candidate)
            if resolved and Path(resolved).resolve() != my_exe:
                self.log_queue.put(f"[SEQ] Using PATH Python: {resolved}")
                return resolved

        return None

    def _toggle_server(self) -> None:
        if self.server_process and self.server_process.poll() is None:
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self) -> None:
        if not SERVER_EXE.exists():
            self.log_queue.put("[SERVER] server_json_config.exe not found. Build first.")
            return

        self.log_queue.put("[SERVER] Starting server...")
        self.server_process = subprocess.Popen(
            [str(SERVER_EXE), str(SERVER_CONFIG.name)],
            cwd=str(APP_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.server_status.set("Running")
        self.server_btn.configure(text="Stop Server")

        threading.Thread(target=self._read_server_output, daemon=True).start()

    def _stop_server(self) -> None:
        if not self.server_process:
            return
        self.log_queue.put("[SERVER] Stopping server...")
        self.server_process.terminate()
        try:
            self.server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.server_process.kill()
        self.server_process = None
        self.server_status.set("Stopped")
        self.client_status.set("Unknown")
        self.server_btn.configure(text="Start Server")

    def _read_server_output(self) -> None:
        if not self.server_process or not self.server_process.stdout:
            return
        for line in self.server_process.stdout:
            line = line.strip()
            if line:
                self.log_queue.put(f"[SERVER] {line}")
                self._parse_server_log(line)
        self.server_status.set("Stopped")
        self.server_btn.configure(text="Start Server")

    def _parse_server_log(self, line: str) -> None:
        lower = line.lower()
        if re.search(r"securechannel.*(open|opened|created)", lower) or re.search(
            r"session.*(activate|activated|created)", lower
        ):
            self.client_status.set("Connected")
        elif re.search(r"securechannel.*(close|closed|deleted)", lower) or re.search(
            r"session.*(close|closed|deleted)", lower
        ):
            self.client_status.set("Disconnected")

    def _toggle_sequencer(self) -> None:
        if self.sequencer_process and self.sequencer_process.poll() is None:
            self._stop_sequencer()
        else:
            self._start_sequencer()

    def _start_sequencer(self) -> None:
        command: Optional[list[str]] = None
        if SEQUENCER_EXE.exists() and SEQUENCER_EXE.name != "opcua_control_app.exe":
            command = [str(SEQUENCER_EXE)]
        elif SEQUENCER_SCRIPT.exists():
            python_exe = self._get_python_exe()
            if not python_exe:
                self.log_queue.put(
                    "[SEQ] Python not found. Set OPCUA_PYTHON_EXE to your python.exe."
                )
                return
            command = [python_exe, str(SEQUENCER_SCRIPT)]
        else:
            self.log_queue.put("[SEQ] opcua_sequencer.py not found.")
            return

        self.log_queue.put(f"[SEQ] Starting sequencer: {command}")
        self.sequencer_process = subprocess.Popen(
            command,
            cwd=str(APP_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.sequencer_status.set("Running")
        self.seq_btn.configure(text="Stop Sequencer")
        threading.Thread(target=self._read_sequencer_output, daemon=True).start()

    def _stop_sequencer(self) -> None:
        if not self.sequencer_process:
            return
        self.log_queue.put("[SEQ] Stopping sequencer...")
        self.sequencer_process.terminate()
        try:
            self.sequencer_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.sequencer_process.kill()
        self.sequencer_process = None
        self.sequencer_status.set("Stopped")
        self.seq_btn.configure(text="Start Sequencer")

    def _read_sequencer_output(self) -> None:
        if not self.sequencer_process or not self.sequencer_process.stdout:
            return
        for line in self.sequencer_process.stdout:
            line = line.strip()
            if line:
                self.log_queue.put(f"[SEQ] {line}")
        self.sequencer_status.set("Stopped")
        self.seq_btn.configure(text="Start Sequencer")

    def _set_operation(self, name: str) -> None:
        url = self.url_entry.get().strip()

        def runner() -> None:
            try:
                self.opc_worker.set_active_control(url, name)
            except Exception as exc:  # noqa: BLE001
                self.log_queue.put(f"[OPC] Failed to set {name}: {exc}")

        threading.Thread(target=runner, daemon=True).start()

    def _clear_controls(self) -> None:
        url = self.url_entry.get().strip()

        def runner() -> None:
            try:
                self.opc_worker.clear_controls(url)
            except Exception as exc:  # noqa: BLE001
                self.log_queue.put(f"[OPC] Failed to clear controls: {exc}")

        threading.Thread(target=runner, daemon=True).start()


def main() -> None:
    import multiprocessing
    multiprocessing.freeze_support()

    root = tk.Tk()
    app = OpcUaControlApp(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
