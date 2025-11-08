# Mac Port Requirements for SlyWriter

## Executive Summary
Before porting SlyWriter to macOS, several technical, legal, and operational requirements must be met. The app currently uses Windows-specific libraries and systems that need cross-platform alternatives.

---

## 1. TECHNICAL REQUIREMENTS

### 1.1 Hardware & Development Tools
- [ ] **Mac hardware** (MacBook, Mac Mini, or iMac) for development and testing
  - Minimum: macOS 11 (Big Sur) or newer
  - Recommended: Latest macOS for development
- [ ] **Xcode** installed (free from Mac App Store)
- [ ] **Command Line Tools** for Xcode
- [ ] **Homebrew** package manager for dependencies

### 1.2 Critical Library Replacements

#### ❌ PROBLEM: `keyboard` library (v0.13.5)
**Current Status**: The `keyboard` library is **primarily Windows-focused** and has limited/broken macOS support.

**Used in files**:
- `typing_engine.py` - Core typing simulation (`keyboard.write()`, `keyboard.send()`)
- `sly_hotkeys.py` - Global hotkey registration (`keyboard.add_hotkey()`)
- `premium_typing.py` - Advanced typing features
- `backend_desktop.py` - Desktop backend integration

**Mac Alternative Options**:

1. **pynput** (RECOMMENDED)
   ```bash
   pip install pynput
   ```
   - ✅ Cross-platform (Windows, Mac, Linux)
   - ✅ Active maintenance
   - ✅ Similar API to keyboard library
   - ✅ Supports keyboard and mouse input/output
   - ⚠️ Requires Accessibility permissions on Mac

   Example replacement:
   ```python
   # OLD (keyboard library)
   import keyboard
   keyboard.write("Hello")
   keyboard.send("backspace")

   # NEW (pynput)
   from pynput.keyboard import Controller, Key
   kb = Controller()
   kb.type("Hello")
   kb.press(Key.backspace)
   kb.release(Key.backspace)
   ```

2. **PyAutoGUI** (ALTERNATIVE)
   ```bash
   pip install pyautogui
   ```
   - ✅ Already in codebase (used in backend)
   - ✅ Cross-platform
   - ⚠️ Slower than pynput
   - ⚠️ Less fine-grained control

**Effort Required**: 🔴 HIGH - Requires refactoring core typing engine

---

### 1.3 macOS Permissions & Security

#### Accessibility Permissions
macOS requires explicit user permission for apps that:
- Simulate keyboard input
- Listen for global hotkeys
- Monitor keystrokes

**Implementation Required**:
1. Add permission requests to app startup
2. Guide users through System Preferences > Security & Privacy > Accessibility
3. Handle permission denial gracefully

#### Code Signing & Notarization
- Mac apps MUST be code-signed to avoid "unidentified developer" warnings
- Notarization required for macOS 10.15+ (Catalina and newer)
- Without this, users get scary security warnings and app may not run

**Requirements**:
- Apple Developer Program membership ($99/year)
- Developer ID certificate
- Notarization process via Apple

---

### 1.4 Python Environment Differences

#### Current: Embedded Python for Windows
- Located in `python-embed/` directory
- Windows-specific binaries

#### Mac Requirements:
1. **Python.org installer** OR **pyinstaller** for bundling
2. Universal binary support (Intel + Apple Silicon)
   - x86_64 for Intel Macs
   - arm64 for M1/M2/M3 Macs
3. Consider creating separate builds or universal binary

**Electron Builder Config Addition**:
```json
"mac": {
  "target": [
    {
      "target": "dmg",
      "arch": ["x64", "arm64"]
    },
    {
      "target": "zip",
      "arch": ["x64", "arm64"]
    }
  ],
  "category": "public.app-category.productivity",
  "hardenedRuntime": true,
  "gatekeeperAssess": false,
  "entitlements": "build/entitlements.mac.plist",
  "entitlementsInherit": "build/entitlements.mac.plist"
}
```

---

### 1.5 File Path & System Differences

#### Path Separators
- Windows: Backslashes `\`
- Mac: Forward slashes `/`

**Fix**: Use Python's `os.path.join()` or `pathlib.Path()` everywhere

#### Application Data Locations
```python
# Windows
config_dir = os.path.join(os.getenv('APPDATA'), 'SlyWriter')

# Mac
config_dir = os.path.join(os.path.expanduser('~/Library/Application Support'), 'SlyWriter')

# Cross-platform solution
import platform
if platform.system() == 'Darwin':  # Mac
    config_dir = os.path.expanduser('~/Library/Application Support/SlyWriter')
elif platform.system() == 'Windows':
    config_dir = os.path.join(os.getenv('APPDATA'), 'SlyWriter')
else:  # Linux
    config_dir = os.path.expanduser('~/.config/slywriter')
