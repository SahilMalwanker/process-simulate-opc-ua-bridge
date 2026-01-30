"""Desktop controller app for OPC UA server + sequencer.

Features:
- Build server
- Start/Stop server
- Start/Stop sequencer
- Toggle First/Second/Thrid/Fourth operations
- Show active operation
- Parse server logs to show client connection status
- Live robot joint display (18 joints across 3 robots)
- Siemens-themed colour scheme
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
from typing import Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, font as tkfont

from asyncua import Client


# ── Siemens colour palette ───────────────────────────────────────────
class SiemensColors:
    BG_DARK     = "#1B1534"   # Deep purple-navy (main bg)
    BG_CARD     = "#252046"   # Slightly lighter card bg
    BG_INPUT    = "#312B54"   # Entry/text widget bg
    TEAL        = "#009999"   # Primary accent (Siemens teal)
    TEAL_HOVER  = "#00B3B3"
    TEAL_DARK   = "#007A7A"
    PETROL      = "#006B82"   # Secondary accent
    TEXT        = "#E8E6F0"   # Primary text
    TEXT_DIM    = "#9B97B0"   # Dimmed text
    TEXT_BRIGHT = "#FFFFFF"
    SUCCESS     = "#00CC66"
    ERROR       = "#FF5566"
    WARN        = "#FFB347"
    BORDER      = "#3D3666"
    OP_ACTIVE   = "#009999"
    OP_INACTIVE = "#3D3666"


# ── Robot joint node paths ───────────────────────────────────────────
ROBOT_NAMES = ["Robot1", "Robot2", "Robot3"]
JOINT_NAMES = ["j1", "j2", "j3", "j4", "j5", "j6"]

ROBOT_JOINTS: List[Tuple[str, str]] = []
for _rn in ROBOT_NAMES:
    for _jn in JOINT_NAMES:
        ROBOT_JOINTS.append((_rn, _jn))  # ("Robot1", "j1"), …


# ── Repo / path helpers ─────────────────────────────────────────────
def _is_repo_root(p: Path) -> bool:
    """Return True if *p* looks like the project root (contains server/).
    Works even without third_party/open62541 (e.g. deployment-only machines).
    """
    server = p / "server"
    return server.is_dir() and (
        (server / "build.ps1").exists()
        or (server / "server_json_config.exe").exists()
        or (server / "ps_server.json5").exists()
    )


def _find_project_root() -> Optional[Path]:
    env_root = os.environ.get("TESTOPC_ROOT")
    if env_root:
        root = Path(env_root).resolve()
        if _is_repo_root(root):
            return root

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
    else:
        exe_dir = Path(__file__).resolve().parent

    for parent in [exe_dir] + list(exe_dir.parents):
        if _is_repo_root(parent):
            return parent

    try:
        from tkinter import filedialog, messagebox
        messagebox.showinfo(
            "OPC UA Control",
            "Could not auto-detect the project folder.\n\n"
            "Please select the project root\n"
            "(the folder that contains server and client).",
        )
        chosen = filedialog.askdirectory(title="Select project root")
        if chosen:
            chosen_path = Path(chosen).resolve()
            if _is_repo_root(chosen_path):
                return chosen_path
    except Exception:
        pass

    return None


PROJECT_ROOT = _find_project_root()
_ROOT = PROJECT_ROOT or Path(__file__).resolve().parent.parent
SERVER_DIR = _ROOT / "server"
CLIENT_DIR = _ROOT / "client"
BUILD_SCRIPT = SERVER_DIR / "build.ps1"
SERVER_EXE = SERVER_DIR / "server_json_config.exe"
SERVER_CONFIG = SERVER_DIR / "ps_server.json5"
SEQUENCER_SCRIPT = CLIENT_DIR / "opcua_sequencer.py"
SEQUENCER_EXE = CLIENT_DIR / "opcua_sequencer.exe"

DEFAULT_OPC_URL = "opc.tcp://127.0.0.1:4841"

CONTROL_TRIGGERS = {
    "FirstOp":  "Trigger.FirstOp",
    "SecondOp": "Trigger.SecondOp",
    "ThridOp":  "Trigger.ThridOp",
    "FourthOp": "Trigger.FourthOp",
}


# ═════════════════════════════════════════════════════════════════════
#  OPC UA background worker
# ═════════════════════════════════════════════════════════════════════
class OpcUaWorker:
    """Background OPC UA client for control triggers + joint reading."""

    def __init__(self, log_queue: queue.Queue, status_queue: queue.Queue) -> None:
        self.log_queue = log_queue
        self.status_queue = status_queue
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.client: Optional[Client] = None
        self.control_nodes: Dict[str, object] = {}
        self.joint_nodes: List[Tuple[str, str, object]] = []  # (robot, joint, node)
        self.connected = False
        self.polling_task: Optional[asyncio.Task] = None

    def start(self) -> None:
        self.thread.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    # ── connect / disconnect ─────────────────────────────────────────
    def connect(self, url: str) -> None:
        fut = asyncio.run_coroutine_threadsafe(self._connect(url), self.loop)
        fut.result(timeout=10)

    async def _connect(self, url: str) -> None:
        if self.connected:
            return
        try:
            self.log_queue.put(f"[OPC] Connecting to {url} …")
            self.client = Client(url=url, timeout=6)
            await self.client.connect()

            # Control trigger nodes
            self.control_nodes = {}
            for name, node_str in CONTROL_TRIGGERS.items():
                node = self.client.get_node(f"ns=1;s={node_str}")
                await node.read_value()
                self.control_nodes[name] = node

            # Joint nodes
            self.joint_nodes = []
            for robot, joint in ROBOT_JOINTS:
                node_id = f"ns=1;s=PS.{robot}.{joint}"
                node = self.client.get_node(node_id)
                self.joint_nodes.append((robot, joint, node))

            self.connected = True
            self.status_queue.put(("opc_connected", True))
            self.polling_task = asyncio.create_task(self._poll_loop())
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
        self.joint_nodes = []
        self.status_queue.put(("opc_connected", False))
        self.log_queue.put("[OPC] Disconnected")

    # ── write helpers ────────────────────────────────────────────────
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

    # ── polling loop (controls + joints) ─────────────────────────────
    async def _poll_loop(self) -> None:
        while self.connected:
            # Controls
            ctrl_data: Dict[str, bool] = {}
            for name, node in self.control_nodes.items():
                try:
                    value = await node.read_value()
                    ctrl_data[name] = bool(value)
                except Exception:
                    ctrl_data[name] = False
            self.status_queue.put(("controls", ctrl_data))

            # Joints
            joint_data: Dict[str, float] = {}
            for robot, joint, node in self.joint_nodes:
                try:
                    value = await node.read_value()
                    joint_data[f"{robot}.{joint}"] = float(value)
                except Exception:
                    joint_data[f"{robot}.{joint}"] = 0.0
            self.status_queue.put(("joints", joint_data))

            await asyncio.sleep(0.15)


# ═════════════════════════════════════════════════════════════════════
#  GUI Application
# ═════════════════════════════════════════════════════════════════════
class OpcUaControlApp:
    """Tkinter GUI with Siemens colour scheme, robot joint display."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OPC UA Control Panel  —  Siemens")
        self.root.geometry("1260x740")
        self.root.configure(bg=SiemensColors.BG_DARK)
        self.root.minsize(1100, 600)

        self.log_queue: queue.Queue = queue.Queue()
        self.status_queue: queue.Queue = queue.Queue()

        self.server_process: Optional[subprocess.Popen[str]] = None
        self.sequencer_process: Optional[subprocess.Popen[str]] = None

        self.server_status  = tk.StringVar(value="Stopped")
        self.client_status  = tk.StringVar(value="Unknown")
        self.sequencer_status = tk.StringVar(value="Stopped")
        self.active_operation = tk.StringVar(value="None")
        self.opc_connected  = tk.StringVar(value="Disconnected")

        # Joint StringVars  {Robot1.j1: StringVar, …}
        self.joint_vars: Dict[str, tk.StringVar] = {}
        for robot, joint in ROBOT_JOINTS:
            self.joint_vars[f"{robot}.{joint}"] = tk.StringVar(value="—")

        self.opc_worker = OpcUaWorker(self.log_queue, self.status_queue)
        self.opc_worker.start()

        self._setup_styles()
        self._build_ui()
        self._poll_queues()

    # ── ttk style configuration ──────────────────────────────────────
    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        C = SiemensColors

        # General frame / label defaults
        style.configure(".", background=C.BG_DARK, foreground=C.TEXT, font=("Segoe UI", 10))
        style.configure("TFrame", background=C.BG_DARK)
        style.configure("TLabel", background=C.BG_DARK, foreground=C.TEXT)
        style.configure("TLabelframe", background=C.BG_DARK, foreground=C.TEAL,
                         bordercolor=C.BORDER, relief="groove")
        style.configure("TLabelframe.Label", background=C.BG_DARK, foreground=C.TEAL,
                         font=("Segoe UI Semibold", 11))

        # Entry
        style.configure("TEntry", fieldbackground=C.BG_INPUT, foreground=C.TEXT,
                         insertcolor=C.TEXT, bordercolor=C.BORDER)
        style.map("TEntry", fieldbackground=[("focus", C.BG_INPUT)])

        # ── Buttons ──────────────────────────────────────────────────
        # Primary teal button
        style.configure("Teal.TButton",
                         background=C.TEAL, foreground=C.TEXT_BRIGHT,
                         font=("Segoe UI Semibold", 10), padding=(14, 6),
                         borderwidth=0, relief="flat")
        style.map("Teal.TButton",
                   background=[("active", C.TEAL_HOVER), ("disabled", C.OP_INACTIVE)],
                   foreground=[("disabled", C.TEXT_DIM)])

        # Danger / stop button
        style.configure("Danger.TButton",
                         background=C.ERROR, foreground=C.TEXT_BRIGHT,
                         font=("Segoe UI Semibold", 10), padding=(14, 6),
                         borderwidth=0, relief="flat")
        style.map("Danger.TButton",
                   background=[("active", "#FF7788")])

        # Operation toggle (inactive)
        style.configure("Op.TButton",
                         background=C.OP_INACTIVE, foreground=C.TEXT_DIM,
                         font=("Segoe UI Semibold", 10), padding=(16, 8),
                         borderwidth=0, relief="flat")
        style.map("Op.TButton",
                   background=[("active", C.TEAL_DARK)])

        # Operation toggle (active)
        style.configure("OpActive.TButton",
                         background=C.TEAL, foreground=C.TEXT_BRIGHT,
                         font=("Segoe UI Semibold", 10), padding=(16, 8),
                         borderwidth=0, relief="flat")
        style.map("OpActive.TButton",
                   background=[("active", C.TEAL_HOVER)])

        # Card frames
        style.configure("Card.TFrame", background=C.BG_CARD, relief="flat")
        style.configure("CardLabel.TLabel", background=C.BG_CARD, foreground=C.TEXT)
        style.configure("CardDim.TLabel", background=C.BG_CARD, foreground=C.TEXT_DIM,
                         font=("Segoe UI", 9))
        style.configure("CardBright.TLabel", background=C.BG_CARD, foreground=C.TEXT_BRIGHT,
                         font=("Segoe UI Semibold", 10))

        # Status labels
        style.configure("StatusOk.TLabel", background=C.BG_CARD, foreground=C.SUCCESS,
                         font=("Segoe UI Semibold", 10))
        style.configure("StatusBad.TLabel", background=C.BG_CARD, foreground=C.ERROR,
                         font=("Segoe UI Semibold", 10))
        style.configure("StatusWarn.TLabel", background=C.BG_CARD, foreground=C.WARN,
                         font=("Segoe UI Semibold", 10))

        # Joint card
        style.configure("Joint.TFrame", background=C.BG_CARD, relief="flat")
        style.configure("JointHeader.TLabel", background=C.BG_CARD, foreground=C.TEAL,
                         font=("Segoe UI Semibold", 11))
        style.configure("JointName.TLabel", background=C.BG_CARD, foreground=C.TEXT_DIM,
                         font=("Segoe UI", 9))
        style.configure("JointValue.TLabel", background=C.BG_CARD, foreground=C.TEXT_BRIGHT,
                         font=("Consolas", 11))

        # Section header
        style.configure("SectionHead.TLabel", background=C.BG_DARK, foreground=C.TEAL,
                         font=("Segoe UI Semibold", 13))

    # ── Build the complete UI ────────────────────────────────────────
    def _build_ui(self) -> None:
        C = SiemensColors

        # ── Top bar (title + url) ─────────────────────────────────────
        topbar = ttk.Frame(self.root, style="TFrame")
        topbar.pack(fill=tk.X, padx=16, pady=(12, 4))

        ttk.Label(topbar, text="⬡  OPC UA Control Panel", style="SectionHead.TLabel").pack(
            side=tk.LEFT)

        url_frame = ttk.Frame(topbar, style="TFrame")
        url_frame.pack(side=tk.RIGHT)
        ttk.Label(url_frame, text="Endpoint:", style="TLabel").pack(side=tk.LEFT, padx=(0, 4))
        self.url_entry = ttk.Entry(url_frame, width=34, style="TEntry")
        self.url_entry.insert(0, DEFAULT_OPC_URL)
        self.url_entry.pack(side=tk.LEFT)

        # ── Main horizontal pane ──────────────────────────────────────
        main_pane = ttk.Frame(self.root, style="TFrame")
        main_pane.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        left_col = ttk.Frame(main_pane, style="TFrame")
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Wide enough for three joint columns (j1-j3 / j4-j6) without clipping
        right_col = ttk.Frame(main_pane, style="TFrame", width=430)
        right_col.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        right_col.pack_propagate(False)

        # ── LEFT: status card ─────────────────────────────────────────
        status_card = ttk.Frame(left_col, style="Card.TFrame", padding=12)
        status_card.pack(fill=tk.X, pady=(0, 8))

        self._status_row(status_card, 0, "Server", self.server_status)
        self._status_row(status_card, 1, "Client (PS)", self.client_status)
        self._status_row(status_card, 2, "OPC Link", self.opc_connected)
        self._status_row(status_card, 3, "Sequencer", self.sequencer_status)
        self._status_row(status_card, 4, "Active Op", self.active_operation)

        if not PROJECT_ROOT:
            ttk.Label(status_card, text="⚠ Project root not found – set TESTOPC_ROOT",
                      style="StatusBad.TLabel").grid(row=5, column=0, columnspan=2,
                                                      sticky=tk.W, pady=(6, 0))

        # ── LEFT: action buttons ──────────────────────────────────────
        btn_card = ttk.Frame(left_col, style="Card.TFrame", padding=12)
        btn_card.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(btn_card, text="⚙  Build Server", style="Teal.TButton",
                   command=self._build_server).grid(row=0, column=0, padx=4, pady=4)

        self.server_btn = ttk.Button(btn_card, text="▶  Start Server",
                                      style="Teal.TButton", command=self._toggle_server)
        self.server_btn.grid(row=0, column=1, padx=4, pady=4)

        self.seq_btn = ttk.Button(btn_card, text="▶  Start Sequencer",
                                   style="Teal.TButton", command=self._toggle_sequencer)
        self.seq_btn.grid(row=0, column=2, padx=4, pady=4)

        ttk.Button(btn_card, text="⏹  Stop All Ops", style="Danger.TButton",
                   command=self._clear_controls).grid(row=0, column=3, padx=4, pady=4)

        # ── LEFT: operation toggles ───────────────────────────────────
        ops_card = ttk.Frame(left_col, style="Card.TFrame", padding=12)
        ops_card.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(ops_card, text="Operations", style="JointHeader.TLabel").grid(
            row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 6))

        self.op_buttons: Dict[str, ttk.Button] = {}
        for idx, name in enumerate(["FirstOp", "SecondOp", "ThridOp", "FourthOp"]):
            btn = ttk.Button(ops_card, text=name, style="Op.TButton",
                             command=lambda n=name: self._set_operation(n))
            btn.grid(row=1, column=idx, padx=4, pady=4, sticky=tk.EW)
            self.op_buttons[name] = btn
            ops_card.columnconfigure(idx, weight=1)

        # ── LEFT: log text ────────────────────────────────────────────
        log_label = ttk.Label(left_col, text="Logs", style="SectionHead.TLabel")
        log_label.pack(anchor=tk.W, pady=(4, 2))

        log_frame = ttk.Frame(left_col, style="Card.TFrame", padding=4)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap=tk.NONE, height=12,
                                bg=C.BG_INPUT, fg=C.TEXT, insertbackground=C.TEXT,
                                font=("Consolas", 9), relief="flat", bd=0,
                                selectbackground=C.TEAL, selectforeground=C.TEXT_BRIGHT)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # ── RIGHT: robot joints ───────────────────────────────────────
        self._build_joints(right_col)

    # ── status helper ────────────────────────────────────────────────
    def _status_row(self, parent: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=f"{label}:", style="CardDim.TLabel").grid(
            row=row, column=0, sticky=tk.W, padx=(0, 8), pady=2)
        lbl = ttk.Label(parent, textvariable=var, style="CardBright.TLabel")
        lbl.grid(row=row, column=1, sticky=tk.W, pady=2)

    # ── build joint panel ────────────────────────────────────────────
    def _build_joints(self, parent: ttk.Frame) -> None:
        C = SiemensColors

        ttk.Label(parent, text="Robot Joints (°)", style="SectionHead.TLabel").pack(
            anchor=tk.W, pady=(0, 6))

        canvas = tk.Canvas(parent, bg=C.BG_DARK, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        inner = ttk.Frame(canvas, style="TFrame")

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(fill=tk.BOTH, expand=True)

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        for robot in ROBOT_NAMES:
            robot_card = ttk.Frame(inner, style="Card.TFrame", padding=10)
            robot_card.pack(fill=tk.X, pady=(0, 8), padx=2)

            ttk.Label(robot_card, text=f"🤖  {robot}", style="JointHeader.TLabel").grid(
                row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 6))

            for j_idx, jname in enumerate(JOINT_NAMES):
                r = 1 + j_idx // 3
                c = (j_idx % 3) * 2
                key = f"{robot}.{jname}"

                ttk.Label(robot_card, text=f"{jname}:", style="JointName.TLabel").grid(
                    row=r, column=c, sticky=tk.E, padx=(8, 2), pady=2)
                ttk.Label(robot_card, textvariable=self.joint_vars[key],
                          style="JointValue.TLabel", width=10, anchor=tk.E).grid(
                    row=r, column=c + 1, sticky=tk.W, padx=(0, 12), pady=2)

                robot_card.columnconfigure(c + 1, weight=1)

    # ── logging ──────────────────────────────────────────────────────
    def _log(self, line: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"{timestamp}  {line}\n")
        self.log_text.see(tk.END)

    # ── queue polling ────────────────────────────────────────────────
    def _poll_queues(self) -> None:
        while not self.log_queue.empty():
            self._log(self.log_queue.get())

        while not self.status_queue.empty():
            key, value = self.status_queue.get()
            if key == "controls":
                self._update_active_operation(value)
            elif key == "opc_connected":
                self.opc_connected.set("Connected" if value else "Disconnected")
            elif key == "joints":
                self._update_joints(value)

        self.root.after(80, self._poll_queues)

    def _update_active_operation(self, controls: Dict[str, bool]) -> None:
        active = "None"
        for name in ["FourthOp", "ThridOp", "SecondOp", "FirstOp"]:
            if controls.get(name):
                active = name
                break
        self.active_operation.set(active)

        # Update button styles
        for name, btn in self.op_buttons.items():
            if controls.get(name):
                btn.configure(style="OpActive.TButton")
            else:
                btn.configure(style="Op.TButton")

    def _update_joints(self, joint_data: Dict[str, float]) -> None:
        for key, value in joint_data.items():
            var = self.joint_vars.get(key)
            if var:
                var.set(f"{value:+.2f}°")

    # ── build server ─────────────────────────────────────────────────
    def _build_server(self) -> None:
        def runner() -> None:
            self.log_queue.put("[BUILD] Starting build.ps1 …")
            try:
                proc = subprocess.Popen(
                    ["powershell.exe", "-ExecutionPolicy", "Bypass",
                     "-File", str(BUILD_SCRIPT)],
                    cwd=str(SERVER_DIR), text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if proc.stdout:
                    for line in proc.stdout:
                        line = line.rstrip()
                        if line:
                            self.log_queue.put(f"[BUILD] {line}")
                rc = proc.wait()
                if rc == 0:
                    self.log_queue.put("[BUILD] Build complete ✔")
                else:
                    self.log_queue.put(f"[BUILD] Build failed (exit code {rc})")
            except Exception as exc:  # noqa: BLE001
                self.log_queue.put(f"[BUILD] Failed: {exc}")

        threading.Thread(target=runner, daemon=True).start()

    # ── python exe helper ────────────────────────────────────────────
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

        # 3. Search PATH for python/py but skip our own EXE
        my_exe = Path(sys.executable).resolve()
        for candidate in ("python", "py", "python3"):
            resolved = shutil.which(candidate)
            if resolved and Path(resolved).resolve() != my_exe:
                self.log_queue.put(f"[SEQ] Using PATH Python: {resolved}")
                return resolved

        # 4. Scan common install locations for any user
        local_app = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        search_roots = []
        if local_app:
            search_roots.append(Path(local_app) / "Programs" / "Python")
        search_roots.append(Path(program_files) / "Python")
        search_roots.append(Path("C:/Python"))

        for root_dir in search_roots:
            if root_dir.is_dir():
                # Sort descending so newest Python version is found first
                for sub in sorted(root_dir.iterdir(), reverse=True):
                    exe = sub / "python.exe"
                    if exe.exists() and exe.resolve() != my_exe:
                        self.log_queue.put(f"[SEQ] Found Python: {exe}")
                        return str(exe)

        self.log_queue.put("[SEQ] Python not found. Install Python or set OPCUA_PYTHON_EXE.")
        return None

    # ── server start / stop ──────────────────────────────────────────
    def _toggle_server(self) -> None:
        if self.server_process and self.server_process.poll() is None:
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self) -> None:
        if not SERVER_EXE.exists():
            self.log_queue.put("[SERVER] server_json_config.exe not found – build first.")
            return

        self.log_queue.put("[SERVER] Starting server …")
        self.server_process = subprocess.Popen(
            [str(SERVER_EXE), str(SERVER_CONFIG.name)],
            cwd=str(SERVER_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.server_status.set("Running")
        self.server_btn.configure(text="⏹  Stop Server", style="Danger.TButton")
        threading.Thread(target=self._read_server_output, daemon=True).start()

    def _stop_server(self) -> None:
        if not self.server_process:
            return
        self.log_queue.put("[SERVER] Stopping server …")
        self.server_process.terminate()
        try:
            self.server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.server_process.kill()
        self.server_process = None
        self.server_status.set("Stopped")
        self.client_status.set("Unknown")
        self.server_btn.configure(text="▶  Start Server", style="Teal.TButton")

    def _read_server_output(self) -> None:
        if not self.server_process or not self.server_process.stdout:
            return
        for line in self.server_process.stdout:
            line = line.strip()
            if line:
                self.log_queue.put(f"[SERVER] {line}")
                self._parse_server_log(line)
        self.server_status.set("Stopped")
        self.server_btn.configure(text="▶  Start Server", style="Teal.TButton")

    def _parse_server_log(self, line: str) -> None:
        lower = line.lower()
        if re.search(r"securechannel.*(open|opened|created)", lower) or \
           re.search(r"session.*(activate|activated|created)", lower):
            self.client_status.set("Connected")
        elif re.search(r"securechannel.*(close|closed|deleted)", lower) or \
             re.search(r"session.*(close|closed|deleted)", lower):
            self.client_status.set("Disconnected")

    # ── sequencer start / stop ───────────────────────────────────────
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
                    "[SEQ] Python not found. Set OPCUA_PYTHON_EXE to your python.exe.")
                return
            command = [python_exe, str(SEQUENCER_SCRIPT)]
        else:
            self.log_queue.put("[SEQ] opcua_sequencer.py not found.")
            return

        self.log_queue.put(f"[SEQ] Starting sequencer: {command}")
        self.sequencer_process = subprocess.Popen(
            command, cwd=str(CLIENT_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.sequencer_status.set("Running")
        self.seq_btn.configure(text="⏹  Stop Sequencer", style="Danger.TButton")
        threading.Thread(target=self._read_sequencer_output, daemon=True).start()

    def _stop_sequencer(self) -> None:
        if not self.sequencer_process:
            return
        self.log_queue.put("[SEQ] Stopping sequencer …")
        self.sequencer_process.terminate()
        try:
            self.sequencer_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.sequencer_process.kill()
        self.sequencer_process = None
        self.sequencer_status.set("Stopped")
        self.seq_btn.configure(text="▶  Start Sequencer", style="Teal.TButton")

    def _read_sequencer_output(self) -> None:
        if not self.sequencer_process or not self.sequencer_process.stdout:
            return
        for line in self.sequencer_process.stdout:
            line = line.strip()
            if line:
                self.log_queue.put(f"[SEQ] {line}")
        self.sequencer_status.set("Stopped")
        self.seq_btn.configure(text="▶  Start Sequencer", style="Teal.TButton")

    # ── operation toggles ────────────────────────────────────────────
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


# ═════════════════════════════════════════════════════════════════════
def main() -> None:
    import multiprocessing
    multiprocessing.freeze_support()

    root = tk.Tk()
    OpcUaControlApp(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
