# Windows App Refactoring Guide
## Preparing for Future Mac Port

**Goal**: Refactor the Windows app NOW to be cross-platform friendly, so when you're ready for Mac, it's a simple implementation swap instead of a complete rewrite.

**Strategy**: Create abstraction layers while only testing on Windows. When Mac time comes, just add Mac implementations.

---

## 🎯 PRIORITY 1: Abstract the Keyboard Library (CRITICAL)

### Problem
The `keyboard` library is used directly in ~20 files. It's Windows-specific and will NOT work on Mac.

### Solution: Create a Typing Abstraction Layer

**Step 1**: Create `platform_keyboard.py`

```python
"""
Cross-platform keyboard input abstraction
Supports both keyboard (Windows) and pynput (Mac/Linux)
"""
import platform
import sys

# Detect platform
IS_WINDOWS = platform.system() == 'Windows'
IS_MAC = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'

# Try to import platform-specific library
if IS_WINDOWS:
    try:
        import keyboard as _kb_win
        BACKEND = 'keyboard'
    except ImportError:
        print("[WARNING] keyboard library not found, falling back to pynput")
        BACKEND = 'pynput'
else:
    # Mac/Linux - must use pynput
    BACKEND = 'pynput'

# Import pynput if needed
if BACKEND == 'pynput':
    try:
        from pynput.keyboard import Controller, Key, Listener, HotKey
        from pynput import keyboard as pynput_kb
        _kb_controller = Controller()
    except ImportError:
        print("[ERROR] Neither keyboard nor pynput available!")
        sys.exit(1)


class KeyboardWrapper:
    """Cross-platform keyboard interface"""

    def __init__(self):
        self.backend = BACKEND
        if self.backend == 'pynput':
            self.controller = _kb_controller

    def write(self, text: str):
        """Type text string"""
        if self.backend == 'keyboard':
            _kb_win.write(text)
        else:
            # pynput
            self.controller.type(text)

    def send(self, key: str):
        """Send special key (backspace, enter, etc.)"""
        if self.backend == 'keyboard':
            _kb_win.send(key)
        else:
            # pynput - map key names
            key_map = {
                'backspace': Key.backspace,
                'enter': Key.enter,
                'tab': Key.tab,
                'space': Key.space,
                'delete': Key.delete,
                'esc': Key.esc,
                'escape': Key.esc,
            }
            pynput_key = key_map.get(key.lower(), key)
            self.controller.press(pynput_key)
            self.controller.release(pynput_key)

    def press(self, key: str):
        """Press key down (without releasing)"""
        if self.backend == 'keyboard':
            _kb_win.press(key)
        else:
            # pynput
            if hasattr(Key, key):
                self.controller.press(getattr(Key, key))
            else:
                self.controller.press(key)

    def release(self, key: str):
        """Release key"""
        if self.backend == 'keyboard':
            _kb_win.release(key)
        else:
            # pynput
            if hasattr(Key, key):
                self.controller.release(getattr(Key, key))
            else:
                self.controller.release(key)


class HotkeyWrapper:
    """Cross-platform global hotkey manager"""

    def __init__(self):
        self.backend = BACKEND
        self.hotkeys = {}  # Store registered hotkeys
        if self.backend == 'pynput':
            self.listener = None
            self.current_keys = set()

    def add_hotkey(self, hotkey_string: str, callback):
        """Register global hotkey"""
        if self.backend == 'keyboard':
            _kb_win.add_hotkey(hotkey_string, callback)
        else:
            # pynput - convert hotkey string to key combination
            # Store for listener
            self.hotkeys[hotkey_string] = callback
            self._restart_listener()

    def remove_hotkey(self, hotkey_string: str):
        """Unregister hotkey"""
        if self.backend == 'keyboard':
            try:
                _kb_win.remove_hotkey(hotkey_string)
            except:
                pass
        else:
            # pynput
            if hotkey_string in self.hotkeys:
                del self.hotkeys[hotkey_string]
                self._restart_listener()

    def unhook_all_hotkeys(self):
        """Remove all hotkeys"""
        if self.backend == 'keyboard':
            _kb_win.unhook_all_hotkeys()
        else:
            # pynput
            self.hotkeys.clear()
            if self.listener:
                self.listener.stop()
                self.listener = None

    def _restart_listener(self):
        """Restart pynput listener with current hotkeys"""
        if self.backend != 'pynput':
            return

        # Stop existing listener
        if self.listener:
            self.listener.stop()

        # Create new listener
        def on_press(key):
            # Track pressed keys
            try:
                self.current_keys.add(key)
            except:
                pass

            # Check if any hotkey matches
            for hotkey_str, callback in self.hotkeys.items():
                if self._check_hotkey_match(hotkey_str):
                    callback()

        def on_release(key):
            # Remove from pressed keys
            try:
                self.current_keys.discard(key)
            except:
                pass

        self.listener = Listener(on_press=on_press, on_release=on_release)
        self.listener.start()

    def _check_hotkey_match(self, hotkey_string: str):
        """Check if current pressed keys match hotkey string"""
        # TODO: Implement proper hotkey matching
        # This is simplified - needs full implementation
        return False

    def parse_hotkey(self, hotkey_string: str):
        """Validate hotkey string format"""
        if self.backend == 'keyboard':
            return _kb_win.parse_hotkey(hotkey_string)
        else:
            # pynput - basic validation
            # TODO: Implement proper parsing
            return hotkey_string


# Singleton instances
_keyboard = KeyboardWrapper()
_hotkey_manager = HotkeyWrapper()


# Public API - drop-in replacement for keyboard library
def write(text: str):
    """Type text string"""
    _keyboard.write(text)

def send(key: str):
    """Send special key"""
    _keyboard.send(key)

def press(key: str):
    """Press key down"""
    _keyboard.press(key)

def release(key: str):
    """Release key"""
    _keyboard.release(key)

def add_hotkey(hotkey_string: str, callback):
    """Register global hotkey"""
    _hotkey_manager.add_hotkey(hotkey_string, callback)

def remove_hotkey(hotkey_string: str):
    """Unregister hotkey"""
    _hotkey_manager.remove_hotkey(hotkey_string)

def unhook_all_hotkeys():
    """Remove all hotkeys"""
    _hotkey_manager.unhook_all_hotkeys()

def parse_hotkey(hotkey_string: str):
    """Validate hotkey string"""
    return _hotkey_manager.parse_hotkey(hotkey_string)
```

