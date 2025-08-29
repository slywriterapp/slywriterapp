# premium_app.py - Modern Premium SlyWriter App

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from PIL import Image, ImageTk
import os
import sys
import config

# Import premium UI components
from premium_ui import PremiumSidebar, PremiumHeader, PremiumCard, PremiumButton, PremiumInput

# Import existing tabs (we'll modernize these)
try:
    # Try to import modern versions first
    from tab_typing_modern_fixed import ModernTypingTab as TypingTab
    from tab_settings_modern import ModernSettingsTab as HotkeysTab
    print("[PREMIUM] Using modern 2025 UI tabs - Fixed version")
except ImportError as e:
    print(f"[PREMIUM] Could not load modern tabs: {e}")
    # Fallback to original tabs
    from tab_typing import TypingTab
    from tab_hotkeys import HotkeysTab
    print("[PREMIUM] Using standard UI tabs")

from tab_humanizer import HumanizerTab
from tab_account import AccountTab
from tab_stats import StatsTab
from tab_learn import LearnTab
from tab_overlay_simple import OverlayTab

# Import existing functionality
from auth import get_saved_user
from sly_config import load_config, save_config
import typing_engine as engine
from functools import wraps
from sly_splash import show_splash_screen
from feature_spotlight import FeatureSpotlight

# Global storage to avoid tkinter attribute corruption
_app_instance_registry = {}
_tab_frames_registry = {}  # Store tab frames separately

