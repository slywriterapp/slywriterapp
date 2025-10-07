# SlyWriter Hotkey Reference

Complete reference for SlyWriter keyboard shortcuts and customization.

## Default Hotkeys

| Hotkey | Action | Description |
|--------|--------|-------------|
| **Ctrl+T** | Start Typing | Begins typing the loaded text |
| **Ctrl+Alt+Q** | Stop Typing | Immediately stops all typing |
| **Ctrl+Alt+P** | Pause/Resume | Toggles typing pause state |
| **Ctrl+Alt+O** | Toggle Overlay | Shows/hides status overlay |
| **Ctrl+Alt+G** | AI Generation | Opens AI text generation dialog |

## Customizing Hotkeys

### Via Settings UI

1. Open SlyWriter
2. Go to **Settings** → **Hotkeys**
3. Click the hotkey you want to change
4. Click **"Record New Hotkey"**
5. Press your desired key combination
6. Click **Save**

### Supported Key Combinations

**Modifiers** (must include at least one):
- `Ctrl` / `Control`
- `Alt`
- `Shift`
- `Win` / `Command` (Windows key)

**Keys**:
- Letters: `A-Z`
- Numbers: `0-9`
- Function keys: `F1-F12`
- Special: `Space`, `Tab`, `Enter`, `Backspace`, `Delete`
- Arrows: `Up`, `Down`, `Left`, `Right`

**Valid Examples**:
- ✅ `Ctrl+T`
- ✅ `Ctrl+Alt+G`
- ✅ `Ctrl+Shift+F5`
- ✅ `Alt+Space`

**Invalid Examples**:
- ❌ `T` (no modifier)
- ❌ `Ctrl+Ctrl+T` (duplicate modifier)
- ❌ `Ctrl+Mouse1` (mouse not supported)

### Best Practices

1. **Use Ctrl+Alt combinations** for less chance of conflicts
2. **Avoid system hotkeys**:
   - `Ctrl+C`, `Ctrl+V`, `Ctrl+Z` (clipboard)
   - `Alt+Tab`, `Alt+F4` (window management)
   - `Win+D`, `Win+L` (Windows shortcuts)
3. **Test in target apps** to ensure they don't conflict
4. **Keep it memorable** - simple is better

## Hotkey Details

### Start Typing (`Ctrl+T`)

**What it does**:
- Starts typing the text loaded in the typing box
- Text must not be empty
- Target application must be focused

**Requirements**:
- Text loaded in app
- Cursor in target text field
- Backend server running

**Behavior**:
- Types with human-like delays
- Includes configured typos and corrections
- Can be paused with `Ctrl+Alt+P`
- Can be stopped with `Ctrl+Alt+Q`

**Tips**:
- Click in target field first
- Wait 1 second before triggering
- Ensure field accepts keyboard input

### Stop Typing (`Ctrl+Alt+Q`)

**What it does**:
- Immediately stops all typing
- Clears typing queue
- Resets typing state

**When to use**:
- Made a mistake
- Need to regain control
- App is typing in wrong place

**Notes**:
- Irreversible - can't resume from stop
- To pause temporarily, use `Ctrl+Alt+P` instead

### Pause/Resume (`Ctrl+Alt+P`)

**What it does**:
- **First press**: Pauses typing
- **Second press**: Resumes from where it left off

**Behavior**:
- Preserves typing queue
- Maintains position in text
- Overlay shows "Paused" status

**Use cases**:
- Need to check something
- Waiting for page to load
- Target app needs attention

### Toggle Overlay (`Ctrl+Alt+O`)

**What it does**:
- Shows/hides the status overlay window

**Overlay Information**:
- Typing status (Idle/Typing/Paused)
- Current position in text
- Words per minute
- Estimated time remaining

**Customization**:
- Position: Drag to move
- Opacity: Settings → Overlay → Opacity
- Always on top: Automatically enabled

**Tips**:
- Pin to corner of screen
- Hide when not needed to save resources
- Shows helpful status when debugging

### AI Generation (`Ctrl+Alt+G`)

**What it does**:
- Opens AI text generation dialog
- Generates contextual text using OpenAI
- Previews before typing

**Workflow**:
1. Press `Ctrl+Alt+G`
2. Enter your prompt
3. AI generates text
4. Review generated text
5. Approve or regenerate
6. Text types automatically

**Requirements**:
- Active subscription
- Internet connection
- OpenAI API access

