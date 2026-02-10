using System;
using System.IO;
using System.Text;
using System.Windows.Forms;
using System.Reflection;
using Tecnomatix.Engineering;

public class MainScript
{
    private static TxRobot[] _robots;
    private static TxPlcInputSignal[] _jointSignals;

    private static PropertyInfo _jointValueProp;
    private static PropertyInfo _jointRealValueProp;

    private static Timer _timer;

    // 3 robots * 6 joints
    private static string[] _jointSignalNames = {
        "PS.Robot1.j1", "PS.Robot1.j2", "PS.Robot1.j3", "PS.Robot1.j4", "PS.Robot1.j5", "PS.Robot1.j6",
        "PS.Robot2.j1", "PS.Robot2.j2", "PS.Robot2.j3", "PS.Robot2.j4", "PS.Robot2.j5", "PS.Robot2.j6",
        "PS.Robot3.j1", "PS.Robot3.j2", "PS.Robot3.j3", "PS.Robot3.j4", "PS.Robot3.j5", "PS.Robot3.j6"
    };

    public static void Main()
    {
        // Toggle start/stop
        if (_timer != null)
        {
            _timer.Stop();
            _timer.Dispose();
            _timer = null;

            _robots = null;
            _jointSignals = null;
            _jointValueProp = null;
            _jointRealValueProp = null;

            TxMessageBox.Show("STOPPED joint broadcasting", "Joint Streamer",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        StartBroadcastingJointsOnly();
    }

    private static void StartBroadcastingJointsOnly()
    {
        // Find up to 3 robots
        TxTypeFilter robotFilter = new TxTypeFilter(typeof(TxRobot));
        TxObjectList allRobots = TxApplication.ActiveDocument.PhysicalRoot.GetAllDescendants(robotFilter);

        if (allRobots == null || allRobots.Count == 0)
        {
            TxMessageBox.Show("No robots found!", "Error",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        int robotCount = Math.Min(3, allRobots.Count);
        _robots = new TxRobot[robotCount];
        for (int i = 0; i < robotCount; i++)
            _robots[i] = allRobots[i] as TxRobot;

        // Load joint signals (only as many as we need for found robots)
        int neededSignals = robotCount * 6;
        _jointSignals = new TxPlcInputSignal[neededSignals];

        int foundJoints = 0;
        for (int i = 0; i < neededSignals && i < _jointSignalNames.Length; i++)
        {
            TxObjectList list = TxApplication.ActiveDocument.GetObjectsByName(_jointSignalNames[i]);
            if (list != null && list.Count > 0)
            {
                _jointSignals[i] = list[0] as TxPlcInputSignal;
                if (_jointSignals[i] != null) foundJoints++;
            }
        }

        // Cache Value.RealValue setters from the first valid signal
        for (int i = 0; i < _jointSignals.Length; i++)
        {
            if (_jointSignals[i] == null) continue;

            _jointValueProp = _jointSignals[i].GetType().GetProperty("Value");
            if (_jointValueProp == null) continue;

            object plcVal = _jointValueProp.GetValue(_jointSignals[i], null);
            if (plcVal == null) continue;

            _jointRealValueProp = plcVal.GetType().GetProperty("RealValue");
            if (_jointRealValueProp == null) continue;

            break;
        }

        if (_jointValueProp == null || _jointRealValueProp == null)
        {
            TxMessageBox.Show("Could not access Value.RealValue on joint signals.", "Error",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        _timer = new Timer();
        _timer.Interval = 1; // 200 Hz
        _timer.Tick += OnTick;
        _timer.Start();

        StringBuilder msg = new StringBuilder();
        msg.AppendLine("JOINT BROADCASTING ACTIVE");
        msg.AppendLine();
        msg.AppendLine("Robots: " + robotCount);
        msg.AppendLine("Joint signals found: " + foundJoints + " / " + neededSignals);
        msg.AppendLine("Rate: 200 Hz (5ms)");
        msg.AppendLine();
        msg.AppendLine("Run script again to STOP.");

        TxMessageBox.Show(msg.ToString(), "Joint Streamer",
            MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    private static void OnTick(object sender, EventArgs e)
    {
        try
        {
            int jointIdx = 0;

            for (int r = 0; r < _robots.Length; r++)
            {
                TxRobot robot = _robots[r];
                if (robot == null) { jointIdx += 6; continue; }

                for (int j = 0; j < 6; j++)
                {
                    if (jointIdx >= _jointSignals.Length) return;

                    TxPlcInputSignal sig = _jointSignals[jointIdx];
                    if (sig != null)
                    {
                        // PS joint is in radians -> convert to degrees
                        double deg = robot.Joints[j].CurrentValue * 180.0 / Math.PI;

                        object plcVal = _jointValueProp.GetValue(sig, null);
                        if (plcVal != null)
                        {
                            _jointRealValueProp.SetValue(plcVal, (float)deg, null);
                            _jointValueProp.SetValue(sig, plcVal, null);
                        }
                    }

                    jointIdx++;
                }
            }
        }
        catch
        {
            // silent (keeps UI responsive)
        }
    }

    public static void MainWithOutput(ref StringWriter output)
    {
        output.Write("Streams TxRobot joint angles into PS.RobotX.jY TxPlcInputSignals.");
    }
}
