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
        StringBuilder info = new StringBuilder();
        info.AppendLine("=== ASSIGN STARTING SIGNALS ONLY ===");
        info.AppendLine();
        
        try
        {
            // [operation_name, starting_signal]
            string[][] assignments = new string[][]
            {
                new string[] { "Feedback.Gen_Rob_Op_Sauggreifer", "Trigger.Op1Start" },
                new string[] { "Feedback.Gen_Rob_Op_Lukas_LSI_600_APP_HL", "Trigger.Op2Start" },
                new string[] { "Feedback.Gen_Rob_Op_Lukas_LSI_600_CUT_HL", "Trigger.Op3Start" },
                new string[] { "Feedback.Gen_Rob_Op_Lukas_LSI_600_APP_HR", "Trigger.Op4Start" },
                new string[] { "Feedback.Gen_Rob_Op_Lukas_LSI_600_CUT_HR", "Trigger.Op5Start" },
                new string[] { "Feedback.Gen_Rob_Op_Lukas_LSI_600_DEP_HR", "Trigger.Op6Start" }
            };
            
            TxTypeFilter opFilter = new TxTypeFilter(typeof(ITxOperation));
            TxObjectList allOps = TxApplication.ActiveDocument.OperationRoot.GetAllDescendants(opFilter);
            
            int successCount = 0;
            
            foreach (string[] assignment in assignments)
            {
                string opName = assignment[0];
                string startSigName = assignment[1];
                
                info.AppendLine("Operation: " + opName);
                
                // Find operation
                ITxOperation targetOp = null;
                foreach (ITxObject obj in allOps)
                {
                    if (obj.Name == opName)
                    {
                        targetOp = obj as ITxOperation;
                        break;
                    }
                }
                
                if (targetOp == null)
                {
                    info.AppendLine("  X Operation not found!");
                    info.AppendLine();
                    continue;
                }
                
                // Assign StartingSignal
                TxObjectList startSigs = TxApplication.ActiveDocument.GetObjectsByName(startSigName);
                if (startSigs != null && startSigs.Count > 0)
                {
                    PropertyInfo startProp = targetOp.GetType().GetProperty("StartingSignal");
                    if (startProp != null && startProp.CanWrite)
                    {
                        try
                        {
                            startProp.SetValue(targetOp, startSigs[0], null);
                            info.AppendLine("  OK StartingSignal -> " + startSigName);
                            successCount++;
                        }
                        catch (Exception ex)
                        {
                            info.AppendLine("  X Error: " + ex.Message);
                        }
                    }
                    else
                    {
                        info.AppendLine("  X StartingSignal property not available");
                    }
                }
                else
                {
                    info.AppendLine("  X Signal not found: " + startSigName);
                }
                
                info.AppendLine();
            }
            
            info.AppendLine("========================================");
            info.AppendLine("Successfully assigned: " + successCount + " / " + assignments.Length);
            info.AppendLine();
            
            if (successCount == assignments.Length)
            {
                info.AppendLine("SUCCESS! All StartingSignals assigned!");
            }
            else
            {
                info.AppendLine("Check errors above");
            }
            
        }
        catch (Exception ex)
        {
            info.AppendLine("ERROR: " + ex.Message);
            info.AppendLine(ex.StackTrace);
        }
        
        TxMessageBox.Show(info.ToString(), "Assign StartingSignals", 
            MessageBoxButtons.OK, MessageBoxIcon.Information);
    }
    
    public static void MainWithOutput(ref StringWriter output)
    {
        output.Write("Assigns Trigger.OpXStart as StartingSignal for each operation.");
    }
}