def require_auth(func):
    """Decorator to require authentication for methods"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'authenticated') or not self.authenticated:
            self.show_auth_required_message()
            return None
        return func(self, *args, **kwargs)
    return wrapper

class PremiumSlyWriter(tk.Tk):
    """Premium SlyWriter Application - Modern UI"""
    
    def __init__(self):
        super().__init__()
        
        # CRITICAL: Store in global registry to avoid tkinter corruption
        self._app_id = id(self)  
        _app_instance_registry[self._app_id] = self
        _tab_frames_registry[self._app_id] = {}
        
        # App configuration
        self.user = None
        self.cfg = load_config()
        self.current_tab = 'Typing'
        self.authenticated = False
        
        # Set up the premium window
        self.setup_premium_window()
        
        # Hide window during setup to prevent threading issues
        self.withdraw()
        
        # Show splash screen first, then force authentication
        show_splash_screen(self, self.after_splash)
    
    def _get_safe_app(self):
        """Get safe app reference from global registry"""
        return _app_instance_registry.get(self._app_id, self)
    
    def after_splash(self):
        """Continue initialization after splash screen"""
        # Force authentication before proceeding
        self.force_authentication()
    
    def setup_premium_window(self):
        """Set up the premium application window"""
        self.title("SlyWriter")
        self.geometry("1400x900")  # Larger for premium feel
        self.minsize(1200, 800)
        
        # Center window
        self.center_window()
        
        # Configure window with no borders
        self.configure(bg='#0F0F23', highlightthickness=0, bd=0)
        
        # Clean up any potential canvas remnants
        for child in self.winfo_children():
            if isinstance(child, tk.Canvas):
                child.destroy()
        
        # Set icon
        try:
            self.iconbitmap("slywriter_logo.ico")
        except:
            pass
    
    def center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        width = 1400
        height = 900
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_static_background(self):
        """Load a perfectly smooth static background with no banding artifacts"""
        try:
            from PIL import Image, ImageTk
            import os
            
            # Look for the static background image
            bg_path = os.path.join('assets', 'backgrounds', 'main_bg.png')
            
            # Check if background exists, if not create perfect gradient
            if not os.path.exists(bg_path):
                print("[STATIC BG] Creating PERFECT gradient - NO BARS, NO BANDING!")
                try:
                    from create_static_bg import create_static_background
                    bg_path = create_static_background()
                except Exception as e:
                    print(f"[STATIC BG] Could not create background: {e}")
                    bg_path = None
            
            if bg_path and os.path.exists(bg_path):
                print(f"[STATIC BG] Loading SMOOTH background: {bg_path}")
                
                # Get window dimensions
                self.update_idletasks()
                width = self.winfo_width() or 1400
                height = self.winfo_height() or 900
                
                # Load and resize image with high quality
                bg_image = Image.open(bg_path)
                bg_image = bg_image.resize((width, height), Image.Resampling.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(bg_image)
                
                # Create background label
                self.bg_label = tk.Label(self, image=self.bg_photo, bd=0, highlightthickness=0)
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                self.bg_label.lower()  # Send to back
                
                # Ensure no canvas remnants
                if hasattr(self, 'bg_canvas'):
                    try:
                        self.bg_canvas.destroy()
                        delattr(self, 'bg_canvas')
                    except:
                        pass
                
                print("[STATIC BG] Static background loaded successfully")
            else:
                print(f"[STATIC BG] Background image not found: {bg_path}")
                # Use solid color fallback
                self.configure(bg='#1A1B3E')
                
        except Exception as e:
            print(f"[STATIC BG] Error loading background: {e}")
            # Fallback to solid color
            self.configure(bg='#1A1B3E')
    
    def load_main_background_old(self):
        """Load animated GIF background or fallback to static image"""
        try:
            pass  # Load main background
            
            # Get window dimensions
            self.update_idletasks()
            width = self.winfo_width() or 1400
            height = self.winfo_height() or 900
            
            # Debug existing state
            has_video_frames = hasattr(self, 'video_frames') and len(getattr(self, 'video_frames', [])) > 0
            has_bg_canvas = hasattr(self, 'bg_canvas') and self.bg_canvas.winfo_exists() if hasattr(self, 'bg_canvas') else False
            has_bg_label = hasattr(self, 'bg_label') and self.bg_label.winfo_exists() if hasattr(self, 'bg_label') else False
            
            pass  # Check existing components
            
            # Check if animation is already running
            if has_video_frames and (has_bg_canvas or has_bg_label):
                print("[PREMIUM] Animation already loaded and running - skipping reload")
                return True
            
            pass  # Remove existing backgrounds
            # Remove any existing background only if we need to reload
            if hasattr(self, 'bg_label'):
                pass  # Destroying bg_label
                self.bg_label.destroy()
            if hasattr(self, 'bg_canvas'):
                pass  # Destroying bg_canvas
                self.bg_canvas.destroy()
            
            # Check for animated backgrounds (MP4 first, then GIF, then PNG)
            mp4_path = os.path.join('assets', 'backgrounds', 'main_bg.mp4')
            gif_path = os.path.join('assets', 'backgrounds', 'main_bg.gif')
            png_path = os.path.join('assets', 'backgrounds', 'main_bg.png')
            
            pass  # Check background files
            
            # Skip MP4 and GIF - go straight to static PNG
            if os.path.exists(png_path):
                pass  # Load static PNG
                # Load static PNG
                self.load_static_background(png_path, width, height)
                print(f"[PREMIUM] Loaded static PNG background from {png_path}")
            else:
                pass  # Use solid color fallback
                # Solid color fallback
                self.configure(bg='#0F0F23')
                print(f"[PREMIUM] Using solid color background fallback")
            
            pass  # Schedule UI raising
            # Force all UI widgets to be raised above background
            self.after(50, self.raise_ui_above_background)
            
            return True
                
        except Exception as e:
            print(f"[PREMIUM] Error loading background: {e}")
            self.configure(bg='#0F0F23')
            return False
    
    def load_animated_gif(self, gif_path, width, height):
        """DISABLED - Animated backgrounds cause artifacts"""
        return False  # Disabled to prevent visual artifacts
        try:
            # Open the GIF and extract frames
            gif_image = Image.open(gif_path)
            self.gif_frames = []
            self.gif_frame_delays = []
            
            # Extract all frames
            frame_num = 0
            while True:
                try:
                    gif_image.seek(frame_num)
                    # Resize frame to fit window
                    frame = gif_image.resize((width, height), Image.Resampling.LANCZOS)
                    # Convert to PhotoImage
                    photo_frame = ImageTk.PhotoImage(frame)
                    self.gif_frames.append(photo_frame)
                    
                    # Get frame delay (default 100ms if not specified)
                    delay = gif_image.info.get('duration', 100)
                    self.gif_frame_delays.append(delay)
                    
                    frame_num += 1
                except EOFError:
                    break
            
            if not self.gif_frames:
                raise Exception("No frames found in GIF")
            
            # Create label for displaying frames
            self.bg_label = tk.Label(self, bd=0, highlightthickness=0)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.bg_label.lower()
            
            # Start animation
            self.current_frame = 0
            self.animate_gif_frame()
            
            print(f"[GIF] Loaded {len(self.gif_frames)} frames")
            
        except Exception as e:
            print(f"[GIF] Error loading animated GIF: {e}")
            # Fallback to solid color
            self.configure(bg='#0F0F23')
    
    def load_static_background_old(self, png_path, width, height):
        """Old static PNG background loader - disabled"""
        pass
    
    def animate_gif_frame(self):
        """Animate GIF frames"""
        try:
            if not hasattr(self, 'gif_frames') or not self.gif_frames:
                return
            
            # Get current frame
            frame = self.gif_frames[self.current_frame]
            delay = self.gif_frame_delays[self.current_frame]
            
            # Update label with current frame
            if hasattr(self, 'bg_label') and self.bg_label.winfo_exists():
                self.bg_label.configure(image=frame)
                self.bg_label.image = frame  # Keep reference
                self.bg_label.lower()  # Ensure it stays behind UI
            
            # Move to next frame
            self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
            
            # Schedule next frame
            self.after(delay, self.animate_gif_frame)
            
        except Exception as e:
            print(f"[GIF] Animation error: {e}")
            # Restart animation after delay
            self.after(1000, self.animate_gif_frame)
    
    def load_video_background(self, mp4_path, width, height):
        """DISABLED - Canvas animations cause ghost bars"""
        return False  # Completely disabled
        try:
            import cv2
            
            # Open video file
            cap = cv2.VideoCapture(mp4_path)
            
            if not cap.isOpened():
                print(f"[MP4] Could not open video file: {mp4_path}")
                return False
            
            # Extract frames
            self.video_frames = []
            self.video_frame_delays = []
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS) or 24
            frame_delay = int(1000 / fps)
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (width, height))
                
                # Convert to PIL Image
                pil_frame = Image.fromarray(frame)
                photo_frame = ImageTk.PhotoImage(pil_frame)
                
                self.video_frames.append(photo_frame)
                self.video_frame_delays.append(frame_delay)
                frame_count += 1
            
            cap.release()
            
            if not self.video_frames:
                print(f"[MP4] No frames extracted from video")
                return False
            
            # Create Canvas directly on the root window for maximum visibility
            self.bg_canvas = tk.Canvas(self, width=width, height=height, 
                                     highlightthickness=0, highlightcolor='#0F0F23', 
                                     bd=0, relief='flat', bg='#0F0F23')
            # Place it to fill the entire window
            self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
            
            print(f"[MP4] Created Canvas with size {width}x{height}")
            
            # Don't lower the canvas - instead we'll raise UI elements above it
            print("[MP4] Canvas created, will position UI elements above it")
            
            # Create a test rectangle to verify canvas drawing works
            self.test_rect = self.bg_canvas.create_rectangle(50, 50, 200, 200, 
                                                           fill='purple', outline='white', width=3)
            
            # Create the image item on canvas
            self.canvas_image_item = self.bg_canvas.create_image(0, 0, anchor='nw', 
                                                               image=self.video_frames[0])
            
            # Also create a test text to verify canvas is working
            self.test_text = self.bg_canvas.create_text(300, 100, text="CANVAS TEST", 
                                                       fill='yellow', font=('Arial', 20, 'bold'))
            
            # Start animation
            self.current_frame = 0
            self._animation_scheduled = True
            self.animate_canvas_video()
            
            # Ensure canvas stays behind everything - use a more aggressive approach
            self.maintain_canvas_behind()
            
            print(f"[MP4] Loaded {len(self.video_frames)} frames at {fps} FPS on Canvas")
            return True
            
        except ImportError:
            print(f"[MP4] OpenCV not available, cannot load MP4")
            return False
        except Exception as e:
            print(f"[MP4] Error loading video: {e}")
            return False
    
    def animate_video_frame(self):
        """Animate MP4 video frames"""
        try:
            if not hasattr(self, 'video_frames') or not self.video_frames:
                print("[MP4] No video frames available")
                self._animation_scheduled = False
                return
            
            if not hasattr(self, 'bg_label') or not self.bg_label.winfo_exists():
                print("[MP4] Background label no longer exists - recreating...")
                self._animation_scheduled = False
                # Try to recreate the background
                self.after(1000, self.load_main_background)
                return
            
            # Get current frame
            frame = self.video_frames[self.current_frame]
            delay = self.video_frame_delays[self.current_frame]
            
            # Update label with current frame
            self.bg_label.configure(image=frame)
            self.bg_label.image = frame  # Keep reference
            self.bg_label.lower()  # Ensure it stays behind UI
            
            # Move to next frame
            self.current_frame = (self.current_frame + 1) % len(self.video_frames)
            
            # Debug: Print every 60 frames to confirm animation is running (less spam)
            if self.current_frame % 60 == 0:
                print(f"[MP4] Animation running - frame {self.current_frame}/{len(self.video_frames)}")
            
            # Schedule next frame
            self.after(delay, self.animate_video_frame)
            
        except Exception as e:
            print(f"[MP4] Animation error: {e}")
            self._animation_scheduled = False
            # Restart animation after delay
            self.after(2000, lambda: setattr(self, '_animation_scheduled', True) or self.animate_video_frame())
    
    def animate_canvas_video(self):
        """Animate video frames on Canvas (more robust)"""
        try:
            if not hasattr(self, 'video_frames') or not self.video_frames:
                print("[MP4] No video frames available for Canvas")
                self._animation_scheduled = False
                return
            
            if not hasattr(self, 'bg_canvas') or not self.bg_canvas.winfo_exists():
                print("[MP4] Canvas no longer exists - recreating background...")
                self._animation_scheduled = False
                self.after(1000, self.load_main_background)
                return
            
            # Get current frame
            frame = self.video_frames[self.current_frame]
            delay = self.video_frame_delays[self.current_frame]
            
            # Update canvas image
            self.bg_canvas.itemconfig(self.canvas_image_item, image=frame)
            self.bg_canvas.image = frame  # Keep reference
            
            # Force canvas update
            self.bg_canvas.update_idletasks()
            
            # Move to next frame
            self.current_frame = (self.current_frame + 1) % len(self.video_frames)
            
            # Debug output every 60 frames
            if self.current_frame % 60 == 0:
                print(f"[MP4] Canvas animation running - frame {self.current_frame}/{len(self.video_frames)}")
                # Debug canvas visibility and image update
                if hasattr(self, 'bg_canvas'):
                    try:
                        canvas_info = self.bg_canvas.place_info()
                        canvas_visible = self.bg_canvas.winfo_viewable()
                        image_size = frame.width(), frame.height()
                        print(f"[MP4] Canvas info - Position: {canvas_info}, Visible: {canvas_visible}, Size: {self.bg_canvas.winfo_width()}x{self.bg_canvas.winfo_height()}")
                        print(f"[MP4] Image info - Frame size: {image_size}, Image ID: {self.canvas_image_item}")
                    except Exception as e:
                        print(f"[MP4] Could not get canvas debug info: {e}")
            
            # Schedule next frame
            self.after(delay, self.animate_canvas_video)
            
        except Exception as e:
            print(f"[MP4] Canvas animation error: {e}")
            self._animation_scheduled = False
            self.after(2000, lambda: setattr(self, '_animation_scheduled', True) or self.animate_canvas_video())
    
    def maintain_canvas_behind(self):
        """Continuously ensure canvas stays behind all UI elements"""
        try:
            if hasattr(self, 'bg_canvas') and self.bg_canvas.winfo_exists():
                # More aggressive canvas positioning - place it first, then raise everything else
                self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
                try:
                    self.bg_canvas.lower()
                except Exception as e:
                    print(f"[MAINTAIN] Canvas lower error (ignoring): {e}")
                    # Alternative: raise everything else above canvas
                    pass
                
                # Raise all other children above the canvas
                for child in self.winfo_children():
                    if child != self.bg_canvas and child.winfo_class() != 'Canvas':
                        try:
                            child.tkraise()
                        except:
                            pass
                
                # Schedule next maintenance check
                self.after(1000, self.maintain_canvas_behind)
                
        except Exception as e:
            # Skip error logging to reduce spam
            # Try again later
            self.after(2000, self.maintain_canvas_behind)
    
    def raise_ui_above_background(self):
        """Ensure all UI elements are above the background"""
        try:
            pass  # Raise UI above background
            
            # Raise main container and its children
            if hasattr(self, 'main_container'):
                pass  # Raise main container
                self.main_container.tkraise()
                
            # Send background to back again - but don't destroy animation
            has_canvas = hasattr(self, 'bg_canvas') and self.bg_canvas.winfo_exists() if hasattr(self, 'bg_canvas') else False
            has_label = hasattr(self, 'bg_label') and self.bg_label.winfo_exists() if hasattr(self, 'bg_label') else False
            
            pass  # Check background state
            
            if has_canvas:
                pass  # Lower canvas behind UI
                # Keep canvas behind UI elements
                for child in self.winfo_children():
                    if child != self.bg_canvas:
                        child.tkraise(self.bg_canvas)
            elif has_label:
                pass  # Lower label behind UI
                self.bg_label.lower()
                # Ensure animation is still scheduled if it was running
                if hasattr(self, 'video_frames') and not hasattr(self, '_animation_scheduled'):
                    pass  # Restart video animation
                    self._animation_scheduled = True
                    self.after(50, self.animate_video_frame)
                
            print("[PREMIUM] Raised UI elements above background")
        except Exception as e:
            print(f"[PREMIUM] Error raising UI: {e}")
    
    def safe_lower_canvas(self):
        """DISABLED - Canvas operations cause artifacts"""
        return  # Disabled to prevent ghost bars
    
    def create_animated_gradient_background(self):
        """DISABLED - was causing horizontal ghost bars"""
        return  # Completely disabled
        # self.animate_gradient()
    
    def create_animated_custom_background(self):
        """Create animated effects on top of custom background"""
        # Draw the base background first
        self.bg_photo = ImageTk.PhotoImage(self.base_bg_image)
        self.bg_canvas.create_image(0, 0, anchor='nw', image=self.bg_photo, tags='base_bg')
        self.bg_canvas.image = self.bg_photo
        
        # Add animated overlay effects
        self.animate_custom_overlay()
    
    def animate_gradient(self):
        """DISABLED - was causing horizontal ghost bars"""
        return  # Completely disabled to prevent ghost bars
        try:
            if not hasattr(self, 'bg_canvas') or not self.bg_canvas.winfo_exists():
                return
            
            # Clear canvas
            self.bg_canvas.delete('gradient')
            
            # Calculate color transitions based on time
            import math
            time_factor = self.animation_time
            
            # Create moving gradient with multiple color zones
            for y in range(0, self.bg_height, 4):  # Step by 4 for performance
                # Calculate multiple wave patterns for complex movement
                wave1 = math.sin(time_factor + y * 0.005) * 0.5 + 0.5
                wave2 = math.cos(time_factor * 0.7 + y * 0.003) * 0.5 + 0.5
                wave3 = math.sin(time_factor * 1.3 + y * 0.007) * 0.5 + 0.5
                
                # Blend multiple colors based on waves
                color_index1 = int(wave1 * (len(self.gradient_colors) - 1))
                color_index2 = int(wave2 * (len(self.gradient_colors) - 1))
                color_index3 = int(wave3 * (len(self.gradient_colors) - 1))
                
                # Get colors
                color1 = self.gradient_colors[color_index1]
                color2 = self.gradient_colors[color_index2]
                color3 = self.gradient_colors[color_index3]
                
                # Blend the colors
                blended_color = self.blend_three_colors(color1, color2, color3, wave1, wave2)
                
                # Draw the line
                self.bg_canvas.create_rectangle(0, y, self.bg_width, y + 4, 
                                              fill=blended_color, outline=blended_color, tags='gradient')
            
            # Update animation time
            self.animation_time += self.animation_speed
            
            # Keep canvas behind UI
            self.safe_lower_canvas()
            
            # Schedule next frame
            self.after(50, self.animate_gradient)  # ~20 FPS
            
        except Exception as e:
            print(f"[ANIMATION] Error in gradient animation: {e}")
            # Try to restart animation
            self.after(1000, self.animate_gradient)
    
    def animate_custom_overlay(self):
        """DISABLED - was causing visual artifacts"""
        return  # Completely disabled
        try:
            if not hasattr(self, 'bg_canvas') or not self.bg_canvas.winfo_exists():
                return
            
            # Clear previous overlay
            self.bg_canvas.delete('overlay')
            
            # Create moving light effects
            import math
            time_factor = self.animation_time
            
            # Create multiple moving light spots
            for i in range(3):
                # Calculate position
                x_offset = math.sin(time_factor + i * 2) * 200 + self.bg_width // 2
                y_offset = math.cos(time_factor * 0.7 + i * 1.5) * 100 + self.bg_height // 2
                
                # Create gradient circle (light effect)
                radius = 150 + math.sin(time_factor + i) * 30
                alpha = 0.1 + math.sin(time_factor + i * 0.5) * 0.05
                
                # Create semi-transparent circle overlay
                color = self.gradient_colors[3 + i % 3]  # Use purple tones
                self.create_circle_gradient(x_offset, y_offset, radius, color, alpha)
            
            # Update animation time
            self.animation_time += self.animation_speed
            
            # Keep canvas behind UI
            self.safe_lower_canvas()
            
            # Schedule next frame
            self.after(60, self.animate_custom_overlay)  # ~16 FPS
            
        except Exception as e:
            print(f"[ANIMATION] Error in custom overlay animation: {e}")
            self.after(1000, self.animate_custom_overlay)
    
    def blend_three_colors(self, color1, color2, color3, weight1, weight2):
        """Blend three colors with given weights"""
        try:
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            rgb1 = hex_to_rgb(color1)
            rgb2 = hex_to_rgb(color2)
            rgb3 = hex_to_rgb(color3)
            
            # Normalize weights
            weight3 = 1 - weight1 - weight2
            total = weight1 + weight2 + weight3
            if total > 0:
                weight1 /= total
                weight2 /= total
                weight3 /= total
            
            # Blend RGB values
            r = int(rgb1[0] * weight1 + rgb2[0] * weight2 + rgb3[0] * weight3)
            g = int(rgb1[1] * weight1 + rgb2[1] * weight2 + rgb3[1] * weight3)
            b = int(rgb1[2] * weight1 + rgb2[2] * weight2 + rgb3[2] * weight3)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color1
    
    def create_circle_gradient(self, x, y, radius, color, alpha):
        """Create a circular gradient effect"""
        try:
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            rgb = hex_to_rgb(color)
            
            # Create concentric circles with decreasing opacity
            steps = 20
            for i in range(steps):
                current_radius = radius * (1 - i / steps)
                current_alpha = alpha * (1 - i / steps)
                
                # Calculate color with alpha effect (simulate transparency)
                bg_rgb = (15, 15, 35)  # Base background color
                blended_r = int(bg_rgb[0] * (1 - current_alpha) + rgb[0] * current_alpha)
                blended_g = int(bg_rgb[1] * (1 - current_alpha) + rgb[1] * current_alpha)
                blended_b = int(bg_rgb[2] * (1 - current_alpha) + rgb[2] * current_alpha)
                
                circle_color = f"#{blended_r:02x}{blended_g:02x}{blended_b:02x}"
                
                # Draw circle
                self.bg_canvas.create_oval(x - current_radius, y - current_radius,
                                         x + current_radius, y + current_radius,
                                         fill=circle_color, outline=circle_color, tags='overlay')
        except:
            pass
    
    def create_canvas_gradient(self, canvas, width, height, color1, color2, direction='vertical'):
        """Create a gradient directly on a canvas"""
        try:
            # Parse colors
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            rgb1 = hex_to_rgb(color1)
            rgb2 = hex_to_rgb(color2)
            
            # Create gradient by drawing multiple rectangles
            if direction == 'vertical':
                for y in range(0, height, 2):  # Step by 2 for performance
                    ratio = y / height
                    r = int(rgb1[0] * (1 - ratio) + rgb2[0] * ratio)
                    g = int(rgb1[1] * (1 - ratio) + rgb2[1] * ratio)
                    b = int(rgb1[2] * (1 - ratio) + rgb2[2] * ratio)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    canvas.create_rectangle(0, y, width, y + 2, fill=color, outline=color)
            else:  # horizontal
                for x in range(0, width, 2):
                    ratio = x / width
                    r = int(rgb1[0] * (1 - ratio) + rgb2[0] * ratio)
                    g = int(rgb1[1] * (1 - ratio) + rgb2[1] * ratio)
                    b = int(rgb1[2] * (1 - ratio) + rgb2[2] * ratio)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    canvas.create_rectangle(x, 0, x + 2, height, fill=color, outline=color)
        except Exception as e:
            print(f"[GRADIENT] Error creating canvas gradient: {e}")
            # Fallback to solid color
            canvas.configure(bg=color1)
    
    def make_transparent_if_background_exists(self, widget):
        """Keep normal backgrounds for static image"""
        # No longer needed for static backgrounds
        pass
    
    
    def create_gradient_background(self, width, height, color1='#0F0F23', color2='#1A1B3E', direction='vertical'):
        """Create a gradient background programmatically"""
        try:
            from PIL import Image, ImageDraw
            
            # Create a new image with the gradient
            img = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(img)
            
            # Parse colors
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            rgb1 = hex_to_rgb(color1)
            rgb2 = hex_to_rgb(color2)
            
            # Create gradient
            if direction == 'vertical':
                for y in range(height):
                    ratio = y / height
                    r = int(rgb1[0] * (1 - ratio) + rgb2[0] * ratio)
                    g = int(rgb1[1] * (1 - ratio) + rgb2[1] * ratio)
                    b = int(rgb1[2] * (1 - ratio) + rgb2[2] * ratio)
                    draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
            else:  # horizontal
                for x in range(width):
                    ratio = x / width
                    r = int(rgb1[0] * (1 - ratio) + rgb2[0] * ratio)
                    g = int(rgb1[1] * (1 - ratio) + rgb2[1] * ratio)
                    b = int(rgb1[2] * (1 - ratio) + rgb2[2] * ratio)
                    draw.rectangle([(x, 0), (x + 1, height)], fill=(r, g, b))
            
            return ImageTk.PhotoImage(img)
            
        except Exception as e:
            print(f"[GRADIENT] Error creating gradient: {e}")
            return None
    
    def load_or_create_background(self, bg_path, width, height, fallback_gradient=None):
        """Load background image or create gradient fallback"""
        try:
            # Try to load custom background first
            if os.path.exists(bg_path):
                bg_image = Image.open(bg_path)
                bg_image = bg_image.resize((width, height), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(bg_image)
            else:
                # Create gradient fallback
                if fallback_gradient:
                    return self.create_gradient_background(width, height, **fallback_gradient)
                else:
                    return self.create_gradient_background(width, height)
        except Exception as e:
            print(f"[BACKGROUND] Error loading/creating background: {e}")
            return None
    
    def create_premium_layout(self):
        """Create the premium UI layout"""
        # Main container with consistent background
        self.main_container = tk.Frame(self, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        self.main_container.pack(fill='both', expand=True)
        
        # Header
        self.header = PremiumHeader(self.main_container, self)
        
        # Content area (sidebar + main content) with consistent background
        self.content_area = tk.Frame(self.main_container, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        self.content_area.pack(fill='both', expand=True)
        
        # Sidebar
        self.sidebar = PremiumSidebar(self.content_area, self)
        
        # Main content area with consistent background
        self.main_content = tk.Frame(self.content_area, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        self.main_content.pack(side='right', fill='both', expand=True, padx=32, pady=32)
        
        # Tab containers - use global registry to avoid tkinter corruption
        self._safe_tab_frames = _tab_frames_registry[self._app_id]
        self.tab_frames = self._safe_tab_frames  # For backward compatibility
        self.create_tab_containers()
    
    def create_tab_containers(self):
        """Create containers for each tab"""
        tab_names = ['Typing', 'AI Hub', 'Learn', 'Stats', 'Overlay', 'Settings', 'Account']
        
        for tab_name in tab_names:
            # Create frame for this tab with normal background
            tab_frame = tk.Frame(self.main_content, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
            _tab_frames_registry[self._app_id][tab_name] = tab_frame
            self._safe_tab_frames = _tab_frames_registry[self._app_id]  # Refresh reference
            
            # Only show the first tab initially
            if tab_name == 'Typing':
                tab_frame.pack(fill='both', expand=True)
    
    def initialize_tabs(self):
        """Initialize all tab content with premium styling"""
        # Map new tab names to old tab classes
        tab_mapping = {
            'Typing': TypingTab,
            'AI Hub': HumanizerTab,  # Renamed from Humanizer
            'Learn': LearnTab,
            'Stats': StatsTab,
            'Overlay': OverlayTab,  # Added back overlay tab
            'Settings': HotkeysTab,  # Renamed from Hotkeys
            'Account': AccountTab
        }
        
        self.tabs = {}
        
        for new_name, tab_class in tab_mapping.items():
            try:
                # Create tab instance with premium container
                # Use global registry to avoid any corruption
                tab_container = _tab_frames_registry[self._app_id][new_name]
                
                # Create premium wrapper for the tab
                tab_wrapper = self.create_premium_tab_wrapper(tab_container, new_name)
                
                # Initialize the actual tab
                if new_name == 'AI Hub':
                    # Special handling for AI Hub (formerly Humanizer)
                    tab_instance = tab_class(tab_wrapper, self)
                    tab_instance.pack(fill='both', expand=True)
                    # Add copy functionality to review tab
                    self.enhance_ai_hub_with_copy(tab_instance)
                elif new_name == 'Typing':
                    # Special handling for Typing tab
                    # Add missing methods for typing tab using safe reference
                    safe_app = self._get_safe_app()
                    safe_app.reset_typing_settings = lambda: None
                    try:
                        tab_instance = tab_class(tab_wrapper, safe_app)
                        tab_instance.pack(fill='both', expand=True)
                    except Exception as tab_error:
                        print(f"[PREMIUM] Error creating {new_name} tab: {tab_error}")
                        # Create fallback simple frame
                        tab_instance = tk.Frame(tab_wrapper, bg='#0F0F23')
                        tk.Label(tab_instance, text=f"{new_name} Tab Loading...",
                                fg='white', bg='#0F0F23',
                                font=('Segoe UI', 14)).pack(pady=50)
                        tab_instance.pack(fill='both', expand=True)
                elif new_name == 'Settings':
                    # Special handling for Settings (formerly Hotkeys)
                    # The real hotkey methods are defined as class methods later in the file
                    tab_instance = tab_class(tab_wrapper, self)
                    tab_instance.pack(fill='both', expand=True)
                else:
                    # Standard tab initialization
                    tab_instance = tab_class(tab_wrapper, self)
                    tab_instance.pack(fill='both', expand=True)
                
                self.tabs[new_name] = tab_instance
                print(f"[PREMIUM] Initialized {new_name} tab")
                
            except Exception as e:
                print(f"[PREMIUM] Error initializing {new_name} tab: {e}")
        
        # Set up engine references
        if 'Stats' in self.tabs:
            engine.set_stats_tab_reference(self.tabs['Stats'])
        if 'Account' in self.tabs:
            engine.set_account_tab_reference(self.tabs['Account'])
        if 'Overlay' in self.tabs:
            engine.set_overlay_tab_reference(self.tabs['Overlay'])
        
        # Register global hotkeys after all tabs are initialized
        try:
            from sly_hotkeys import register_hotkeys
            # Set hotkeys_tab reference for hotkey registration
            if 'Settings' in self.tabs:
                self.hotkeys_tab = self.tabs['Settings']
            register_hotkeys(self)
            print("[PREMIUM] Registered global hotkeys successfully")
        except Exception as e:
            print(f"[PREMIUM] Error registering hotkeys: {e}")
    
    def create_premium_tab_wrapper(self, parent, tab_name):
        """Create a premium wrapper for tab content"""
        # Main tab container with premium styling
        wrapper = tk.Frame(parent, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        wrapper.pack(fill='both', expand=True)
        
        # Tab header with title and description - more connected design
        header_card = PremiumCard(wrapper, title="", height=120)  # Taller to accommodate both title and desc
        header_card.pack(fill='x', pady=(0, 20))
        
        # Tab title - larger and more prominent
        title_label = tk.Label(header_card.content,
                              text=tab_name,
                              font=('Segoe UI', 18, 'bold'),  # Larger, bolder title
                              fg='#FFFFFF',
                              bg='#2D2F5A')
        title_label.pack(anchor='w', pady=(10, 5))  # More padding
        
        # Tab description - directly under title with smaller gap
        descriptions = {
            'Typing': 'AI-powered typing automation with human-like behavior',
            'AI Hub': 'Advanced AI text generation and humanization features',
            'Learn': 'Interactive learning mode with personalized lessons',
            'Stats': 'Comprehensive analytics and usage insights',
            'Overlay': 'Real-time floating overlay with status display',
            'Settings': 'Hotkeys, profiles, and application configuration',
            'Account': 'Profile management, billing, and subscription details'
        }
        
        desc_label = tk.Label(header_card.content,
                             text=descriptions.get(tab_name, ''),
                             font=('Segoe UI', 11),  # Slightly larger description text
                             fg='#B4B4B8',
                             bg='#2D2F5A',
                             wraplength=600,  # Prevent text cutoff
                             justify='left')
        desc_label.pack(anchor='w', pady=(0, 10))  # Small gap from title, more bottom padding
        
        # Content area for the actual tab
        content_frame = tk.Frame(wrapper, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        content_frame.pack(fill='both', expand=True)
        
        return content_frame
    
    def enhance_ai_hub_with_copy(self, ai_hub_tab):
        """Add copy functionality to AI Hub (formerly Humanizer) tab"""
        try:
            # Find the output areas and add copy buttons
            # This will work with the existing humanizer tab structure
            
            # We'll add this enhancement after the tab is fully initialized
            self.after(100, lambda: self._add_copy_buttons_to_ai_hub(ai_hub_tab))
            
        except Exception as e:
            print(f"[PREMIUM] Error enhancing AI Hub: {e}")
    
    def _add_copy_buttons_to_ai_hub(self, ai_hub_tab):
        """Add copy buttons to AI Hub outputs"""
        try:
            # Look for text widgets that contain output
            def add_copy_to_widget(widget, parent_frame):
                if isinstance(widget, tk.Text):
                    # Create copy button for this text widget
                    copy_btn = PremiumButton(parent_frame, "📋 Copy", 
                                           command=lambda: self.copy_text_from_widget(widget),
                                           style="secondary")
                    copy_btn.pack(pady=(5, 0))
            
            # Recursively find and enhance text widgets
            self._find_and_enhance_text_widgets(ai_hub_tab, add_copy_to_widget)
            
        except Exception as e:
            print(f"[PREMIUM] Error adding copy buttons: {e}")
    
    def _find_and_enhance_text_widgets(self, widget, enhance_func):
        """Recursively find text widgets and enhance them"""
        try:
            for child in widget.winfo_children():
                if isinstance(child, tk.Text) and child.cget('state') != 'disabled':
                    # This is an output text widget, add copy functionality
                    parent = child.master
                    enhance_func(child, parent)
                else:
                    # Recurse into child widgets
                    self._find_and_enhance_text_widgets(child, enhance_func)
        except:
            pass
    
    def copy_text_from_widget(self, text_widget):
        """Copy text from a widget to clipboard"""
        try:
            content = text_widget.get('1.0', 'end-1c')
            if content.strip():
                self.clipboard_clear()
                self.clipboard_append(content)
                self.show_success_notification("Text copied to clipboard!")
                
                # Deduct words for premium functionality
                word_count = len(content.split())
                if hasattr(self, 'tabs') and 'Account' in self.tabs:
                    self.tabs['Account'].usage_mgr.add_usage(word_count)
                    
        except Exception as e:
            print(f"[PREMIUM] Error copying text: {e}")
    
    def show_success_notification(self, message):
        """Show a brief success notification"""
        # Create a temporary notification
        notification = tk.Toplevel(self)
        notification.overrideredirect(True)
        notification.configure(bg='#10B981')
        
        # Position it in the top-right
        x = self.winfo_x() + self.winfo_width() - 300
        y = self.winfo_y() + 50
        notification.geometry(f"250x60+{x}+{y}")
        
        # Notification content
        tk.Label(notification, text="✅ " + message,
                font=('Segoe UI', 10, 'bold'),
                fg='white', bg='#10B981').pack(expand=True)
        
        # Auto-hide after 2 seconds
        self.after(2000, notification.destroy)
    
    def switch_to_tab(self, tab_name):
        """Switch to a specific tab"""
        # Quick auth check - only verify if authenticated flag exists, no expensive calls
        if not hasattr(self, 'authenticated') or not self.authenticated:
            print(f"[AUTH] Tab access blocked - authentication required for {tab_name}")
            self.show_auth_required_message()
            return
        
        # Hide all tabs using global registry
        for name, frame in _tab_frames_registry[self._app_id].items():
            frame.pack_forget()
        
        # Show selected tab using global registry
        if tab_name in _tab_frames_registry[self._app_id]:
            _tab_frames_registry[self._app_id][tab_name].pack(fill='both', expand=True)
            self.current_tab = tab_name
            
            # Track tab usage for spotlight system
            if tab_name == 'AI Hub':
                self.track_feature_usage('ai_humanizer')
            elif tab_name == 'Stats':
                self.track_feature_usage('typing_stats')
                # Apply theme immediately for Stats tab to prevent white flash
                if tab_name in self.tabs:
                    self._apply_theme_recursively(self.tabs[tab_name])
            elif tab_name == 'Learn':
                self.track_feature_usage('learning_system')
            elif tab_name == 'Settings':
                self.track_feature_usage('global_hotkeys')
            
            pass  # Switched to tab
            
            # Apply theme only once with minimal delay to avoid lag (except Stats which is immediate)
            if tab_name in self.tabs and not hasattr(self.tabs[tab_name], '_theme_applied') and tab_name != 'Stats':
                self.after_idle(lambda: self._apply_theme_to_tab_once(tab_name))
            elif tab_name != 'Stats':  # Mark other tabs as theme applied
                if tab_name in self.tabs:
                    self.tabs[tab_name]._theme_applied = True
        
        # Update sidebar selection
        if hasattr(self, 'sidebar'):
            self.sidebar.current_tab = tab_name
    
    def apply_premium_theme(self):
        """Apply premium theme colors and styling"""
        # Update window background
        self.configure(bg='#0F0F23')
        
        # Apply theme to all components
        self._apply_theme_recursively(self)
        
        # Apply theme to all tabs after they're initialized
        self.after(200, self._apply_theme_to_all_tabs)
        
        # Schedule periodic theme reapplication to catch dynamic widgets
        self.after(1000, self._periodic_theme_check)
    
    def _apply_theme_recursively(self, widget):
        """Apply theme to widget and all children"""
        try:
            widget_class = widget.__class__.__name__
            
            # Skip widgets that should maintain their custom styling
            if hasattr(widget, '_premium_styled') and widget._premium_styled:
                return
            
            # Apply theme based on widget type
            if isinstance(widget, tk.Frame):
                current_bg = widget.cget('bg')
                if current_bg in ['white', '#ffffff', '#FFFFFF', 'SystemButtonFace', '']:
                    widget.configure(bg='#0F0F23')
                elif current_bg not in ['#0F0F23', '#1A1B3E', '#410899']:
                    widget.configure(bg='#0F0F23')
            
            elif isinstance(widget, tk.Label):
                current_bg = widget.cget('bg')
                current_fg = widget.cget('fg')
                if current_bg in ['white', '#ffffff', '#FFFFFF', 'SystemButtonFace', '']:
                    widget.configure(bg='#0F0F23', fg='#FFFFFF')
                elif current_bg not in ['#0F0F23', '#1A1B3E', '#410899']:
                    widget.configure(bg='#0F0F23')
                if current_fg in ['black', '#000000', '#000', 'SystemButtonText']:
                    widget.configure(fg='#FFFFFF')
            
            elif isinstance(widget, tk.Text):
                current_bg = widget.cget('bg')
                current_fg = widget.cget('fg')
                # Force all text widgets to dark theme
                widget.configure(bg='#1A1B3E', fg='#FFFFFF', insertbackground='#FFFFFF', 
                               selectbackground='#410899', selectforeground='#FFFFFF',
                               highlightbackground='#410899', highlightcolor='#410899')
                pass  # Applied dark theme to Text widget
            
            elif isinstance(widget, tk.Entry):
                current_bg = widget.cget('bg')
                current_fg = widget.cget('fg')
                # Force all entry widgets to dark theme
                widget.configure(bg='#1A1B3E', fg='#FFFFFF', insertbackground='#FFFFFF',
                               selectbackground='#410899', selectforeground='#FFFFFF',
                               highlightbackground='#410899', highlightcolor='#410899',
                               disabledbackground='#2D2F5A', disabledforeground='#B4B4B8')
                pass  # Applied dark theme to Entry widget
            
            elif isinstance(widget, tk.Button):
                current_bg = widget.cget('bg')
                current_fg = widget.cget('fg')
                # Use proper purple theme colors
                from config import ACCENT_PURPLE
                purple_bg = ACCENT_PURPLE  # #8B5CF6
                purple_hover = '#7C3AED'   # Darker purple for hover/active
                
                # Apply purple styling to ALL buttons unless they're already purple
                if current_bg != purple_bg:
                    widget.configure(
                        bg=purple_bg, 
                        fg='#FFFFFF', 
                        activebackground=purple_hover, 
                        activeforeground='#FFFFFF',
                        bd=0,
                        relief='flat',
                        cursor='hand2',
                        font=('Segoe UI', 10, 'bold')
                    )
                    
                    # Add hover effects for better interactivity
                    def make_hover_handlers(btn):
                        def on_enter(event):
                            btn.config(bg=purple_hover)
                        def on_leave(event):  
                            btn.config(bg=purple_bg)
                        return on_enter, on_leave
                    
                    # Remove existing hover bindings to avoid conflicts
                    widget.unbind('<Enter>')
                    widget.unbind('<Leave>')
                    
                    enter_handler, leave_handler = make_hover_handlers(widget)
                    widget.bind('<Enter>', enter_handler)
                    widget.bind('<Leave>', leave_handler)
                    
                if current_fg in ['black', '#000000', '#000']:
                    widget.configure(fg='#FFFFFF')
            
            elif isinstance(widget, tk.Checkbutton):
                current_bg = widget.cget('bg')
                current_fg = widget.cget('fg')
                # Use proper purple theme colors
                from config import ACCENT_PURPLE
                if current_bg != '#0F0F23':  # Apply to all checkbuttons, not just white ones
                    widget.configure(
                        bg='#0F0F23', 
                        fg='#FFFFFF', 
                        activebackground='#0F0F23', 
                        activeforeground='#FFFFFF', 
                        selectcolor=ACCENT_PURPLE,  # Use proper purple for checkbox
                        font=('Segoe UI', 10),
                        bd=0,
                        highlightthickness=0
                    )
                if current_fg in ['black', '#000000', '#000']:
                    widget.configure(fg='#FFFFFF')
            
            elif isinstance(widget, tk.Radiobutton):
                current_bg = widget.cget('bg')
                current_fg = widget.cget('fg')
                if current_bg in ['white', '#ffffff', '#FFFFFF', 'SystemButtonFace']:
                    widget.configure(bg='#0F0F23', fg='#FFFFFF', activebackground='#0F0F23', activeforeground='#FFFFFF', selectcolor='#410899')
                if current_fg in ['black', '#000000', '#000']:
                    widget.configure(fg='#FFFFFF')
            
            elif isinstance(widget, tk.Listbox):
                current_bg = widget.cget('bg')
                current_fg = widget.cget('fg')
                if current_bg in ['white', '#ffffff', '#FFFFFF', 'SystemListBackground']:
                    widget.configure(bg='#1A1B3E', fg='#FFFFFF', selectbackground='#410899', selectforeground='#FFFFFF')
                if current_fg in ['black', '#000000', '#000']:
                    widget.configure(fg='#FFFFFF')
            
            elif isinstance(widget, tk.Canvas):
                current_bg = widget.cget('bg')
                if current_bg in ['white', '#ffffff', '#FFFFFF', 'SystemCanvas']:
                    widget.configure(bg='#0F0F23')
            
            elif isinstance(widget, (tk.Scrollbar, ttk.Scrollbar)):
                # Hide scrollbar by making it nearly invisible and very thin
                try:
                    if isinstance(widget, tk.Scrollbar):
                        widget.configure(bg='#0F0F23', troughcolor='#0F0F23', activebackground='#0F0F23',
                                       width=1, relief='flat', bd=0, highlightthickness=0)
                    else:  # ttk.Scrollbar
                        # For ttk scrollbars, we'll make them very thin and nearly invisible
                        style = ttk.Style()
                        style.configure('Hidden.Vertical.TScrollbar', 
                                      width=1, 
                                      background='#0F0F23',
                                      troughcolor='#0F0F23',
                                      borderwidth=0,
                                      relief='flat')
                        widget.configure(style='Hidden.Vertical.TScrollbar')
                except:
                    pass
                pass  # Applied dark theme to Scrollbar widget - hidden style
            
            elif isinstance(widget, tk.Scale):
                # Hide scale widgets by making them nearly invisible
                widget.configure(bg='#0F0F23', fg='#0F0F23', troughcolor='#0F0F23',
                               activebackground='#0F0F23', highlightbackground='#0F0F23',
                               bd=0, highlightthickness=0, relief='flat',
                               sliderlength=1, width=1)  # Make slider nearly invisible
                pass  # Applied dark theme to Scale widget - hidden style
            
            elif isinstance(widget, tk.Spinbox):
                widget.configure(bg='#1A1B3E', fg='#FFFFFF', insertbackground='#FFFFFF',
                               selectbackground='#410899', selectforeground='#FFFFFF',
                               buttonbackground='#410899')
                pass  # Applied dark theme to Spinbox widget
            
            # Handle ttk widgets differently
            elif 'ttk.' in widget_class.lower() or hasattr(widget, 'configure'):
                self._apply_ttk_theme(widget)
            
            # Catch-all for any remaining widgets with white backgrounds
            else:
                try:
                    if hasattr(widget, 'cget') and hasattr(widget, 'configure'):
                        current_bg = widget.cget('bg')
                        if current_bg in ['white', '#ffffff', '#FFFFFF', 'SystemButtonFace', 'SystemWindow', '']:
                            # Apply generic dark styling
                            widget.configure(bg='#1A1B3E')
                            print(f"[THEME] Applied fallback dark theme to {widget_class}")
                        
                        # Also check foreground
                        if hasattr(widget, 'cget'):
                            try:
                                current_fg = widget.cget('fg')
                                if current_fg in ['black', '#000000', '#000', 'SystemButtonText']:
                                    widget.configure(fg='#FFFFFF')
                            except:
                                pass
                except:
                    pass
            
            # Recurse to children
            for child in widget.winfo_children():
                self._apply_theme_recursively(child)
                
        except Exception as e:
            pass  # Ignore theme errors
    
    def _apply_ttk_theme(self, widget):
        """Apply theme to ttk widgets"""
        try:
            # Configure ttk widget styles
            style = ttk.Style()
            widget_class = widget.__class__.__name__
            
            # Create a unique style name for this widget type
            style_name = f"Premium.T{widget_class.replace('ttk.', '').replace('tk.', '')}"
            
            if 'Notebook' in widget_class:
                from config import ACCENT_PURPLE
                style.configure(f'Premium.TNotebook', background='#0F0F23', borderwidth=0)
                style.configure(f'Premium.TNotebook.Tab', 
                              background='#1A1B3E', foreground='#FFFFFF', 
                              padding=[10, 5], borderwidth=0)
                style.map(f'Premium.TNotebook.Tab', 
                         background=[('selected', ACCENT_PURPLE), ('active', '#7C3AED')])
                widget.configure(style='Premium.TNotebook')
            
            elif 'Frame' in widget_class:
                style.configure(f'Premium.TFrame', background='#0F0F23', borderwidth=0)
                widget.configure(style='Premium.TFrame')
            
            elif 'Label' in widget_class:
                style.configure(f'Premium.TLabel', background='#0F0F23', foreground='#FFFFFF')
                widget.configure(style='Premium.TLabel')
            
            elif 'Button' in widget_class:
                from config import ACCENT_PURPLE
                style.configure(f'Premium.TButton', 
                              background=ACCENT_PURPLE, foreground='#FFFFFF',
                              borderwidth=0, focuscolor='none')
                style.map(f'Premium.TButton', 
                         background=[('active', '#7C3AED'), ('pressed', '#6D28D9')])
                widget.configure(style='Premium.TButton')
            
            elif 'Scale' in widget_class:
                from config import ACCENT_PURPLE
                style.configure(f'Premium.TScale',
                              background='#1A1B3E',  # Track background
                              troughcolor='#2D2F5A',  # Track/trough color
                              borderwidth=0,
                              sliderlength=20,
                              sliderrelief='flat')
                style.map(f'Premium.TScale',
                         background=[('active', ACCENT_PURPLE), ('pressed', '#7C3AED')],
                         slidercolor=[('active', ACCENT_PURPLE), ('pressed', '#7C3AED')])
                widget.configure(style='Premium.TScale')
            
            elif 'Entry' in widget_class:
                from config import ACCENT_PURPLE
                style.configure(f'Premium.TEntry', 
                              fieldbackground='#1A1B3E', foreground='#FFFFFF', 
                              bordercolor=ACCENT_PURPLE, insertcolor='#FFFFFF')
                style.map(f'Premium.TEntry',
                         focuscolor=[('focus', ACCENT_PURPLE)])
                widget.configure(style='Premium.TEntry')
            
            elif 'Combobox' in widget_class:
                from config import ACCENT_PURPLE
                style.configure(f'Premium.TCombobox', 
                              fieldbackground='#1A1B3E', foreground='#FFFFFF', 
                              bordercolor=ACCENT_PURPLE, arrowcolor='#FFFFFF')
                style.map(f'Premium.TCombobox',
                         focuscolor=[('focus', ACCENT_PURPLE)])
                widget.configure(style='Premium.TCombobox')
            
            elif 'Progressbar' in widget_class:
                from config import ACCENT_PURPLE
                style.configure(f'Premium.TProgressbar',
                              background=ACCENT_PURPLE, troughcolor='#1A1B3E',
                              borderwidth=0, lightcolor=ACCENT_PURPLE, darkcolor=ACCENT_PURPLE)
                widget.configure(style='Premium.TProgressbar')
            
            
            print(f"[THEME] Applied dark theme to {widget_class} widget")
            
        except Exception as e:
            # Try to apply basic styling if ttk styling fails
            try:
                if hasattr(widget, 'configure'):
                    if 'bg' in widget.configure():
                        widget.configure(bg='#1A1B3E')
                    if 'fg' in widget.configure():
                        widget.configure(fg='#FFFFFF')
            except:
                pass
    
    def _apply_theme_to_all_tabs(self):
        """Apply theme to all tab contents"""
        try:
            for tab_name, tab_instance in self.tabs.items():
                # Apply theme to each tab silently
                self._apply_theme_recursively(tab_instance)
                
                # Force update the tab
                tab_instance.update_idletasks()
                
        except Exception as e:
            print(f"[PREMIUM] Error applying theme to tabs: {e}")
    
    def _apply_theme_to_tab_once(self, tab_name):
        """Apply theme to a specific tab only once to avoid performance issues"""
        try:
            if tab_name in self.tabs:
                tab_instance = self.tabs[tab_name]
                self._apply_theme_recursively(tab_instance)
                # Mark as theme applied to avoid reapplying
                tab_instance._theme_applied = True
        except Exception as e:
            print(f"[PREMIUM] Error applying theme to tab {tab_name}: {e}")
    
    def _periodic_theme_check(self):
        """Periodically check and fix any widgets that lost their theme"""
        try:
            # Only reapply theme to current visible tab less frequently
            if hasattr(self, 'current_tab') and self.current_tab in self.tabs:
                # Only apply if not already applied recently
                tab_instance = self.tabs[self.current_tab]
                if not hasattr(tab_instance, '_theme_last_applied') or \
                   (hasattr(tab_instance, '_theme_last_applied') and 
                    (tab_instance._theme_last_applied + 5000) < self.tk.call('clock', 'milliseconds')):
                    self._apply_theme_recursively(tab_instance)
                    tab_instance._theme_last_applied = self.tk.call('clock', 'milliseconds')
            
            # Schedule next check (less frequent to reduce lag)
            self.after(5000, self._periodic_theme_check)
        except Exception as e:
            print(f"[PREMIUM] Error in periodic theme check: {e}")
    
    def force_background_refresh(self):
        """Force refresh all background images - but don't restart if already running"""
        try:
            pass  # Force background refresh
            
            # Check animation state
            has_video_frames = hasattr(self, 'video_frames') and len(getattr(self, 'video_frames', [])) > 0
            has_bg_canvas = hasattr(self, 'bg_canvas') and self.bg_canvas.winfo_exists() if hasattr(self, 'bg_canvas') else False
            has_bg_label = hasattr(self, 'bg_label') and self.bg_label.winfo_exists() if hasattr(self, 'bg_label') else False
            
            pass  # Check refresh state
            
            # DON'T reload main background if animation is already running
            if has_video_frames and (has_bg_canvas or has_bg_label):
                print("[PREMIUM] Background animation already running - skipping reload")
                # Just ensure it stays behind
                if has_bg_canvas:
                    pass  # Lower existing canvas
                    # Keep canvas behind UI elements
                    for child in self.winfo_children():
                        if child != self.bg_canvas:
                            child.tkraise(self.bg_canvas)
                elif has_bg_label:
                    pass  # Lower existing label
                    self.bg_label.lower()
                return
            
            # Only reload if background is missing
            print("[PREMIUM] Background missing - reloading...")
            self.load_main_background()
            
            # Ensure background stays behind everything
            if hasattr(self, 'bg_canvas'):
                self.safe_lower_canvas()
            elif hasattr(self, 'bg_label'):
                self.bg_label.lower()
            
            # Refresh sidebar background
            if hasattr(self, 'sidebar'):
                self.sidebar.load_sidebar_background()
            
            # Refresh all card backgrounds
            self._refresh_card_backgrounds(self)
            
        except Exception as e:
            print(f"[PREMIUM] Error refreshing backgrounds: {e}")
    
    def _refresh_card_backgrounds(self, widget):
        """Recursively refresh card backgrounds"""
        try:
            # Check if this widget is a PremiumCard
            if hasattr(widget, 'load_card_background'):
                widget.load_card_background()
            
            # Recurse to children
            for child in widget.winfo_children():
                self._refresh_card_backgrounds(child)
                
        except Exception as e:
            pass
    
    def force_authentication(self):
        """Force user authentication before app access"""
        try:
            # Try to get saved user first
            saved_user = get_saved_user()
            if saved_user:
                self.user = saved_user
                self.authenticated = True
                self.on_successful_auth(saved_user)
                print(f"[AUTH] Authenticated with saved credentials: {saved_user.get('email', 'user')}")
                return
            
            # No saved user - force login
            self.show_login_screen()
            
        except Exception as e:
            print(f"[AUTH] Authentication error: {e}")
            self.show_login_screen()
    
    def show_login_screen(self):
        """Show login screen and block access until authenticated"""
        # Create login overlay
        self.login_overlay = tk.Frame(self, bg='#0F0F23')
        self.login_overlay.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Login content
        login_frame = tk.Frame(self.login_overlay, bg='#1A1B3E', pady=40, padx=60)
        login_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title = tk.Label(login_frame, text="SlyWriter", 
                        font=('Arial', 24, 'bold'), fg='white', bg='#1A1B3E')
        title.pack(pady=(0, 20))
        
        # Subtitle
        subtitle = tk.Label(login_frame, text="Please sign in to continue", 
                           font=('Arial', 14), fg='#A0A0A0', bg='#1A1B3E')
        subtitle.pack(pady=(0, 30))
        
        # Login button
        login_btn = tk.Button(login_frame, text="Sign in with Google", 
                             font=('Arial', 12, 'bold'), 
                             bg='#4285F4', fg='white', 
                             padx=30, pady=12,
                             command=self.perform_google_login,
                             cursor='hand2')
        login_btn.pack(pady=10)
        
        # Status label
        self.login_status = tk.Label(login_frame, text="", 
                                   font=('Arial', 10), fg='#FF6B6B', bg='#1A1B3E')
        self.login_status.pack(pady=(10, 0))
        
        # Show the window
        self.deiconify()
    
    def perform_google_login(self):
        """Perform Google OAuth login"""
        try:
            # Check if login_status exists before updating
            if hasattr(self, 'login_status') and self.login_status.winfo_exists():
                self.login_status.configure(text="Signing in...", fg='#FFA500')
                self.update()
            
            # Import here to avoid circular imports
            from auth import sign_in_with_google
            
            user_info = sign_in_with_google()
            
            if user_info:
                self.user = user_info
                self.authenticated = True
                
                # Remove login overlay
                if hasattr(self, 'login_overlay'):
                    self.login_overlay.destroy()
                
                # Continue with app initialization
                self.on_successful_auth(user_info)
                print(f"[AUTH] Successfully authenticated: {user_info.get('email', 'user')}")
            else:
                # Check if login_status still exists before updating
                if hasattr(self, 'login_status') and self.login_status.winfo_exists():
                    self.login_status.configure(text="Login failed. Please try again.", fg='#FF6B6B')
                
        except Exception as e:
            print(f"[AUTH] Login error: {e}")
            # Check if login_status still exists before updating
            try:
                if hasattr(self, 'login_status') and self.login_status.winfo_exists():
                    self.login_status.configure(text="Login error. Please try again.", fg='#FF6B6B')
            except:
                print("[AUTH] Could not update login status - widget may have been destroyed")
    
    def on_successful_auth(self, user_info):
        """Handle successful authentication"""
        self.user = user_info
        self.authenticated = True
        
        # Hide window during setup to prevent threading issues
        self.withdraw()
        
        # Create premium UI structure first
        self.create_premium_layout()
        
        # Initialize tabs
        self.initialize_tabs()
        
        # Apply premium theme
        self.apply_premium_theme()
        
        # Show window first
        self.after(50, self.show_premium_app)
        
        # Load static background image
        self.after(200, self.load_static_background)
        
        # Update UI with user info
        self.after(300, self.update_user_info_ui)
        
        # Initialize feature spotlight system
        self.after(500, self.initialize_spotlight_system)
    
    def initialize_spotlight_system(self):
        """Initialize the feature discovery and spotlight system"""
        try:
            self.spotlight = FeatureSpotlight(self)
            print("[SPOTLIGHT] Feature discovery system initialized")
            
            # Show welcome tip for new users after a short delay
            self.after(3000, self.show_welcome_tip_if_new_user)
            
        except Exception as e:
            print(f"[SPOTLIGHT] Error initializing spotlight system: {e}")
    
    def show_welcome_tip_if_new_user(self):
        """Show a welcome tip for new users"""
        try:
            if hasattr(self, 'spotlight'):
                stats = self.spotlight.get_discovery_stats()
                
                # If user has discovered less than 20% of features, show a tip
                if stats['discovery_percentage'] < 20:
                    self.spotlight.show_tip()
                    
        except Exception as e:
            print(f"[SPOTLIGHT] Error showing welcome tip: {e}")
    
    def track_feature_usage(self, feature_name):
        """Track feature usage for spotlight system"""
        try:
            if hasattr(self, 'spotlight'):
                self.spotlight.track_feature_usage(feature_name)
        except Exception as e:
            print(f"[SPOTLIGHT] Error tracking feature usage: {e}")
    
    def show_random_tip(self):
        """Manually show a random tip (for testing/debugging)"""
        try:
            if hasattr(self, 'spotlight'):
                self.spotlight.show_tip()
        except Exception as e:
            print(f"[SPOTLIGHT] Error showing random tip: {e}")
    
    def show_feature_spotlight(self, feature_id):
        """Show spotlight for a specific feature"""
        try:
            if hasattr(self, 'spotlight'):
                self.spotlight.show_feature_spotlight(feature_id)
        except Exception as e:
            print(f"[SPOTLIGHT] Error showing feature spotlight: {e}")
    
    def regenerate_background(self):
        """Force regeneration of background to eliminate any banding artifacts"""
        try:
            print("[PREMIUM] 🔥 FORCE REGENERATING background - eliminating ALL artifacts!")
            from create_static_bg import create_static_background
            
            # Remove existing background
            import os
            bg_path = os.path.join('assets', 'backgrounds', 'main_bg.png')
            if os.path.exists(bg_path):
                os.remove(bg_path)
                print("[PREMIUM] 🗑️ Removed old background with potential artifacts")
            
            # Create new perfect background
            new_bg_path = create_static_background()
            print(f"[PREMIUM] ✅ Generated PERFECT background: {new_bg_path}")
            
            # Reload background immediately
            self.load_static_background()
            
            # Show notification
            self.show_notification("🎨 Background regenerated - zero artifacts!")
            
        except Exception as e:
            print(f"[PREMIUM] Error regenerating background: {e}")
    
    def show_auth_required_message(self):
        """Show authentication required message and redirect to login"""
        print("[AUTH] Authentication required - redirecting to login")
        
        # Clear any existing UI
        for widget in self.winfo_children():
            widget.destroy()
        
        # Show login screen again
        self.authenticated = False
        self.user = None
        self.show_login_screen()
    
    def check_auth_status(self):
        """Check if user is still authenticated"""
        if not hasattr(self, 'authenticated') or not self.authenticated:
            return False
        
        # Additional check: verify saved credentials are still valid
        try:
            from auth import get_saved_user
            saved_user = get_saved_user()
            if not saved_user:
                self.authenticated = False
                return False
        except:
            self.authenticated = False
            return False
        
        return True
    
    def update_user_info_ui(self):
        """Update UI components with Google user information"""
        if not self.user:
            print("[UI] No user info available for UI update")
            return
        
        # Update header with user information
        if hasattr(self, 'header') and self.header:
            try:
                self.header.update_user_info(self.user)
                print(f"[UI] Updated header with user info: {self.user.get('name', 'Unknown')}")
            except Exception as e:
                print(f"[UI] Error updating header: {e}")
        
        # Update any other UI components that show user info
        self.update_user_plan_info()
    
    def update_user_plan_info(self):
        """Update user plan information across the UI"""
        if not self.user:
            return
        
        # For now, we'll use a default plan - this can be enhanced with server integration
        user_plan = "Premium"  # This should come from server/user data
        
        # Store plan info
        if hasattr(self, 'cfg'):
            self.cfg['user_plan'] = user_plan
        
        print(f"[UI] User plan set to: {user_plan}")
    
    def check_saved_login(self):
        """Check for saved user login - DEPRECATED, use force_authentication instead"""
        pass
    
    def on_login(self, user_info):
        """Handle user login"""
        self.user = user_info
        
        # Enable all tabs
        # In premium version, all tabs are always accessible
        
        # Update account tab
        if 'Account' in self.tabs:
            try:
                self.tabs['Account'].update_for_login(user_info)
                self.tabs['Account'].usage_mgr.load_usage()
                self.tabs['Account'].usage_mgr.update_usage_display()
            except Exception as e:
                print(f"[PREMIUM] Error updating account tab: {e}")
        
        # Update typing tab
        if 'Typing' in self.tabs:
            try:
                self.tabs['Typing'].update_from_config()
            except Exception as e:
                print(f"[PREMIUM] Error updating typing tab: {e}")
        
        print(f"[PREMIUM] User logged in: {user_info.get('email', 'Unknown')}")
    
    def on_logout(self):
        """Handle user logout"""
        self.user = None
        
        # Switch to account tab
        self.switch_to_tab('Account')
        
        # Update tabs
        if 'Account' in self.tabs:
            try:
                # Account tab will handle its own logout UI
                pass
            except Exception as e:
                print(f"[PREMIUM] Error during logout: {e}")
        
        print("[PREMIUM] User logged out")
    
    def create_simple_background_effect(self):
        """Create a simple animated background effect using window background color"""
        try:
            import math
            import time
            
            print("[SIMPLE BG] Creating simple background animation")
            
            # Start simple color animation
            self.bg_animation_phase = 0
            self.animate_simple_background()
            
        except Exception as e:
            print(f"[SIMPLE BG] Error creating background effect: {e}")
    
    def animate_simple_background(self):
        """Animate the window background with subtle color changes"""
        try:
            import math
            
            # Create subtle color animation
            time_factor = self.bg_animation_phase * 0.05
            
            # Base colors (dark purple theme)
            base_r, base_g, base_b = 15, 15, 35  # #0F0F23
            
            # Add subtle animation
            r = int(base_r + math.sin(time_factor) * 3)
            g = int(base_g + math.sin(time_factor * 1.3) * 3) 
            b = int(base_b + math.sin(time_factor * 0.7) * 8)
            
            # Ensure values stay in valid range
            r = max(10, min(25, r))
            g = max(10, min(25, g))
            b = max(25, min(50, b))
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # Apply to main window
            self.configure(bg=color)
            
            self.bg_animation_phase += 1
            
            # Schedule next frame (slow animation)
            self.after(100, self.animate_simple_background)
            
        except Exception as e:
            # Fallback to static color
            self.configure(bg='#0F0F23')
            # Try again later
            self.after(1000, self.animate_simple_background)
    
    def create_background_overlay_disabled(self):
        """Create background animation as an overlay on the main content area"""
        try:
            print("[OVERLAY] Creating background overlay on main content area")
            
            mp4_path = os.path.join('assets', 'backgrounds', 'main_bg.mp4')
            gif_path = os.path.join('assets', 'backgrounds', 'main_bg.gif')
            
            if not (os.path.exists(mp4_path) or os.path.exists(gif_path)):
                print("[OVERLAY] No animation files found")
                return
                
            # Create overlay canvas on the main content area instead of root
            if hasattr(self, 'main_content') and self.main_content.winfo_exists():
                # Get main content area dimensions
                self.main_content.update_idletasks()
                width = self.main_content.winfo_width() or 800
                height = self.main_content.winfo_height() or 600
                
                print(f"[OVERLAY] Creating overlay on main_content ({width}x{height})")
                
                # Create overlay canvas
                self.overlay_canvas = tk.Canvas(self.main_content, 
                                              width=width, height=height,
                                              highlightthickness=0, bd=0, bg='#0F0F23')
                self.overlay_canvas.place(x=0, y=0, relwidth=1, relheight=1)
                
                # Load and start animation on overlay
                if os.path.exists(mp4_path):
                    self.load_mp4_on_overlay(mp4_path)
                elif os.path.exists(gif_path):
                    self.load_gif_on_overlay(gif_path)
                    
                print("[OVERLAY] Background overlay created successfully")
            else:
                print("[OVERLAY] Main content area not found")
                
        except Exception as e:
            print(f"[OVERLAY] Error creating background overlay: {e}")
    
    def load_gif_on_overlay(self, gif_path):
        """Load GIF animation on the overlay canvas"""
        try:
            from PIL import Image, ImageTk
            
            gif_image = Image.open(gif_path)
            self.overlay_frames = []
            
            frame_num = 0
            while True:
                try:
                    gif_image.seek(frame_num)
                    # Resize to fit overlay
                    width = self.overlay_canvas.winfo_width() or 800
                    height = self.overlay_canvas.winfo_height() or 600
                    frame = gif_image.copy().resize((width, height), Image.Resampling.LANCZOS)
                    photo_frame = ImageTk.PhotoImage(frame)
                    self.overlay_frames.append(photo_frame)
                    frame_num += 1
                except EOFError:
                    break
            
            if self.overlay_frames:
                # Create image on overlay canvas
                self.overlay_image = self.overlay_canvas.create_image(
                    0, 0, anchor='nw', image=self.overlay_frames[0])
                
                # Start overlay animation
                self.overlay_frame_idx = 0
                self.animate_overlay()
                
                # Keep overlay visible by raising it periodically
                self.maintain_overlay_visibility()
                
                print(f"[OVERLAY] Loaded {len(self.overlay_frames)} GIF frames")
                
        except Exception as e:
            print(f"[OVERLAY] Error loading GIF: {e}")
    
    def load_mp4_on_overlay(self, mp4_path):
        """Load MP4 animation on the overlay canvas"""
        try:
            import cv2
            from PIL import Image, ImageTk
            
            cap = cv2.VideoCapture(mp4_path)
            self.overlay_frames = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize to fit overlay
                width = self.overlay_canvas.winfo_width() or 800
                height = self.overlay_canvas.winfo_height() or 600
                
                pil_image = Image.fromarray(frame)
                pil_image = pil_image.resize((width, height), Image.Resampling.LANCZOS)
                photo_frame = ImageTk.PhotoImage(pil_image)
                self.overlay_frames.append(photo_frame)
            
            cap.release()
            
            if self.overlay_frames:
                # Create image on overlay canvas
                self.overlay_image = self.overlay_canvas.create_image(
                    0, 0, anchor='nw', image=self.overlay_frames[0])
                
                # Start overlay animation
                self.overlay_frame_idx = 0
                self.animate_overlay()
                
                # Keep overlay visible by raising it periodically
                self.maintain_overlay_visibility()
                
                print(f"[OVERLAY] Loaded {len(self.overlay_frames)} MP4 frames")
            
        except ImportError:
            print("[OVERLAY] OpenCV not available, falling back to GIF")
            # Try GIF instead
            gif_path = os.path.join('assets', 'backgrounds', 'main_bg.gif')
            if os.path.exists(gif_path):
                self.load_gif_on_overlay(gif_path)
        except Exception as e:
            print(f"[OVERLAY] Error loading MP4: {e}")
    
    def animate_overlay(self):
        """Animate the overlay background"""
        try:
            if hasattr(self, 'overlay_frames') and self.overlay_frames:
                frame = self.overlay_frames[self.overlay_frame_idx]
                self.overlay_canvas.itemconfig(self.overlay_image, image=frame)
                
                self.overlay_frame_idx = (self.overlay_frame_idx + 1) % len(self.overlay_frames)
                
                # Schedule next frame (12 FPS for GIF)
                self.after(83, self.animate_overlay)
                
        except Exception as e:
            print(f"[OVERLAY] Animation error: {e}")
    
    def maintain_overlay_visibility(self):
        """Keep the overlay canvas visible by continuously raising it"""
        try:
            if hasattr(self, 'overlay_canvas') and self.overlay_canvas.winfo_exists():
                # Only lower the overlay behind interactive elements, don't raise it aggressively
                try:
                    # Lower overlay so UI elements can be clicked
                    self.overlay_canvas.lower()
                except:
                    pass  # Ignore canvas positioning errors
                
                # Schedule next visibility check - much less frequently
                self.after(2000, self.maintain_overlay_visibility)  # Check every 2 seconds
                
        except Exception as e:
            # Skip error logging to reduce spam
            # Try again later
            self.after(5000, self.maintain_overlay_visibility)
    
    def raise_all_ui_above_canvas(self):
        """Aggressively raise all UI elements above the background canvas"""
        try:
            print("[UI RAISE] Raising all UI elements above background canvas")
            
            # If we have a canvas, make sure all other elements are above it
            if hasattr(self, 'bg_canvas') and self.bg_canvas.winfo_exists():
                print("[UI RAISE] Canvas exists, raising UI elements...")
                
                # Raise main container and all its children
                if hasattr(self, 'main_container'):
                    self.main_container.tkraise()
                    print("[UI RAISE] Raised main_container")
                    
                    # Recursively raise all children
                    self.raise_widget_tree(self.main_container)
                
                print("[UI RAISE] All UI elements raised above canvas")
            else:
                print("[UI RAISE] No canvas found, UI raising not needed")
                
        except Exception as e:
            print(f"[UI RAISE] Error raising UI elements: {e}")
    
    def raise_widget_tree(self, widget):
        """Recursively raise a widget and all its children"""
        try:
            widget.tkraise()
            for child in widget.winfo_children():
                self.raise_widget_tree(child)
        except:
            pass  # Skip widgets that can't be raised
    
    def final_canvas_position(self):
        """DISABLED - Canvas operations cause artifacts"""
        return  # Disabled completely
        try:
            if hasattr(self, 'bg_canvas') and self.bg_canvas.winfo_exists():
                print("[CANVAS] Final positioning - ensuring background is visible")
                
                # Place canvas to fill the entire window
                self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
                
                # Lower it to the very bottom
                try:
                    self.bg_canvas.lower()
                except Exception as e:
                    print(f"[CANVAS] Lower error (ignoring): {e}")
                    # Alternative positioning - raise everything else above it
                    for child in self.winfo_children():
                        if child != self.bg_canvas:
                            try:
                                child.tkraise()
                            except:
                                pass
                
                # Verify it exists and get debug info
                try:
                    canvas_info = self.bg_canvas.place_info()
                    canvas_visible = self.bg_canvas.winfo_viewable()
                    canvas_size = f"{self.bg_canvas.winfo_width()}x{self.bg_canvas.winfo_height()}"
                    print(f"[CANVAS] Final state - Visible: {canvas_visible}, Size: {canvas_size}")
                    print(f"[CANVAS] Position info: {canvas_info}")
                except Exception as e:
                    print(f"[CANVAS] Error getting final debug info: {e}")
                    
        except Exception as e:
            print(f"[CANVAS] Error in final positioning: {e}")
    
    def show_premium_app(self):
        """Show the premium app after loading is complete"""
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
            
            # Ensure background stays behind everything
            if hasattr(self, 'bg_label'):
                self.bg_label.lower()
            # Canvas operations disabled to prevent artifacts
            
            # Force background refresh after app is visible
            self.after(100, self.force_background_refresh)
            
            # Canvas operations disabled to prevent visual artifacts
            
            print("[PREMIUM] Premium UI loaded successfully! 🎨✨")
        except Exception as e:
            print(f"[PREMIUM] Error showing app: {e}")

    # ========================================
    # MISSING METHODS FROM REGULAR TYPINGAPP
    # ========================================
    
    def start_typing(self):
        """Start typing operation - delegate to typing tab"""
        if 'Typing' in self.tabs:
            self.tabs['Typing'].start_typing()
    
    def stop_typing(self):
        """Stop typing operation - delegate to typing tab"""
        if 'Typing' in self.tabs:
            self.tabs['Typing'].stop_typing()
    
    def pause_typing(self):
        """Pause typing operation - delegate to typing tab"""
        if 'Typing' in self.tabs:
            self.tabs['Typing'].pause_typing()

    def on_setting_change(self):
        """Handle setting changes - delegate to config module"""
        try:
            from sly_config import on_setting_change as config_on_setting_change
            config_on_setting_change(self)
        except Exception as e:
            print(f"[PREMIUM] Error in on_setting_change: {e}")

    def on_profile_change(self, event=None):
        """Handle profile changes - delegate to config module"""
        try:
            from sly_config import on_profile_change as config_on_profile_change
            config_on_profile_change(self)
        except Exception as e:
            print(f"[PREMIUM] Error in on_profile_change: {e}")

    def reset_typing_settings(self):
        """Reset typing settings - delegate to config module"""
        try:
            from sly_config import reset_typing_settings as config_reset_typing_settings
            config_reset_typing_settings(self)
        except Exception as e:
            print(f"[PREMIUM] Error in reset_typing_settings: {e}")

    def set_start_hotkey(self, hotkey):
        """Set start hotkey - delegate to hotkeys module"""
        print(f"[PREMIUM] set_start_hotkey called with: {hotkey}")
        try:
            from sly_hotkeys import set_start_hotkey as hotkeys_set_start_hotkey
            hotkeys_set_start_hotkey(self, hotkey)
            print(f"[PREMIUM] Successfully set start hotkey: {hotkey}")
        except Exception as e:
            print(f"[PREMIUM] Error setting start hotkey: {e}")

    def set_stop_hotkey(self, hotkey):
        """Set stop hotkey - delegate to hotkeys module"""
        try:
            from sly_hotkeys import set_stop_hotkey as hotkeys_set_stop_hotkey
            hotkeys_set_stop_hotkey(self, hotkey)
        except Exception as e:
            print(f"[PREMIUM] Error setting stop hotkey: {e}")

    def set_pause_hotkey(self, hotkey):
        """Set pause hotkey - delegate to hotkeys module"""
        try:
            from sly_hotkeys import set_pause_hotkey as hotkeys_set_pause_hotkey
            hotkeys_set_pause_hotkey(self, hotkey)
        except Exception as e:
            print(f"[PREMIUM] Error setting pause hotkey: {e}")

    def set_overlay_hotkey(self, hotkey):
        """Set overlay hotkey - delegate to hotkeys module"""
        print(f"[PREMIUM] set_overlay_hotkey called with: {hotkey}")
        try:
            from sly_hotkeys import set_overlay_hotkey as hotkeys_set_overlay_hotkey
            hotkeys_set_overlay_hotkey(self, hotkey)
            print(f"[PREMIUM] Successfully set overlay hotkey: {hotkey}")
        except Exception as e:
            print(f"[PREMIUM] Error setting overlay hotkey: {e}")

    def set_ai_generation_hotkey(self, hotkey):
        """Set AI generation hotkey - delegate to hotkeys module"""
        try:
            from sly_hotkeys import set_ai_generation_hotkey as hotkeys_set_ai_generation_hotkey
            hotkeys_set_ai_generation_hotkey(self, hotkey)
        except Exception as e:
            print(f"[PREMIUM] Error setting AI generation hotkey: {e}")

    def reset_hotkeys(self):
        """Reset hotkeys - delegate to hotkeys module"""
        try:
            from sly_hotkeys import reset_hotkeys as hotkeys_reset_hotkeys
            hotkeys_reset_hotkeys(self)
        except Exception as e:
            print(f"[PREMIUM] Error resetting hotkeys: {e}")

    def save_config(self):
        """Save configuration - delegate to config module"""
        try:
            from sly_config import save_config as config_save_config
            config_save_config(self.cfg)
        except Exception as e:
            print(f"[PREMIUM] Error saving config: {e}")

    def load_main_background(self):
        """Load main background - delegate to existing method"""
        try:
            # IMPORTANT: Destroy any existing canvas to prevent ghost bars
            if hasattr(self, 'bg_canvas'):
                try:
                    self.bg_canvas.destroy()
                    delattr(self, 'bg_canvas')
                    print("[PREMIUM] Destroyed old background canvas")
                except:
                    pass
            
            # Use only static background, no animations
            self.load_static_background()
        except Exception as e:
            print(f"[PREMIUM] Error loading main background: {e}")


def run_premium_app():
    """Run the premium SlyWriter application"""
    try:
        app = PremiumSlyWriter()
        app.mainloop()
    except Exception as e:
        print(f"[PREMIUM] Error starting app: {e}")
        # Fallback to original app
        from sly_app import TypingApp
        fallback_app = TypingApp()
        fallback_app.mainloop()


if __name__ == "__main__":
    run_premium_app()