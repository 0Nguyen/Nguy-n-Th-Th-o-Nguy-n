Dim shell
Dim fso
Dim projectDir
Dim result
Dim command
Dim launcherPath
Dim readyFlagPath
Dim errorFlagPath
Dim pythonFound
Dim pyFound
Dim startTime
Dim timeoutSeconds
Dim flagText
Dim flagStream

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = projectDir
launcherPath = projectDir & "\scripts\launcher_offline.py"
readyFlagPath = projectDir & "\launcher_offline_ready.flag"
errorFlagPath = projectDir & "\launcher_offline_error.flag"
timeoutSeconds = 75

If Not fso.FileExists(launcherPath) Then
    MsgBox "Missing scripts\launcher_offline.py in project folder.", vbCritical, "Over-Ordering Sentinel"
    WScript.Quit 1
End If

If fso.FileExists(readyFlagPath) Then
    fso.DeleteFile readyFlagPath, True
End If

If fso.FileExists(errorFlagPath) Then
    fso.DeleteFile errorFlagPath, True
End If

pythonFound = shell.Run("cmd /c where python >nul 2>nul", 0, True)
pyFound = shell.Run("cmd /c where py >nul 2>nul", 0, True)

If pythonFound = 0 Then
    command = "python -X utf8 """ & launcherPath & """"
    shell.Run command, 0, False
End If

If pythonFound <> 0 And pyFound = 0 Then
    command = "py -X utf8 """ & launcherPath & """"
    shell.Run command, 0, False
End If

If pythonFound <> 0 And pyFound <> 0 Then
    MsgBox "Python is required. Please install Python 3.10+ and add it to PATH.", vbCritical, "Over-Ordering Sentinel"
    WScript.Quit 1
End If

startTime = Timer
Do
    If fso.FileExists(readyFlagPath) Then
        WScript.Quit 0
    End If

    If fso.FileExists(errorFlagPath) Then
        Set flagStream = fso.OpenTextFile(errorFlagPath, 1, False)
        flagText = flagStream.ReadAll
        flagStream.Close

        If Len(Trim(flagText)) = 0 Then
            MsgBox "Launcher failed. See " & projectDir & "\launcher_offline_error.log for details.", vbCritical, "Over-Ordering Sentinel"
        Else
            MsgBox flagText, vbCritical, "Over-Ordering Sentinel"
        End If
        WScript.Quit 1
    End If

    WScript.Sleep 250
Loop While (Timer - startTime + 86400) Mod 86400 < timeoutSeconds

MsgBox "Launcher failed. See " & projectDir & "\launcher_offline_error.log for details.", vbCritical, "Over-Ordering Sentinel"
WScript.Quit 1
