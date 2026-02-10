using System;
using System.IO;
using System.Text;
using System.Windows.Forms;
using System.Reflection;
using Tecnomatix.Engineering;

public class MainScript
{
    public static void Main()
    {
        string[] signalNames = { 
            "PS.Robot1.j1", "PS.Robot1.j2", "PS.Robot1.j3", "PS.Robot1.j4", "PS.Robot1.j5", "PS.Robot1.j6",
            "PS.Robot2.j1", "PS.Robot2.j2", "PS.Robot2.j3", "PS.Robot2.j4", "PS.Robot2.j5", "PS.Robot2.j6",
            "PS.Robot3.j1", "PS.Robot3.j2", "PS.Robot3.j3", "PS.Robot3.j4", "PS.Robot3.j5", "PS.Robot3.j6"
        };
        
        StringBuilder info = new StringBuilder();
        info.AppendLine("=== EXTERNAL CONNECTION VERIFICATION ===");
        info.AppendLine();
        
        int assignedCount = 0;
        int connectedCount = 0;
        
        foreach (string name in signalNames)
        {
            TxObjectList signals = TxApplication.ActiveDocument.GetObjectsByName(name);
            if (signals == null || signals.Count == 0)
            {
                info.AppendLine("? " + name + ": NOT FOUND");
                continue;
            }
                
            object signal = signals[0];
            
            // Get connection properties
            PropertyInfo opcProp = signal.GetType().GetProperty("OpcConnection");
            PropertyInfo extProp = signal.GetType().GetProperty("ExternalConnection");
            PropertyInfo exitProp = signal.GetType().GetProperty("IsConnectedToLBExit");
            PropertyInfo entryProp = signal.GetType().GetProperty("IsConnectedToLBEntry");
            
            string opcVal = (opcProp != null) ? (opcProp.GetValue(signal, null) as string) : "";
            string extVal = (extProp != null) ? (extProp.GetValue(signal, null) as string) : "";
            
            bool exitConn = false;
            bool entryConn = false;
            
            if (exitProp != null)
            {
                try { exitConn = (bool)exitProp.GetValue(signal, null); } catch { }
            }
            
            if (entryProp != null)
            {
                try { entryConn = (bool)entryProp.GetValue(signal, null); } catch { }
            }
            
            // Check assignment
            bool isAssigned = (opcVal == "Test123" || extVal == "Test123");
            bool isConnected = (exitConn || entryConn);
            
            if (isAssigned)
            {
                assignedCount++;
                if (isConnected)
                {
                    connectedCount++;
                    info.AppendLine("?? " + name + " [ASSIGNED & CONNECTED]");
                }
                else
                {
                    info.AppendLine("?  " + name + " [ASSIGNED, waiting for connection]");
                }
            }
            else
            {
                info.AppendLine("?  " + name + " [NOT ASSIGNED]");
            }
        }
        
        info.AppendLine();
        info.AppendLine("=== SUMMARY ===");
        info.AppendLine("Signals assigned: " + assignedCount + " / 18");
        info.AppendLine("Signals connected: " + connectedCount + " / 18");
        info.AppendLine();
        
        if (assignedCount == 18 && connectedCount == 18)
        {
            info.AppendLine("?? PERFECT! All signals assigned AND connected!");
            info.AppendLine();
            info.AppendLine("Ready to stream robot joints to OPC UA!");
        }
        else if (assignedCount == 18 && connectedCount == 0)
        {
            info.AppendLine("? All signals assigned to Test123");
            info.AppendLine("? Connection not active yet");
            info.AppendLine();
            info.AppendLine("TO ACTIVATE CONNECTION:");
            info.AppendLine("1. Modeling ? Connectivity ? External Connection");
            info.AppendLine("2. Find 'Test123' connection");
            info.AppendLine("3. Click 'Connect' or 'Start' button");
            info.AppendLine("4. Or restart simulation");
        }
        else if (assignedCount < 18)
        {
            info.AppendLine("? Some signals not assigned. Run batch assign again.");
        }
        
        TxMessageBox.Show(info.ToString(), "Connection Verification", MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    public static void MainWithOutput(ref StringWriter output)
    {
        output.Write("Verifies external connection assignment and status.");
    }
}
