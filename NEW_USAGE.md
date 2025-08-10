# SlyWriter Usage Guide - Refactored Structure

## Running the Application

### Method 1: Using the original entry point (backward compatibility)
```bash
python gui_main.py
```

### Method 2: Using the new package structure
```bash
python -m slywriter
```

### Method 3: Direct import and run
```python
from slywriter import main
main()
```

## Import Examples

### New Recommended Imports
```python
# Core functionality
from slywriter.core import config, engine, auth
from slywriter.core.config import LIME_GREEN, DEFAULT_CONFIG
from slywriter.core.engine import start_typing_from_input, stop_typing_func

# UI components  
from slywriter.ui import TypingApp
from slywriter.themes import apply_app_theme

# Utilities
from slywriter.utils import Tooltip, show_splash_screen
```

### Backward Compatible Imports (still work)
```python
import config  # Shows deprecation warning
import typing_engine  # Shows deprecation warning
import auth  # Shows deprecation warning
from utils import Tooltip  # Shows deprecation warning
```

## Development Benefits

### Before Refactoring
- 23 Python files scattered in root directory
- Large monolithic files (up to 407 lines)
- 3 separate theme files with duplicate code
- Unclear module relationships
- Difficult to test individual components

### After Refactoring
- Organized package structure with clear hierarchy
- Smaller, focused modules (average ~150 lines)
- Consolidated theme management
- Clear separation of concerns
- Easy to test individual components
- Better IDE support with proper packages

## Directory Structure Comparison

### Before
```
C:\Typing Project\
├── config.py (108 lines)
├── typing_engine.py (329 lines)
├── sly_app.py (276 lines)
├── tab_typing.py (365 lines)
├── premium_typing.py (407 lines)
├── sly_theme.py (44 lines)
├── typing_theme.py (104 lines)
├── account_theme.py (70 lines)
├── [... 15 more files in root]
```

### After
```
C:\Typing Project\
├── slywriter/                 # Main package
│   ├── core/                  # Core functionality
│   │   ├── config.py
│   │   ├── engine.py
│   │   └── auth.py
│   ├── ui/                    # User interface
│   │   ├── app.py
│   │   ├── components/
│   │   └── tabs/
│   ├── themes/                # Consolidated themes
│   │   └── manager.py
│   ├── logic/                 # Business logic
│   ├── server/                # Server components
│   └── utils/                 # Utilities
├── config.py                  # Compatibility layer
├── typing_engine.py           # Compatibility layer
├── gui_main.py               # Compatibility entry point
└── [other original files]
```

## Testing the Refactored Code

```bash
# Test new structure imports
cd "C:\Typing Project"
python -c "from slywriter.main import main; print('New structure works!')"

# Test backward compatibility
python -c "import config; print('Backward compatibility works!')"

# Run the application
python gui_main.py
```

## Migration Recommendations

1. **For new development**: Use the new package structure
2. **For existing code**: No immediate changes needed due to compatibility layers
3. **Gradual migration**: Replace old imports with new ones over time
4. **Testing**: The refactored structure is easier to unit test

The refactored codebase maintains 100% backward compatibility while providing a much cleaner, more maintainable structure for future development.