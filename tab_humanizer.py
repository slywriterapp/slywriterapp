import tkinter as tk
from tkinter import ttk, messagebox
import config  # Make sure config is imported for color constants
from sly_config import save_config

class HumanizerTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.build_ui()

    def build_ui(self):
        self.columnconfigure(1, weight=1)
        saved = self.app.cfg["settings"].get("humanizer", {})

        self.options = {
            "grade_level":     tk.IntVar(value=saved.get("grade_level", 11)),
            "tone":            tk.StringVar(value=saved.get("tone", "Neutral")),
            "depth":           tk.IntVar(value=saved.get("depth", 3)),
            "rewrite_style":   tk.StringVar(value=saved.get("rewrite_style", "Clear")),
            "use_of_evidence": tk.StringVar(value=saved.get("use_of_evidence", "Optional")),
            "response_length": tk.IntVar(value=saved.get("response_length", 3)),
            "academic_format": tk.StringVar(value=saved.get("academic_format", "None")),
            "required_pages":  tk.IntVar(value=saved.get("required_pages", 1)),
        }
        
        # Boolean settings for toggles
        self.humanizer_enabled = tk.BooleanVar(value=self.app.cfg["settings"].get("humanizer_enabled", True))
        self.review_mode = tk.BooleanVar(value=self.app.cfg["settings"].get("review_mode", False))
        self.learning_mode = tk.BooleanVar(value=self.app.cfg["settings"].get("learning_mode", False))

        self.widgets_to_style = []
        self.dynamic_labels = []
        self.scale_label_frames = []

        # AI Text Generation toggles
        self.toggle_section(row=0)
        
        self.label("Text to Humanize:", row=1)
        self.input_box = self.textbox(row=2)

        self.label("Humanized Output:", row=3)
        self.output_box = self.textbox(row=4, state="disabled")

        # AI Generation Settings
        self.label("── AI Text Generation Settings ──", row=5, style="header")
        self.slider("Response Length", "response_length", 1, 5, row=6, left="Very Short", right="Very Long")
        self.length_info_label = tk.Label(self, text="", font=("Segoe UI", 9), fg="gray")
        self.length_info_label.grid(row=6, column=1, sticky="s", padx=10, pady=(0, 5))
        self.widgets_to_style.append(self.length_info_label)
        
        # Academic Format Settings
        self.dropdown("Academic Format", "academic_format", ["None", "MLA", "APA", "Chicago", "IEEE"], row=7)
        self.slider("Required Pages", "required_pages", 1, 20, row=8, left="1 page", right="20 pages")
        self.page_info_label = tk.Label(self, text="", font=("Segoe UI", 9), fg="gray")
        self.page_info_label.grid(row=8, column=1, sticky="s", padx=10, pady=(0, 5))
        self.widgets_to_style.append(self.page_info_label)

        # Original Humanizer Settings
        self.label("── Traditional Humanizer Settings ──", row=9, style="header")
        self.slider("Grade Level", "grade_level", 3, 16, row=10, left="3rd", right="16th")
        self.dropdown("Tone", "tone", ["Neutral", "Formal", "Casual", "Witty"], row=11)
        self.slider("Depth of Answer", "depth", 1, 5, row=12, left="Shallow", right="Deep")
        self.dropdown("Rewrite Style", "rewrite_style", ["Clear", "Concise", "Creative"], row=13)
        self.dropdown("Use of Evidence", "use_of_evidence", ["None", "Optional", "Required"], row=14)

        self.humanize_btn = tk.Button(self, text="Run Humanizer", command=self.run_humanizer)
        self.humanize_btn.grid(row=15, column=0, columnspan=2, pady=15)
        self.widgets_to_style.append(self.humanize_btn)
        
        # Update dynamic labels on startup
        self._update_length_info()
        self._update_page_info()

    def toggle_section(self, row):
        """Create toggle switches for main AI features"""
        toggle_frame = tk.Frame(self)
        toggle_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # First row with 3 toggles
        first_row = tk.Frame(toggle_frame)
        first_row.pack(fill='x', pady=(0, 5))
        first_row.columnconfigure((0, 1, 2), weight=1)
        
        # Humanizer On/Off Toggle
        humanizer_frame = tk.Frame(first_row)
        humanizer_frame.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        tk.Label(humanizer_frame, text="AI Humanizer:", font=("Segoe UI", 10, "bold")).pack(side='left')
        humanizer_check = tk.Checkbutton(
            humanizer_frame,
            text="On",
            variable=self.humanizer_enabled,
            command=lambda: self.update_bool_setting("humanizer_enabled", self.humanizer_enabled.get())
        )
        humanizer_check.pack(side='left', padx=(5, 0))
        
        # Review Mode Toggle  
        review_frame = tk.Frame(first_row)
        review_frame.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        tk.Label(review_frame, text="Review Mode:", font=("Segoe UI", 10, "bold")).pack(side='left')
        review_check = tk.Checkbutton(
            review_frame,
            text="On",
            variable=self.review_mode,
            command=lambda: self.update_bool_setting("review_mode", self.review_mode.get())
        )
        review_check.pack(side='left', padx=(5, 0))
        
        # Learning Mode Toggle
        learning_frame = tk.Frame(first_row)
        learning_frame.grid(row=0, column=2, sticky="w")
        
        tk.Label(learning_frame, text="Learning Mode:", font=("Segoe UI", 10, "bold")).pack(side='left')
        learning_check = tk.Checkbutton(
            learning_frame,
            text="On",
            variable=self.learning_mode,
            command=lambda: self.update_bool_setting("learning_mode", self.learning_mode.get())
        )
        learning_check.pack(side='left', padx=(5, 0))
        
        # Warning label
        warning_label = tk.Label(toggle_frame, 
                               text="⚠️ Words deducted even if review declined (API costs apply)",
                               font=("Segoe UI", 9, "italic"), fg="orange")
        warning_label.pack(pady=(0, 0))
        
        # Add to styling
        self.widgets_to_style.extend([
            toggle_frame, first_row, humanizer_frame, review_frame, learning_frame,
            humanizer_check, review_check, learning_check, warning_label
        ])

    def label(self, text, row, style="normal"):
        if style == "header":
            lbl = tk.Label(self, text=text, anchor="center", font=("Segoe UI", 11, "bold"))
            lbl.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        else:
            lbl = tk.Label(self, text=text, anchor="w")
            lbl.grid(row=row, column=0, columnspan=2, sticky="w", padx=10)
        self.widgets_to_style.append(lbl)

    def textbox(self, row, state="normal"):
        box = tk.Text(self, height=6, wrap="word", state=state)
        box.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10)
        self.widgets_to_style.append(box)
        return box

    def slider(self, label, key, frm, to, row, left=None, right=None):
        lbl = tk.Label(self, text=label)
        lbl.grid(row=row, column=0, sticky="w", padx=10)
        self.widgets_to_style.append(lbl)

        frame = tk.Frame(self)
        frame.grid(row=row, column=1, sticky="ew", padx=10)
        frame.columnconfigure(0, weight=1)

        label_frame = tk.Frame(frame)
        label_frame.grid(row=0, column=0, sticky="ew")
        label_frame.columnconfigure((0, 1, 2), weight=1)

        left_label = tk.Label(label_frame, text=left or str(frm))
        center_label = tk.Label(label_frame, text=str(self.options[key].get()))
        right_label = tk.Label(label_frame, text=right or str(to))

        self.dynamic_labels.append(center_label)
        self.scale_label_frames.append(label_frame)
        self.scale_label_frames.append(frame)

        left_label.grid(row=0, column=0, sticky="w")
        center_label.grid(row=0, column=1)
        right_label.grid(row=0, column=2, sticky="e")

        scale = tk.Scale(
            frame, from_=frm, to=to, orient="horizontal",
            variable=self.options[key], showvalue=0,
            resolution=1, sliderrelief="flat", highlightthickness=0,
            borderwidth=0
        )
        scale.grid(row=1, column=0, sticky="ew", pady=(0, 4))

        def update(val):
            val = int(float(val))
            self.options[key].set(val)
            center_label.config(text=str(val))
            self.update_setting(key, val)
            
            # Update dynamic info labels
            if key == "response_length":
                self._update_length_info()
            elif key == "required_pages":
                self._update_page_info()

        scale.config(command=update)

        self.widgets_to_style += [
            left_label, center_label, right_label,
            scale
        ]
        setattr(self, f"{key}_scale", scale)

    def dropdown(self, label, key, choices, row):
        lbl = tk.Label(self, text=label)
        lbl.grid(row=row, column=0, sticky="w", padx=10)
        combo = ttk.Combobox(self, textvariable=self.options[key], values=choices, state="readonly")
        combo.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
        def dropdown_update(e, k=key):
            self.update_setting(k, self.options[k].get())
            # Update page info when academic format changes
            if k == "academic_format":
                self._update_page_info()
                
        combo.bind("<<ComboboxSelected>>", dropdown_update)
        self.widgets_to_style.append(lbl)
        setattr(self, f"{key}_combo", combo)

    def update_setting(self, key, value):
        self.app.cfg["settings"].setdefault("humanizer", {})[key] = value
        save_config(self.app.cfg)
    
    def update_bool_setting(self, key, value):
        """Update boolean settings in main settings section"""
        self.app.cfg["settings"][key] = value
        save_config(self.app.cfg)
    
    def _update_length_info(self):
        """Update the response length information label"""
        length = self.options["response_length"].get()
        
        # Estimate sentences and words
        length_info = {
            1: "~1-2 sentences (~15-30 words)",
            2: "~2-4 sentences (~30-80 words)", 
            3: "~4-8 sentences (~80-160 words)",
            4: "~8-15 sentences (~160-300 words)",
            5: "~15+ sentences (~300+ words)"
        }
        
        info_text = length_info.get(length, "Medium length")
        if hasattr(self, 'length_info_label'):
            self.length_info_label.config(text=info_text)
    
    def _update_page_info(self):
        """Update the page requirement information based on academic format"""
        pages = self.options["required_pages"].get()
        format_type = self.options["academic_format"].get()
        
        # Academic format word/character estimates per page
        format_estimates = {
            "MLA": {"words_per_page": 275, "chars_per_page": 1800},
            "APA": {"words_per_page": 260, "chars_per_page": 1700},
            "Chicago": {"words_per_page": 250, "chars_per_page": 1650},
            "IEEE": {"words_per_page": 280, "chars_per_page": 1850},
            "None": {"words_per_page": 250, "chars_per_page": 1650}
        }
        
        if format_type in format_estimates:
            est = format_estimates[format_type]
            total_words = est["words_per_page"] * pages
            total_chars = est["chars_per_page"] * pages
            
            if pages == 1:
                info_text = f"~{total_words} words (~{total_chars} chars)"
            else:
                info_text = f"~{total_words} words (~{total_chars} chars) for {pages} pages"
                
            if hasattr(self, 'page_info_label'):
                self.page_info_label.config(text=info_text)

    def run_humanizer(self):
        raw_text = self.input_box.get("1.0", "end-1c").strip()
        if not raw_text:
            messagebox.showwarning("Missing Text", "Please enter text to humanize.")
            return

        settings = {k: v.get() for k, v in self.options.items()}
        print("▶ Humanizer settings selected:", settings)
        print("▶ Input text:", raw_text)

        output = f"[Humanized text at grade {settings['grade_level']}, tone: {settings['tone']}]"

        self.output_box.config(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", output)
        self.output_box.config(state="disabled")

    def set_theme(self, dark):
        bg = config.DARK_BG if dark else config.LIGHT_BG
        fg = config.DARK_FG if dark else config.LIGHT_FG
        entry_bg = config.DARK_ENTRY_BG if dark else "white"
        entry_fg = config.LIGHT_FG if dark else config.DARK_FG
        trough_color_dark = "#444444"
        trough_color_light = "#cccccc"  # lighter gray for light mode to increase visibility

        self.configure(bg=bg)
        for widget in self.widgets_to_style:
            try:
                widget.configure(bg=bg, fg=fg)
            except:
                pass

        for label in self.dynamic_labels:
            label.configure(bg=bg, fg=fg)

        self.input_box.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        self.output_box.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)

        # Apply slider style without border and with visible rail color depending on theme
        for key in ["grade_level", "depth"]:
            scale = getattr(self, f"{key}_scale", None)
            if scale:
                scale.config(
                    troughcolor=trough_color_dark if dark else trough_color_light,
                    highlightbackground=bg,
                    highlightcolor=bg,
                    borderwidth=0,
                    sliderrelief="flat",
                    highlightthickness=0,
                )

        # Set background for label frames related to sliders
        for frame in self.scale_label_frames:
            try:
                frame.configure(bg=bg)
                for child in frame.winfo_children():
                    try:
                        child.configure(bg=bg, fg=fg)
                    except:
                        pass
            except:
                pass

        style = ttk.Style()
        style.theme_use("default")
        combo_style = "Dark.TCombobox" if dark else "Light.TCombobox"
        style.configure(combo_style,
                        fieldbackground=entry_bg,
                        background=entry_bg,
                        foreground=entry_fg,
                        selectforeground=entry_fg,
                        selectbackground=entry_bg)

        for key in ["tone", "rewrite_style", "use_of_evidence"]:
            combo = getattr(self, f"{key}_combo", None)
            if combo:
                combo.configure(style=combo_style)