**Step 2**: Replace all `import keyboard` with `import platform_keyboard as keyboard`

**Files to update**:
- `typing_engine.py` - Change `import keyboard` → `import platform_keyboard as keyboard`
- `sly_hotkeys.py` - Change `import keyboard` → `import platform_keyboard as keyboard`
- `premium_typing.py` - Same change
- `backend_desktop.py` - Same change
- All other files using `keyboard`

**Step 3**: Test on Windows
- Install pynput: `pip install pynput`
- Test that typing still works
- Test that hotkeys still work
- If issues, fix the abstraction layer

**Step 4**: Add pynput to requirements.txt
```
pynput>=1.7.6  # Cross-platform keyboard/mouse control
```

---

## 🎯 PRIORITY 2: Platform Detection Utility

### Create `platform_utils.py`

```python
"""
Platform detection and utilities
"""
import platform
import os
import sys

# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_MAC = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'

def get_platform():
    """Get current platform name"""
    return platform.system()

def get_app_data_dir(app_name='SlyWriter'):
    """Get platform-specific application data directory"""
    if IS_WINDOWS:
        # Windows: %APPDATA%\SlyWriter
        base = os.getenv('APPDATA')
        if not base:
            base = os.path.expanduser('~\\AppData\\Roaming')
        return os.path.join(base, app_name)

    elif IS_MAC:
        # Mac: ~/Library/Application Support/SlyWriter
        return os.path.expanduser(f'~/Library/Application Support/{app_name}')

    else:
        # Linux: ~/.config/slywriter
        return os.path.expanduser(f'~/.config/{app_name.lower()}')

def get_documents_dir():
    """Get platform-specific documents directory"""
    if IS_WINDOWS:
        # Try to get Documents folder
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
            docs = winreg.QueryValueEx(key, 'Personal')[0]
            winreg.CloseKey(key)
            return docs
        except:
            return os.path.expanduser('~/Documents')

    elif IS_MAC:
        return os.path.expanduser('~/Documents')

    else:
        # Linux
        return os.path.expanduser('~/Documents')

def get_default_hotkeys():
    """Get platform-specific default hotkeys"""
    if IS_MAC:
        # Mac uses Cmd instead of Ctrl
        return {
            'start': 'cmd+option+s',
            'stop': 'cmd+option+x',
            'pause': 'cmd+option+p',
            'overlay': 'cmd+option+o',
            'ai_generation': 'cmd+option+g'
        }
    else:
        # Windows/Linux use Ctrl
        return {
            'start': 'ctrl+alt+s',
            'stop': 'ctrl+alt+x',
            'pause': 'ctrl+alt+p',
            'overlay': 'ctrl+alt+o',
            'ai_generation': 'ctrl+alt+g'
        }

def normalize_path(path):
    """Normalize file path for current platform"""
    return os.path.normpath(path)

def ensure_dir_exists(path):
    """Create directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)
    return path
```

