"""Main entry point for SlyWriter application."""

import os
import sys

# Ensure working directory and sys.path are set to this script's location
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up to project root
os.chdir(script_dir)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from .ui import TypingApp


def main():
    """Main application entry point."""
    app = TypingApp()
    app.mainloop()


if __name__ == '__main__':
    main()