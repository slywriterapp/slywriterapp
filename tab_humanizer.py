import tkinter as tk
from tkinter import ttk, messagebox
import config  # Make sure config is imported for color constants

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
        }

        self.widgets_to_style = []
        self.dynamic_labels = []
        self.scale_label_frames = []

        self.label("Text to Humanize:", row=0)
        self.input_box = self.textbox(row=1)

        self.label("Humanized Output:", row=2)
        self.output_box = self.textbox(row=3, state="disabled")

        # Sliders
        self.slider("Grade Level", "grade_level", 3, 16, row=4, left="3rd", right="16th")
        self.dropdown("Tone", "tone", ["Neutral", "Formal", "Casual", "Witty"], row=5)
        self.slider("Depth of Answer", "depth", 1, 5, row=6, left="Shallow", right="Deep")
        self.dropdown("Rewrite Style", "rewrite_style", ["Clear", "Concise", "Creative"], row=7)
        self.dropdown("Use of Evidence", "use_of_evidence", ["None", "Optional", "Required"], row=8)

        self.humanize_btn = tk.Button(self, text="Run Humanizer", command=self.run_humanizer)
        self.humanize_btn.grid(row=9, column=0, columnspan=2, pady=15)
        self.widgets_to_style.append(self.humanize_btn)

    def label(self, text, row):
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
        combo.bind("<<ComboboxSelected>>", lambda e, k=key: self.update_setting(k, self.options[k].get()))
        self.widgets_to_style.append(lbl)
        setattr(self, f"{key}_combo", combo)

    def update_setting(self, key, value):
        self.app.cfg["settings"].setdefault("humanizer", {})[key] = value
        self.app.save_config()

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