```

---

### 1.6 Keyboard Shortcuts

Mac uses different modifier keys:
- Windows: `Ctrl` → Mac: `Cmd` (⌘)
- Windows: `Alt` → Mac: `Option` (⌥)
- Windows: `Win` → Mac: `Cmd` (⌘)

**Current hotkeys** (from `sly_hotkeys.py`):
- Start: `ctrl+alt+s` → Mac: `cmd+option+s`
- Stop: `ctrl+alt+x` → Mac: `cmd+option+x`
- Pause: `ctrl+alt+p` → Mac: `cmd+option+p`
- Overlay: `ctrl+alt+o` → Mac: `cmd+option+o`
- AI Gen: `ctrl+alt+g` → Mac: `cmd+option+g`

**Solution**: Detect platform and auto-adjust hotkeys OR allow users to customize

---

## 2. ELECTRON BUILD CONFIGURATION

### 2.1 Add macOS Target to package.json

Add to `slywriter-electron/package.json`:

```json
{
  "build": {
    "mac": {
      "target": ["dmg", "zip"],
      "category": "public.app-category.productivity",
      "icon": "assets/icon.icns",
      "hardenedRuntime": true,
      "gatekeeperAssess": false,
      "entitlements": "build/entitlements.mac.plist",
      "entitlementsInherit": "build/entitlements.mac.plist",
      "darkModeSupport": true
    },
    "dmg": {
      "contents": [
        {
          "x": 130,
          "y": 220
        },
        {
          "x": 410,
          "y": 220,
          "type": "link",
          "path": "/Applications"
        }
      ],
      "window": {
        "width": 540,
        "height": 380
      }
    }
  }
}
```

### 2.2 Create Mac Entitlements File

Create `slywriter-electron/build/entitlements.mac.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.automation.apple-events</key>
    <true/>
    <key>com.apple.security.device.audio-input</key>
    <false/>
    <key>com.apple.security.device.camera</key>
    <false/>
