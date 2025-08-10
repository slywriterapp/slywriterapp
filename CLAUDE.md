# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

This is SlyWriter, a desktop typing automation application built with Python and tkinter. The app simulates human-like typing with realistic delays, typos, and pausing patterns to avoid detection by anti-automation systems.

## Architecture

### Main Application Components

- **gui_main.py**: Application entry point - initializes and runs the main TypingApp
- **sly_app.py**: Core TypingApp class using ttkbootstrap, manages tabs and overall application state
- **typing_engine.py**: Core typing automation engine with threading, global stop/pause flags, and keystroke simulation

### Tab-based UI Structure

The application uses a tabbed interface with these main tabs:
- **TypingTab** (tab_typing.py): Main typing functionality with text input/preview
- **AccountTab** (tab_account.py): User authentication and plan management
- **HumanizerTab** (tab_humanizer.py): Advanced human-like typing features
- **HotkeysTab** (tab_hotkeys.py): Global hotkey configuration
- **StatsTab** (tab_stats.py): Usage statistics and diagnostics

### Key Modules

- **typing_logic.py**: Text processing logic (humanization, formatting)
- **typing_ui.py**: UI components for the typing tab
- **premium_typing.py**: Advanced typing features with AI-generated filler text
- **config.py**: Application configuration constants and defaults
- **auth.py**: User authentication handling
- **utils.py**: Shared utilities and helper functions

### Configuration System

- **sly_config.py**: Profile management and configuration loading/saving
- **config.json**: Persistent application settings and user profiles
- **sly_theme.py**: Theme management for dark/light modes
- **sly_hotkeys.py**: Global hotkey registration and management

### Server Component

- **slywriter_server.py**: Flask server for usage tracking and plan management

## Development Commands

### Running the Application
```bash
python gui_main.py
```

### Running the Server (for usage tracking)
```bash
python slywriter_server.py
```

### Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

Key dependencies:
- ttkbootstrap (modern tkinter UI)
- keyboard (global hotkeys and keystroke simulation)
- openai (AI text generation)
- Flask (local server)

## Key Global State

The application uses several global threading events in typing_engine.py:
- `stop_flag`: Global stop signal for typing operations
- `pause_flag`: Global pause signal for typing operations
- `_typing_thread`: Current typing thread reference

These are singleton events shared across the entire application to ensure consistent control.

## Configuration Files

- **config.json**: User settings, profiles, and preferences
- **usage_data.json**: Local usage tracking data
- **client_secret.json**: OAuth credentials (sensitive)
- **typing_log.txt**: Application logging output

## Threading Model

The app uses threading for:
- Non-blocking typing operations (typing_engine.py)
- Global hotkey listening (keyboard library)
- UI updates via tkinter's after() method for thread safety

## Important Notes

- All file paths use absolute paths derived from script directory
- The app changes working directory to script location on startup
- UI updates from worker threads must use widget.after() for thread safety
- Global hotkeys are registered/unregistered dynamically based on user settings