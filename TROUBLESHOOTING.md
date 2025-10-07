# SlyWriter Troubleshooting Guide

This guide covers common issues and their solutions.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Backend Server Issues](#backend-server-issues)
- [Hotkey Issues](#hotkey-issues)
- [Typing Issues](#typing-issues)
- [Update Issues](#update-issues)
- [Performance Issues](#performance-issues)
- [Getting Help](#getting-help)

---

## Installation Issues

### Windows SmartScreen Warning

**Problem**: "Windows protected your PC" message appears

**Solution**:
1. Click "More info"
2. Click "Run anyway"
3. This happens because the app isn't code-signed yet (coming soon)

### Antivirus Blocks Installation

**Problem**: Antivirus software blocks or deletes the installer

**Solution**:
1. Temporarily disable antivirus
2. Add SlyWriter to exceptions/whitelist
3. Re-enable antivirus after installation
4. Common paths to whitelist:
   - `C:\Users\<username>\AppData\Local\Programs\SlyWriter\`
   - `%APPDATA%\slywriter-desktop\`

### Installation Fails Midway

**Problem**: Installer crashes or shows error

**Solution**:
1. Close all SlyWriter processes in Task Manager
2. Delete `%APPDATA%\slywriter-desktop\` folder
3. Run installer as Administrator (right-click → Run as administrator)
4. Make sure you have at least 500MB free space

---

## Backend Server Issues

### "Backend server failed to start"

**Problem**: Splash screen shows "ERROR: Backend server failed to start"

**Solutions**:

1. **Check Firewall**:
   - Add exception for `SlyWriter.exe`
   - Allow connections on port 8000
   - Windows Defender: Settings → Firewall → Allow an app

2. **Check Port Availability**:
   ```cmd
   netstat -ano | findstr :8000
   ```
   - If port 8000 is in use, close the conflicting application
   - Common culprits: Other dev servers, WAMP, XAMPP

3. **Retry Setup**:
   - Click "↻ Retry Setup" button on error screen
   - If problem persists, delete `%APPDATA%\slywriter-desktop\python-embed\`
   - Restart app to re-download Python

4. **Check Logs**:
   - Click "Copy Logs" button on error screen
   - Send logs to support@slywriterapp.com

### Python Download Fails

**Problem**: "Failed to download Python" or timeout errors

**Solution**:
1. Check internet connection
2. Temporarily disable proxy/VPN
3. Check firewall isn't blocking downloads
4. Download Python manually:
   - Get from: https://www.python.org/ftp/python/3.11.7/python-3.11.7-embed-amd64.zip
   - Extract to: `%APPDATA%\slywriter-desktop\python-embed\`
   - Restart app

### Package Installation Fails

**Problem**: "Failed to install <package>" errors

**Solution**:
1. Check internet connection
2. Delete `%APPDATA%\slywriter-desktop\python-embed\` folder
3. Restart app to reinstall fresh
4. If specific package fails:
   ```cmd
   cd %APPDATA%\slywriter-desktop\python-embed
   python.exe -m pip install --no-cache-dir <package-name>
   ```

### Backend Starts But Can't Connect

**Problem**: Backend shows "running on port 8000" but app can't connect

**Solution**:
1. Check Windows Firewall
2. Try accessing manually: http://localhost:8000/docs
3. If docs load, check app logs
4. Restart app

---

## Hotkey Issues

### Hotkeys Don't Work

**Problem**: Pressing hotkeys does nothing

**Solutions**:

1. **Run as Administrator**:
   - Right-click SlyWriter icon
   - Select "Run as administrator"
   - Global hotkeys need admin rights on some systems

2. **Check for Conflicts**:
   - Other apps may be using the same hotkeys
   - Change hotkeys in Settings → Hotkeys
   - Test with different combinations

3. **Restart App**:
   - Close SlyWriter completely (check Task Manager)
   - Restart the app
   - Hotkeys re-register on startup

### Hotkey Fires in Wrong App

**Problem**: Hotkey triggers in SlyWriter window instead of target app

**Solution**:
1. Click in target text field first
2. Ensure target app has focus (click its window)
3. Wait 1 second before pressing hotkey
4. Some apps (like Electron apps) may block global hotkeys

### Can't Change Hotkeys

**Problem**: Hotkey recording doesn't work

**Solution**:
1. Click "Record" button
2. Press desired key combination **once**
3. Wait for confirmation
4. If it doesn't register, try simpler combinations (avoid F-keys with some keyboards)

---

## Typing Issues

### Typing Doesn't Start

**Problem**: Press Ctrl+T but nothing types

**Solutions**:

1. **Check Text is Loaded**:
   - Verify text is in the typing box
   - Text must not be empty

2. **Check Target Field**:
   - Click in the text field where you want to type
   - Field must accept keyboard input
   - Some protected fields may block automation

3. **Check Backend Status**:
   - Overlay should show "Ready" status
   - If not, backend may not be running
   - Restart app

4. **Run as Administrator**:
   - Some apps require admin rights for keyboard automation
   - Right-click → Run as administrator

### Typing is Too Fast/Slow

**Problem**: Typing speed doesn't match settings

**Solution**:
1. Go to Settings → Typing
2. Adjust "Base Delay" (milliseconds between keystrokes)
3. Adjust "Variation" for more human-like delays
4. Test in a text editor

### Typing Produces Wrong Characters

**Problem**: Characters are incorrect or missing

**Solution**:
1. Check keyboard layout matches target app
2. Ensure target app isn't in a special input mode
3. Try with simple text field first (Notepad)
4. Some special characters may not work in all apps

### Typing Stops Midway

**Problem**: Typing stops before finishing

**Solution**:
1. Check if you pressed Ctrl+Alt+Q (stop hotkey)
2. Check backend logs for errors
3. Target app may have stolen focus
4. App may have input length limits

---

## Update Issues

### Update Check Fails

**Problem**: "Failed to check for updates" error

**Solution**:
1. Check internet connection
2. Check firewall isn't blocking GitHub
3. Update manually:
   - Visit https://github.com/slywriterapp/slywriterapp/releases/latest
   - Download latest installer
   - Run to update

### Update Download Fails

**Problem**: Update downloads but won't install

**Solution**:
1. Close SlyWriter completely
2. Check Task Manager for lingering processes
3. Download installer manually (see above)
4. Run installer

### App Won't Start After Update

**Problem**: App crashes or won't open after updating

**Solution**:
1. Check if processes are stuck in Task Manager
2. Delete `%APPDATA%\slywriter-desktop\` folder (**warning**: loses settings)
3. Reinstall fresh from latest release
4. Contact support if issue persists

---

## Performance Issues

### High CPU Usage

**Problem**: SlyWriter uses excessive CPU

**Causes**:
- Overlay update loops
- Backend processing
- Multiple processes running

**Solutions**:
1. Close overlay if not needed (Ctrl+Alt+O)
2. Check Task Manager for multiple SlyWriter processes
3. Kill extra processes
4. Restart app

### High Memory Usage

**Problem**: SlyWriter uses too much RAM

**Solution**:
1. Normal usage: 150-300MB
2. If >500MB, restart app
3. Check for memory leaks (report to support)
4. Close and reopen overlay

### App is Slow/Laggy

**Problem**: UI is unresponsive

**Solution**:
1. Close other heavy applications
2. Ensure 4GB+ RAM available
3. Restart app
4. Check backend status (should be running)

---

## Getting Help

### Before Contacting Support

1. **Collect Information**:
   - App version (shown in splash screen)
   - Windows version (Settings → System → About)
   - Error message (screenshot or copy)
   - Steps to reproduce

2. **Copy Logs**:
   - Click "Copy Logs" button if error screen shows it
   - Or locate: `%APPDATA%\slywriter-desktop\logs\`
   - Include in support email

3. **Try Safe Mode**:
   - Close all other applications
   - Disable antivirus temporarily
   - Run SlyWriter as Administrator
   - Test if issue persists

### Contact Support

- **Email**: support@slywriterapp.com
- **GitHub Issues**: https://github.com/slywriterapp/slywriterapp/issues
- **Include**:
  - App version
  - Windows version
  - Error logs
  - Steps to reproduce
  - What you've already tried

---

## Advanced Troubleshooting

### Clean Reinstall

If nothing else works, perform a clean reinstall:

1. **Uninstall**:
   - Settings → Apps → SlyWriter → Uninstall
   - OR run `%LOCALAPPDATA%\Programs\SlyWriter\Uninstall SlyWriter.exe`

2. **Clean App Data**:
   ```cmd
   rmdir /s /q "%APPDATA%\slywriter-desktop"
   rmdir /s /q "%LOCALAPPDATA%\Programs\SlyWriter"
   ```

3. **Kill Processes**:
   - Open Task Manager
   - End all `SlyWriter.exe` and `python.exe` (from SlyWriter) processes

4. **Reinstall**:
   - Download latest installer
   - Run as Administrator
   - Follow setup wizard

### Manual Backend Start (Debugging)

To test backend separately:

```cmd
cd %APPDATA%\slywriter-desktop\python-embed
python.exe -m uvicorn backend_api:app --host 0.0.0.0 --port 8000
```

If this works but app doesn't, it's an Electron issue. Report to support.

### Check File Integrity

Verify installation files exist:

**Required Files**:
- `%LOCALAPPDATA%\Programs\SlyWriter\SlyWriter.exe`
- `%LOCALAPPDATA%\Programs\SlyWriter\resources\backend_api.py`
- `%APPDATA%\slywriter-desktop\python-embed\python.exe` (after first run)

If any are missing, reinstall.

---

## Known Issues

### Windows 11 22H2 Hotkey Delay

**Issue**: Hotkeys work but have 1-2 second delay

**Workaround**:
- Update to Windows 11 23H2 or later
- OR use alternative hotkey combinations
- Microsoft is aware of this issue

### Typing in Certain Apps

**Issue**: Typing doesn't work in specific applications

**Workaround**:
- Run both SlyWriter and target app as Administrator
- Some apps with elevated privileges block automation
- Try paste mode instead of typing mode (coming soon)

---

**Last Updated**: 2025-01-07
**App Version**: 2.4.7