---

## 🎯 PRIORITY 3: Update Config System

### Update `config.py`

**Add platform-aware config directory**:

```python
import os
from platform_utils import get_app_data_dir, ensure_dir_exists

# Base directory - platform-specific
if os.path.exists(os.path.join(os.path.dirname(__file__), 'config.json')):
    # Running from source - use current directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
else:
    # Running from installed app - use app data directory
    BASE_DIR = ensure_dir_exists(get_app_data_dir('SlyWriter'))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LOG_FILE = os.path.join(BASE_DIR, "typing_log.txt")
```

**Update default hotkeys**:

```python
from platform_utils import get_default_hotkeys

DEFAULT_CONFIG = {
    "settings": {
        # ... existing settings ...
        "hotkeys": get_default_hotkeys(),  # Platform-specific defaults
    }
}
```

---

## 🎯 PRIORITY 4: Test pynput on Windows FIRST

### Why?
Validate that pynput works on Windows before Mac development. This catches issues early.

### Testing Plan

**Test 1: Basic Typing**
```python
# test_pynput_windows.py
from pynput.keyboard import Controller, Key
import time

kb = Controller()

print("Testing pynput typing in 3 seconds...")
print("Focus on Notepad or any text editor")
time.sleep(3)

# Test 1: Type text
kb.type("Hello from pynput!")

# Test 2: Backspace
time.sleep(0.5)
for _ in range(5):
    kb.press(Key.backspace)
    kb.release(Key.backspace)
    time.sleep(0.1)

# Test 3: Enter
kb.press(Key.enter)
kb.release(Key.enter)

kb.type("New line!")

print("Test complete!")
```

**Test 2: Typing Speed/Latency**
```python
# test_pynput_speed.py
from pynput.keyboard import Controller
import time

kb = Controller()

print("Testing typing speed in 3 seconds...")
time.sleep(3)

# Type 100 characters and measure time
start = time.time()
test_text = "a" * 100
kb.type(test_text)
elapsed = time.time() - start

print(f"Typed 100 chars in {elapsed:.3f}s")
print(f"Speed: {100/elapsed:.1f} chars/sec")
```

**Test 3: Compare keyboard vs pynput**
```python
# compare_libraries.py
import keyboard
from pynput.keyboard import Controller
import time

kb_pynput = Controller()

print("Comparing keyboard library vs pynput")
print("Focus on text editor in 3 seconds...")
time.sleep(3)

# Test keyboard library
start = time.time()
keyboard.write("keyboard library: Hello World!")
keyboard_time = time.time() - start

keyboard.send('enter')
time.sleep(0.5)

# Test pynput
start = time.time()
kb_pynput.type("pynput library: Hello World!")
pynput_time = time.time() - start

print(f"\nkeyboard: {keyboard_time:.4f}s")
print(f"pynput: {pynput_time:.4f}s")
print(f"Difference: {abs(keyboard_time - pynput_time):.4f}s")
```