**Tips**:
- Be specific in prompts
- Use for writer's block
- Review before approving
- Can edit generated text

## Advanced Hotkey Features

### Global vs Local Hotkeys

**Global Hotkeys**:
- Work from any application
- Require admin rights on some systems
- All SlyWriter hotkeys are global

**Benefits**:
- Control typing from anywhere
- No need to switch to SlyWriter
- Quick access to features

**Limitations**:
- May conflict with other apps
- Need elevation on some Windows versions
- Can't use if another app registered first

### Hotkey Conflicts

**If hotkey doesn't work**:

1. **Check for conflicts**:
   ```
   - Other automation tools (AutoHotkey, AHK)
   - IDE shortcuts (VS Code, Visual Studio)
   - Gaming software (Discord, Steam)
   - System utilities (PowerToys)
   ```

2. **Resolution**:
   - Change conflicting app's hotkey
   - OR change SlyWriter hotkey
   - Use less common combinations

3. **Test hotkey**:
   - Run as Administrator
   - Close other apps
   - Try alternative combinations

### Running as Administrator

**Why it helps**:
- Global hotkeys have full system access
- Can automate elevated applications
- Bypasses some Windows security restrictions

**How to**:
1. Right-click SlyWriter icon
2. Select "Run as administrator"
3. Allow UAC prompt

**Permanent**:
1. Right-click SlyWriter shortcut
2. Properties → Compatibility
3. Check "Run this program as an administrator"
4. Apply → OK

## Hotkey Configuration File

**Location**: `%APPDATA%\slywriter-desktop\hotkeys.json`

**Format**:
```json
{
  "start": "ctrl+t",
  "stop": "ctrl+alt+q",
  "pause": "ctrl+alt+p",
  "overlay": "ctrl+alt+o",
  "ai_generation": "ctrl+alt+g"
}
```

**Manual editing** (advanced):
1. Close SlyWriter
2. Edit `hotkeys.json`
3. Save changes
4. Restart SlyWriter

**Validation**:
- Keys must be lowercase
- Use `+` to separate keys
- Include at least one modifier
- Invalid entries use defaults

## Troubleshooting Hotkeys

### Hotkey doesn't register

**Solution**:
1. Run SlyWriter as Administrator
2. Check no other app is using the hotkey
3. Try different combination
4. Restart SlyWriter

### Hotkey works randomly

**Cause**: App focus or timing issues

**Solution**:
1. Ensure target app has focus
2. Wait 1 second before pressing
3. Click in text field first
4. Check backend is running

### Can't record new hotkey

**Solution**:
1. Click in recording box
2. Press combination once (don't hold)
3. Wait for confirmation
4. Try simpler combination if fails

### Hotkey triggers in SlyWriter window

**Expected**: Some hotkeys trigger both globally and locally

**Solution**:
- Click in target app first
- Minimize or hide SlyWriter
- Hotkey should work in target

## Tips & Tricks

### Recommended Hotkey Sets

**Minimal conflict (recommended)**:
```
Start: Ctrl+Alt+T
Stop: Ctrl+Alt+Q
Pause: Ctrl+Alt+P
Overlay: Ctrl+Alt+O
AI Gen: Ctrl+Alt+G
```

**Numpad users**:
```
Start: Ctrl+Num1
Stop: Ctrl+Num2
Pause: Ctrl+Num3
Overlay: Ctrl+Num0
AI Gen: Ctrl+Num5
```

**One-handed**:
```
Start: F9
Stop: F10
Pause: F11
Overlay: F12
AI Gen: F8
```

### Workflow Tips

1. **Set text**
   → Load/paste text in app

2. **Position cursor**
   → Click in target field

3. **Start typing**
   → Press `Ctrl+T`

4. **Monitor**
   → Use overlay (`Ctrl+Alt+O`)

5. **Control**
   → Pause (`Ctrl+Alt+P`) or Stop (`Ctrl+Alt+Q`)

### Quick Reference Card

Print this for easy access:

```
┌─────────────────────────────────┐
│     SLYWRITER HOTKEYS v2.4.7    │
├─────────────────────────────────┤
│ Ctrl+T          Start Typing    │
│ Ctrl+Alt+Q      Stop            │
│ Ctrl+Alt+P      Pause/Resume    │
│ Ctrl+Alt+O      Toggle Overlay  │
│ Ctrl+Alt+G      AI Generation   │
└─────────────────────────────────┘
```

---

**Last Updated**: 2025-01-07
**App Version**: 2.4.7

For issues, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
