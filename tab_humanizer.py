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
        # Create main scrollable frame
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind to configure the scroll region and make scrollable_frame expand to canvas width
        def _on_canvas_configure(event):
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # Make the scrollable frame fill the canvas width
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas.find_all()[0], width=canvas_width)
        
        self.canvas.bind('<Configure>', _on_canvas_configure)
        
        # Make scrollable_frame the main container and configure its columns for full width
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(1, weight=2)  # Give more weight to the right column
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
        
        # Response type switch
        self.response_type = tk.StringVar(value=saved.get("response_type", "short_response"))

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
        
        # Response Type Switch
        self.response_type_section(row=6)
        
        # Settings Info Display Area
        self.info_display_section(row=7)
        
        # Response Length (for short responses)
        self.slider("Response Length", "response_length", 1, 5, row=8, left="Very Short", right="Very Long")
        
        # Academic Format Settings (for essays)
        self.dropdown("Academic Format", "academic_format", ["None", "MLA", "APA", "Chicago", "IEEE"], row=9)
        self.slider("Required Pages", "required_pages", 1, 20, row=10, left="1 page", right="20 pages")

        # Original Humanizer Settings
        self.label("── Traditional Humanizer Settings ──", row=11, style="header")
        self.slider("Grade Level", "grade_level", 3, 16, row=12, left="3rd", right="16th")
        self.dropdown("Tone", "tone", ["Neutral", "Formal", "Casual", "Witty"], row=13)
        self.slider("Depth of Answer", "depth", 1, 5, row=14, left="Shallow", right="Deep")
        self.dropdown("Rewrite Style", "rewrite_style", ["Clear", "Concise", "Creative"], row=15)
        self.dropdown("Use of Evidence", "use_of_evidence", ["None", "Optional", "Required"], row=16)

        # Button container for centering
        btn_frame = tk.Frame(self.scrollable_frame)
        btn_frame.grid(row=17, column=0, columnspan=2, pady=15, padx=(10, 20))
        
        self.humanize_btn = tk.Button(btn_frame, text="Run Humanizer", command=self.run_humanizer, width=20)
        self.humanize_btn.pack()
        
        self.widgets_to_style.extend([btn_frame, self.humanize_btn])
        
        # Update dynamic labels on startup
        self._update_info_display()
        self._toggle_sections_visibility()

    def response_type_section(self, row):
        """Create response type selection (Short Response vs Essay)"""
        # Center the radio buttons directly under the header
        radio_frame = tk.Frame(self.scrollable_frame)
        radio_frame.grid(row=row, column=0, columnspan=2, pady=5)
        
        short_radio = tk.Radiobutton(
            radio_frame, text="Short Response", 
            variable=self.response_type, value="short_response",
            command=self._on_response_type_change
        )
        short_radio.pack(side='left', padx=(0, 15))
        
        essay_radio = tk.Radiobutton(
            radio_frame, text="Essay/Document", 
            variable=self.response_type, value="essay",
            command=self._on_response_type_change
        )
        essay_radio.pack(side='left')
        
        self.widgets_to_style.extend([radio_frame, short_radio, essay_radio])

    def info_display_section(self, row):
        """Create a dedicated area for displaying length/page information"""
        info_frame = tk.LabelFrame(self.scrollable_frame, text="Current Settings Preview", font=("Segoe UI", 9, "bold"))
        info_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=(10, 20), pady=5)
        info_frame.columnconfigure(0, weight=1)
        
        self.info_text = tk.Text(info_frame, height=3, wrap="word", state="disabled", 
                                font=("Segoe UI", 9), relief="flat")
        self.info_text.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        
        self.widgets_to_style.extend([info_frame, self.info_text])

    def _on_response_type_change(self):
        """Handle response type change"""
        self.update_setting("response_type", self.response_type.get())
        self._toggle_sections_visibility()
        self._update_info_display()

    def _toggle_sections_visibility(self):
        """Show/hide sections based on response type"""
        is_essay = self.response_type.get() == "essay"
        
        # Show/hide response length slider
        if hasattr(self, 'response_length_scale'):
            self.response_length_scale.grid_remove() if is_essay else self.response_length_scale.grid()
        
        # Show/hide academic format and pages
        if hasattr(self, 'academic_format_combo'):
            self.academic_format_combo.grid_remove() if not is_essay else self.academic_format_combo.grid()
        if hasattr(self, 'required_pages_scale'):
            self.required_pages_scale.grid_remove() if not is_essay else self.required_pages_scale.grid()

    def _update_info_display(self):
        """Update the central info display with current settings"""
        if not hasattr(self, 'info_text'):
            return
            
        self.info_text.config(state="normal")
        self.info_text.delete("1.0", "end")
        
        if self.response_type.get() == "short_response":
            length = self.options["response_length"].get()
            length_info = {
                1: "Very Short: ~1-2 sentences (~15-30 words)",
                2: "Short: ~2-4 sentences (~30-80 words)", 
                3: "Medium: ~4-8 sentences (~80-160 words)",
                4: "Long: ~8-15 sentences (~160-300 words)",
                5: "Very Long: ~15+ sentences (~300+ words)"
            }
            info = length_info.get(length, "Medium length")
            self.info_text.insert("1.0", f"📝 {info}\n\n💡 Perfect for quick responses and answers")
        else:  # essay
            pages = self.options["required_pages"].get()
            format_type = self.options["academic_format"].get()
            
            format_estimates = {
                "MLA": {"words_per_page": 275}, "APA": {"words_per_page": 260},
                "Chicago": {"words_per_page": 250}, "IEEE": {"words_per_page": 280},
                "None": {"words_per_page": 250}
            }
            
            est = format_estimates.get(format_type, {"words_per_page": 250})
            total_words = est["words_per_page"] * pages
            
            format_text = f" ({format_type} format)" if format_type != "None" else ""
            page_text = "page" if pages == 1 else "pages"
            
            self.info_text.insert("1.0", f"📄 {pages} {page_text}: ~{total_words} words{format_text}\n\n🎓 Perfect for essays, reports, and documents")
        
        self.info_text.config(state="disabled")

    def toggle_section(self, row):
        """Create toggle switches for main AI features"""
        toggle_frame = tk.Frame(self.scrollable_frame)
        toggle_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=(10, 20), pady=5)
        
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
            lbl = tk.Label(self.scrollable_frame, text=text, anchor="center", font=("Segoe UI", 11, "bold"))
            lbl.grid(row=row, column=0, columnspan=2, sticky="ew", padx=(10, 20), pady=(10, 5))
        else:
            lbl = tk.Label(self.scrollable_frame, text=text, anchor="w")
            lbl.grid(row=row, column=0, columnspan=2, sticky="w", padx=(10, 20))
        self.widgets_to_style.append(lbl)

    def textbox(self, row, state="normal"):
        box = tk.Text(self.scrollable_frame, height=6, wrap="word", state=state)
        box.grid(row=row, column=0, columnspan=2, sticky="ew", padx=(10, 20))
        self.widgets_to_style.append(box)
        return box

    def slider(self, label, key, frm, to, row, left=None, right=None):
        lbl = tk.Label(self.scrollable_frame, text=label)
        lbl.grid(row=row, column=0, sticky="w", padx=(10, 20))
        self.widgets_to_style.append(lbl)

        frame = tk.Frame(self.scrollable_frame)
        frame.grid(row=row, column=1, sticky="ew", padx=(10, 20))
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
            
            # Update central info display
            self._update_info_display()

        scale.config(command=update)

        self.widgets_to_style += [
            left_label, center_label, right_label,
            scale
        ]
        setattr(self, f"{key}_scale", scale)

    def dropdown(self, label, key, choices, row):
        lbl = tk.Label(self.scrollable_frame, text=label)
        lbl.grid(row=row, column=0, sticky="w", padx=(10, 20))
        combo = ttk.Combobox(self.scrollable_frame, textvariable=self.options[key], values=choices, state="readonly")
        combo.grid(row=row, column=1, sticky="ew", padx=(10, 20), pady=5)
        def dropdown_update(e, k=key):
            self.update_setting(k, self.options[k].get())
            # Update central info display
            self._update_info_display()
                
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
        if hasattr(self, 'canvas'):
            self.canvas.configure(bg=bg)
        if hasattr(self, 'scrollable_frame'):
            self.scrollable_frame.configure(bg=bg)
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