**Run tests**:
```bash
pip install pynput
python test_pynput_windows.py
python test_pynput_speed.py
python compare_libraries.py
```

**Expected Results**:
- pynput should work on Windows
- Speed should be comparable to keyboard library
- If slower, quantify the difference (acceptable if <10% slower)

---

## 🎯 PRIORITY 5: Fix All File Paths

### Audit Current Files

**Already Good** ✅:
- `config.py` - Uses `os.path.join()`
- Most core files seem to use proper path handling

**Check for Issues**:
```bash
# Search for hardcoded backslashes in paths
grep -r "\\\\Users" *.py
grep -r "C:\\\\" *.py
grep -r "\\\\AppData" *.py
```

**Replace Pattern**:
```python
# BAD ❌
path = "C:\\Users\\username\\file.txt"
path = folder + "\\subfolder\\file.txt"

# GOOD ✅
path = os.path.join("C:", "Users", "username", "file.txt")
path = os.path.join(folder, "subfolder", "file.txt")

# BETTER ✅ (Python 3.4+)
from pathlib import Path
path = Path.home() / "Documents" / "file.txt"
```

---

## 🎯 PRIORITY 6: Refactor Hotkey System

### Update `sly_hotkeys.py`

**Replace**:
```python
import keyboard
```

**With**:
```python
import platform_keyboard as keyboard
from platform_utils import IS_MAC, IS_WINDOWS
```

**Add platform-aware hotkey display**:
```python
def format_hotkey_for_display(hotkey: str) -> str:
    """Format hotkey string for display (with platform symbols)"""
    if IS_MAC:
        # Replace text with Mac symbols
        hotkey = hotkey.replace('cmd', '⌘')
        hotkey = hotkey.replace('option', '⌥')
        hotkey = hotkey.replace('ctrl', '⌃')
        hotkey = hotkey.replace('shift', '⇧')

    return hotkey.title()
```

---

## 🎯 PRIORITY 7: Version Detection in Main App

### Update `gui_main.py` or `sly_app.py`

**Add platform info to diagnostics**:
```python
import platform
from platform_utils import get_platform, IS_WINDOWS, IS_MAC, IS_LINUX

def show_about_dialog():
    """Show about/version info"""
    platform_name = get_platform()
    python_version = platform.python_version()

    info = f"""
    SlyWriter v{APP_VERSION}

    Platform: {platform_name}
    Python: {python_version}
    Keyboard Backend: {keyboard.BACKEND}

    © 2025 SlyWriter LLC
    """
    # Show in messagebox
```

---

## 🎯 IMPLEMENTATION CHECKLIST

### Phase 1: Create Abstraction Layers (Week 1)
- [ ] Create `platform_utils.py`
- [ ] Create `platform_keyboard.py` with keyboard + pynput support
- [ ] Add pynput to `requirements.txt`
- [ ] Test pynput on Windows

### Phase 2: Update Core Files (Week 2)
- [ ] Update `typing_engine.py` - Use platform_keyboard
- [ ] Update `sly_hotkeys.py` - Use platform_keyboard
- [ ] Update `config.py` - Platform-aware config directory
- [ ] Update `premium_typing.py` - Use platform_keyboard
- [ ] Update `backend_desktop.py` - Use platform_keyboard

### Phase 3: Test Everything on Windows (Week 3)
- [ ] Run full app with pynput backend on Windows
- [ ] Test all typing features
- [ ] Test all hotkeys
- [ ] Test AI generation
- [ ] Test humanizer
- [ ] Performance testing
- [ ] Fix any issues found

### Phase 4: Deploy to Windows Users (Week 4)
- [ ] Build new Windows installer with cross-platform code
- [ ] Beta test with 10-20 users
- [ ] Monitor for issues
- [ ] Collect feedback on performance
- [ ] Fix any regression bugs

