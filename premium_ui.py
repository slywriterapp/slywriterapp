# premium_ui.py - Modern Premium UI Components

import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import math
import threading
import io

class PremiumSidebar:
    """Premium sidebar navigation with smooth animations"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.current_tab = None
        self.currently_hovered_button = None
        
        # Create sidebar frame
        self.sidebar = tk.Frame(parent, width=280, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        
        # Load background
        self.load_sidebar_background()
        
        # Create navigation items
        self.nav_items = []
        self.create_navigation()
        
    def load_sidebar_background(self):
        """Load and apply custom sidebar background with gradient support"""
        try:
            # Get sidebar dimensions
            self.sidebar.update_idletasks()
            width = 280
            height = self.sidebar.winfo_height() or 900
            
            bg_path = os.path.join('assets', 'backgrounds', 'sidebar_bg.png')
            
            # Define gradient fallback for sidebar
            sidebar_gradient = {
                'color1': '#1A1B3E',  # Sidebar dark blue
                'color2': '#2D2F5A',  # Slightly lighter for depth
                'direction': 'vertical'
            }
            
            # Load background or create gradient
            self.bg_photo = self.load_or_create_background(bg_path, width, height, sidebar_gradient)
            
            if self.bg_photo:
                # Remove any existing background
                if hasattr(self, 'sidebar_bg_label'):
                    self.sidebar_bg_label.destroy()
                
                # Create background label that fills the sidebar
                self.sidebar_bg_label = tk.Label(self.sidebar, image=self.bg_photo, bd=0, highlightthickness=0)
                self.sidebar_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                self.sidebar_bg_label.lower()  # Send to back
                self.sidebar_bg_label.image = self.bg_photo  # Keep reference
                
                # Ensure sidebar background matches
                self.sidebar.configure(bg='#0F0F23', highlightthickness=0)
                
                if os.path.exists(bg_path):
                    print(f"[SIDEBAR] Loaded custom sidebar background from {bg_path}")
                else:
                    print(f"[SIDEBAR] Created gradient sidebar background ({width}x{height})")
                return True
            else:
                raise Exception("Failed to create sidebar background")
                
        except Exception as e:
            print(f"[SIDEBAR] Error loading background: {e}")
        
        # Fallback to solid color
        self.sidebar.configure(bg='#0F0F23', highlightthickness=0)
        print(f"[SIDEBAR] Using fallback solid color background")
        return False
    
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
    
    def create_gradient_background(self, width, height, color1='#1A1B3E', color2='#2D2F5A', direction='vertical'):
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
    
    def create_navigation(self):
        """Create premium navigation buttons"""
        # Header with logo and title - reduced height to avoid overlap
        header_frame = tk.Frame(self.sidebar, bg='#0F0F23', height=50, highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        header_frame.pack(fill='x', pady=(90, 20))  # Increased top padding to go below main header
        header_frame.pack_propagate(False)
        
        # Logo and title
        title_frame = tk.Frame(header_frame, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        title_frame.pack(expand=True)
        
        # Load logo if available
        try:
            logo_path = os.path.join('assets', 'icons', 'logo.png')
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((24, 24), Image.Resampling.LANCZOS)  # Smaller logo
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                
                logo_label = tk.Label(title_frame, image=self.logo_photo, bg='#0F0F23', highlightthickness=0, bd=0)
                logo_label.pack()
        except:
            pass
            
        title_label = tk.Label(title_frame, text="SlyWriter", 
                              font=('Segoe UI', 14, 'bold'),  # Smaller font
                              fg='#FFFFFF', bg='#0F0F23', highlightthickness=0, bd=0)
        title_label.pack(pady=(4, 0))  # Reduced padding
        
        # Navigation items
        nav_items = [
            ('Typing', 'home', 'Main typing functionality'),
            ('AI Hub', 'robot', 'AI-powered features'),
            ('Learn', 'book', 'Educational content'),
            ('Stats', 'chart', 'Analytics and reporting'),
            ('Overlay', 'monitor', 'Real-time overlay display'),
            ('Settings', 'settings', 'Configuration'),
            ('Account', 'user', 'Profile and billing')
        ]
        
        # Navigation container
        nav_container = tk.Frame(self.sidebar, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        nav_container.pack(fill='x', padx=20)
        
        for name, icon, tooltip in nav_items:
            nav_item = self.create_nav_item(nav_container, name, icon, tooltip)
            self.nav_items.append(nav_item)
    
    def create_nav_item(self, parent, name, icon_name, tooltip):
        """Create a single navigation item with premium styling"""
        # Main container
        item_frame = tk.Frame(parent, bg='#1A1B3E', height=48)
        item_frame.pack(fill='x', pady=2)
        item_frame.pack_propagate(False)
        
        # Create gradient background for nav item
        nav_bg = self.create_nav_button_background(item_frame, name)
        
        # Interactive button
        btn = tk.Button(item_frame, 
                       text=f"  {name}",
                       font=('Segoe UI', 11, 'normal'),
                       fg='#B4B4B8',
                       bg='#1A1B3E',
                       activebackground='#410899',
                       activeforeground='#FFFFFF',
                       relief='flat',
                       anchor='w',
                       padx=20,
                       bd=0,
                       cursor='hand2')
        btn.pack(fill='both', expand=True)
        
        # Load and set icon
        self.set_nav_icon(btn, icon_name)
        
        # Bind events
        btn.bind('<Button-1>', lambda e: self.on_nav_click(name))
        btn.bind('<Enter>', lambda e: self.on_nav_hover(btn, True))
        btn.bind('<Leave>', lambda e: self.on_nav_hover(btn, False))
        
        return {'frame': item_frame, 'button': btn, 'name': name, 'background': nav_bg}
    
    def create_nav_button_background(self, parent, name):
        """Create gradient background for navigation button"""
        try:
            # Check for custom nav button backgrounds
            bg_paths = {
                'normal': os.path.join('assets', 'backgrounds', 'nav_button_normal.png'),
                'hover': os.path.join('assets', 'backgrounds', 'nav_button_hover.png'),
                'active': os.path.join('assets', 'backgrounds', 'nav_button_active.png')
            }
            
            width = 280
            height = 48
            
            # Try to load custom backgrounds or create gradients
            backgrounds = {}
            for state, path in bg_paths.items():
                if os.path.exists(path):
                    # Load custom background
                    bg_image = Image.open(path)
                    bg_image = bg_image.resize((width, height), Image.Resampling.LANCZOS)
                    backgrounds[state] = ImageTk.PhotoImage(bg_image)
                    print(f"[NAV] Loaded custom {state} button background")
                else:
                    # Create gradient background
                    gradient_configs = {
                        'normal': {'color1': '#1A1B3E', 'color2': '#2D2F5A', 'direction': 'horizontal'},
                        'hover': {'color1': '#410899', 'color2': '#5D1FB3', 'direction': 'horizontal'}, 
                        'active': {'color1': '#5D1FB3', 'color2': '#410899', 'direction': 'horizontal'}
                    }
                    gradient = self.create_gradient_background(width, height, **gradient_configs[state])
                    if gradient:
                        backgrounds[state] = gradient
                        print(f"[NAV] Created gradient {state} button background")
            
            return backgrounds
            
        except Exception as e:
            print(f"[NAV] Error creating button backgrounds: {e}")
            return None
    
    def set_nav_icon(self, button, icon_name):
        """Load and set icon for navigation button"""
        # Emoji fallbacks for each icon
        emoji_fallbacks = {
            'home': '⌨️',      # Typing
            'robot': '🤖',     # AI Hub  
            'book': '🎓',      # Learn
            'chart': '📊',     # Stats
            'monitor': '👁',    # Overlay
            'settings': '⚙️',  # Settings
            'user': '👤'       # Account
        }
        
        try:
            icon_path = os.path.join('assets', 'icons', f'{icon_name}.png')
            if os.path.exists(icon_path):
                icon_img = Image.open(icon_path)
                icon_img = icon_img.resize((20, 20), Image.Resampling.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_img)
                
                button.configure(image=icon_photo, compound='left')
                button.image = icon_photo  # Keep reference
            else:
                # Use emoji fallback if icon file doesn't exist
                emoji = emoji_fallbacks.get(icon_name, '')
                current_text = button.cget('text').strip()
                if emoji and not current_text.startswith(emoji):
                    button.configure(text=f"  {emoji} {current_text}")
        except Exception as e:
            # Use emoji fallback on any error
            emoji = emoji_fallbacks.get(icon_name, '')
            current_text = button.cget('text').strip()
            if emoji and not current_text.startswith(emoji):
                button.configure(text=f"  {emoji} {current_text}")
            print(f"[SIDEBAR] Using emoji fallback for {icon_name}: {e}")
    
    def on_nav_hover(self, button, is_hover):
        """Handle navigation item hover effects"""
        # Find which tab this button corresponds to
        button_tab_name = None
        for item in self.nav_items:
            if item['button'] == button:
                button_tab_name = item['name']
                break
        
        # Don't change active tab appearance
        if button_tab_name == self.current_tab:
            return
        
        if is_hover:
            # Highlight on hover (only if not active tab)
            button.configure(bg='#2D2F5A', fg='#FFFFFF')
        else:
            # Reset to normal when not hovering
            button.configure(bg='#1A1B3E', fg='#B4B4B8')
    
    def on_nav_click(self, tab_name):
        """Handle navigation item clicks"""
        # Quick authentication check - no expensive calls
        if not hasattr(self.app, 'authenticated') or not self.app.authenticated:
            print(f"[AUTH] Navigation blocked - authentication required for {tab_name}")
            if hasattr(self.app, 'show_auth_required_message'):
                self.app.show_auth_required_message()
            return
        
        # Update active state
        for item in self.nav_items:
            if item['name'] == tab_name:
                item['button'].configure(bg='#410899', fg='#FFFFFF')
                self.current_tab = tab_name
            else:
                item['button'].configure(bg='#1A1B3E', fg='#B4B4B8')
        
        # Reset hover tracking since we have a new active tab
        self.currently_hovered_button = None
        
        # Switch tab content
        self.app.switch_to_tab(tab_name)


class PremiumHeader:
    """Premium header with Google account integration"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        
        # Create header frame with proper height and no overlapping
        self.header = tk.Frame(parent, height=80, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        self.header.pack(side='top', fill='x', pady=0)
        self.header.pack_propagate(False)
        
        # Load background
        self.load_header_background()
        
        # Create header content
        self.create_header_content()
    
    def load_header_background(self):
        """Load and apply custom header background"""
        try:
            bg_path = os.path.join('assets', 'backgrounds', 'header_bg.png')
            if os.path.exists(bg_path):
                bg_image = Image.open(bg_path)
                bg_image = bg_image.resize((1200, 64), Image.Resampling.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(bg_image)
                
                bg_label = tk.Label(self.header, image=self.bg_photo)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"[HEADER] Using fallback background: {e}")
            self.header.configure(bg='#0F0F23')
    
    def create_header_content(self):
        """Create header content with account info"""
        # Clear any existing content to prevent overlapping
        for widget in self.header.winfo_children():
            if not isinstance(widget, tk.Label):  # Don't destroy background label
                widget.destroy()
        
        # Left side - Speed Profiles (consistent with main background)
        left_frame = tk.Frame(self.header, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        left_frame.pack(side='left', padx=32, pady=12)
        
        self.create_speed_profiles_section(left_frame)
        
        # Right side - Account (consistent with main background)
        right_frame = tk.Frame(self.header, bg='#0F0F23', highlightthickness=0, bd=0, highlightbackground='#0F0F23')
        right_frame.pack(side='right', padx=32, pady=12)
        
        # Feature discovery progress (small indicator)
        self.discovery_indicator = tk.Label(right_frame, text="", 
                                          font=('Segoe UI', 8), 
                                          fg='#8B5CF6', bg='#0F0F23', highlightthickness=0)
        self.discovery_indicator.pack(side='right', padx=(0, 8))
        
        # Update discovery indicator
        self.app.after(1000, self.update_discovery_indicator)  # Delay to let spotlight system initialize
        
        # Notifications
        notif_btn = self.create_icon_button(right_frame, 'bell', self.show_notifications)
        notif_btn.pack(side='right', padx=(0, 16))
        
        # Account dropdown
        account_frame = tk.Frame(right_frame, bg='#0F0F23', highlightthickness=0, bd=0)
        account_frame.pack(side='right')
        
        # Profile picture (circular)
        self.create_profile_picture(account_frame)
        
        # Account info
        account_info = tk.Frame(account_frame, bg='#0F0F23', highlightthickness=0, bd=0)
        account_info.pack(side='right', padx=(0, 12))
        
        # User name (dynamic)
        self.name_label = tk.Label(account_info, 
                             text="Loading...",
                             font=('Segoe UI', 10, 'bold'),
                             fg='#FFFFFF',
                             bg='#0F0F23')
        self.name_label.pack(anchor='e')
        
        # Plan info (dynamic)
        self.plan_label = tk.Label(account_info,
                             text="Loading...",
                             font=('Segoe UI', 8),
                             fg='#B4B4B8',
                             bg='#0F0F23')
        self.plan_label.pack(anchor='e')
        
        # Dropdown arrow
        dropdown_btn = self.create_icon_button(account_frame, 'chevron-down', self.show_account_menu)
        dropdown_btn.pack(side='right')
    
    def create_speed_profiles_section(self, parent_frame):
        """Create speed profiles dropdown section"""
        # Profile section frame
        profile_frame = tk.Frame(parent_frame, bg='#0F0F23', highlightthickness=0, bd=0)
        profile_frame.pack(side='left')
        
        # Profile icon and label
        profile_icon_frame = tk.Frame(profile_frame, bg='#0F0F23', highlightthickness=0, bd=0)
        profile_icon_frame.pack(side='left', padx=(0, 8))
        
        # Speed icon (⚡)
        profile_icon = tk.Label(profile_icon_frame, text="⚡", font=('Segoe UI', 16), 
                               fg='#8B5CF6', bg='#1A1B3E')
        profile_icon.pack()
        
        # Profile info frame
        profile_info_frame = tk.Frame(profile_frame, bg='#0F0F23', highlightthickness=0, bd=0)
        profile_info_frame.pack(side='left')
        
        # Profile label
        profile_label = tk.Label(profile_info_frame, text="Speed Profile", 
                                font=('Segoe UI', 8), fg='#B4B4B8', bg='#1A1B3E')
        profile_label.pack(anchor='w')
        
        # Get current profile from app config
        current_profile = getattr(self.app, 'cfg', {}).get('active_profile', 'Default')
        
        # Profile dropdown
        from tkinter import ttk
        style = ttk.Style()
        style.configure('Header.TCombobox',
                       fieldbackground='#2A2B4E',
                       background='#2A2B4E',
                       foreground='#FFFFFF',
                       arrowcolor='#8B5CF6',
                       borderwidth=1,
                       relief='solid')
        
        # Configure dropdown list style for better spacing
        style.map('Header.TCombobox',
                  fieldbackground=[('readonly', '#2A2B4E')],
                  selectbackground=[('readonly', '#8B5CF6')],
                  selectforeground=[('readonly', '#FFFFFF')])
        
        # Configure the dropdown list box style with better spacing
        style.configure('Header.TCombobox.Listbox',
                       background='#2A2B4E',
                       foreground='#FFFFFF',
                       selectbackground='#8B5CF6',
                       selectforeground='#FFFFFF',
                       font=('Segoe UI', 9),
                       relief='flat',
                       borderwidth=0)
        
        # Configure dropdown option styling for better vertical spacing
        try:
            # Configure the dropdown menu to have more space
            style.map('Header.TCombobox', 
                     fieldbackground=[('readonly', '#2A2B4E')],
                     selectbackground=[('focus', '#8B5CF6')],
                     selectforeground=[('focus', '#FFFFFF')])
            
            # Try to configure listbox padding (may not work on all systems)
            self.app.option_add('*TCombobox*Listbox.font', ('Segoe UI', 11))
            self.app.option_add('*TCombobox*Listbox.background', '#2A2B4E')
            self.app.option_add('*TCombobox*Listbox.foreground', '#FFFFFF')
            self.app.option_add('*TCombobox*Listbox.selectBackground', '#8B5CF6')
        except Exception as e:
            print(f"[DROPDOWN] Could not configure listbox: {e}")
        
        self.profile_var = tk.StringVar(value=current_profile)
        
        # Create combobox with better spacing
        self.profile_combo = ttk.Combobox(profile_info_frame, 
                                         textvariable=self.profile_var,
                                         values=['Default', 'Speed-Type', 'Ultra-Slow'],
                                         state='readonly',
                                         style='Header.TCombobox',
                                         width=16,  # Even wider
                                         height=10,  # Maximum height
                                         font=('Segoe UI', 11))  # Larger font for better readability
        self.profile_combo.pack(anchor='w', pady=(2, 0))
        self.profile_combo.bind('<<ComboboxSelected>>', self.on_profile_change)
        
        # Store references for theme updates
        self.profile_widgets = [profile_frame, profile_icon_frame, profile_info_frame, 
                               profile_icon, profile_label]
    
    def on_profile_change(self, event=None):
        """Handle speed profile change"""
        new_profile = self.profile_var.get()
        print(f"[HEADER] Speed profile changed to: {new_profile}")
        
        # Update app config
        if hasattr(self.app, 'cfg'):
            self.app.cfg['active_profile'] = new_profile
            
            # Apply profile settings to app config
            import config
            if new_profile in config.PROFILE_PRESETS:
                preset = config.PROFILE_PRESETS[new_profile]
                self.app.cfg['settings'].update({
                    'min_delay': preset['min_delay'],
                    'max_delay': preset['max_delay'],
                    'typos_on': preset['typos_on'],
                    'pause_freq': preset['pause_freq'],
                    'autocap': preset['autocap']
                })
                
                # Save config
                try:
                    from sly_config import save_config
                    save_config(self.app.cfg)
                    print(f"[HEADER] Applied and saved profile: {new_profile}")
                except Exception as e:
                    print(f"[HEADER] Error saving profile config: {e}")
                
                # Update typing tab if it exists and has update methods
                if hasattr(self.app, 'tabs') and 'Typing' in self.app.tabs:
                    typing_tab = self.app.tabs['Typing']
                    if hasattr(typing_tab, 'load_profile'):
                        typing_tab.load_profile(new_profile)
                    elif hasattr(typing_tab, 'update_from_config'):
                        typing_tab.update_from_config()
    
    def update_user_info(self, user_info):
        """Update header with Google user information"""
        try:
            # Update name
            if hasattr(self, 'name_label') and user_info.get('name'):
                self.name_label.configure(text=user_info['name'])
                
                # Update initials in profile picture as fallback
                if hasattr(self, 'profile_text_label'):
                    initials = ''.join([n[0].upper() for n in user_info['name'].split()[:2]])
                    self.profile_text_label.configure(text=initials)
            
            # Update plan (default to Premium for now)
            if hasattr(self, 'plan_label'):
                plan_text = getattr(self.app, 'user_plan', 'Premium')
                self.plan_label.configure(text=f"{plan_text} Plan")
            
            # Update profile picture if available
            if hasattr(self, 'profile_label') and user_info.get('picture'):
                print(f"[HEADER] User has profile picture URL: {user_info['picture'][:50]}...")
                self.load_profile_picture(user_info['picture'])
            else:
                print("[HEADER] No profile picture URL in user info")
                
        except Exception as e:
            print(f"[HEADER] Error updating user info: {e}")
    
    def load_profile_picture(self, picture_url):
        """Load profile picture from URL in background thread"""
        def download_and_process():
            try:
                import requests
                print(f"[HEADER] Loading profile picture from: {picture_url}")
                
                # Download image with timeout
                response = requests.get(picture_url, timeout=10)
                if response.status_code == 200:
                    # Load image
                    img_data = io.BytesIO(response.content)
                    img = Image.open(img_data)
                    
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize to circular (40x40 to match frame size)
                    img = img.resize((40, 40), Image.Resampling.LANCZOS)
                    
                    # Create circular mask
                    mask = Image.new('L', (40, 40), 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0, 39, 39), fill=255)
                    
                    # Apply mask
                    output = Image.new('RGBA', (40, 40), (0, 0, 0, 0))
                    output.paste(img, (0, 0))
                    output.putalpha(mask)
                    
                    # Schedule UI update on main thread
                    def update_ui():
                        try:
                            self.profile_photo = ImageTk.PhotoImage(output)
                            if hasattr(self, 'profile_label'):
                                self.profile_label.configure(image=self.profile_photo)
                                self.profile_label.image = self.profile_photo  # Keep reference
                                
                                # Hide the text overlay once picture loads
                                if hasattr(self, 'profile_text_label'):
                                    self.profile_text_label.place_forget()
                                
                                print("[HEADER] Profile picture loaded successfully")
                        except Exception as e:
                            print(f"[HEADER] Error updating profile picture UI: {e}")
                    
                    # Use after_idle for thread-safe UI update
                    if hasattr(self, 'profile_label'):
                        self.profile_label.after_idle(update_ui)
                else:
                    print(f"[HEADER] Failed to download profile picture: {response.status_code}")
                    
            except Exception as e:
                print(f"[HEADER] Error loading profile picture: {e}")
        
        # Start download in background thread
        threading.Thread(target=download_and_process, daemon=True).start()
    
    def create_profile_picture(self, parent):
        """Create circular profile picture"""
        # Create circular frame
        profile_frame = tk.Frame(parent, bg='#0F0F23', width=40, height=40)
        profile_frame.pack(side='right', padx=(0, 12))
        profile_frame.pack_propagate(False)
        
        # Create default circular purple background with initials
        try:
            # Create a circular purple background
            profile_img = Image.new('RGBA', (40, 40), (0, 0, 0, 0))
            draw = ImageDraw.Draw(profile_img)
            
            # Draw purple circle
            draw.ellipse((0, 0, 39, 39), fill='#410899')
            
            # Convert to PhotoImage
            self.default_photo = ImageTk.PhotoImage(profile_img)
            
            # Single profile label that will be updated with Google picture
            self.profile_label = tk.Label(profile_frame, 
                                        image=self.default_photo,
                                        bg='#0F0F23',
                                        highlightthickness=0)
            self.profile_label.place(relx=0.5, rely=0.5, anchor='center')
            self.profile_label.image = self.default_photo
            
            # Add initials text overlay initially
            self.profile_text_label = tk.Label(profile_frame,
                                              text="?",  # Default placeholder
                                              font=('Segoe UI', 14, 'bold'),
                                              fg='#FFFFFF',
                                              bg='#410899')
            self.profile_text_label.place(relx=0.5, rely=0.5, anchor='center')
            
        except Exception as e:
            print(f"[HEADER] Error creating profile picture: {e}")
            # Fallback to simple text
            self.profile_label = tk.Label(profile_frame, 
                                        text="👤",
                                        font=('Segoe UI', 16),
                                        fg='#FFFFFF',
                                        bg='#410899')
            self.profile_label.place(relx=0.5, rely=0.5, anchor='center')
    
    def create_icon_button(self, parent, icon_name, command):
        """Create an icon button"""
        btn = tk.Button(parent,
                       text="",
                       font=('Segoe UI', 10),
                       fg='#B4B4B8',
                       bg='#1A1B3E',
                       activebackground='#2D2F5A',
                       activeforeground='#FFFFFF',
                       relief='flat',
                       bd=0,
                       cursor='hand2',
                       command=command)
        
        # Load icon
        icon = self.load_icon(icon_name, 20)
        if icon:
            btn.configure(image=icon)
            btn.image = icon
        
        return btn
    
    def load_icon(self, icon_name, size):
        """Load and resize icon"""
        try:
            icon_path = os.path.join('assets', 'icons', f'{icon_name}.png')
            if os.path.exists(icon_path):
                icon_img = Image.open(icon_path)
                icon_img = icon_img.resize((size, size), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(icon_img)
        except Exception as e:
            print(f"[HEADER] Could not load icon {icon_name}: {e}")
        return None
    
    def show_notifications(self):
        """Show notifications dropdown with updates and discount codes"""
        print("[HEADER] Notifications clicked")
        
        # Track notification usage
        if hasattr(self.app, 'track_feature_usage'):
            self.app.track_feature_usage('notification_system')
        
        # Create notifications popup
        self.create_notifications_popup()
    
    def create_notifications_popup(self):
        """Create notifications popup window"""
        # Create popup window
        popup = tk.Toplevel(self.header)
        popup.title("Notifications")
        popup.geometry("400x500")
        popup.configure(bg='#1A1B3E')
        popup.transient(self.header)
        popup.grab_set()
        
        # Position popup relative to bell button
        popup.geometry("+%d+%d" % (self.header.winfo_rootx() + 300, 
                                 self.header.winfo_rooty() + 70))
        
        # Header
        header_frame = tk.Frame(popup, bg='#1A1B3E')
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        tk.Label(header_frame, text="📢 Notifications", 
                font=('Segoe UI', 16, 'bold'), 
                fg='#FFFFFF', bg='#1A1B3E').pack(side='left')
        
        # Close button
        close_btn = tk.Button(header_frame, text="✕", 
                            font=('Segoe UI', 12, 'bold'),
                            fg='#FFFFFF', bg='#1A1B3E', 
                            bd=0, cursor='hand2',
                            command=popup.destroy)
        close_btn.pack(side='right')
        
        # Scrollable content
        canvas = tk.Canvas(popup, bg='#1A1B3E', highlightthickness=0)
        scrollbar = ttk.Scrollbar(popup, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1A1B3E')
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        
        canvas.pack(side='left', fill='both', expand=True, padx=(20, 0), pady=(0, 20))
        scrollbar.pack(side='right', fill='y', pady=(0, 20), padx=(0, 20))
        
        # Load notifications
        self.load_notifications(scrollable_frame)
        
        # Update scroll region
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox('all'))
        
        # Configure canvas width
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        canvas.bind('<Configure>', configure_canvas_width)
    
    def load_notifications(self, parent):
        """Load notifications from various sources"""
        notifications = []
        
        # Try to fetch from remote source (could be your Discord webhook, website API, etc.)
        try:
            notifications = self.fetch_remote_notifications()
        except Exception as e:
            print(f"[NOTIFICATIONS] Error fetching remote notifications: {e}")
        
        # Fallback to local notifications
        if not notifications:
            notifications = self.get_default_notifications()
        
        # Display notifications
        for i, notif in enumerate(notifications):
            self.create_notification_item(parent, notif, i)
    
    def fetch_remote_notifications(self):
        """Fetch notifications from remote source (webhook, API, etc.)"""
        import requests
        import json
        
        # Option 1: Simple JSON endpoint
        # You could host a simple JSON file with your notifications
        # Example: https://yourdomain.com/slywriter-notifications.json
        
        try:
            # Replace with your actual notification URL
            # This could be a GitHub raw file, your website, or a simple API
            response = requests.get(
                "https://api.github.com/repos/yourusername/slywriter-notifications/contents/notifications.json",
                timeout=5
            )
            
            if response.status_code == 200:
                # If using GitHub API, decode base64
                import base64
                content = json.loads(response.json()['content'])
                decoded = base64.b64decode(content).decode('utf-8')
                return json.loads(decoded)
                
        except Exception as e:
            print(f"[NOTIFICATIONS] Error fetching from remote: {e}")
            
        # Option 2: Discord Webhook approach (read-only)
        # Unfortunately, Discord webhooks are send-only, but you could:
        # 1. Use a Discord bot to read messages from a channel
        # 2. Use Discord's API to read messages from a public channel
        # 3. Use a third-party service that bridges Discord to API
        
        return []
    
    def get_default_notifications(self):
        """Get default/fallback notifications"""
        return [
            {
                "id": 1,
                "type": "update",
                "title": "🚀 SlyWriter v2.0 Released!",
                "message": "New AI detection avoidance, improved typing patterns, and better performance.",
                "timestamp": "2025-09-15T10:00:00Z",
                "action_text": "View Changelog",
                "action_url": "https://yourwebsite.com/changelog"
            },
            {
                "id": 2,
                "type": "discount",
                "title": "💰 50% Off Premium - Limited Time!",
                "message": "Use code WINTER50 for 50% off your first month of Premium.",
                "timestamp": "2025-09-10T15:30:00Z",
                "action_text": "Claim Discount",
                "action_url": "https://yourwebsite.com/premium?code=WINTER50"
            },
            {
                "id": 3,
                "type": "info",
                "title": "📢 Join Our Discord Community",
                "message": "Get the latest updates, discount codes, and connect with other users.",
                "timestamp": "2025-09-05T12:00:00Z",
                "action_text": "Join Discord",
                "action_url": "https://discord.gg/your-invite-code"
            }
        ]
    
    def create_notification_item(self, parent, notification, index):
        """Create a single notification item"""
        # Notification container
        item_frame = tk.Frame(parent, bg='#2D2F5A', relief='flat', bd=0)
        item_frame.pack(fill='x', pady=(0, 10), padx=5)
        
        # Content frame
        content_frame = tk.Frame(item_frame, bg='#2D2F5A')
        content_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Type icon and title
        header_frame = tk.Frame(content_frame, bg='#2D2F5A')
        header_frame.pack(fill='x', pady=(0, 8))
        
        # Title
        title_label = tk.Label(header_frame, 
                              text=notification.get('title', 'Notification'),
                              font=('Segoe UI', 12, 'bold'),
                              fg='#FFFFFF', bg='#2D2F5A',
                              wraplength=350, justify='left')
        title_label.pack(anchor='w')
        
        # Message
        message_label = tk.Label(content_frame,
                                text=notification.get('message', ''),
                                font=('Segoe UI', 10),
                                fg='#B4B4B8', bg='#2D2F5A',
                                wraplength=350, justify='left')
        message_label.pack(anchor='w', pady=(0, 10))
        
        # Action button (if provided)
        if notification.get('action_text') and notification.get('action_url'):
            action_btn = tk.Button(content_frame,
                                 text=notification['action_text'],
                                 font=('Segoe UI', 9, 'bold'),
                                 fg='#FFFFFF', bg='#8B5CF6',
                                 bd=0, pady=8, padx=16,
                                 cursor='hand2',
                                 command=lambda url=notification['action_url']: self.open_url(url))
            action_btn.pack(anchor='w')
        
        # Timestamp
        if notification.get('timestamp'):
            try:
                from datetime import datetime, timezone
                
                # Try to parse timestamp - handle different formats
                timestamp = notification['timestamp']
                if 'T' in timestamp and 'Z' in timestamp:
                    # ISO format: 2025-09-15T10:00:00Z
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    # Try to parse as timestamp
                    dt = datetime.fromtimestamp(float(timestamp))
                
                time_str = dt.strftime('%b %d, %Y at %I:%M %p')
                
                time_label = tk.Label(content_frame,
                                    text=time_str,
                                    font=('Segoe UI', 8),
                                    fg='#6B7280', bg='#2D2F5A')
                time_label.pack(anchor='e', pady=(5, 0))
            except Exception as e:
                print(f"[NOTIFICATIONS] Error parsing timestamp: {e}")
    
    def open_url(self, url):
        """Open URL in default browser"""
        try:
            import webbrowser
            webbrowser.open(url)
            print(f"[NOTIFICATIONS] Opened URL: {url}")
        except Exception as e:
            print(f"[NOTIFICATIONS] Error opening URL: {e}")
    
    def update_discovery_indicator(self):
        """Update the feature discovery progress indicator"""
        try:
            if hasattr(self.app, 'spotlight') and self.app.spotlight:
                stats = self.app.spotlight.get_discovery_stats()
                percentage = int(stats['discovery_percentage'])
                
                if percentage < 30:
                    text = f"✨ {percentage}%"
                    color = '#FF6B6B'  # Red for low discovery
                elif percentage < 70:
                    text = f"🌟 {percentage}%"
                    color = '#FFA500'  # Orange for medium discovery
                else:
                    text = f"🏆 {percentage}%"
                    color = '#10B981'  # Green for high discovery
                
                if hasattr(self, 'discovery_indicator'):
                    self.discovery_indicator.configure(text=text, fg=color)
                
                # Schedule next update
                self.app.after(30000, self.update_discovery_indicator)  # Update every 30 seconds
                
        except Exception as e:
            print(f"[HEADER] Error updating discovery indicator: {e}")
    
    def show_account_menu(self):
        """Show account dropdown menu"""
        print("[HEADER] Account menu clicked")
        # TODO: Implement account menu


class PremiumCard:
    """Premium card component with shadows and rounded corners"""
    
    def __init__(self, parent, title="", width=None, height=None):
        self.parent = parent
        
        # Create card frame with normal background
        self.card = tk.Frame(parent, bg='#2D2F5A', relief='flat', bd=0)
        if width and height:
            self.card.configure(width=width, height=height)
            self.card.pack_propagate(False)
        
        # Load background
        self.load_card_background()
        
        # Add title if provided
        if title:
            self.create_title(title)
        
        # Content area with normal background
        self.content = tk.Frame(self.card, bg='#1A1B3E')
        self.content.pack(fill='both', expand=True, padx=20, pady=20)
    
    def load_card_background(self):
        """Load and apply custom card background with gradient support"""
        try:
            # Update to get current dimensions
            self.card.update_idletasks()
            
            # Use actual card dimensions if available
            width = self.card.winfo_width() or 400
            height = self.card.winfo_height() or 300
            
            # Minimum size to prevent tiny images
            width = max(width, 300)
            height = max(height, 200)
            
            bg_path = os.path.join('assets', 'backgrounds', 'card_bg.png')
            
            # Define gradient fallback for cards
            card_gradient = {
                'color1': '#2D2F5A',  # Card background
                'color2': '#1A1B3E',  # Darker at bottom
                'direction': 'vertical'
            }
            
            # Try to load custom background first
            if os.path.exists(bg_path):
                bg_image = Image.open(bg_path)
                bg_image = bg_image.resize((width, height), Image.Resampling.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(bg_image)
            else:
                # Create gradient fallback
                self.bg_photo = self.create_gradient_background(width, height, **card_gradient)
            
            if self.bg_photo:
                # Remove any existing background
                if hasattr(self, 'card_bg_label'):
                    self.card_bg_label.destroy()
                
                # Create background label
                self.card_bg_label = tk.Label(self.card, image=self.bg_photo, bd=0, highlightthickness=0)
                self.card_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                self.card_bg_label.lower()  # Send to back
                self.card_bg_label.image = self.bg_photo  # Keep reference
                
                # Set card background to match
                self.card.configure(bg='#2D2F5A')
                
                if os.path.exists(bg_path):
                    print(f"[CARD] Loaded custom card background from {bg_path} ({width}x{height})")
                else:
                    print(f"[CARD] Created gradient card background ({width}x{height})")
                return True
            else:
                raise Exception("Failed to create card background")
                
        except Exception as e:
            print(f"[CARD] Error loading background: {e}")
        
        # Apply modern styling fallback
        self.card.configure(bg='#2D2F5A', highlightbackground='#374151', highlightthickness=1)
        print(f"[CARD] Using fallback solid color background")
        return False
    
    def create_title(self, title):
        """Create card title"""
        title_frame = tk.Frame(self.card, bg='#1A1B3E', height=50)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame,
                              text=title,
                              font=('Segoe UI', 14, 'bold'),
                              fg='#FFFFFF',
                              bg='#0F0F23')
        title_label.pack(side='left', padx=20, pady=15)
    
    def pack(self, **kwargs):
        """Pack the card"""
        self.card.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the card"""
        self.card.grid(**kwargs)


class PremiumButton:
    """Premium button with gradients and hover effects"""
    
    def __init__(self, parent, text="", command=None, style="primary", width=None):
        self.parent = parent
        self.command = command
        self.style = style
        
        # Button styles
        self.styles = {
            'primary': {
                'bg': '#410899',
                'fg': '#FFFFFF',
                'hover_bg': '#6B46C1',
                'active_bg': '#312E81'
            },
            'secondary': {
                'bg': 'transparent',
                'fg': '#410899',
                'hover_bg': '#410899',
                'hover_fg': '#FFFFFF',
                'border': '#410899'
            },
            'ghost': {
                'bg': 'transparent',
                'fg': '#B4B4B8',
                'hover_fg': '#410899'
            }
        }
        
        # Create button
        self.create_button(text, width)
    
    def create_button(self, text, width):
        """Create the premium button"""
        style_config = self.styles[self.style]
        
        self.button = tk.Button(self.parent,
                               text=text,
                               font=('Segoe UI', 10, 'bold'),
                               fg=style_config['fg'],
                               bg=style_config['bg'],
                               relief='flat',
                               bd=0,
                               cursor='hand2',
                               command=self.command)
        
        if width:
            self.button.configure(width=width)
        
        # Bind hover effects
        self.button.bind('<Enter>', self.on_hover)
        self.button.bind('<Leave>', self.on_leave)
        self.button.bind('<Button-1>', self.on_press)
        self.button.bind('<ButtonRelease-1>', self.on_release)
    
    def on_hover(self, event):
        """Handle hover effect"""
        style_config = self.styles[self.style]
        self.button.configure(bg=style_config.get('hover_bg', style_config['bg']))
        if 'hover_fg' in style_config:
            self.button.configure(fg=style_config['hover_fg'])
    
    def on_leave(self, event):
        """Handle leave effect"""
        style_config = self.styles[self.style]
        self.button.configure(bg=style_config['bg'], fg=style_config['fg'])
    
    def on_press(self, event):
        """Handle press effect"""
        style_config = self.styles[self.style]
        self.button.configure(bg=style_config.get('active_bg', style_config['bg']))
    
    def on_release(self, event):
        """Handle release effect"""
        self.on_hover(event)  # Return to hover state
    
    def pack(self, **kwargs):
        """Pack the button"""
        self.button.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the button"""
        self.button.grid(**kwargs)
    
    def configure(self, **kwargs):
        """Configure the button"""
        self.button.configure(**kwargs)


class PremiumInput:
    """Premium input field with modern styling"""
    
    def __init__(self, parent, placeholder="", width=None):
        self.parent = parent
        self.placeholder = placeholder
        self.has_focus = False
        
        # Create input
        self.create_input(width)
    
    def create_input(self, width):
        """Create the premium input field"""
        # Container for border effects
        self.container = tk.Frame(self.parent, bg='#374151', relief='flat', bd=0)
        
        # Actual entry widget
        self.entry = tk.Entry(self.container,
                             font=('Segoe UI', 10),
                             bg='#1A1B3E',
                             fg='#B4B4B8',
                             relief='flat',
                             bd=0,
                             insertbackground='#410899')
        
        if width:
            self.entry.configure(width=width)
        
        self.entry.pack(padx=1, pady=1, fill='both', expand=True)
        
        # Placeholder text
        if self.placeholder:
            self.entry.insert(0, self.placeholder)
            self.entry.configure(fg='#6B7280')
        
        # Bind events
        self.entry.bind('<FocusIn>', self.on_focus_in)
        self.entry.bind('<FocusOut>', self.on_focus_out)
    
    def on_focus_in(self, event):
        """Handle focus in"""
        self.has_focus = True
        self.container.configure(bg='#410899')  # Purple border
        
        # Clear placeholder
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, tk.END)
            self.entry.configure(fg='#FFFFFF')
    
    def on_focus_out(self, event):
        """Handle focus out"""
        self.has_focus = False
        self.container.configure(bg='#374151')  # Gray border
        
        # Restore placeholder if empty
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.configure(fg='#6B7280')
    
    def pack(self, **kwargs):
        """Pack the input"""
        self.container.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the input"""
        self.container.grid(**kwargs)
    
    def get(self):
        """Get input value"""
        value = self.entry.get()
        return "" if value == self.placeholder else value
    
    def set(self, value):
        """Set input value"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.entry.configure(fg='#FFFFFF')