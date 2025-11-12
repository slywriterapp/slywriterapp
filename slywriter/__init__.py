"""
SlyWriter - Desktop typing automation application.

This package provides a desktop typing automation application built with Python and tkinter.
The app simulates human-like typing with realistic delays, typos, and pausing patterns.
"""

__version__ = "2.6.6"
__author__ = "SlyWriter"

# Avoid importing main at package level to prevent circular imports
def main():
    """Main application entry point."""
    from .main import main as _main
    return _main()

__all__ = ["main"]