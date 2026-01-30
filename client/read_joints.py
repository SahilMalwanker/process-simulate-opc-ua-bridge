"""Fast OPC UA joint reader for Robot1..Robot3.

Reads all joints (j1..j6) for three robots as quickly as possible.
Uses asyncua and batched reads to minimize overhead.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time
from typing import List

from asyncua import Client

OPC_SERVER = "opc.tcp://127.0.0.1:4841"
DEFAULT_INTERVAL = 0.05  # seconds; set to 0 for max speed


def build_joint_node_ids() -> List[str]:
    """Return NodeId strings for Robot1..Robot3 joints j1..j6."""
    node_ids: List[str] = []
    for robot_index in range(1, 4):
        for joint_index in range(1, 7):
            node_ids.append(f"ns=1;s=PS.Robot{robot_index}.j{joint_index}")
    return node_ids


async def read_loop(url: str, interval: float, once: bool) -> None:
    """Continuously read joint values with minimal delay."""
    node_ids = build_joint_node_ids()
    async with Client(url=url) as client:
        nodes = [client.get_node(node_id) for node_id in node_ids]

        while True:
            start = time.perf_counter()
            values = await client.read_values(nodes)
            elapsed_ms = (time.perf_counter() - start) * 1000.0

            # Print line-by-line for readability
            def chunk(values_list: List[float], size: int) -> List[List[float]]:
                return [values_list[i : i + size] for i in range(0, len(values_list), size)]

            r1, r2, r3 = chunk(values, 6)
            line = (
                f"{elapsed_ms:.2f} ms | "
                + "R1:" + " ".join(f"j{i+1}={v:.3f}" for i, v in enumerate(r1))
                + " | R2:" + " ".join(f"j{i+1}={v:.3f}" for i, v in enumerate(r2))
                + " | R3:" + " ".join(f"j{i+1}={v:.3f}" for i, v in enumerate(r3))
            )
            print(line, flush=True)

            if once:
                break
            if interval > 0:
                await asyncio.sleep(interval)


async def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="Fast OPC UA joint reader")
    parser.add_argument("--url", default=OPC_SERVER, help="OPC UA server URL")
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL,
        help="Read interval in seconds (0 for max speed)",
    )
    parser.add_argument("--once", action="store_true", help="Read once and exit")
    args = parser.parse_args()

    try:
        await read_loop(args.url, args.interval, args.once)
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    asyncio.run(main())
