# tab_learn.py - Research-Based Learning System

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import config
import json
import os
import random
from datetime import datetime, timedelta
from collections import defaultdict
import requests

class LearnTab(tk.Frame):
    """
    Advanced Learning System implementing research-based methodologies:
    - Active Recall & Spaced Repetition
    - Feynman Technique (simple explanations)
    - Elaborative Interrogation
    - Interleaving (mixed practice)
    - Dual Coding (visual + verbal)
    - Adaptive Difficulty (ZPD)
    - Bloom's Taxonomy progression
    """
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # Learning state management
        self.current_lesson = None
        self.current_stage = "overview"  # overview, deep_dive, practice, review
        self.lesson_history = []
        self.spaced_repetition_queue = []
        self.user_knowledge_map = defaultdict(lambda: {"confidence": 0, "last_reviewed": None, "review_count": 0})
        
        # Learning preferences (will be customizable)
        self.learning_style = "adaptive"  # visual, auditory, kinesthetic, reading, adaptive
        self.difficulty_preference = "adaptive"  # beginner, intermediate, advanced, adaptive
        self.explanation_style = "feynman"  # feynman, academic, analogy, example
        
        # Load user progress
        self.load_learning_data()
        self.build_modern_ui()
        self.setup_auto_capture()
    
    def build_modern_ui(self):
        """Build modern, research-based learning interface"""
        
        # Create scrollable canvas (like humanizer tab)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Configure canvas to expand with content
        def _on_canvas_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas.find_all()[0], width=canvas_width)
        
        self.canvas.bind('<Configure>', _on_canvas_configure)
        
        # Configure scrollable frame columns
        self.scrollable_frame.columnconfigure(0, weight=1)
        
        self.widgets_to_style = []
        
        # Header Section
        self.build_header()
        
        # Learning Dashboard
        self.build_dashboard()
        
        # Settings Panel
        self.build_settings_panel()
        
        # Main Learning Area
        self.build_learning_area()
        
        # Progress Tracking
        self.build_progress_section()
    
    def build_header(self):
        """Build the header with adaptive learning status"""
        header_frame = tk.Frame(self.scrollable_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.columnconfigure(1, weight=1)
        
        # Title with brain emoji
        title_label = tk.Label(
            header_frame, 
            text="🧠 Adaptive Learning Center",
            font=('Segoe UI', 18, 'bold'),
            fg=config.LIME_GREEN
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Learning status indicator
        self.status_label = tk.Label(
            header_frame,
            text="Ready to learn • Click 'Capture from AI' or select a topic below",
            font=('Segoe UI', 10, 'italic'),
            fg=config.GRAY_600
        )
        self.status_label.grid(row=0, column=1, sticky="e", padx=(20, 0))
        
        self.widgets_to_style.extend([header_frame, title_label, self.status_label])
    
    def build_dashboard(self):
        """Build learning dashboard with quick actions and spaced repetition"""
        dashboard_frame = tk.LabelFrame(
            self.scrollable_frame, 
            text="📊 Learning Dashboard", 
            font=('Segoe UI', 12, 'bold'),
            padx=15, pady=15
        )
        dashboard_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        dashboard_frame.columnconfigure((0, 1, 2), weight=1)
        
        # Quick Actions
        actions_frame = tk.Frame(dashboard_frame)
        actions_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        tk.Label(actions_frame, text="🚀 Quick Actions", font=('Segoe UI', 10, 'bold')).pack(anchor="w")
        
        self.capture_btn = tk.Button(
            actions_frame, 
            text="📝 Capture from AI Generation",
            command=self.capture_from_ai,
            font=('Segoe UI', 9, 'bold'),
            bg=config.PRIMARY_BLUE,
            fg="white",
            relief="flat",
            padx=15, pady=8
        )
        self.capture_btn.pack(fill="x", pady=(5, 2))
        
        self.new_topic_btn = tk.Button(
            actions_frame,
            text="🎯 Start Custom Topic",
            command=self.start_custom_topic,
            font=('Segoe UI', 9),
            bg=config.GRAY_300,
            relief="flat",
            padx=15, pady=8
        )
        self.new_topic_btn.pack(fill="x", pady=2)
        
        # Spaced Repetition Queue
        review_frame = tk.Frame(dashboard_frame)
        review_frame.grid(row=0, column=1, sticky="ew", padx=10)
        
        tk.Label(review_frame, text="🔄 Spaced Repetition", font=('Segoe UI', 10, 'bold')).pack(anchor="w")
        
        self.review_queue_label = tk.Label(
            review_frame,
            text="2 topics ready for review",
            font=('Segoe UI', 9),
            fg=config.WARNING_ORANGE
        )
        self.review_queue_label.pack(anchor="w", pady=(5, 2))
        
        self.review_btn = tk.Button(
            review_frame,
            text="📖 Review Now",
            command=self.start_spaced_review,
            font=('Segoe UI', 9),
            bg=config.WARNING_ORANGE,
            fg="white",
            relief="flat",
            padx=15, pady=8
        )
        self.review_btn.pack(fill="x", pady=2)
        
        # Learning Statistics
        stats_frame = tk.Frame(dashboard_frame)
        stats_frame.grid(row=0, column=2, sticky="ew", padx=(10, 0))
        
        tk.Label(stats_frame, text="📈 Your Progress", font=('Segoe UI', 10, 'bold')).pack(anchor="w")
        
        self.stats_text = tk.Text(
            stats_frame, 
            height=4, 
            width=20,
            font=('Segoe UI', 8),
            relief="flat",
            bg=config.LIGHT_BG,
            state="disabled"
        )
        self.stats_text.pack(fill="x", pady=(5, 0))
        
        self.widgets_to_style.extend([
            dashboard_frame, actions_frame, review_frame, stats_frame,
            self.capture_btn, self.new_topic_btn, self.review_btn, self.review_queue_label, self.stats_text
        ])
    
    def build_settings_panel(self):
        """Build customizable learning settings panel"""
        settings_frame = tk.LabelFrame(
            self.scrollable_frame,
            text="⚙️ Learning Preferences",
            font=('Segoe UI', 12, 'bold'),
            padx=15, pady=15
        )
        settings_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        settings_frame.columnconfigure((0, 1, 2, 3), weight=1)
        
        # Learning Style
        style_frame = tk.Frame(settings_frame)
        style_frame.grid(row=0, column=0, sticky="ew", padx=(0, 15))
        
        tk.Label(style_frame, text="🎨 Learning Style", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.learning_style_var = tk.StringVar(value=self.learning_style)
        style_combo = ttk.Combobox(
            style_frame,
            textvariable=self.learning_style_var,
            values=["Adaptive", "Visual", "Auditory", "Reading/Writing", "Kinesthetic"],
            state="readonly",
            font=('Segoe UI', 8)
        )
        style_combo.pack(fill="x", pady=(2, 0))
        style_combo.bind("<<ComboboxSelected>>", self.update_learning_preferences)
        
        # Difficulty Level
        difficulty_frame = tk.Frame(settings_frame)
        difficulty_frame.grid(row=0, column=1, sticky="ew", padx=15)
        
        tk.Label(difficulty_frame, text="🎯 Difficulty", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.difficulty_var = tk.StringVar(value=self.difficulty_preference)
        difficulty_combo = ttk.Combobox(
            difficulty_frame,
            textvariable=self.difficulty_var,
            values=["Adaptive", "Beginner", "Intermediate", "Advanced", "Expert"],
            state="readonly",
            font=('Segoe UI', 8)
        )
        difficulty_combo.pack(fill="x", pady=(2, 0))
        difficulty_combo.bind("<<ComboboxSelected>>", self.update_learning_preferences)
        
        # Explanation Style
        explanation_frame = tk.Frame(settings_frame)
        explanation_frame.grid(row=0, column=2, sticky="ew", padx=15)
        
        tk.Label(explanation_frame, text="💭 Explanation Style", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        self.explanation_var = tk.StringVar(value=self.explanation_style)
        explanation_combo = ttk.Combobox(
            explanation_frame,
            textvariable=self.explanation_var,
            values=["Feynman (Simple)", "Academic", "Analogies", "Examples", "Step-by-Step"],
            state="readonly",
            font=('Segoe UI', 8)
        )
        explanation_combo.pack(fill="x", pady=(2, 0))
        explanation_combo.bind("<<ComboboxSelected>>", self.update_learning_preferences)
        
        # Quiz and Advanced Options
        advanced_frame = tk.Frame(settings_frame)
        advanced_frame.grid(row=0, column=3, sticky="ew", padx=(15, 0))
        
        tk.Label(advanced_frame, text="🧭 Personalize", font=('Segoe UI', 9, 'bold')).pack(anchor="w")
        
        # Learning Style Quiz Button
        self.quiz_btn = tk.Button(
            advanced_frame,
            text="📝 Take Quiz",
            command=self.show_learning_style_quiz,
            font=('Segoe UI', 8),
            bg='lightblue',
            width=12,
            cursor='hand2'
        )
        self.quiz_btn.pack(fill="x", pady=(2, 5))
        
        self.interleaving_var = tk.BooleanVar(value=True)
        interleaving_check = tk.Checkbutton(
            advanced_frame,
            text="Interleaving",
            variable=self.interleaving_var,
            font=('Segoe UI', 8)
        )
        interleaving_check.pack(anchor="w")
        
        self.elaboration_var = tk.BooleanVar(value=True)
        elaboration_check = tk.Checkbutton(
            advanced_frame,
            text="Elaborative Q&A",
            variable=self.elaboration_var,
            font=('Segoe UI', 8)
        )
        elaboration_check.pack(anchor="w")
        
        self.widgets_to_style.extend([
            settings_frame, style_frame, difficulty_frame, explanation_frame, advanced_frame,
            style_combo, difficulty_combo, explanation_combo, interleaving_check, elaboration_check
        ])
    
    def build_learning_area(self):
        """Build main learning content area with Bloom's Taxonomy progression"""
        learning_frame = tk.LabelFrame(
            self.scrollable_frame,
            text="📚 Learning Content",
            font=('Segoe UI', 12, 'bold'),
            padx=15, pady=15
        )
        learning_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        learning_frame.columnconfigure(0, weight=1)
        
        # Learning Stage Selector (Bloom's Taxonomy)
        stage_frame = tk.Frame(learning_frame)
        stage_frame.pack(fill="x", pady=(0, 15))
        
        self.stage_buttons = {}
        stages = [
            ("🧠 Overview", "remember", "Understanding the basics"),
            ("🔍 Deep Dive", "understand", "Connecting concepts"),
            ("🎯 Practice", "apply", "Active application"),
            ("🔬 Advanced", "analyze", "Critical analysis"),
            ("📝 Review", "evaluate", "Spaced repetition")
        ]
        
        for i, (text, stage, description) in enumerate(stages):
            btn = tk.Button(
                stage_frame,
                text=text,
                command=lambda s=stage: self.switch_learning_stage(s),
                font=('Segoe UI', 9, 'bold'),
                relief="flat",
                padx=15, pady=8,
                bg=config.GRAY_300 if stage != self.current_stage else config.PRIMARY_BLUE,
                fg="black" if stage != self.current_stage else "white"
            )
            btn.pack(side="left", padx=(0, 5) if i < len(stages)-1 else 0)
            self.stage_buttons[stage] = btn
        
        # Content Display Area
        content_frame = tk.Frame(learning_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Content text area with scrollbar
        self.content_text = tk.Text(
            content_frame,
            height=20,
            wrap="word",
            font=('Segoe UI', 11),
            relief="flat",
            padx=20, pady=20,
            state="disabled"
        )
        content_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scrollbar.set)
        
        self.content_text.pack(side="left", fill="both", expand=True)
        content_scrollbar.pack(side="right", fill="y")
        
        # Interactive Elements Panel
        self.interactive_frame = tk.Frame(learning_frame)
        self.interactive_frame.pack(fill="x", pady=(15, 0))
        
        self.widgets_to_style.extend([
            learning_frame, stage_frame, content_frame, self.content_text, self.interactive_frame
        ] + list(self.stage_buttons.values()))
    
    def build_progress_section(self):
        """Build progress tracking with spaced repetition scheduling"""
        progress_frame = tk.LabelFrame(
            self.scrollable_frame,
            text="📈 Learning Progress & Analytics",
            font=('Segoe UI', 12, 'bold'),
            padx=15, pady=15
        )
        progress_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(10, 20))
        progress_frame.columnconfigure((0, 1), weight=1)
        
        # Knowledge Map Visualization
        knowledge_frame = tk.Frame(progress_frame)
        knowledge_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        tk.Label(knowledge_frame, text="🗺️ Knowledge Map", font=('Segoe UI', 10, 'bold')).pack(anchor="w")
        
        self.knowledge_canvas = tk.Canvas(
            knowledge_frame,
            height=150,
            bg=config.LIGHT_BG,
            relief="flat"
        )
        self.knowledge_canvas.pack(fill="x", pady=(5, 0))
        
        # Learning History & Next Reviews
        history_frame = tk.Frame(progress_frame)
        history_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        tk.Label(history_frame, text="📅 Upcoming Reviews", font=('Segoe UI', 10, 'bold')).pack(anchor="w")
        
        self.review_listbox = tk.Listbox(
            history_frame,
            height=8,
            font=('Segoe UI', 9),
            relief="flat"
        )
        review_scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.review_listbox.yview)
        self.review_listbox.configure(yscrollcommand=review_scrollbar.set)
        
        self.review_listbox.pack(side="left", fill="both", expand=True, pady=(5, 0))
        review_scrollbar.pack(side="right", fill="y", pady=(5, 0))
        
        self.widgets_to_style.extend([
            progress_frame, knowledge_frame, history_frame, 
            self.knowledge_canvas, self.review_listbox
        ])
        
        # Initialize with demo data
        self.update_progress_display()
    
    # Core Learning Methods
    def setup_auto_capture(self):
        """Setup automatic capture from AI generation hotkey"""
        # This will be called when AI generation hotkey is used
        # We'll modify ai_text_generator.py to call this
        pass
    
    def capture_from_ai(self):
        """Capture the most recent AI generation for learning"""
        # Try to get the last AI generated content
        try:
            # Check if there's content in the humanizer tab
            if hasattr(self.app, 'humanizer_tab') and self.app.humanizer_tab.output_box.get("1.0", "end-1c").strip():
                content = self.app.humanizer_tab.output_box.get("1.0", "end-1c").strip()
                input_text = self.app.humanizer_tab.input_box.get("1.0", "end-1c").strip()
                self.create_lesson_from_content(input_text, content)
            else:
                messagebox.showinfo("No Content", "No AI-generated content found. Generate some text first using the AI features.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture content: {str(e)}")
    
    def start_custom_topic(self):
        """Start learning about a custom topic"""
        topic = tk.simpledialog.askstring("Custom Topic", "What would you like to learn about?")
        if topic:
            self.generate_lesson(topic, custom=True)
    
    def create_lesson_from_content(self, input_text, generated_content):
        """Create a comprehensive lesson from AI-generated content"""
        # Extract topic from input text
        topic = input_text[:100] + "..." if len(input_text) > 100 else input_text
        
        self.status_label.config(text=f"Creating lesson: {topic[:50]}...")
        self.update_idletasks()
        
        # Generate comprehensive lesson using the server
        lesson_data = self.generate_comprehensive_lesson(topic, generated_content)
        
        if lesson_data:
            self.current_lesson = lesson_data
            self.display_lesson(lesson_data)
            self.add_to_spaced_repetition(topic)
            self.status_label.config(text=f"Learning: {topic[:50]}...")
    
    def generate_comprehensive_lesson(self, topic, base_content=None):
        """Generate a multi-stage lesson using research-based methods"""
        try:
            # Build comprehensive prompt for lesson generation
            prompt = self.build_lesson_prompt(topic, base_content)
            
            # Call server to generate lesson
            server_url = "https://slywriterapp.onrender.com"
            response = requests.post(f"{server_url}/ai_generate_lesson", 
                                   json={"prompt": prompt}, 
                                   timeout=30)
            
            if response.status_code == 200:
                lesson_text = response.json().get("lesson", "")
                if lesson_text:
                    # Parse the structured lesson response
                    return self.parse_lesson_response(lesson_text, topic)
            
            return None
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate lesson: {str(e)}")
            return None
    
    def build_lesson_prompt(self, topic, base_content=None):
        """Build comprehensive prompt using learning science principles"""
        
        # Get user preferences
        style = self.learning_style_var.get() if hasattr(self, 'learning_style_var') else 'Adaptive'
        difficulty = self.difficulty_var.get() if hasattr(self, 'difficulty_var') else 'Adaptive'
        explanation = self.explanation_var.get() if hasattr(self, 'explanation_var') else 'Feynman (Simple)'
        
        prompt = f"""Create a comprehensive, research-based lesson about: {topic}
        
LEARNING PRINCIPLES TO IMPLEMENT:
1. FEYNMAN TECHNIQUE: Explain complex concepts in simple terms
2. ACTIVE RECALL: Include questions and exercises
3. SPACED REPETITION: Create review checkpoints
4. ELABORATIVE INTERROGATION: Add "why" and "how" questions
5. DUAL CODING: Combine verbal and visual elements
6. BLOOM'S TAXONOMY: Progress from basic to advanced

USER PREFERENCES:
- Learning Style: {style}
- Difficulty Level: {difficulty}
- Explanation Style: {explanation}

LESSON STRUCTURE (use these exact headers):

OVERVIEW:
[Provide a clear, simple introduction using Feynman technique]

KEY CONCEPTS:
[List 3-5 main concepts with simple explanations]

DEEP DIVE:
[Detailed explanations with why/how questions]

REAL-WORLD EXAMPLES:
[3-5 practical examples and applications]

VISUAL ELEMENTS:
[Describe diagrams, charts, or visual aids that would help]

ACTIVE RECALL QUESTIONS:
[5-10 questions for self-testing]

COMMON MISCONCEPTIONS:
[Address typical misunderstandings]

CONNECTIONS:
[How this relates to other topics]

REVIEW SCHEDULE:
[Spaced repetition timing suggestions]

NEXT STEPS:
[What to learn next in this topic area]

"""
        
        if base_content:
            prompt += f"\nBASE CONTENT TO BUILD FROM:\n{base_content}\n"
        
        prompt += """
IMPORTANT: Make this lesson engaging, practical, and memorable. Use analogies, stories, and examples.
Focus on understanding WHY things work, not just memorizing facts."""
        
        return prompt
    
    def parse_lesson_response(self, lesson_text, topic):
        """Parse structured lesson response into organized data"""
        lesson_data = {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
        
        # Parse sections based on headers
        sections = {
            "OVERVIEW:": "overview",
            "KEY CONCEPTS:": "concepts", 
            "DEEP DIVE:": "deep_dive",
            "REAL-WORLD EXAMPLES:": "examples",
            "VISUAL ELEMENTS:": "visual",
            "ACTIVE RECALL QUESTIONS:": "questions",
            "COMMON MISCONCEPTIONS:": "misconceptions",
            "CONNECTIONS:": "connections",
            "REVIEW SCHEDULE:": "review",
            "NEXT STEPS:": "next_steps"
        }
        
        current_section = None
        current_content = []
        
        for line in lesson_text.split('\n'):
            line = line.strip()
            if line in sections:
                if current_section:
                    lesson_data["stages"][current_section] = '\n'.join(current_content)
                current_section = sections[line]
                current_content = []
            elif line and current_section:
                current_content.append(line)
        
        # Add final section
        if current_section and current_content:
            lesson_data["stages"][current_section] = '\n'.join(current_content)
        
        return lesson_data
    
    def display_lesson(self, lesson_data):
        """Display lesson content in the learning area"""
        if not lesson_data or "stages" not in lesson_data:
            return
        
        self.current_lesson = lesson_data
        self.switch_learning_stage("remember")  # Start with overview
    
    def switch_learning_stage(self, stage):
        """Switch between learning stages using Bloom's Taxonomy"""
        if not self.current_lesson:
            self.content_text.config(state="normal")
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", "No lesson loaded. Click 'Capture from AI' or 'Start Custom Topic' to begin learning.")
            self.content_text.config(state="disabled")
            return
        
        self.current_stage = stage
        
        # Update button states
        for s, btn in self.stage_buttons.items():
            if s == stage:
                btn.config(bg=config.PRIMARY_BLUE, fg="white")
            else:
                btn.config(bg=config.GRAY_300, fg="black")
        
        # Display appropriate content
        content = self.get_stage_content(stage)
        
        self.content_text.config(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", content)
        self.content_text.config(state="disabled")
        
        # Update interactive elements
        self.update_interactive_elements(stage)
    
    def get_stage_content(self, stage):
        """Get content for specific learning stage"""
        if not self.current_lesson or "stages" not in self.current_lesson:
            return "No lesson content available."
        
        stages = self.current_lesson["stages"]
        
        if stage == "remember":  # Overview
            content = f"📚 LESSON: {self.current_lesson['topic']}\n\n"
            content += "🧠 OVERVIEW\n" + "="*50 + "\n\n"
            content += stages.get("overview", "No overview available.")
            content += "\n\n🔑 KEY CONCEPTS\n" + "="*50 + "\n\n"
            content += stages.get("concepts", "No key concepts available.")
            
        elif stage == "understand":  # Deep Dive
            content = "🔍 DEEP DIVE ANALYSIS\n" + "="*50 + "\n\n"
            content += stages.get("deep_dive", "No deep dive content available.")
            content += "\n\n💡 REAL-WORLD EXAMPLES\n" + "="*50 + "\n\n"
            content += stages.get("examples", "No examples available.")
            
        elif stage == "apply":  # Practice
            content = "🎯 ACTIVE PRACTICE\n" + "="*50 + "\n\n"
            content += "Test your understanding with these questions:\n\n"
            content += stages.get("questions", "No practice questions available.")
            content += "\n\n🎨 VISUAL LEARNING\n" + "="*50 + "\n\n"
            content += stages.get("visual", "No visual elements described.")
            
        elif stage == "analyze":  # Advanced
            content = "🔬 ADVANCED ANALYSIS\n" + "="*50 + "\n\n"
            content += "🚨 COMMON MISCONCEPTIONS\n" + "-"*30 + "\n\n"
            content += stages.get("misconceptions", "No misconceptions listed.")
            content += "\n\n🔗 CONNECTIONS TO OTHER TOPICS\n" + "-"*30 + "\n\n"
            content += stages.get("connections", "No connections listed.")
            
        elif stage == "evaluate":  # Review
            content = "📝 SPACED REPETITION REVIEW\n" + "="*50 + "\n\n"
            content += "📅 REVIEW SCHEDULE\n" + "-"*30 + "\n\n"
            content += stages.get("review", "No review schedule available.")
            content += "\n\n🎯 NEXT LEARNING STEPS\n" + "-"*30 + "\n\n"
            content += stages.get("next_steps", "No next steps available.")
        
        else:
            content = "Invalid learning stage selected."
        
        return content
    
    def update_interactive_elements(self, stage):
        """Update interactive elements based on current stage"""
        # Clear existing interactive elements
        for widget in self.interactive_frame.winfo_children():
            widget.destroy()
        
        if stage == "apply":  # Practice stage gets interactive quiz
            self.create_quiz_interface()
        elif stage == "evaluate":  # Review stage gets confidence tracking
            self.create_confidence_interface()
    
    def create_quiz_interface(self):
        """Create interactive quiz for practice stage"""
        quiz_frame = tk.Frame(self.interactive_frame)
        quiz_frame.pack(fill="x", pady=10)
        
        tk.Label(quiz_frame, text="🎯 Interactive Quiz", font=('Segoe UI', 12, 'bold')).pack(anchor="w")
        
        # Quiz question
        self.quiz_question_label = tk.Label(
            quiz_frame,
            text="Click 'Next Question' to start the quiz!",
            font=('Segoe UI', 10),
            wraplength=600,
            justify="left"
        )
        self.quiz_question_label.pack(anchor="w", pady=(5, 10))
        
        # Answer options
        self.quiz_answer_frame = tk.Frame(quiz_frame)
        self.quiz_answer_frame.pack(fill="x", pady=(0, 10))
        
        # Quiz controls
        quiz_controls = tk.Frame(quiz_frame)
        quiz_controls.pack(fill="x")
        
        self.next_question_btn = tk.Button(
            quiz_controls,
            text="📋 Next Question",
            command=self.generate_quiz_question,
            bg=config.PRIMARY_BLUE,
            fg="white",
            relief="flat",
            padx=15, pady=5
        )
        self.next_question_btn.pack(side="left", padx=(0, 10))
        
        self.quiz_feedback_label = tk.Label(
            quiz_controls,
            text="",
            font=('Segoe UI', 10, 'italic')
        )
        self.quiz_feedback_label.pack(side="left")
    
    def create_confidence_interface(self):
        """Create confidence tracking for review stage"""
        confidence_frame = tk.Frame(self.interactive_frame)
        confidence_frame.pack(fill="x", pady=10)
        
        tk.Label(confidence_frame, text="🎯 Knowledge Confidence", font=('Segoe UI', 12, 'bold')).pack(anchor="w")
        
        tk.Label(
            confidence_frame,
            text="How confident are you with this material?",
            font=('Segoe UI', 10)
        ).pack(anchor="w", pady=(5, 10))
        
        button_frame = tk.Frame(confidence_frame)
        button_frame.pack(anchor="w")
        
        confidence_levels = [
            ("😰 Need to review again", 1),
            ("🤔 Somewhat confident", 2), 
            ("😊 Pretty confident", 3),
            ("🎯 Very confident", 4),
            ("🏆 Complete mastery", 5)
        ]
        
        for text, level in confidence_levels:
            btn = tk.Button(
                button_frame,
                text=text,
                command=lambda l=level: self.update_confidence(l),
                font=('Segoe UI', 9),
                relief="flat",
                padx=10, pady=5,
                bg=config.GRAY_300
            )
            btn.pack(side="left", padx=(0, 5))
    
    def generate_quiz_question(self):
        """Generate a quiz question using active recall"""
        if not self.current_lesson or "stages" not in self.current_lesson:
            return
        
        # Extract questions from lesson content
        questions_text = self.current_lesson["stages"].get("questions", "")
        if not questions_text:
            self.quiz_question_label.config(text="No quiz questions available for this lesson.")
            return
        
        # Parse questions (simple implementation)
        questions = [q.strip() for q in questions_text.split('\n') if q.strip() and not q.strip().startswith('-')]
        
        if questions:
            question = random.choice(questions)
            self.quiz_question_label.config(text=question)
            self.quiz_feedback_label.config(text="Think about your answer, then check the lesson content!")
    
    def update_confidence(self, level):
        """Update confidence level for spaced repetition"""
        if not self.current_lesson:
            return
        
        topic = self.current_lesson["topic"]
        
        # Update knowledge map
        self.user_knowledge_map[topic]["confidence"] = level
        self.user_knowledge_map[topic]["last_reviewed"] = datetime.now()
        self.user_knowledge_map[topic]["review_count"] += 1
        
        # Schedule next review based on confidence
        next_review_days = [7, 3, 1, 0.5, 0.1][level-1]  # Lower confidence = sooner review
        next_review = datetime.now() + timedelta(days=next_review_days)
        
        # Add to spaced repetition queue
        self.add_to_spaced_repetition(topic, next_review)
        
        # Save progress
        self.save_learning_data()
        
        # Update display
        self.update_progress_display()
        
        messagebox.showinfo("Confidence Updated", f"Confidence level set to {level}/5. Next review scheduled for {next_review.strftime('%Y-%m-%d')}.")
    
    def add_to_spaced_repetition(self, topic, next_review=None):
        """Add topic to spaced repetition queue"""
        if next_review is None:
            next_review = datetime.now() + timedelta(days=1)  # Default 1 day
        
        # Remove existing entries for this topic
        self.spaced_repetition_queue = [item for item in self.spaced_repetition_queue if item["topic"] != topic]
        
        # Add new entry
        self.spaced_repetition_queue.append({
            "topic": topic,
            "next_review": next_review.isoformat(),
            "difficulty": 1  # Will be updated based on performance
        })
        
        self.save_learning_data()
    
    def start_spaced_review(self):
        """Start spaced repetition review session"""
        # Find topics due for review
        now = datetime.now()
        due_topics = []
        
        for item in self.spaced_repetition_queue:
            next_review = datetime.fromisoformat(item["next_review"])
            if next_review <= now:
                due_topics.append(item)
        
        if not due_topics:
            messagebox.showinfo("No Reviews", "No topics are due for review right now. Great job staying on top of your learning!")
            return
        
        # Start review with first due topic
        topic_data = due_topics[0]
        topic = topic_data["topic"]
        
        # Find lesson data for this topic
        for lesson in self.lesson_history:
            if lesson.get("topic") == topic:
                self.current_lesson = lesson
                self.switch_learning_stage("evaluate")
                self.status_label.config(text=f"Reviewing: {topic[:50]}...")
                break
    
    def update_learning_preferences(self, event=None):
        """Update learning preferences when user changes settings"""
        if hasattr(self, 'learning_style_var'):
            self.learning_style = self.learning_style_var.get().lower()
        if hasattr(self, 'difficulty_var'):
            self.difficulty_preference = self.difficulty_var.get().lower()
        if hasattr(self, 'explanation_var'):
            self.explanation_style = self.explanation_var.get().lower()
        
        self.save_learning_data()
    
    def update_progress_display(self):
        """Update progress visualization and review queue"""
        # Update stats text
        total_lessons = len(self.lesson_history)
        total_reviews = sum(data["review_count"] for data in self.user_knowledge_map.values())
        avg_confidence = sum(data["confidence"] for data in self.user_knowledge_map.values()) / len(self.user_knowledge_map) if self.user_knowledge_map else 0
        
        stats_text = f"📚 Lessons: {total_lessons}\n🔄 Reviews: {total_reviews}\n🎯 Avg Confidence: {avg_confidence:.1f}/5\n📈 Learning Streak: 3 days"
        
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", stats_text)
        self.stats_text.config(state="disabled")
        
        # Update review queue
        self.review_listbox.delete(0, "end")
        now = datetime.now()
        
        # Sort by next review date
        sorted_queue = sorted(self.spaced_repetition_queue, 
                             key=lambda x: datetime.fromisoformat(x["next_review"]))
        
        for item in sorted_queue[:10]:  # Show next 10 reviews
            next_review = datetime.fromisoformat(item["next_review"])
            if next_review <= now:
                status = "🔴 Due now"
            elif next_review <= now + timedelta(days=1):
                status = "🟡 Due soon"
            else:
                days_until = (next_review - now).days
                status = f"🟢 Due in {days_until} days"
            
            topic_short = item["topic"][:30] + "..." if len(item["topic"]) > 30 else item["topic"]
            self.review_listbox.insert("end", f"{status} - {topic_short}")
        
        # Update review queue count
        due_count = len([item for item in self.spaced_repetition_queue 
                        if datetime.fromisoformat(item["next_review"]) <= now])
        self.review_queue_label.config(text=f"{due_count} topics ready for review")
        
        # Update knowledge map visualization
        self.update_knowledge_map()
    
    def update_knowledge_map(self):
        """Update knowledge map visualization"""
        self.knowledge_canvas.delete("all")
        
        if not self.user_knowledge_map:
            self.knowledge_canvas.create_text(150, 75, text="Start learning to see your knowledge map!", 
                                            font=('Segoe UI', 10), fill=config.GRAY_600)
            return
        
        # Simple visualization of knowledge areas
        canvas_width = self.knowledge_canvas.winfo_width() or 400
        canvas_height = 150
        
        topics = list(self.user_knowledge_map.keys())
        for i, topic in enumerate(topics[:8]):  # Show up to 8 topics
            data = self.user_knowledge_map[topic]
            confidence = data["confidence"]
            
            # Position
            x = 50 + (i % 4) * 80
            y = 40 + (i // 4) * 70
            
            # Color based on confidence
            colors = ["#EF4444", "#F59E0B", "#10B981", "#3B82F6", "#8B5CF6"]
            color = colors[min(confidence-1, 4)] if confidence > 0 else "#9CA3AF"
            
            # Draw topic circle
            self.knowledge_canvas.create_oval(x-15, y-15, x+15, y+15, fill=color, outline="white", width=2)
            
            # Topic name
            topic_short = topic[:8] + "..." if len(topic) > 8 else topic
            self.knowledge_canvas.create_text(x, y+25, text=topic_short, font=('Segoe UI', 8), 
                                            fill=config.GRAY_800, width=60)
    
    def load_learning_data(self):
        """Load user learning progress from file"""
        try:
            if os.path.exists("learning_data.json"):
                with open("learning_data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.lesson_history = data.get("lesson_history", [])
                    self.spaced_repetition_queue = data.get("spaced_repetition_queue", [])
                    self.user_knowledge_map = defaultdict(lambda: {"confidence": 0, "last_reviewed": None, "review_count": 0})
                    self.user_knowledge_map.update(data.get("knowledge_map", {}))
                    self.learning_style = data.get("learning_style", "adaptive")
                    self.difficulty_preference = data.get("difficulty_preference", "adaptive")
                    self.explanation_style = data.get("explanation_style", "feynman")
        except Exception as e:
            print(f"Error loading learning data: {e}")
    
    def save_learning_data(self):
        """Save user learning progress to file"""
        try:
            data = {
                "lesson_history": self.lesson_history,
                "spaced_repetition_queue": self.spaced_repetition_queue,
                "knowledge_map": dict(self.user_knowledge_map),
                "learning_style": self.learning_style,
                "difficulty_preference": self.difficulty_preference,
                "explanation_style": self.explanation_style,
                "last_updated": datetime.now().isoformat()
            }
            with open("learning_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving learning data: {e}")
    
    def set_theme(self, dark):
        """Apply theme to learn tab"""
        bg = config.DARK_BG if dark else config.LIGHT_BG
        fg = config.DARK_FG if dark else config.LIGHT_FG
        
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
        
        # Update knowledge canvas
        if hasattr(self, 'knowledge_canvas'):
            self.knowledge_canvas.configure(bg=bg)
        
        # Update content text
        if hasattr(self, 'content_text'):
            entry_bg = config.DARK_ENTRY_BG if dark else "white"
            self.content_text.configure(bg=entry_bg, fg=fg, insertbackground=fg)
    
    def on_topic_select(self, event):
        """Handle topic selection from listbox"""
        selection = self.topic_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.lesson_history):
                lesson = self.lesson_history[index]
                self.display_lesson(lesson)
                self.quiz_btn.config(state='normal')
                self.review_btn.config(state='normal')
    
    def display_lesson(self, lesson):
        """Display a lesson in the viewer"""
        self.current_lesson = lesson
        
        # Update header
        question = lesson.get('original_question', 'Unknown Topic')[:50] + "..."
        self.lesson_header.config(text=f"📖 {question}")
        
        # Update content
        self.lesson_text.config(state='normal')
        self.lesson_text.delete('1.0', 'end')
        
        # Format the lesson content
        content = self._format_lesson_content(lesson)
        self.lesson_text.insert('1.0', content)
        self.lesson_text.config(state='disabled')
    
    def _format_lesson_content(self, lesson):
        """Format lesson content for display"""
        content = []
        
        # Original question
        content.append("🔍 ORIGINAL QUESTION")
        content.append("=" * 50)
        content.append(lesson.get('original_question', 'No question available'))
        content.append("\n")
        
        # Explanation style used
        style = lesson.get('explanation_style', 'casual')
        content.append(f"📝 EXPLANATION STYLE: {style.title()}")
        content.append("=" * 50)
        content.append("\n")
        
        # Main explanation
        content.append("💡 STEP-BY-STEP EXPLANATION")
        content.append("=" * 50)
        content.append(lesson.get('explanation', 'No explanation available'))
        content.append("\n")
        
        # Key points
        if 'key_points' in lesson:
            content.append("🎯 KEY POINTS")
            content.append("=" * 50)
            for i, point in enumerate(lesson['key_points'], 1):
                content.append(f"{i}. {point}")
            content.append("\n")
        
        # Real world examples
        if 'examples' in lesson:
            content.append("🌍 REAL-WORLD EXAMPLES")
            content.append("=" * 50)
            for i, example in enumerate(lesson['examples'], 1):
                content.append(f"Example {i}: {example}")
            content.append("\n")
        
        # Follow-up questions
        if 'follow_up_questions' in lesson:
            content.append("❓ FOLLOW-UP QUESTIONS")
            content.append("=" * 50)
            for i, question in enumerate(lesson['follow_up_questions'], 1):
                content.append(f"{i}. {question}")
            content.append("\n")
        
        return "\n".join(content)
    
    def add_new_lesson(self, lesson_data):
        """Add a new lesson to the history and display it"""
        # Add to history
        self.lesson_history.insert(0, lesson_data)  # Most recent first
        
        # Update topic listbox
        self.refresh_topic_list()
        
        # Auto-select and display the new lesson
        self.topic_listbox.selection_set(0)
        self.display_lesson(lesson_data)
        self.quiz_btn.config(state='normal')
        self.review_btn.config(state='normal')
        
        # Save to storage
        self.save_learning_history()
    
    def refresh_topic_list(self):
        """Refresh the topic listbox with current lessons"""
        self.topic_listbox.delete(0, 'end')
        
        for lesson in self.lesson_history:
            # Create a display name from the original question
            question = lesson.get('original_question', 'Unknown Topic')
            # Truncate long questions
            display_name = question[:60] + "..." if len(question) > 60 else question
            
            # Add timestamp if available
            if 'timestamp' in lesson:
                import datetime
                try:
                    dt = datetime.datetime.fromisoformat(lesson['timestamp'])
                    time_str = dt.strftime("%m/%d %H:%M")
                    display_name = f"[{time_str}] {display_name}"
                except:
                    pass
            
            self.topic_listbox.insert('end', display_name)
    
    def start_quiz(self):
        """Start a quiz for the current lesson"""
        if not self.current_lesson:
            return
            
        # Show quiz type selection dialog
        self._show_quiz_type_dialog()
    
    def mark_for_review(self):
        """Mark current lesson for daily review"""
        if not self.current_lesson:
            return
            
        # Add to review list if not already there
        if not self.current_lesson.get('marked_for_review', False):
            self.current_lesson['marked_for_review'] = True
            self.save_learning_history()
            messagebox.showinfo("Review", "Lesson marked for daily review!")
        else:
            messagebox.showinfo("Review", "This lesson is already marked for review.")
    
    def show_settings(self):
        """Show learning preferences settings"""
        messagebox.showinfo("Settings", "Learning settings coming soon!\n\nThis will include:\n• Explanation style preferences\n• Quiz frequency settings\n• Review reminders\n• Goal tracking")
    
    def load_learning_history(self):
        """Load learning history from config"""
        self.lesson_history = self.app.cfg.get('learning_history', [])
        self.refresh_topic_list()
    
    def save_learning_history(self):
        """Save learning history to config"""
        # Limit history to reasonable size (e.g., 100 lessons)
        max_lessons = 100
        if len(self.lesson_history) > max_lessons:
            self.lesson_history = self.lesson_history[:max_lessons]
        
        self.app.cfg['learning_history'] = self.lesson_history
        self.app.save_config()
    
    def set_theme(self, dark_mode):
        """Update theme colors"""
        bg_color = "#181816" if dark_mode else "#ffffff"
        fg_color = "#ffffff" if dark_mode else "#000000"
        entry_bg = "#3c3c3c" if dark_mode else "#ffffff"
        
        # Update widgets
        for widget in self.widgets_to_style:
            try:
                if isinstance(widget, (tk.Text, tk.Listbox)):
                    widget.config(bg=entry_bg, fg=fg_color, insertbackground=fg_color)
                elif isinstance(widget, tk.Button):
                    # Skip theme buttons that have custom colors
                    if widget != self.quiz_btn:
                        widget.config(bg=bg_color, fg=fg_color)
                else:
                    widget.config(bg=bg_color, fg=fg_color)
            except Exception:
                pass
    
    def show_learning_style_quiz(self):
        """Show learning style assessment quiz"""
        quiz_window = tk.Toplevel(self.app)
        quiz_window.title("🧭 Learning Style Assessment")
        quiz_window.geometry("700x600")
        quiz_window.resizable(False, False)
        quiz_window.transient(self.app)
        quiz_window.grab_set()
        
        # Center the window
        quiz_window.update_idletasks()
        x = (self.app.winfo_x() + (self.app.winfo_width() // 2)) - (quiz_window.winfo_width() // 2)
        y = (self.app.winfo_y() + (self.app.winfo_height() // 2)) - (quiz_window.winfo_height() // 2)
        quiz_window.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(quiz_window)
        header_frame.pack(fill='x', padx=20, pady=15)
        
        tk.Label(header_frame, text="🧭 Discover Your Learning Style", 
                font=('Segoe UI', 16, 'bold')).pack()
        tk.Label(header_frame, text="Answer these questions to personalize your learning experience",
                font=('Segoe UI', 10), wraplength=600).pack(pady=(5, 0))
        
        # Scrollable quiz area
        canvas = tk.Canvas(quiz_window, highlightthickness=0)
        scrollbar = ttk.Scrollbar(quiz_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 20))
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=(0, 20))
        
        # Quiz questions with scientific backing
        self.quiz_responses = {}
        questions = self._get_learning_style_questions()
        
        for i, question_data in enumerate(questions):
            self._create_quiz_question(scrollable_frame, i, question_data)
        
        # Update scroll region
        def update_scroll():
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind('<Configure>', lambda e: update_scroll())
        
        # Submit button
        submit_frame = tk.Frame(quiz_window)
        submit_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        submit_btn = tk.Button(submit_frame, text="📊 Analyze My Learning Style",
                              command=lambda: self._process_quiz_results(quiz_window),
                              font=('Segoe UI', 12, 'bold'), bg='#4CAF50', fg='white',
                              cursor='hand2', pady=8)
        submit_btn.pack()
    
    def _get_learning_style_questions(self):
        """Get research-based learning style assessment questions"""
        return [
            {
                'text': "When learning something new, I prefer to:",
                'options': [
                    ('A', "See diagrams, charts, or visual demonstrations", 'visual'),
                    ('B', "Listen to explanations or discuss it with others", 'auditory'), 
                    ('C', "Read detailed written instructions", 'reading'),
                    ('D', "Try it hands-on and learn by doing", 'kinesthetic')
                ]
            },
            {
                'text': "I remember information best when:",
                'options': [
                    ('A', "I can see it written down or in pictures", 'visual'),
                    ('B', "I hear it explained or repeat it out loud", 'auditory'),
                    ('C', "I read about it in detail", 'reading'),
                    ('D', "I practice using it myself", 'kinesthetic')
                ]
            },
            {
                'text': "When studying, I find it most helpful to:",
                'options': [
                    ('A', "Create mind maps, flowcharts, or highlight in colors", 'visual'),
                    ('B', "Record lectures or study with background music", 'auditory'),
                    ('C', "Take detailed notes and read textbooks", 'reading'),
                    ('D', "Use flashcards or practice exercises", 'kinesthetic')
                ]
            },
            {
                'text': "When someone gives me directions, I prefer:",
                'options': [
                    ('A', "A map or visual landmarks", 'visual'),
                    ('B', "Verbal step-by-step instructions", 'auditory'),
                    ('C', "Written directions I can refer back to", 'reading'),
                    ('D', "To walk through it once myself", 'kinesthetic')
                ]
            },
            {
                'text': "I concentrate best when:",
                'options': [
                    ('A', "My workspace is organized and visually clean", 'visual'),
                    ('B', "There's some background noise or music", 'auditory'),
                    ('C', "I have all my materials and references ready", 'reading'),
                    ('D', "I can move around or fidget while thinking", 'kinesthetic')
                ]
            },
            {
                'text': "When explaining something to others, I tend to:",
                'options': [
                    ('A', "Draw pictures or use gestures", 'visual'),
                    ('B', "Tell stories or use verbal examples", 'auditory'),
                    ('C', "Write it down or send detailed explanations", 'reading'),
                    ('D', "Show them how to do it step by step", 'kinesthetic')
                ]
            },
            {
                'text': "I learn a new skill fastest by:",
                'options': [
                    ('A', "Watching demonstrations or tutorials", 'visual'),
                    ('B', "Having someone explain it to me", 'auditory'),
                    ('C', "Reading manuals or guides", 'reading'),
                    ('D', "Jumping in and experimenting", 'kinesthetic')
                ]
            },
            {
                'text': "When solving problems, I prefer to:",
                'options': [
                    ('A', "Visualize the solution or draw it out", 'visual'),
                    ('B', "Talk through it with others", 'auditory'),
                    ('C', "Research and read about similar problems", 'reading'),
                    ('D', "Try different approaches until something works", 'kinesthetic')
                ]
            }
        ]
    
    def _create_quiz_question(self, parent, question_num, question_data):
        """Create a single quiz question with radio buttons"""
        question_frame = tk.LabelFrame(parent, text=f"Question {question_num + 1}",
                                      font=('Segoe UI', 10, 'bold'), padx=15, pady=10)
        question_frame.pack(fill='x', padx=10, pady=8)
        
        # Question text
        question_label = tk.Label(question_frame, text=question_data['text'],
                                 font=('Segoe UI', 11), wraplength=600, justify='left')
        question_label.pack(anchor='w', pady=(0, 10))
        
        # Response variable
        self.quiz_responses[question_num] = tk.StringVar()
        
        # Options
        for letter, text, style in question_data['options']:
            option_frame = tk.Frame(question_frame)
            option_frame.pack(fill='x', pady=2)
            
            radio = tk.Radiobutton(option_frame, text=f"{letter}) {text}",
                                  variable=self.quiz_responses[question_num],
                                  value=style, font=('Segoe UI', 10),
                                  wraplength=550, justify='left')
            radio.pack(anchor='w')
    
    def _process_quiz_results(self, quiz_window):
        """Process quiz results and update learning preferences"""
        # Count responses for each learning style
        style_counts = {'visual': 0, 'auditory': 0, 'reading': 0, 'kinesthetic': 0}
        total_responses = 0
        
        for response_var in self.quiz_responses.values():
            style = response_var.get()
            if style:
                style_counts[style] += 1
                total_responses += 1
        
        if total_responses < len(self.quiz_responses) * 0.7:  # At least 70% answered
            messagebox.showwarning("Incomplete Quiz", 
                                 "Please answer at least 70% of the questions for accurate results.")
            return
        
        # Find dominant style
        dominant_style = max(style_counts, key=style_counts.get)
        
        # Calculate percentages
        percentages = {style: (count / total_responses * 100) if total_responses > 0 else 0 
                      for style, count in style_counts.items()}
        
        # Close quiz window
        quiz_window.destroy()
        
        # Show results
        self._show_quiz_results(dominant_style, percentages, style_counts)
        
        # Update learning preferences
        self._apply_quiz_results(dominant_style)
    
    def _show_quiz_results(self, dominant_style, percentages, style_counts):
        """Show quiz results in a detailed window"""
        results_window = tk.Toplevel(self.app)
        results_window.title("🎯 Your Learning Style Results")
        results_window.geometry("600x500")
        results_window.resizable(False, False)
        results_window.transient(self.app)
        results_window.grab_set()
        
        # Center window
        results_window.update_idletasks()
        x = (self.app.winfo_x() + (self.app.winfo_width() // 2)) - (results_window.winfo_width() // 2)
        y = (self.app.winfo_y() + (self.app.winfo_height() // 2)) - (results_window.winfo_height() // 2)
        results_window.geometry(f"+{x}+{y}")
        
        # Results content
        main_frame = tk.Frame(results_window)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        style_icons = {'visual': '👁️', 'auditory': '👂', 'reading': '📚', 'kinesthetic': '🤲'}
        style_names = {'visual': 'Visual', 'auditory': 'Auditory', 'reading': 'Reading/Writing', 'kinesthetic': 'Kinesthetic'}
        
        header_text = f"{style_icons[dominant_style]} Your Primary Learning Style: {style_names[dominant_style]}"
        tk.Label(main_frame, text=header_text, font=('Segoe UI', 16, 'bold')).pack(pady=(0, 20))
        
        # Style breakdown
        tk.Label(main_frame, text="📊 Style Breakdown:", font=('Segoe UI', 12, 'bold')).pack(anchor='w')
        
        breakdown_frame = tk.Frame(main_frame)
        breakdown_frame.pack(fill='x', pady=10)
        
        for style in ['visual', 'auditory', 'reading', 'kinesthetic']:
            style_frame = tk.Frame(breakdown_frame)
            style_frame.pack(fill='x', pady=2)
            
            icon = style_icons[style]
            name = style_names[style]
            percentage = percentages[style]
            
            # Create a simple progress bar effect
            bar_length = int(percentage / 5)  # Scale to 20 chars max
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            tk.Label(style_frame, text=f"{icon} {name}: {bar} {percentage:.1f}%",
                    font=('Segoe UI', 10)).pack(anchor='w')
        
        # Recommendations
        tk.Label(main_frame, text="💡 Personalized Recommendations:", 
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(20, 10))
        
        recommendations = self._get_style_recommendations(dominant_style)
        rec_text = tk.Text(main_frame, height=8, wrap='word', font=('Segoe UI', 10))
        rec_text.pack(fill='both', expand=True)
        rec_text.insert('1.0', recommendations)
        rec_text.config(state='disabled')
        
        # Apply button
        apply_btn = tk.Button(main_frame, text="✅ Apply These Settings",
                             command=lambda: [self._apply_quiz_results(dominant_style), results_window.destroy()],
                             font=('Segoe UI', 12, 'bold'), bg='#4CAF50', fg='white',
                             cursor='hand2', pady=8)
        apply_btn.pack(pady=(20, 0))
    
    def _get_style_recommendations(self, style):
        """Get personalized recommendations based on learning style"""
        recommendations = {
            'visual': """🎨 VISUAL LEARNER RECOMMENDATIONS:

• Use mind maps, diagrams, and flowcharts in lessons
• Enable visual elements in lesson generation
• Highlight key concepts with colors and formatting
• Create concept maps to connect related topics
• Use charts and graphs to represent data
• Watch video demonstrations when available
• Organize information spatially on the screen

Your lessons will now include more visual representations, diagrams, and color-coded information to match your visual learning preference.""",

            'auditory': """🎵 AUDITORY LEARNER RECOMMENDATIONS:

• Read lessons aloud or use text-to-speech
• Discuss concepts with others when possible
• Use rhythmic patterns to remember key points
• Listen to background music while studying
• Record yourself explaining concepts
• Use verbal associations and word play
• Study in environments with some ambient sound

Your lessons will now include more verbal explanations, discussion prompts, and audio-friendly formatting to match your auditory learning preference.""",

            'reading': """📖 READING/WRITING LEARNER RECOMMENDATIONS:

• Take detailed written notes during lessons
• Create written summaries of key concepts
• Use lists, bullet points, and structured text
• Read additional resources on topics
• Write practice questions and answers
• Keep a learning journal or glossary
• Use written reflection exercises

Your lessons will now include more detailed text, structured information, and writing exercises to match your reading/writing learning preference.""",

            'kinesthetic': """🤲 KINESTHETIC LEARNER RECOMMENDATIONS:

• Use hands-on practice exercises and simulations
• Take breaks to move around while studying
• Use physical objects or models when possible
• Try real-world applications of concepts
• Break learning into active, shorter sessions
• Use gestures and movement to reinforce learning
• Practice skills immediately after learning them

Your lessons will now include more interactive exercises, practical applications, and activity-based learning to match your kinesthetic learning preference."""
        }
        
        return recommendations.get(style, "No specific recommendations available.")
    
    def _apply_quiz_results(self, dominant_style):
        """Apply quiz results to learning preferences"""
        # Map quiz results to preference values
        style_mapping = {
            'visual': 'Visual',
            'auditory': 'Auditory', 
            'reading': 'Reading/Writing',
            'kinesthetic': 'Kinesthetic'
        }
        
        # Update the learning style preference
        mapped_style = style_mapping.get(dominant_style, 'Adaptive')
        self.learning_style = mapped_style
        self.learning_style_var.set(mapped_style)
        
        # Also update explanation style based on learning style
        explanation_mapping = {
            'visual': 'Examples',
            'auditory': 'Step-by-Step',
            'reading': 'Academic',
            'kinesthetic': 'Feynman (Simple)'
        }
        
        explanation_style = explanation_mapping.get(dominant_style, 'Feynman (Simple)')
        self.explanation_style = explanation_style
        self.explanation_var.set(explanation_style)
        
        # Save preferences
        self.save_learning_data()
        
        # Show confirmation
        messagebox.showinfo("Settings Applied", 
                          f"Your learning preferences have been updated!\n\n"
                          f"Learning Style: {mapped_style}\n"
                          f"Explanation Style: {explanation_style}\n\n"
                          f"Future lessons will be personalized to your learning style.")

    def _show_quiz_type_dialog(self):
        """Show dialog to select quiz type"""
        dialog = tk.Toplevel(self.app)
        dialog.title("Quiz Settings")
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.transient(self.app)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (self.app.winfo_x() + (self.app.winfo_width() // 2)) - (dialog.winfo_width() // 2)
        y = (self.app.winfo_y() + (self.app.winfo_height() // 2)) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        tk.Label(dialog, text="🎯 Create Quiz", font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        # Quiz type selection
        type_frame = tk.Frame(dialog)
        type_frame.pack(pady=10)
        
        tk.Label(type_frame, text="Quiz Type:", font=('Segoe UI', 11)).pack()
        
        quiz_type = tk.StringVar(value="multiple_choice")
        type_options = [
            ("📝 Multiple Choice", "multiple_choice"),
            ("✅ True/False", "true_false"),
            ("💭 Short Answer", "short_answer")
        ]
        
        for text, value in type_options:
            tk.Radiobutton(type_frame, text=text, variable=quiz_type, value=value,
                          font=('Segoe UI', 10)).pack(anchor='w')
        
        # Number of questions
        num_frame = tk.Frame(dialog)
        num_frame.pack(pady=10)
        
        tk.Label(num_frame, text="Number of Questions:", font=('Segoe UI', 11)).pack()
        num_questions = tk.IntVar(value=3)
        tk.Spinbox(num_frame, from_=1, to=10, textvariable=num_questions, width=5).pack()
        
        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def create_quiz():
            dialog.destroy()
            self._generate_quiz(quiz_type.get(), num_questions.get())
        
        tk.Button(btn_frame, text="Create Quiz", command=create_quiz,
                 bg=config.LIME_GREEN, fg='white', font=('Segoe UI', 10, 'bold')).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 font=('Segoe UI', 10)).pack(side='left', padx=5)
    
    def _generate_quiz(self, quiz_type, num_questions):
        """Generate and display quiz"""
        try:
            import requests
            import threading
            
            def quiz_worker():
                try:
                    # Prepare lesson content for API
                    lesson_content = self.current_lesson.get('explanation', '')
                    original_question = self.current_lesson.get('original_question', '')
                    
                    data = {
                        'lesson_content': lesson_content,
                        'original_question': original_question,
                        'quiz_type': quiz_type,
                        'num_questions': num_questions,
                        'user_id': getattr(self.app, 'user_id', None)
                    }
                    
                    response = requests.post(
                        'https://slywriterapp.onrender.com/ai_generate_quiz',
                        json=data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            quiz_data = result.get('quiz')
                            # Show quiz on main thread
                            self.app.after_idle(lambda: self._show_quiz_window(quiz_data))
                        else:
                            self.app.after_idle(lambda: messagebox.showerror("Quiz Error", 
                                                                            f"Failed to generate quiz: {result.get('error', 'Unknown error')}"))
                    else:
                        self.app.after_idle(lambda: messagebox.showerror("Quiz Error", 
                                                                        f"Server error: {response.status_code}"))
                        
                except Exception as e:
                    self.app.after_idle(lambda: messagebox.showerror("Quiz Error", 
                                                                    f"Error generating quiz: {str(e)}"))
            
            # Show loading message
            messagebox.showinfo("Quiz", "Generating quiz questions...\nThis may take a moment.")
            
            # Start quiz generation in background
            quiz_thread = threading.Thread(target=quiz_worker, daemon=True)
            quiz_thread.start()
            
        except Exception as e:
            messagebox.showerror("Quiz Error", f"Error starting quiz generation: {str(e)}")