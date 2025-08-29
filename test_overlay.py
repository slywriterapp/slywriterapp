import tkinter as tk
from tab_overlay_simple import OverlayTab

# Create a simple test window
root = tk.Tk()
root.title("Overlay Tab Test")
root.geometry("800x600")

# Create a simple app object with cfg
class TestApp:
    def __init__(self):
        self.cfg = {'settings': {'dark_mode': True}}

app = TestApp()

# Create the overlay tab
overlay_tab = OverlayTab(root, app)
overlay_tab.pack(fill='both', expand=True)

print("Overlay tab created. Check if sliders are visible.")

# Check if sliders exist
if hasattr(overlay_tab, 'opacity_scale'):
    print(f"[YES] Opacity scale exists: {overlay_tab.opacity_scale}")
else:
    print("[NO] Opacity scale NOT found")

if hasattr(overlay_tab, 'width_scale'):
    print(f"[YES] Width scale exists: {overlay_tab.width_scale}")
else:
    print("[NO] Width scale NOT found")
    
if hasattr(overlay_tab, 'height_scale'):
    print(f"[YES] Height scale exists: {overlay_tab.height_scale}")
else:
    print("[NO] Height scale NOT found")

root.mainloop()