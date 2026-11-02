' BeaconHunt Launcher — double-click to open the GUI with NO console window.
' Tries pythonw first (truly windowless); falls back to python launched hidden.
Option Explicit
Dim sh, fso, here, script, pyw, ok
Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
here   = fso.GetParentFolderName(WScript.ScriptFullName)
script = here & "\beaconhunt_launcher.py"
sh.CurrentDirectory = here

ok = False
On Error Resume Next
' pythonw.exe runs without a console at all.
sh.Run "pythonw.exe """ & script & """", 0, False
If Err.Number = 0 Then ok = True
Err.Clear
If Not ok Then
  ' py launcher (windowless variant)
  sh.Run "pyw.exe """ & script & """", 0, False
  If Err.Number = 0 Then ok = True
  Err.Clear
End If
If Not ok Then
  ' Last resort: python.exe, but hide the window (style 0).
  sh.Run "python.exe """ & script & """", 0, False
End If
On Error GoTo 0
