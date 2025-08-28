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

        # Workflow explanation
        self.workflow_section(row=0)
        
        # Prominent mode toggles
        self.prominent_modes_section(row=1)

        # AI Generation Settings
        self.modern_ai_settings_section(row=2)
        
        # Traditional Humanizer Settings
        self.modern_humanizer_settings_section(row=3)
        
        # Update dynamic labels on startup (after all widgets are created)
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
        
        # Show/hide response length frame (for short responses)
        if hasattr(self, 'response_length_scale'):
            parent_frame = self.response_length_scale.master
            if is_essay:
                parent_frame.grid_remove()
            else:
                parent_frame.grid()  # Show for short responses
        
        # Show/hide academic format frame (for essays)
        if hasattr(self, 'academic_format_combo'):
            format_frame = self.academic_format_combo.master
            if not is_essay:
                format_frame.grid_remove()
            else:
                format_frame.grid()  # Show for essays
                
        # Show/hide required pages frame (for essays)
        if hasattr(self, 'required_pages_scale'):
            pages_frame = self.required_pages_scale.master
            if not is_essay:
                pages_frame.grid_remove()
            else:
                pages_frame.grid()  # Show for essays

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

    def workflow_section(self, row):
        """Create clear workflow explanation"""
        workflow_frame = tk.LabelFrame(self.scrollable_frame, text="🔄 SlyWriter Workflow", 
                                      font=("Segoe UI", 12, "bold"), padx=15, pady=10)
        workflow_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=(10, 20), pady=15)
        
        # Workflow steps
        workflow_text = """How SlyWriter Works:

1. Highlight text anywhere on your computer
2. Press AI hotkey (Ctrl+Alt+G by default) 
3. Text gets enhanced by AI
4. Text gets humanized (if enabled)
5. Final text is typed out automatically

Note: No copy-pasting needed! Works in any application."""
        
        workflow_label = tk.Label(workflow_frame, text=workflow_text, 
                                 font=("Segoe UI", 10), justify="left", wraplength=600)
        workflow_label.pack(anchor="w")
        
        self.widgets_to_style.extend([workflow_frame, workflow_label])
    
    def prominent_modes_section(self, row):
        """Create prominent mode toggles with enhanced styling"""
        modes_frame = tk.LabelFrame(self.scrollable_frame, text="⚙️ AI Enhancement Modes", 
                                   font=("Segoe UI", 12, "bold"), padx=15, pady=15)
        modes_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=(10, 20), pady=15)
        modes_frame.columnconfigure((0, 1, 2), weight=1)
        
        # AI Humanizer Mode
        humanizer_card = tk.Frame(modes_frame, relief="solid", bd=2, padx=15, pady=12)
        humanizer_card.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        tk.Label(humanizer_card, text="🤖 AI Humanizer", 
                font=("Segoe UI", 11, "bold")).pack()
        tk.Label(humanizer_card, text="Makes AI text sound natural", 
                font=("Segoe UI", 9)).pack()
        
        humanizer_check = tk.Checkbutton(humanizer_card, text="Enable", 
                                        variable=self.humanizer_enabled,
                                        command=lambda: self.update_bool_setting("humanizer_enabled", self.humanizer_enabled.get()),
                                        font=("Segoe UI", 10, "bold"))
        humanizer_check.pack(pady=5)
        
        # Review Mode  
        review_card = tk.Frame(modes_frame, relief="solid", bd=2, padx=15, pady=12)
        review_card.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        tk.Label(review_card, text="👁️ Review Mode", 
                font=("Segoe UI", 11, "bold")).pack()
        tk.Label(review_card, text="Preview before typing", 
                font=("Segoe UI", 9)).pack()
        
        review_check = tk.Checkbutton(review_card, text="Enable", 
                                     variable=self.review_mode,
                                     command=lambda: self.update_bool_setting("review_mode", self.review_mode.get()),
                                     font=("Segoe UI", 10, "bold"))
        review_check.pack(pady=5)
        
        # Learning Mode with Recommended tag
        learning_card = tk.Frame(modes_frame, relief="solid", bd=2, padx=15, pady=12)
        learning_card.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        
        # Header with recommended tag
        header_frame = tk.Frame(learning_card)
        header_frame.pack()
        
        tk.Label(header_frame, text="🎓 Learning Mode", 
                font=("Segoe UI", 11, "bold")).pack()
        
        recommended_label = tk.Label(header_frame, text="✨ RECOMMENDED", 
                                    font=("Segoe UI", 8, "bold"), 
                                    fg="gold", bg="navy", padx=6, pady=2)
        recommended_label.pack(pady=(2, 0))
        
        tk.Label(learning_card, text="Auto-creates lessons", 
                font=("Segoe UI", 9)).pack()
        
        learning_check = tk.Checkbutton(learning_card, text="Enable", 
                                       variable=self.learning_mode,
                                       command=lambda: self.update_bool_setting("learning_mode", self.learning_mode.get()),
                                       font=("Segoe UI", 10, "bold"))
        learning_check.pack(pady=5)
        
        # Warning about word costs
        warning_label = tk.Label(modes_frame, 
                               text="⚠️ Words deducted even if review declined (API costs apply)",
                               font=("Segoe UI", 9, "italic"), fg="orange")
        warning_label.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        # Add to styling
        self.widgets_to_style.extend([
            modes_frame, humanizer_card, review_card, learning_card, header_frame,
            humanizer_check, review_check, learning_check, warning_label, recommended_label
        ])
    
    def modern_ai_settings_section(self, row):
        """Create modern AI text generation settings section"""
        ai_frame = tk.LabelFrame(self.scrollable_frame, text="🤖 AI Text Generation Settings", 
                                font=("Segoe UI", 12, "bold"), padx=15, pady=15)
        ai_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=(10, 20), pady=15)
        ai_frame.columnconfigure((0, 1), weight=1)
        
        # Response Type Switch
        self.response_type_section_modern(ai_frame, row=0)
        
        # Settings Info Display Area
        self.info_display_section_modern(ai_frame, row=1)
        
        # Response Length (for short responses) - Learn tab style
        response_frame = tk.Frame(ai_frame)
        response_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        
        tk.Label(response_frame, text="📏 Response Length", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.response_length_scale = ttk.Scale(
            response_frame,
            from_=1, to=5,
            variable=self.options["response_length"],
            orient='horizontal',
            command=lambda val: self.update_slider_value("response_length", val)
        )
        self.response_length_scale.pack(fill="x", pady=(2, 0))
        
        self.response_length_label = tk.Label(response_frame, text="Medium", font=('Segoe UI', 8))
        self.response_length_label.pack()
        setattr(self, "response_length_center_label", self.response_length_label)
        
        # Academic Format Settings (for essays)
        format_frame = tk.Frame(ai_frame)  
        format_frame.grid(row=2, column=1, sticky="ew", padx=15, pady=5)
        
        tk.Label(format_frame, text="📄 Academic Format", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.academic_format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.options["academic_format"],
            values=["None", "MLA", "APA", "Chicago", "IEEE"],
            state="readonly",
            width=15
        )
        self.academic_format_combo.pack(fill="x", pady=(2, 0))
        self.academic_format_combo.bind("<<ComboboxSelected>>", 
                                       lambda e: self.update_combo_setting("academic_format"))
        
        # Required Pages (for essays)
        pages_frame = tk.Frame(ai_frame)
        pages_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=5)
        
        tk.Label(pages_frame, text="📃 Required Pages", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.required_pages_scale = ttk.Scale(
            pages_frame,
            from_=1, to=20,
            variable=self.options["required_pages"],
            orient='horizontal',
            command=lambda val: self.update_slider_value("required_pages", val)
        )
        self.required_pages_scale.pack(fill="x", pady=(2, 0))
        
        self.required_pages_label = tk.Label(pages_frame, text="1 page", font=('Segoe UI', 8))
        self.required_pages_label.pack()
        setattr(self, "required_pages_center_label", self.required_pages_label)
        
        self.widgets_to_style.extend([ai_frame, response_frame, format_frame, pages_frame])
    
    def modern_humanizer_settings_section(self, row):
        """Create modern traditional humanizer settings section"""
        humanizer_frame = tk.LabelFrame(self.scrollable_frame, text="⚙️ Traditional Humanizer Settings", 
                                       font=("Segoe UI", 12, "bold"), padx=15, pady=15)
        humanizer_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=(10, 20), pady=15)
        humanizer_frame.columnconfigure((0, 1), weight=1)
        
        # Grade Level - Learn tab style
        grade_frame = tk.Frame(humanizer_frame)
        grade_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=5)
        
        tk.Label(grade_frame, text="📚 Grade Level", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.grade_level_scale = ttk.Scale(
            grade_frame,
            from_=3, to=16,
            variable=self.options["grade_level"],
            orient='horizontal',
            command=lambda val: self.update_slider_value("grade_level", val)
        )
        self.grade_level_scale.pack(fill="x", pady=(2, 0))
        
        self.grade_level_label = tk.Label(grade_frame, text="11th Grade", font=('Segoe UI', 8))
        self.grade_level_label.pack()
        setattr(self, "grade_level_center_label", self.grade_level_label)
        
        # Depth of Answer - Learn tab style  
        depth_frame = tk.Frame(humanizer_frame)
        depth_frame.grid(row=0, column=1, sticky="ew", padx=15, pady=5)
        
        tk.Label(depth_frame, text="🔍 Depth of Answer", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.depth_scale = ttk.Scale(
            depth_frame,
            from_=1, to=5,
            variable=self.options["depth"],
            orient='horizontal',
            command=lambda val: self.update_slider_value("depth", val)
        )
        self.depth_scale.pack(fill="x", pady=(2, 0))
        
        self.depth_label = tk.Label(depth_frame, text="Medium", font=('Segoe UI', 8))
        self.depth_label.pack()
        setattr(self, "depth_center_label", self.depth_label)
        
        # Tone - Learn tab style
        tone_frame = tk.Frame(humanizer_frame)
        tone_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        
        tk.Label(tone_frame, text="🎵 Tone", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.tone_combo = ttk.Combobox(
            tone_frame,
            textvariable=self.options["tone"],
            values=["Neutral", "Formal", "Casual", "Witty"],
            state="readonly",
            width=15
        )
        self.tone_combo.pack(fill="x", pady=(2, 0))
        self.tone_combo.bind("<<ComboboxSelected>>", 
                            lambda e: self.update_combo_setting("tone"))
        
        # Rewrite Style - Learn tab style
        style_frame = tk.Frame(humanizer_frame)
        style_frame.grid(row=1, column=1, sticky="ew", padx=15, pady=5)
        
        tk.Label(style_frame, text="✍️ Rewrite Style", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.rewrite_style_combo = ttk.Combobox(
            style_frame,
            textvariable=self.options["rewrite_style"],
            values=["Clear", "Concise", "Creative"],
            state="readonly",
            width=15
        )
        self.rewrite_style_combo.pack(fill="x", pady=(2, 0))
        self.rewrite_style_combo.bind("<<ComboboxSelected>>", 
                                     lambda e: self.update_combo_setting("rewrite_style"))
        
        # Use of Evidence - Learn tab style
        evidence_frame = tk.Frame(humanizer_frame)
        evidence_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        
        tk.Label(evidence_frame, text="📊 Use of Evidence", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.use_of_evidence_combo = ttk.Combobox(
            evidence_frame,
            textvariable=self.options["use_of_evidence"],
            values=["None", "Optional", "Required"],
            state="readonly",
            width=15
        )
        self.use_of_evidence_combo.pack(fill="x", pady=(2, 0))
        self.use_of_evidence_combo.bind("<<ComboboxSelected>>", 
                                       lambda e: self.update_combo_setting("use_of_evidence"))
        
        self.widgets_to_style.extend([humanizer_frame, grade_frame, depth_frame, tone_frame, style_frame, evidence_frame])
    
    def response_type_section_modern(self, parent_frame, row):
        """Create modern response type selection"""
        # Center the radio buttons
        radio_frame = tk.Frame(parent_frame)
        radio_frame.grid(row=row, column=0, columnspan=2, pady=(10, 5))
        
        tk.Label(radio_frame, text="🎯 Response Type", font=('Segoe UI', 10, 'bold')).pack()
        
        button_frame = tk.Frame(radio_frame)
        button_frame.pack(pady=(5, 0))
        
        short_radio = tk.Radiobutton(
            button_frame, text="📝 Short Response", 
            variable=self.response_type, value="short_response",
            command=self._on_response_type_change,
            font=('Segoe UI', 9)
        )
        short_radio.pack(side='left', padx=(0, 15))
        
        essay_radio = tk.Radiobutton(
            button_frame, text="📄 Essay/Document", 
            variable=self.response_type, value="essay",
            command=self._on_response_type_change,
            font=('Segoe UI', 9)
        )
        essay_radio.pack(side='left')
        
        self.widgets_to_style.extend([radio_frame, button_frame, short_radio, essay_radio])
    
    def info_display_section_modern(self, parent_frame, row):
        """Create modern settings preview area"""
        info_frame = tk.Frame(parent_frame)
        info_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=15, pady=(5, 10))
        
        tk.Label(info_frame, text="📊 Current Settings Preview", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.info_text = tk.Text(info_frame, height=3, wrap="word", state="disabled", 
                                font=("Segoe UI", 9), relief="sunken", bd=1)
        self.info_text.pack(fill="x", pady=(2, 0))
        
        self.widgets_to_style.extend([info_frame, self.info_text])

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

        scale = ttk.Scale(
            frame, from_=frm, to=to, orient="horizontal",
            variable=self.options[key],
            command=lambda val, k=key: self.update_slider_value(k, val)
        )
        scale.grid(row=1, column=0, sticky="ew", pady=(0, 4))

        # Store references for the update method
        setattr(self, f"{key}_center_label", center_label)

        self.widgets_to_style += [
            left_label, center_label, right_label,
            scale
        ]
        setattr(self, f"{key}_scale", scale)
        setattr(self, f"{key}_label", lbl)  # Store label reference for hiding

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
        setattr(self, f"{key}_label", lbl)  # Store label reference for hiding

    def update_setting(self, key, value):
        self.app.cfg["settings"].setdefault("humanizer", {})[key] = value
        save_config(self.app.cfg)
    
    def update_bool_setting(self, key, value):
        """Update boolean settings in main settings section"""
        self.app.cfg["settings"][key] = value
        save_config(self.app.cfg)
    
    def update_slider_value(self, key, value):
        """Update slider value and center label with better text"""
        val = int(float(value))
        self.options[key].set(val)
        
        # Update the center label with descriptive text
        center_label = getattr(self, f"{key}_center_label", None)
        if center_label:
            if key == "response_length":
                length_text = {1: "Very Short", 2: "Short", 3: "Medium", 4: "Long", 5: "Very Long"}
                center_label.config(text=length_text.get(val, str(val)))
            elif key == "required_pages":
                page_text = "page" if val == 1 else "pages"
                center_label.config(text=f"{val} {page_text}")
            elif key == "grade_level":
                if val <= 12:
                    center_label.config(text=f"{val}th Grade")
                else:
                    grade_names = {13: "Freshman", 14: "Sophomore", 15: "Junior", 16: "Senior/Graduate"}
                    center_label.config(text=grade_names.get(val, f"Grade {val}"))
            elif key == "depth":
                depth_names = {1: "Shallow", 2: "Basic", 3: "Medium", 4: "Deep", 5: "Comprehensive"}
                center_label.config(text=depth_names.get(val, str(val)))
            else:
                center_label.config(text=str(val))
        
        self.update_setting(key, val)
        
        # Update central info display
        self._update_info_display()
    
    def update_combo_setting(self, key):
        """Update combobox setting and trigger info display update"""
        self.update_setting(key, self.options[key].get())
        self._update_info_display()
    

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

        # TTK scales are themed automatically through ttk.Style
        # No manual theming needed as they adapt to the current theme

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
