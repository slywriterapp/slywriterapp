# gui_main.py - SlyWriter Premium Launcher

from premium_app import run_premium_app
from sly_app import TypingApp
import os

def main():
    """Launch SlyWriter with premium UI if assets are available"""
    
    # Check if premium assets exist
    assets_exist = (
        os.path.exists(os.path.join('assets', 'backgrounds', 'main_bg.png')) and
        os.path.exists(os.path.join('assets', 'backgrounds', 'sidebar_bg.png')) and
        os.path.exists(os.path.join('assets', 'backgrounds', 'card_bg.png')) and
        os.path.exists(os.path.join('assets', 'icons'))
    )
    
    if assets_exist:
        print("[PREMIUM] Launching SlyWriter Premium UI...")
        try:
            run_premium_app()
        except Exception as e:
            print(f"[PREMIUM] Error launching premium UI: {e}")
            print("[FALLBACK] Launching standard UI...")
            app = TypingApp()
            app.mainloop()
    else:
        print("[STANDARD] Premium assets not found, launching standard UI...")
        print("[TIP] Add custom backgrounds and icons to /assets/ folder for premium UI")
        app = TypingApp()
        app.mainloop()

if __name__ == '__main__':
    main()
