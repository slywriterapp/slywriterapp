import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.simpledialog as sd
from auth import sign_in_with_google, sign_out, get_saved_user
from account_usage import AccountUsageManager

SERVER_URL = "https://slywriterapp.onrender.com"

class AccountTab(tk.Frame):
    def __init__(self, parent, app):
        # Theme: white or black only
        dark = app.cfg['settings'].get('dark_mode', False)
        bg = "#181816" if dark else "#ffffff"
        super().__init__(parent, bg=bg)
        self.app = app
        # Check if user is already authenticated in the main app
        if hasattr(app, 'user') and app.user:
            self.google_info = app.user
            print(f"[ACCOUNT TAB] Using existing authentication for {app.user.get('email', 'user')}")
        else:
            self.google_info = None
            
        self._pending_auto_login = None

        self.usage_mgr = AccountUsageManager(self)
        # --- Add is_premium fallback if not present ---
        if not hasattr(self.usage_mgr, "is_premium"):
            self.usage_mgr.is_premium = lambda: getattr(self.usage_mgr, "plan", "free") in ("pro", "premium", "enterprise")

        self.bar_width = 300
        self.bar_height = 20

        self.build_ui(bg)

        # If already authenticated, don't check for saved user again
        if not self.google_info:
            saved = get_saved_user()
            if saved:
                self._pending_auto_login = saved

        self.start_auto_update()

    def build_ui(self, bg):
        # Use ttk.Buttons for proper theme support
        self.signin_btn = ttk.Button(self, text="Sign In with Google", command=self._do_google_sign_in)
        self.signin_btn.pack(pady=(20, 8))

        self.manual_btn = ttk.Button(self, text="Manual Sign In", command=self._do_manual_sign_in)
        self.manual_btn.pack(pady=8)

        self.logout_btn = ttk.Button(self, text="Log Out", command=self._do_logout)
        self.logout_btn.pack(pady=(8, 12))
        self.logout_btn.pack_forget()  # Hide by default

        self.status_label = tk.Label(self, text="", bg=bg)
        self.status_label.pack(pady=5)

        self.usage_label = tk.Label(self, text="", bg=bg)
        self.usage_label.pack(pady=(20, 2))

        # Progress bar with TTK Progressbar for proper theming
        self.progress_frame = tk.Frame(self, bg=bg)
        self.progress_frame.pack(pady=(5, 10))
        
        # Label for progress bar
        self.progress_label = tk.Label(self.progress_frame, text="Usage Progress", 
                                     font=('Segoe UI', 9), bg=bg)
        self.progress_label.pack()
        
        # TTK Progressbar with purple theme
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            length=300,
            mode='determinate',
            value=0
        )
        self.progress_bar.pack(pady=(5, 0))
        
        # Keep canvas for compatibility with existing code
        self.canvas = tk.Canvas(self, width=300, height=self.bar_height, 
                               bd=0, highlightthickness=0, bg=bg)
        # Hide canvas - we're using TTK progressbar instead
        self.canvas.pack_forget()
        self.bar_border = self.canvas.create_rectangle(0, 0, 300, self.bar_height, outline="#666", width=1)
        self.canvas_progress_bar = self.canvas.create_rectangle(0, 0, 0, self.bar_height, fill="#4CAF50", outline="")

        self.referral_label = tk.Label(self, text="", wraplength=280, justify="center", bg=bg)
        self.referral_label.pack(pady=5)

        # Redeem Referral Code Section
        self.redeem_frame = tk.LabelFrame(self, text="🎁 Redeem Referral Code",
                                         font=('Segoe UI', 10, 'bold'), bg=bg,
                                         bd=2, relief='groove')
        self.redeem_frame.pack(pady=10, padx=20, fill='x')
        self.redeem_frame.pack_forget()  # Hidden by default, show when logged in

        # Info text
        redeem_info = tk.Label(self.redeem_frame,
                              text="Have a friend's referral code? Redeem it here to get 500 bonus words!",
                              wraplength=280, justify="center", bg=bg, font=('Segoe UI', 9))
        redeem_info.pack(pady=(5, 10))

        # Entry and button frame
        redeem_input_frame = tk.Frame(self.redeem_frame, bg=bg)
        redeem_input_frame.pack(pady=(0, 10))

        self.referral_code_entry = tk.Entry(redeem_input_frame, width=20,
                                           font=('Segoe UI', 10),
                                           justify='center')
        self.referral_code_entry.pack(side='left', padx=(10, 5))
        self.referral_code_entry.insert(0, "Enter code...")
        self.referral_code_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(e))
        self.referral_code_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(e))

        self.redeem_btn = ttk.Button(redeem_input_frame, text="Redeem",
                                    command=self._redeem_referral_code)
        self.redeem_btn.pack(side='left', padx=(5, 10))

        # Status message
        self.redeem_status = tk.Label(self.redeem_frame, text="",
                                     wraplength=280, justify="center",
                                     bg=bg, font=('Segoe UI', 9))
        self.redeem_status.pack(pady=(0, 5))

        # Upgrade/Referral Progress Panel - HIDDEN
        self.upgrade_frame = tk.LabelFrame(self, text="🚀 Upgrade & Referrals", 
                                          font=('Segoe UI', 10, 'bold'), bg=bg,
                                          bd=0, relief='flat')  # Remove border
        self.upgrade_frame.pack_forget()  # Hide completely
        
        # Referral Pass Progress
        self.referral_progress_frame = tk.Frame(self.upgrade_frame, bg=bg)
        self.referral_progress_frame.pack(fill='x', padx=10, pady=8)
        
        self.referral_status_label = tk.Label(self.referral_progress_frame, 
                                             text="🎯 Referral Pass Progress", 
                                             font=('Segoe UI', 9, 'bold'), bg=bg)
        self.referral_status_label.pack(anchor='w')
        
        self.referral_details_label = tk.Label(self.referral_progress_frame, 
                                              text="", wraplength=280, justify="left", bg=bg)
        self.referral_details_label.pack(anchor='w', pady=(2, 5))
        
        # Upgrade recommendations
        self.upgrade_recommendation = tk.Label(self.upgrade_frame, text="", 
                                              wraplength=280, justify="center", 
                                              font=('Segoe UI', 9), bg=bg)
        self.upgrade_recommendation.pack(pady=5)
        
        # Action buttons
        self.upgrade_buttons_frame = tk.Frame(self.upgrade_frame, bg=bg)
        self.upgrade_buttons_frame.pack(pady=5)
        
        self.view_plans_btn = ttk.Button(self.upgrade_buttons_frame, text="💎 View Plans", 
                                        command=self.show_plans_comparison)
        self.view_plans_btn.pack(side='left', padx=5)
        
        self.referral_info_btn = ttk.Button(self.upgrade_buttons_frame, text="🎯 Referral Pass Info", 
                                           command=self.show_referral_pass_info)
        self.referral_info_btn.pack(side='left', padx=5)

    def set_theme(self, dark):
        bg = "#181816" if dark else "#ffffff"
        fg = "white" if dark else "black"
        canvas_bg = bg

        for widget in [
            self, self.status_label, self.usage_label, self.referral_label,
            self.upgrade_frame, self.referral_progress_frame, self.referral_status_label,
            self.referral_details_label, self.upgrade_recommendation, self.upgrade_buttons_frame,
            self.redeem_frame, self.redeem_status
        ]:
            try:
                widget.configure(bg=bg, fg=fg)
            except Exception:
                pass
        self.canvas.configure(bg=canvas_bg)
        border_color = "#ffffff" if dark else "#000000"
        self.canvas.itemconfig(self.bar_border, outline=border_color)
        self.canvas.itemconfig(self.progress_bar, fill="#66ff00", outline="")

        # ttk Buttons are theme-aware so no need to configure color unless you want to override
        self.update_progress_bar(self.usage_mgr.words_used, self.usage_mgr.get_word_limit())

    def _do_google_sign_in(self):
        info = sign_in_with_google()
        if info:
            self.google_info = info
            # --- Referral bonus logic ---
            import requests
            try:
                uid = info.get("id")
                check = requests.get(f"{SERVER_URL}/get_referrals", params={"user_id": uid})
                if check.status_code == 200:
                    referred_by = check.json().get("referred_by")
                    bonus_check = check.json().get("bonus_claimed", False)
                    if referred_by and not bonus_check:
                        bonus_resp = requests.post(f"{SERVER_URL}/referral_bonus", json={
                            "referrer_id": referred_by,
                            "referred_id": uid
                        })
                        if bonus_resp.status_code == 200 and bonus_resp.json().get("status") == "bonus_applied":
                            messagebox.showinfo("Referral Bonus", "You and your referrer each earned 1000 bonus words!")
            except Exception as e:
                print("⚠️ Referral auto-bonus error:", e)

            self.usage_mgr.load_usage()
            self._render_user_status()
            self.usage_mgr.update_usage_display()
            self.app.on_login(info)
            
            # Force immediate UI update for words left bar
            self.update_idletasks()

    def _do_manual_sign_in(self):
        email = sd.askstring("Manual Sign-In", "Enter your email:")
        if not email:
            return
        import requests
        try:
            r = requests.post(f"{SERVER_URL}/manual_login_start", json={"email": email})
            if r.status_code == 200:
                code = sd.askstring("Verify Email", "Enter the verification code sent to your email:")
                if not code:
                    return
                r2 = requests.post(f"{SERVER_URL}/manual_login_verify", json={"email": email, "code": code})
                if r2.status_code == 200:
                    user_info = r2.json()
                    self.google_info = user_info
                    self.usage_mgr.load_usage()
                    self._render_user_status()
                    self.usage_mgr.update_usage_display()
                    self.app.on_login(user_info)
                    
                    # Force immediate UI update for words left bar
                    self.update_idletasks()
                    messagebox.showinfo("Manual Sign-In", "Logged in successfully!")
                else:
                    messagebox.showerror("Manual Sign-In", "Invalid code. Try again.")
            else:
                messagebox.showerror("Manual Sign-In", "Could not send verification code. Try again.")
        except Exception as e:
            messagebox.showerror("Manual Sign-In", f"Error: {e}")

    def _do_logout(self):
        # 1. Clear session, usage, and UI
        sign_out()
        self.google_info = None
        self.usage_mgr.words_used = 0
        self.usage_mgr.referrals = 0
        self.usage_mgr.referral_code = None
        self.usage_mgr.plan = "free"
        self.usage_mgr.update_usage_display()
        self.status_label.config(text="")
        self.usage_label.config(text="")
        self.referral_label.config(text="")
        self.canvas.coords(self.progress_bar, 0, 0, 0, self.bar_height)

        # Hide redeem box on logout
        self.redeem_frame.pack_forget()

        # 2. Show sign-in buttons, hide logout, and ensure they're enabled
        self.signin_btn.pack(pady=(20, 8))
        self.signin_btn.config(state='normal')  # Ensure button is enabled
        self.manual_btn.pack(pady=8)
        self.manual_btn.config(state='normal')   # Ensure button is enabled
        self.logout_btn.pack_forget()
        
        # 3. App disables other tabs and selects Account
        self.app.on_logout()
        self.app.notebook.select(self.app.tabs["Account"])
        
        # 4. Reset typing tab to clear any user-specific state
        if hasattr(self.app, 'typing_tab'):
            # Clear text areas
            if hasattr(self.app.typing_tab, 'clear_text_areas'):
                self.app.typing_tab.clear_text_areas()
        
        # 5. Force UI refresh to ensure proper state
        self.update()
        
        messagebox.showinfo("Logged Out", "You have been logged out successfully. The app has been reset to a fresh state.")

    def _render_user_status(self):
        # Hide sign-in buttons if signed in, show logout; vice versa if not
        if self.google_info:
            email = self.google_info.get("email", "Unknown")
            plan_str = "Premium" if self.is_premium() else "Free"
            self.status_label.config(text=f"Signed in as: {email}  •  {plan_str} Plan")
            self.signin_btn.pack_forget()
            self.manual_btn.pack_forget()
            self.logout_btn.pack(pady=(8, 12))
        else:
            self.status_label.config(text="")
            self.signin_btn.pack(pady=(20, 8))
            self.manual_btn.pack(pady=8)
            self.logout_btn.pack_forget()

    def is_premium(self):
        """Check premium status using AccountUsageManager."""
        return self.usage_mgr.is_premium()

    def _clear_placeholder(self, event):
        """Clear placeholder text when entry is focused"""
        if self.referral_code_entry.get() == "Enter code...":
            self.referral_code_entry.delete(0, tk.END)
            self.referral_code_entry.config(fg='black')

    def _restore_placeholder(self, event):
        """Restore placeholder text if entry is empty"""
        if not self.referral_code_entry.get():
            self.referral_code_entry.insert(0, "Enter code...")
            self.referral_code_entry.config(fg='gray')

    def _redeem_referral_code(self):
        """Redeem a referral code via the API"""
        import requests

        # Get code from entry
        code = self.referral_code_entry.get().strip()
        if not code or code == "Enter code...":
            self.redeem_status.config(text="❌ Please enter a referral code", fg='red')
            return

        # Check if user is logged in
        if not self.google_info:
            self.redeem_status.config(text="❌ Please log in first", fg='red')
            return

        # Disable button while processing
        self.redeem_btn.config(state='disabled')
        self.redeem_status.config(text="⏳ Redeeming...", fg='orange')
        self.update()

        try:
            # Get auth token
            token = self.google_info.get('token')
            if not token:
                raise Exception("No auth token found")

            # Call API endpoint
            response = requests.post(
                f"{SERVER_URL}/api/referral/redeem",
                json={"referral_code": code.upper()},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    message = data.get('message', 'Success!')
                    self.redeem_status.config(text=f"✅ {message}", fg='green')
                    # Clear the entry
                    self.referral_code_entry.delete(0, tk.END)
                    self.referral_code_entry.insert(0, "Enter code...")
                    self.referral_code_entry.config(fg='gray')
                    # Refresh usage to show new bonus words
                    self.usage_mgr.load_usage()
                    self.usage_mgr.update_usage_display()
                    # Hide redeem box after successful redemption
                    self.after(3000, lambda: self.redeem_frame.pack_forget())
                else:
                    error = data.get('error', 'Unknown error')
                    self.redeem_status.config(text=f"❌ {error}", fg='red')
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error = error_data.get('error', f'Error {response.status_code}')
                self.redeem_status.config(text=f"❌ {error}", fg='red')

        except requests.exceptions.Timeout:
            self.redeem_status.config(text="❌ Request timed out. Please try again.", fg='red')
        except Exception as e:
            print(f"Error redeeming referral code: {e}")
            self.redeem_status.config(text=f"❌ Error: {str(e)}", fg='red')
        finally:
            # Re-enable button
            self.redeem_btn.config(state='normal')

    def _check_and_show_redeem_box(self):
        """Check if user can redeem a code and show/hide the redeem box accordingly"""
        import requests

        try:
            # Get auth token
            token = self.google_info.get('token')
            if not token:
                self.redeem_frame.pack_forget()
                return

            # Check if user already has a referrer via /auth/profile endpoint
            response = requests.get(
                f"{SERVER_URL}/auth/profile",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                # Check if user has already used a referral code (either during signup or in-app)
                referred_by = data.get('referred_by')

                if referred_by:
                    # User already has a referrer - hide the redeem box permanently
                    print(f"[Redeem Box] User already redeemed a code (referred_by={referred_by}), hiding box")
                    self.redeem_frame.pack_forget()
                else:
                    # User hasn't used a referral code yet - show the redeem box
                    print("[Redeem Box] User can redeem a code, showing box")
                    self.redeem_frame.pack(pady=10, padx=20, fill='x')
                    self.redeem_status.config(text="")  # Clear any previous status
            else:
                # Hide on error
                print(f"[Redeem Box] Error fetching profile (status {response.status_code}), hiding box")
                self.redeem_frame.pack_forget()

        except Exception as e:
            print(f"[Redeem Box] Error checking redeem eligibility: {e}")
            # Hide on error to be safe
            self.redeem_frame.pack_forget()

    def update_for_login(self, user_info):
        self.google_info = user_info
        self.usage_mgr.load_usage()
        self._render_user_status()
        self.usage_mgr.update_usage_display()
        # Show redeem box if user hasn't redeemed a code yet
        self._check_and_show_redeem_box()
        
        # Force immediate UI update for words left bar
        self.update_idletasks()

    def start_auto_update(self):
        # If we have existing authentication, render user status immediately
        if self.google_info:
            self.usage_mgr.load_usage()
            self._render_user_status()
            
        self.usage_mgr.update_usage_display()
        self.after(5000, self.start_auto_update)

    # --- Convenience proxies ---
    def increment_words_used(self, amount=10):
        self.usage_mgr.increment_words_used(amount)

    def has_words_remaining(self):
        return self.usage_mgr.has_words_remaining()

    # --- Progress bar update helper ---
    def update_progress_bar(self, used, limit):
        percent = min(used / max(1, limit), 1.0)
        fill_px = int(self.bar_width * percent)
        self.canvas.coords(self.progress_bar, 0, 0, fill_px, self.bar_height)
        # Border always stays as full bar
        
        # Update referral progress display
        self.update_referral_progress_display()
    
    def update_referral_progress_display(self):
        """Update the referral pass progress display"""
        if not self.google_info:
            self.referral_details_label.config(text="Sign in to track referral progress")
            self.upgrade_recommendation.config(text="")
            return
        
        # Get referral pass status
        status = self.usage_mgr.get_referral_pass_status()
        recommendation = self.usage_mgr.get_upgrade_recommendations()
        
        # Update referral progress
        progress_text = f"Referrals: {status['referrals_progress']} • Usage: {status['usage_progress']}"
        if status['qualified']:
            progress_text = "✅ " + progress_text + " - QUALIFIED!"
        else:
            progress_text = "📊 " + progress_text
            
        self.referral_details_label.config(text=progress_text)
        
        # Update recommendation
        self.upgrade_recommendation.config(text=recommendation['message'])
    
    def show_plans_comparison(self):
        """Show detailed plans comparison window"""
        plans_window = tk.Toplevel(self.app)
        plans_window.title("💎 SlyWriter Plans Comparison")
        plans_window.geometry("800x600")
        plans_window.resizable(False, False)
        plans_window.transient(self.app)
        plans_window.grab_set()
        
        # Center window
        plans_window.update_idletasks()
        x = (self.app.winfo_x() + (self.app.winfo_width() // 2)) - (plans_window.winfo_width() // 2)
        y = (self.app.winfo_y() + (self.app.winfo_height() // 2)) - (plans_window.winfo_height() // 2)
        plans_window.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(plans_window)
        header_frame.pack(fill='x', padx=20, pady=15)
        
        tk.Label(header_frame, text="💎 Choose Your SlyWriter Plan", 
                font=('Segoe UI', 18, 'bold')).pack()
        tk.Label(header_frame, text="Compare features and find the perfect plan for your needs",
                font=('Segoe UI', 11), wraplength=700).pack(pady=(5, 0))
        
        # Plans comparison
        plans_frame = tk.Frame(plans_window)
        plans_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        plans = ['free', 'pro', 'premium', 'enterprise']
        plan_colors = {'free': '#E3F2FD', 'pro': '#E8F5E8', 'premium': '#FFF3E0', 'enterprise': '#F3E5F5'}
        plan_names = {'free': 'Free', 'pro': 'Pro', 'premium': 'Premium', 'enterprise': 'Enterprise'}
        plan_prices = {'free': 'Free', 'pro': '$9.99/mo', 'premium': '$19.99/mo', 'enterprise': 'Contact Us'}
        
        for i, plan in enumerate(plans):
            plan_frame = tk.LabelFrame(plans_frame, text=f"{plan_names[plan]} - {plan_prices[plan]}", 
                                      font=('Segoe UI', 12, 'bold'), bg=plan_colors[plan])
            plan_frame.grid(row=0, column=i, sticky='nsew', padx=5, pady=5)
            plans_frame.columnconfigure(i, weight=1)
            
            # Plan benefits
            benefits = self.usage_mgr.get_plan_benefits(plan)
            for benefit in benefits:
                benefit_label = tk.Label(plan_frame, text=f"✓ {benefit}", 
                                       font=('Segoe UI', 10), bg=plan_colors[plan],
                                       anchor='w', justify='left')
                benefit_label.pack(fill='x', padx=10, pady=2)
            
            # Current plan indicator
            if self.usage_mgr.plan == plan:
                current_label = tk.Label(plan_frame, text="🌟 Current Plan", 
                                        font=('Segoe UI', 10, 'bold'), 
                                        bg=plan_colors[plan], fg='green')
                current_label.pack(pady=5)
        
        # Referral Pass section
        referral_frame = tk.LabelFrame(plans_window, text="🎯 Referral Pass - Free Premium Access", 
                                      font=('Segoe UI', 12, 'bold'))
        referral_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        referral_text = tk.Text(referral_frame, height=6, wrap='word', font=('Segoe UI', 10))
        referral_text.pack(fill='x', padx=10, pady=10)
        referral_text.insert('1.0', self.usage_mgr.get_referral_pass_explanation())
        referral_text.config(state='disabled')
        
        # Close button
        close_btn = tk.Button(plans_window, text="Close", command=plans_window.destroy,
                             font=('Segoe UI', 11), padx=20, pady=5)
        close_btn.pack(pady=(0, 15))
    
    def show_referral_pass_info(self):
        """Show detailed referral pass information"""
        info_window = tk.Toplevel(self.app)
        info_window.title("🎯 Referral Pass System")
        info_window.geometry("600x500")
        info_window.resizable(False, False)
        info_window.transient(self.app)
        info_window.grab_set()
        
        # Center window
        info_window.update_idletasks()
        x = (self.app.winfo_x() + (self.app.winfo_width() // 2)) - (info_window.winfo_width() // 2)
        y = (self.app.winfo_y() + (self.app.winfo_height() // 2)) - (info_window.winfo_height() // 2)
        info_window.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(info_window)
        header_frame.pack(fill='x', padx=20, pady=15)
        
        tk.Label(header_frame, text="🎯 Referral Pass System", 
                font=('Segoe UI', 16, 'bold')).pack()
        tk.Label(header_frame, text="Earn free Premium access by growing our community",
                font=('Segoe UI', 11), wraplength=550).pack(pady=(5, 0))
        
        # Current status
        if self.google_info:
            status_frame = tk.LabelFrame(info_window, text="📊 Your Current Progress", 
                                        font=('Segoe UI', 12, 'bold'))
            status_frame.pack(fill='x', padx=20, pady=10)
            
            status = self.usage_mgr.get_referral_pass_status()
            
            progress_text = f"""Referrals: {status['referrals_progress']}
Usage: {status['usage_progress']}

{f"🎉 Congratulations! You qualify for free Premium access!" if status['qualified'] else f"Keep going! You need {status['referrals_needed']} more referrals and {status['usage_needed']} more words."}"""
            
            tk.Label(status_frame, text=progress_text, font=('Segoe UI', 10), 
                    justify='left').pack(padx=10, pady=10)
        
        # Explanation
        explanation_frame = tk.LabelFrame(info_window, text="ℹ️ How It Works", 
                                         font=('Segoe UI', 12, 'bold'))
        explanation_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        explanation_text = tk.Text(explanation_frame, wrap='word', font=('Segoe UI', 10))
        explanation_text.pack(fill='both', expand=True, padx=10, pady=10)
        explanation_text.insert('1.0', self.usage_mgr.get_referral_pass_explanation())
        explanation_text.config(state='disabled')
        
        # Close button
        close_btn = tk.Button(info_window, text="Close", command=info_window.destroy,
                             font=('Segoe UI', 11), padx=20, pady=5)
        close_btn.pack(pady=(0, 15))
