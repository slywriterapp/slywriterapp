# SlyWriter - AI-Powered Typing Automation

**Version 2.4.7** | Windows Desktop Application

SlyWriter is a premium AI typing assistant that simulates human-like typing with realistic delays, typos, and pausing patterns to avoid detection by anti-automation systems.

## Features

- ✨ **AI-Powered Text Generation** - Generate contextual text using OpenAI
- ⌨️ **Human-Like Typing** - Realistic delays, typos, and corrections
- 🎯 **Global Hotkeys** - Control typing from anywhere
- 👁️ **Overlay UI** - See typing status in real-time
- 🔄 **Auto-Update** - Automatic updates to the latest version
- 🐍 **Bundled Python** - No manual Python installation required

## Installation

### Windows 10/11

1. **Download** the latest release:
   - Go to [Releases](https://github.com/slywriterapp/slywriterapp/releases/latest)
   - Download `SlyWriter-Setup-x.x.x.exe`

2. **Run the installer**:
   - Double-click the downloaded file
   - Follow the installation wizard
   - Choose installation directory (default: `C:\Users\<username>\AppData\Local\Programs\SlyWriter`)

3. **First Launch**:
   - The app will automatically download Python (~30MB)
   - Install required packages (~1-2 minutes)
   - Start the backend server
   - Show the login screen

4. **Login**:
   - Sign in with your SlyWriter account
   - Or create a new account at [slywriterapp.com](https://slywriterapp.onrender.com)

## Quick Start

### 1. Basic Typing

1. Open any text field (Word, Google Docs, email, etc.)
2. Press **Ctrl+T** to start typing
3. Press **Ctrl+Alt+Q** to stop
4. Press **Ctrl+Alt+P** to pause/resume

### 2. AI Text Generation

1. Press **Ctrl+Alt+G** to open AI generation
2. Enter your prompt
3. Review and approve the generated text
4. Text will be typed automatically

### 3. Overlay

Press **Ctrl+Alt+O** to show/hide the status overlay

## Default Hotkeys

| Hotkey | Action |
|--------|--------|
| `Ctrl+T` | Start typing |
| `Ctrl+Alt+Q` | Stop typing |
| `Ctrl+Alt+P` | Pause/Resume typing |
| `Ctrl+Alt+O` | Toggle overlay |
| `Ctrl+Alt+G` | AI text generation |

**Customize hotkeys** in the app settings.

## System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 2GB minimum, 4GB recommended
- **Disk Space**: 500MB for app + Python + dependencies
- **Internet**: Required for initial setup and AI features

## Configuration

### User Data Location

- **Config**: `%APPDATA%\slywriter-desktop\`
- **Logs**: `%APPDATA%\slywriter-desktop\logs\`
- **Python**: `%APPDATA%\slywriter-desktop\python-embed\`

### Settings

Access settings in the app:
- **Typing**: Speed, delay patterns, typo frequency
- **Hotkeys**: Customize keyboard shortcuts
- **Account**: Manage subscription and usage
- **Overlay**: Position and appearance

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.

**Quick Fixes:**

- **Backend won't start?** → Check firewall settings, restart app
- **Hotkeys not working?** → Run as administrator
- **Update fails?** → Download installer manually from releases

## Support

- **Issues**: [GitHub Issues](https://github.com/slywriterapp/slywriterapp/issues)
- **Email**: support@slywriterapp.com
- **Documentation**: [HOTKEYS.md](./HOTKEYS.md) | [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## License

Proprietary - See [LICENSE](./LICENSE) for details

## Credits

Built with:
- [Electron](https://www.electronjs.org/) - Desktop framework
- [FastAPI](https://fastapi.tiangolo.com/) - Backend API
- [OpenAI](https://openai.com/) - AI text generation
- [Python 3.11](https://www.python.org/) - Backend runtime

---

**© 2025 SlyWriter. All rights reserved.**
