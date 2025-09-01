' VBScript to create a desktop shortcut for SlyWriter
Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")

' Create shortcut
Set oShellLink = WshShell.CreateShortcut(strDesktop & "\SlyWriter.lnk")
oShellLink.TargetPath = WScript.Arguments(0) & "\SlyWriter.bat"
oShellLink.WindowStyle = 1
oShellLink.IconLocation = WScript.Arguments(0) & "\slywriter-electron\assets\icon.ico"
oShellLink.Description = "SlyWriter - AI Typing Assistant"
oShellLink.WorkingDirectory = WScript.Arguments(0)
oShellLink.Save

MsgBox "Desktop shortcut created successfully!", vbInformation, "SlyWriter"