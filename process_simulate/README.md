# Process Simulate

Process Simulate connects to the OPC UA server as a client through an external connection. Name the signals after the server's NodeIds, for example signal `PS.Robot1.j1` for node `ns=1;s=PS.Robot1.j1`, so each signal maps to one variable.

| Signal type | Direction | Example |
|---|---|---|
| Start signals | server → Process Simulate | `Trigger.Op1_1Start` |
| End signals | Process Simulate → server | `Feedback.Pick_Part_end` |
| Joint angles | Process Simulate → server | `PS.Robot1.j1` … `PS.Robot3.j6` |

## Scripts

Tecnomatix .NET scripts with the standard `MainScript.Main()` entry point. Run them from inside Process Simulate.

| Script | What it does |
|---|---|
| [scripts/BroadcastRobotJoints.cs](scripts/BroadcastRobotJoints.cs) | Toggle. The first run starts a timer that copies the current joint values of up to three robots, converted from radians to degrees, into the signals `PS.Robot1.j1` … `PS.Robot3.j6`. The next run stops it. |
| [scripts/VerifyJointSignalConnections.cs](scripts/VerifyJointSignalConnections.cs) | Checks that the 18 joint signals exist, are assigned to the external connection and are connected, then shows a summary. |
| [scripts/AssignStartingSignals.cs](scripts/AssignStartingSignals.cs) | Sets the *StartingSignal* of each operation listed in its `assignments` table to the matching start signal. |

Notes:

- `BroadcastRobotJoints.cs` takes the first three robots in the order Process Simulate returns them. Robot1 to Robot3 are not matched by name.
- `VerifyJointSignalConnections.cs` expects the external connection to be called `Test123`. Change the name in the script to match yours.
- Edit the `assignments` table in `AssignStartingSignals.cs` before you run it. It still uses the earlier start-signal names `Trigger.Op1Start` … `Trigger.Op6Start`; the server uses `Trigger.Op<g>_<n>Start`.

## Study

Put your Process Simulate study (`.psz`) in `studies/`. Studies often contain proprietary models, so `*.psz` files are git-ignored.

## Typical setup

1. Start the server with `server/run_server.bat`.
2. In the study, point the OPC UA external connection at `opc.tcp://<server-ip>:4841` and map the signals.
3. Run `VerifyJointSignalConnections.cs` to check the joint signals.
4. Run `BroadcastRobotJoints.cs` to start streaming joint values (run it again to stop).
5. Drive operations from the operator panel or the sequencer.