</dict>
</plist>
```

### 2.3 Icon Conversion

- Current: `icon.ico` (Windows format)
- Need: `icon.icns` (Mac format)

**Tools**:
```bash
# Using Image2icon (Mac app - free)
# OR
# Using iconutil (built-in Mac command)
iconutil -c icns icon.iconset
```

---

## 3. LEGAL & BUSINESS REQUIREMENTS

### 3.1 Apple Developer Program
- **Cost**: $99/year
- **Required for**: Code signing, notarization, App Store distribution (optional)
- **Signup**: https://developer.apple.com/programs/

### 3.2 Age Restrictions
- App is **18+ only** (confirmed in Terms of Service)
- Apple App Store: No age gate enforcement needed (similar to web)
- Distribute via direct download (like Windows) to avoid App Store review delays

### 3.3 Terms & Privacy Policy
- ✅ Already created and comprehensive
- ✅ Cover both platforms
- ⚠️ May need to add Mac-specific permissions disclosure:
  - Accessibility permission usage
  - Keylogging capabilities (typing simulation)

---

## 4. TESTING REQUIREMENTS

### 4.1 Platform Testing Matrix
Test on:
- [ ] macOS 11 Big Sur (Intel)
- [ ] macOS 12 Monterey (Intel)
- [ ] macOS 13 Ventura (Intel & Apple Silicon)
- [ ] macOS 14 Sonoma (Intel & Apple Silicon)
- [ ] macOS 15 Sequoia (latest - if released)

### 4.2 Feature Testing
- [ ] Typing simulation in all major apps (Google Docs, Word, Notes, etc.)
- [ ] Global hotkeys work system-wide
- [ ] Clipboard integration (pyperclip on Mac)
- [ ] AI text generation
- [ ] Humanizer features
- [ ] Referral system
- [ ] Auto-update functionality

### 4.3 Performance Testing
- [ ] Typing speed/latency matches Windows version
- [ ] Memory usage acceptable
- [ ] CPU usage during typing
- [ ] Battery impact on laptops

---

## 5. DISTRIBUTION STRATEGY

### Option A: Direct Download (RECOMMENDED - Same as Windows)
- Host `.dmg` file on GitHub Releases
- Users download and drag to Applications folder
- Requires code signing + notarization

**Pros**:
- Same as current Windows approach
- No App Store review process
- Faster updates
- More control

**Cons**:
- Users must trust "unidentified developer" (mitigated by code signing)
- No App Store discoverability

### Option B: Mac App Store
- Submit to Apple for review
- Stricter guidelines
- 30% revenue cut on subscriptions

**Pros**:
- Built-in distribution
- User trust
- Automatic updates

**Cons**:
- Review delays (1-7 days)
- 30% fee
- Strict sandboxing (may break hotkeys)
- May reject due to "typing automation" concerns

**Recommendation**: Start with **Direct Download**, consider App Store later if demand warrants it.

---

## 6. ESTIMATED DEVELOPMENT EFFORT

| Task | Effort | Priority |
|------|--------|----------|
| Replace `keyboard` library with `pynput` | 3-5 days | 🔴 Critical |
| macOS permissions & security setup | 2-3 days | 🔴 Critical |
| Cross-platform file paths | 1 day | 🟡 High |
| Electron build config for Mac | 1 day | 🟡 High |
| Icon conversion & assets | 0.5 day | 🟢 Medium |
| Apple Developer account setup | 0.5 day | 🟡 High |
| Code signing & notarization | 2-3 days | 🔴 Critical |
| Platform-specific hotkey handling | 1 day | 🟢 Medium |
| Testing on multiple macOS versions | 3-5 days | 🔴 Critical |
| Documentation updates | 1 day | 🟢 Medium |

**Total Estimated Time**: 15-25 days

---

## 7. COST BREAKDOWN

| Item | Cost | Frequency |
|------|------|-----------|
| Apple Developer Program | $99 | Annual |
| Mac hardware (if needed) | $599+ (Mac Mini M2) | One-time |
| Testing devices (optional) | $0-$1000+ | One-time |

**Minimum**: $99/year (if you already have a Mac)
**Typical**: $700-$1200 initial + $99/year

---

## 8. PREREQUISITES CHECKLIST

Before starting Mac port development:

### Business/Legal
- [ ] Apple Developer Program account created ($99)
- [ ] Payment method for annual renewal set up
- [ ] Terms of Service reviewed for Mac compliance
- [ ] Privacy Policy updated with Mac permission disclosures

### Hardware/Software
- [ ] Mac computer available (Intel or Apple Silicon)
- [ ] macOS 11+ installed
- [ ] Xcode installed
- [ ] Homebrew installed
- [ ] Python 3.9+ for Mac installed

### Development
- [ ] Git repository accessible from Mac
- [ ] Development environment set up on Mac
- [ ] Test user accounts created
- [ ] Backend server accessible from Mac for testing

### Design/Assets
- [ ] Mac icon file (.icns) created
- [ ] DMG background image designed (optional)
- [ ] Installer graphics prepared

### Documentation
- [ ] Mac installation guide drafted
- [ ] Mac-specific troubleshooting docs prepared
- [ ] Permission request guide for users created

---

## 9. RECOMMENDED APPROACH

### Phase 1: Proof of Concept (1-2 weeks)
1. Get Mac hardware
2. Set up development environment
3. Replace `keyboard` library with `pynput` in isolated test
4. Build basic Electron app for Mac
5. Test core typing functionality

### Phase 2: Full Port (2-3 weeks)
1. Update all platform-specific code
2. Configure Electron builder for Mac
3. Set up code signing
4. Test on multiple macOS versions
5. Fix bugs and optimize

### Phase 3: Distribution (1 week)
1. Set up notarization
2. Create release process
3. Update website/docs
4. Launch beta test with select users
5. Public release

---

## 10. ALTERNATIVES TO CONSIDER

### Option 1: Web-Only for Mac Users
- Direct Mac users to web version (slywriter.ai)
- Saves development time
- Less maintenance burden
- **Downside**: No system-wide hotkeys, limited OS integration

### Option 2: Progressive Web App (PWA)
- Create installable web app
- Works on Mac, Windows, Linux
- **Downside**: Limited system access, no global hotkeys

### Option 3: Delay Mac Port
- Focus on Windows market first (larger education market in US)
- Gather more resources/users
- Port later when ROI justifies effort

---

## 11. KEY RISKS

| Risk | Impact | Mitigation |
|------|--------|------------|
| Apple rejects app for "cheating tool" | 🔴 High | Use direct download, avoid App Store |
| Accessibility permissions confuse users | 🟡 Medium | Clear onboarding guide with screenshots |
| pynput doesn't match keyboard library behavior | 🔴 High | Thorough testing, fallback options |
| Code signing issues | 🟡 Medium | Follow Apple docs carefully, test early |
| Performance worse than Windows | 🟢 Low | Optimize, use native Mac APIs where needed |
| Hotkeys conflict with Mac system shortcuts | 🟡 Medium | Allow customization, choose safe defaults |

---

## 12. SUCCESS METRICS

Track these after Mac release:
- [ ] Mac downloads vs Windows downloads (target: 20-30% of Windows)
- [ ] Mac user retention rate
- [ ] Mac-specific bug reports (should be <10% of total)
- [ ] Mac user satisfaction (NPS score)
- [ ] Performance parity (typing speed within 5% of Windows)

---

## CONCLUSION

**Mac port is FEASIBLE but requires significant effort.**

**Minimum Requirements to Start**:
1. ✅ $99 Apple Developer account
2. ✅ Mac computer for development
3. ✅ 3-4 weeks dedicated development time
4. ✅ Replace keyboard library with pynput
5. ✅ Set up code signing & notarization

**Recommended Timeline**:
- Start port after reaching 1,000+ Windows users
- Use revenue to fund Mac development
- Launch Mac version as "beta" to test market demand

**Next Steps** (if proceeding):
1. Purchase Apple Developer Program membership
2. Acquire Mac hardware if needed
3. Set up Mac development environment
4. Create proof-of-concept with pynput
5. Decide on distribution strategy