### Phase 5: Mac Port (Future - When Ready)
- [ ] Get Mac hardware
- [ ] Test on Mac
- [ ] Fix Mac-specific issues
- [ ] Build Mac installer
- [ ] Release Mac beta

---

## ⚠️ TESTING REQUIREMENTS

### Test Matrix

| Feature | keyboard lib | pynput | Status |
|---------|-------------|--------|--------|
| Basic typing | ✅ Works | ⏳ Test | Pending |
| Typos/corrections | ✅ Works | ⏳ Test | Pending |
| Backspace | ✅ Works | ⏳ Test | Pending |
| Grammarly mode | ✅ Works | ⏳ Test | Pending |
| Global hotkeys | ✅ Works | ⏳ Test | Pending |
| Pause/Resume | ✅ Works | ⏳ Test | Pending |
| Speed (WPM) | ✅ Fast | ⏳ Test | Pending |
| Special chars | ✅ Works | ⏳ Test | Pending |

### Performance Benchmarks

**Test**: Type 1000 words, measure time

**Acceptable Results**:
- keyboard lib: X seconds
- pynput: Within 10% of keyboard lib time
- If pynput is >10% slower, investigate optimization

---

## 🎯 BENEFITS OF THIS APPROACH

### Now (Windows Only)
1. ✅ Code is cleaner (abstraction layers)
2. ✅ Easier to maintain (single place to change keyboard logic)
3. ✅ Can test pynput on Windows (validate it works)
4. ✅ Platform-aware config system
5. ✅ No breaking changes for Windows users

### Later (Mac Port)
1. ✅ Just add Mac-specific implementations
2. ✅ Most code already works cross-platform
3. ✅ Reduced Mac port time from 15-25 days → 5-10 days
4. ✅ Lower risk (already tested abstractions)
5. ✅ Easier to maintain both platforms

---

## 💡 RECOMMENDED ORDER

**Week 1**:
1. Create `platform_utils.py`
2. Create `platform_keyboard.py`
3. Install pynput and test on Windows

**Week 2**:
1. Update `typing_engine.py` to use platform_keyboard
2. Update `sly_hotkeys.py` to use platform_keyboard
3. Test thoroughly

**Week 3**:
1. Update remaining files
2. Full integration testing
3. Performance testing

**Week 4**:
1. Build installer with new code
2. Beta test with small group
3. Fix any issues
4. Release as minor version update (v2.6.4)

---

## 🚨 RISKS & MITIGATIONS

| Risk | Mitigation |
|------|------------|
| pynput slower than keyboard | Test early, quantify difference, optimize if needed |
| pynput breaks features | Thorough testing, keep keyboard as fallback |
| Users report issues | Beta test first, have rollback plan |
| Hotkeys don't work with pynput | Research pynput hotkey implementation, may need different library |
| Breaking changes | Version bump, clear changelog, support old version |

---

## 📊 SUCCESS METRICS

After refactoring and deploying v2.6.4:

- [ ] ✅ All Windows users upgraded without issues
- [ ] ✅ No performance regression (<5% slower acceptable)
- [ ] ✅ All features work identically
- [ ] ✅ Bug reports <1% of users
- [ ] ✅ pynput backend confirmed working on Windows
- [ ] ✅ Code is ready for Mac port when decision is made

---

## SUMMARY

**What to do NOW on Windows**:
1. ✅ Create abstraction layers (platform_keyboard.py, platform_utils.py)
2. ✅ Test pynput works on Windows
3. ✅ Gradually replace keyboard library calls with abstracted calls
4. ✅ Test thoroughly on Windows
5. ✅ Deploy to Windows users as v2.6.4
6. ✅ When Mac port is greenlit, you're 70% done already

**This approach**:
- Doesn't disrupt current Windows users
- Validates cross-platform code on Windows first
- Reduces future Mac port effort by 50-70%
- Makes codebase cleaner and more maintainable
- Allows incremental testing and deployment
