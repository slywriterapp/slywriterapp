Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Typing Project\slywriter-electron"
WshShell.Run "cmd /c npm run dev", 0
Set WshShell = Nothing