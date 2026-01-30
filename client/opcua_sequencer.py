"""OPC UA Operation Sequence Automation System.

Async OPC UA client that triggers operations in order and waits for
feedback reset signals before continuing. Uses asyncua and asyncio.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from asyncua import Client


# ============================
# Configuration Defaults
# ============================
OPC_SERVER = "opc.tcp://127.0.0.1:4841"  # Change to your server endpoint
SIGNAL_READ_INTERVAL = 0.1
OPERATION_TIMEOUT = 60.0
FEEDBACK_RESET_TIMEOUT = 30.0
INTER_OPERATION_DELAY = 0.5
INTER_CYCLE_DELAY = 0.5


# ============================
# Operation Group Definitions (4)
# ============================
CONTROL_TRIGGERS = {
    "FirstOp": "Trigger.FirstOp",
    "SecondOp": "Trigger.SecondOp",
    "ThridOp": "Trigger.ThridOp",
    "FourthOp": "Trigger.FourthOp",
}

OPERATION_GROUPS: Dict[str, List[Dict[str, str]]] = {
    "FirstOp": [
        {
            "name": "Op1 - Sauggreifer Original",
            "trigger": "Trigger.Op1_1Start",
            "feedback": "Feedback.Gen_Rob_Op_Sauggreifer_Original_end",
        },
    ],
    "SecondOp": [
        {
            "name": "Op2.1 - Enclosure",
            "trigger": "Trigger.Op2_1Start",
            "feedback": "Feedback.Enclosure_Op_end_1",
        },
        {
            "name": "Op2.2 - Sauggreifer",
            "trigger": "Trigger.Op2_2Start",
            "feedback": "Feedback.Gen_Rob_Op_Sauggreifer_end_1",
        },
        {
            "name": "Op2.3 - APP HL",
            "trigger": "Trigger.Op2_3Start",
            "feedback": "Feedback.Gen_Rob_Op_Lukas_LSI_600_APP_HL_end_1",
        },
        {
            "name": "Op2.4 - LSI 600",
            "trigger": "Trigger.Op2_4Start",
            "feedback": "Feedback.Gen_Rob_Op_Lukas_LSI_600_end_1_1",
        },
        {
            "name": "Op2.5 - APPROACH HL (end_1_2)",
            "trigger": "Trigger.Op2_5Start",
            "feedback": "Feedback.Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_2",
        },
        {
            "name": "Op2.6 - APPROACH HL (end_1_1_1)",
            "trigger": "Trigger.Op2_6Start",
            "feedback": "Feedback.Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_1_1",
        },
        {
            "name": "Op2.7 - DEP HR",
            "trigger": "Trigger.Op2_7Start",
            "feedback": "Feedback.Gen_Rob_Op_Lukas_LSI_600_DEP_HR_end_1",
        },
    ],
    "ThridOp": [
        {
            "name": "Op3.1 - APP HL",
            "trigger": "Trigger.Op3_1Start",
            "feedback": "Feedback.Gen_Rob_Op_Lukas_LSI_600_APP_HL_end",
        },
        {
            "name": "Op3.2 - LSI 600",
            "trigger": "Trigger.Op3_2Start",
            "feedback": "Feedback.Gen_Rob_Op_Lukas_LSI_600_end_1",
        },
        {
            "name": "Op3.3 - APPROACH HL (end_1)",
            "trigger": "Trigger.Op3_3Start",
            "feedback": "Feedback.Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1",
        },
        {
            "name": "Op3.4 - APPROACH HL (end_1_1)",
            "trigger": "Trigger.Op3_4Start",
            "feedback": "Feedback.Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_1",
        },
        {
            "name": "Op3.5 - DEP HR",
            "trigger": "Trigger.Op3_5Start",
            "feedback": "Feedback.Gen_Rob_Op_Lukas_LSI_600_DEP_HR_end",
        },
    ],
    "FourthOp": [
        {
            "name": "Op4.1 - Enclosure",
            "trigger": "Trigger.Op4_1Start",
            "feedback": "Feedback.Enclosure_Op_end",
        },
    ],
}


# ============================
# Logging Utilities
# ============================
class ColorFormatter(logging.Formatter):
    """Colorized log formatter for console output."""

    COLORS = {
        "DEBUG": "\033[37m",
        "INFO": "\033[36m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[41m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        color = self.COLORS.get(record.levelname, "")
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


def configure_logging() -> logging.Logger:
    """Configure and return a colorized logger."""
    logger = logging.getLogger("opcua_sequencer")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = ColorFormatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


# ============================
# Data Models
# ============================
@dataclass
class OperationStep:
    """Single step within an operation group."""

    name: str
    trigger: str
    feedback: str
    timeout: float = OPERATION_TIMEOUT


# ============================
# Exceptions
# ============================
class NodeNotFoundError(Exception):
    """Raised when a trigger or feedback node cannot be resolved."""


class OperationStoppedError(Exception):
    """Raised when an active control trigger turns off mid-operation."""


# ============================
# Operation Sequencer
# ============================
class OperationSequencer:
    """Async OPC UA sequencer for executing operations in strict order."""

    def __init__(
        self,
        opc_url: str,
        operation_groups: Dict[str, List[OperationStep]],
        control_triggers: Dict[str, str],
        signal_read_interval: float = SIGNAL_READ_INTERVAL,
        operation_timeout: float = OPERATION_TIMEOUT,
        feedback_reset_timeout: float = FEEDBACK_RESET_TIMEOUT,
        inter_operation_delay: float = INTER_OPERATION_DELAY,
        inter_cycle_delay: float = INTER_CYCLE_DELAY,
        dry_run: bool = False,
    ) -> None:
        """Initialize the sequencer and prepare configuration values."""
        self.opc_url = opc_url
        self.operation_groups = operation_groups
        self.control_triggers = control_triggers
        self.signal_read_interval = signal_read_interval
        self.operation_timeout = operation_timeout
        self.feedback_reset_timeout = feedback_reset_timeout
        self.inter_operation_delay = inter_operation_delay
        self.inter_cycle_delay = inter_cycle_delay
        self.dry_run = dry_run

        self.logger = configure_logging()
        self.client: Optional[Client] = None
        self.trigger_nodes: Dict[str, Any] = {}
        self.feedback_nodes: Dict[str, Any] = {}
        self.control_nodes: Dict[str, Any] = {}

    async def connect(self) -> None:
        """Establish OPC UA connection and cache nodes."""
        self.logger.info("Connecting to OPC UA server: %s", self.opc_url)
        self.client = Client(url=self.opc_url)
        try:
            await self.client.connect()
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Connection failed: %s", exc)
            raise

        # Cache nodes for control triggers
        for control_name, control_node in self.control_triggers.items():
            await self._cache_node(control_node, self.control_nodes, control_name)

        # Cache nodes for triggers and feedback signals
        for steps in self.operation_groups.values():
            for step in steps:
                await self._cache_node(step.trigger, self.trigger_nodes)
                await self._cache_node(step.feedback, self.feedback_nodes)

        self.logger.info("Connected and nodes cached")

    async def disconnect(self) -> None:
        """Disconnect from server and clean up resources."""
        if not self.client:
            return

        # Emergency stop: ensure all triggers are off
        if not self.dry_run:
            await self._reset_all_triggers()

        try:
            await self.client.disconnect()
        finally:
            self.client = None
            self.logger.info("Disconnected")

    async def _cache_node(
        self,
        node_name: str,
        cache: Dict[str, Any],
        cache_key: Optional[str] = None,
    ) -> None:
        """Resolve a node by string NodeId and cache it."""
        if not self.client:
            raise ConnectionError("Client not connected")
        node_id = f"ns=1;s={node_name}"
        try:
            node = self.client.get_node(node_id)
            # Read once to validate the node exists
            await node.read_value()
            cache[cache_key or node_name] = node
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Node not found: %s (%s)", node_name, exc)
            cache[cache_key or node_name] = None

    async def _reset_all_triggers(self) -> None:
        """Set all triggers to FALSE on shutdown for safety."""
        for steps in self.operation_groups.values():
            for step in steps:
                await self.set_trigger(step.trigger, False)
        for control_name in self.control_triggers.keys():
            await self.set_control(control_name, False)

    async def set_control(self, name: str, value: bool) -> None:
        """Set a control trigger (FirstOp/SecondOp/ThridOp/FourthOp)."""
        node = self.control_nodes.get(name)
        if node is None:
            raise NodeNotFoundError(f"Control node not found: {name}")
        if self.dry_run:
            self.logger.info("[DRY RUN] Control %s = %s", name, value)
            return
        await node.write_value(value)
        self.logger.info("Control %s = %s", name, value)

    async def set_trigger(self, name: str, value: bool) -> None:
        """Set a trigger signal to the specified boolean value."""
        node = self.trigger_nodes.get(name)
        if node is None:
            raise NodeNotFoundError(f"Trigger node not found: {name}")
        if self.dry_run:
            self.logger.info("[DRY RUN] Trigger %s = %s", name, value)
            return
        await node.write_value(value)
        self.logger.info("Trigger %s = %s", name, value)

    async def read_feedback(self, name: str) -> bool:
        """Read a feedback signal value and return it as boolean."""
        node = self.feedback_nodes.get(name)
        if node is None:
            raise NodeNotFoundError(f"Feedback node not found: {name}")
        value = await node.read_value()
        return bool(value)

    async def read_control(self, name: str) -> bool:
        """Read a control trigger value."""
        node = self.control_nodes.get(name)
        if node is None:
            raise NodeNotFoundError(f"Control node not found: {name}")
        value = await node.read_value()
        return bool(value)

    async def _select_active_group(self) -> Optional[str]:
        """Select active group based on control triggers and reset others."""
        priority = ["FourthOp", "ThridOp", "SecondOp", "FirstOp"]
        active = None
        active_states: Dict[str, bool] = {}
        for name in priority:
            active_states[name] = await self.read_control(name)
        for name in priority:
            if active_states[name]:
                active = name
                break
        if active:
            for name, state in active_states.items():
                if name != active and state:
                    await self.set_control(name, False)
        return active

    async def wait_for_feedback_high(self, name: str, timeout: float) -> None:
        """Wait for a feedback signal to become TRUE with timeout."""
        await self._wait_for_feedback(name, True, timeout)

    async def wait_for_feedback_low(self, name: str, timeout: float) -> None:
        """Wait for a feedback signal to become FALSE with timeout."""
        await self._wait_for_feedback(name, False, timeout)

    async def _wait_for_feedback(self, name: str, target: bool, timeout: float) -> None:
        """Wait for feedback signal to reach a target state with timeout."""
        start = time.monotonic()
        last_value: Optional[bool] = None
        while True:
            current = await self.read_feedback(name)
            if last_value is None or current != last_value:
                self.logger.info("Feedback %s = %s", name, current)
                last_value = current
            if current == target:
                return
            if time.monotonic() - start > timeout:
                raise asyncio.TimeoutError(
                    f"Timeout waiting for {name} to become {target}"
                )
            await asyncio.sleep(self.signal_read_interval)

    async def _wait_for_feedback_with_control(
        self,
        name: str,
        target: bool,
        timeout: float,
        active_control: str,
    ) -> None:
        """Wait for feedback while ensuring the active control stays TRUE."""
        start = time.monotonic()
        last_value: Optional[bool] = None
        while True:
            if not await self.read_control(active_control):
                raise OperationStoppedError(
                    f"Control {active_control} turned off while waiting for {name}"
                )
            current = await self.read_feedback(name)
            if last_value is None or current != last_value:
                self.logger.info("Feedback %s = %s", name, current)
                last_value = current
            if current == target:
                return
            if time.monotonic() - start > timeout:
                raise asyncio.TimeoutError(
                    f"Timeout waiting for {name} to become {target}"
                )
            await asyncio.sleep(self.signal_read_interval)

    async def run_single_cycle(self) -> None:
        """Execute one full sequence for the active group."""
        active = await self._select_active_group()
        if not active:
            self.logger.warning("No control trigger active. Nothing to run.")
            return
        self.logger.info("============================================================")
        self.logger.info("# SINGLE CYCLE (%s)", active)
        self.logger.info("============================================================")
        steps = self.operation_groups[active]
        for index, step in enumerate(steps, start=1):
            current_active = await self._select_active_group()
            if current_active != active:
                self.logger.info(
                    "Control trigger changed (%s → %s). Stopping cycle.",
                    active,
                    current_active,
                )
                return
            try:
                await self._run_operation(index, len(steps), step, active)
            except OperationStoppedError:
                self.logger.info("Control %s turned off. Stopping cycle.", active)
                return

    async def run_continuous_loop(self, num_cycles: Optional[int]) -> None:
        """Execute N cycles or loop infinitely if num_cycles is None."""
        cycle = 0
        while num_cycles is None or cycle < num_cycles:
            active = await self._select_active_group()
            if not active:
                await asyncio.sleep(self.signal_read_interval)
                continue
            cycle += 1
            self.logger.info("============================================================")
            self.logger.info("# CYCLE %s (%s)", cycle, active)
            self.logger.info("============================================================")
            await self._run_cycle_with_recovery(active)
            self.logger.info("Cycle %s complete", cycle)
            await asyncio.sleep(self.inter_cycle_delay)

    async def _run_cycle_with_recovery(self, active: str) -> None:
        """Run a cycle for the active group with error handling."""
        steps = self.operation_groups[active]
        for index, step in enumerate(steps, start=1):
            current_active = await self._select_active_group()
            if current_active != active:
                self.logger.info(
                    "Control trigger changed (%s → %s). Stopping cycle.",
                    active,
                    current_active,
                )
                return
            try:
                await self._run_operation(index, len(steps), step, active)
            except NodeNotFoundError as exc:
                self.logger.error("Skipping operation: %s", exc)
                continue
            except OperationStoppedError:
                self.logger.info("Control %s turned off. Stopping cycle.", active)
                return
            except asyncio.TimeoutError as exc:
                self.logger.error("Operation timeout: %s", exc)
                continue
            except Exception as exc:  # noqa: BLE001
                self.logger.error("Unexpected error: %s", exc)
                continue

    async def _run_operation(
        self,
        index: int,
        total: int,
        step: OperationStep,
        active_control: str,
    ) -> None:
        """Execute a single step with proper feedback handling."""
        self.logger.info("[STEP %s/%s] %s", index, total, step.name)

        # Handle stale feedback before starting
        feedback_value = await self.read_feedback(step.feedback)
        if feedback_value:
            self.logger.warning(
                "Feedback %s already TRUE. Waiting for reset...",
                step.feedback,
            )
            await self._wait_for_feedback_with_control(
                step.feedback,
                False,
                self.feedback_reset_timeout,
                active_control,
            )

        # Trigger ON
        self.logger.info("→ Turning ON %s", step.trigger)
        await self.set_trigger(step.trigger, True)

        # Wait for feedback TRUE
        self.logger.info("⏳ Waiting for %s to go TRUE...", step.feedback)
        try:
            await self._wait_for_feedback_with_control(
                step.feedback,
                True,
                step.timeout,
                active_control,
            )
        except OperationStoppedError:
            self.logger.info("Control %s turned off. Stopping operation.", active_control)
            await self.set_trigger(step.trigger, False)
            raise
        self.logger.info("✅ %s = TRUE (Operation Complete)", step.feedback)

        # Trigger OFF
        self.logger.info("→ Turning OFF %s", step.trigger)
        await self.set_trigger(step.trigger, False)

        # Wait for feedback FALSE (reset)
        self.logger.info("⏳ Waiting for %s to go FALSE (reset)...", step.feedback)
        await self._wait_for_feedback_with_control(
            step.feedback,
            False,
            self.feedback_reset_timeout,
            active_control,
        )
        self.logger.info("✅ %s = FALSE (Ready for next) ", step.feedback)

        # Inter-operation delay
        self.logger.info("→ Waiting %.1f seconds before next operation...", self.inter_operation_delay)
        await asyncio.sleep(self.inter_operation_delay)


# ============================
# Entry Point
# ============================
async def main() -> None:
    """Main async entry point for the sequencer."""
    parser = argparse.ArgumentParser(description="OPC UA Operation Sequencer")
    parser.add_argument("--url", default=OPC_SERVER, help="OPC UA server URL")
    parser.add_argument("--cycles", type=int, default=None, help="Number of cycles (omit for infinite)")
    parser.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without writing triggers")
    args = parser.parse_args()

    # Convert operation group dicts to dataclass instances
    operation_groups = {
        group_name: [
            OperationStep(
                name=step["name"],
                trigger=step["trigger"],
                feedback=step["feedback"],
                timeout=OPERATION_TIMEOUT,
            )
            for step in steps
        ]
        for group_name, steps in OPERATION_GROUPS.items()
    }

    sequencer = OperationSequencer(
        opc_url=args.url,
        operation_groups=operation_groups,
        control_triggers=CONTROL_TRIGGERS,
        signal_read_interval=SIGNAL_READ_INTERVAL,
        operation_timeout=OPERATION_TIMEOUT,
        feedback_reset_timeout=FEEDBACK_RESET_TIMEOUT,
        inter_operation_delay=INTER_OPERATION_DELAY,
        inter_cycle_delay=INTER_CYCLE_DELAY,
        dry_run=args.dry_run,
    )

    try:
        await sequencer.connect()
        if args.once:
            await sequencer.run_single_cycle()
        else:
            await sequencer.run_continuous_loop(args.cycles)
    except KeyboardInterrupt:
        sequencer.logger.warning("Interrupted by user")
    finally:
        await sequencer.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
