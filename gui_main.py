# gui_main.py - SlyWriter Premium Launcher

from premium_app import run_premium_app
from sly_app import TypingApp
import os
import sys

def main():
    """Launch SlyWriter with premium UI if assets are available"""

    # ============================================================================
    # TERMS OF SERVICE CHECK - MANDATORY
    # ============================================================================
    print("[LEGAL] Checking Terms of Service acceptance...")

    try:
        from terms_dialog import check_terms_acceptance, show_terms_dialog, save_terms_acceptance

        if not check_terms_acceptance():
            print("[LEGAL] Terms not accepted. Showing Terms of Service dialog...")

            # Show terms dialog (blocking)
            accepted = show_terms_dialog(parent=None)

            if not accepted:
                print("[LEGAL] Terms declined. Application cannot start.")
                print("[EXIT] User must accept Terms of Service to use SlyWriter.")
                sys.exit(0)

            # Save acceptance
            save_terms_acceptance()
            print("[LEGAL] Terms accepted and saved.")
        else:
            print("[LEGAL] Terms already accepted. Continuing...")

    except Exception as e:
        print(f"[ERROR] Failed to check terms: {e}")
        print("[FALLBACK] Continuing anyway (development mode)")

    # ============================================================================
    # LAUNCH APPLICATION
    # ============================================================================

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
