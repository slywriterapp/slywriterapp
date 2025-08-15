# tab_learn.py

import tkinter as tk
from tkinter import ttk, messagebox
import config

class LearnTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_lesson = None
        self.lesson_history = []
        self.build_ui()
        self.load_learning_history()
    
    def build_ui(self):
        """Build the learning tab interface"""
        # Title with logo
        title_frame = tk.Frame(self)
        title_frame.pack(pady=(20, 10))
        
        title_label = tk.Label(
            title_frame, 
            text="🎓 Learning Center",
            font=('Segoe UI', 16, 'bold'),
            fg=config.LIME_GREEN
        )
        title_label.pack()
        
        # Description
        desc_label = tk.Label(
            self,
            text="Interactive lessons generated from your AI text generation queries.\nExplore topics deeper with step-by-step explanations, quizzes, and examples.",
            font=('Segoe UI', 10),
            justify='center',
            wraplength=500
        )
        desc_label.pack(pady=(0, 20))
        
        # Main content area with two panes
        main_frame = tk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Left pane - Topic selector
        left_pane = tk.Frame(main_frame, relief='ridge', bd=1)
        left_pane.pack(side='left', fill='y', padx=(0, 10))
        left_pane.config(width=250)
        left_pane.pack_propagate(False)
        
        # Topic selector header
        selector_header = tk.Label(left_pane, text="📚 Learning Topics", 
                                  font=('Segoe UI', 12, 'bold'))
        selector_header.pack(pady=10)
        
        # Topic listbox with scrollbar
        listbox_frame = tk.Frame(left_pane)
        listbox_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.topic_listbox = tk.Listbox(listbox_frame, selectmode='single')
        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=self.topic_listbox.yview)
        self.topic_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.topic_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind selection event
        self.topic_listbox.bind('<<ListboxSelect>>', self.on_topic_select)
        
        # Right pane - Lesson viewer
        right_pane = tk.Frame(main_frame, relief='ridge', bd=1)
        right_pane.pack(side='right', fill='both', expand=True)
        
        # Lesson viewer header
        self.lesson_header = tk.Label(right_pane, text="📖 Select a topic to start learning", 
                                     font=('Segoe UI', 12, 'bold'))
        self.lesson_header.pack(pady=10)
        
        # Lesson content area with scrollbar
        content_frame = tk.Frame(right_pane)
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Create scrollable text widget
        self.lesson_text = tk.Text(content_frame, wrap='word', state='disabled',
                                  font=('Segoe UI', 11), padx=10, pady=10)
        lesson_scrollbar = ttk.Scrollbar(content_frame, orient='vertical', command=self.lesson_text.yview)
        self.lesson_text.configure(yscrollcommand=lesson_scrollbar.set)
        
        self.lesson_text.pack(side='left', fill='both', expand=True)
        lesson_scrollbar.pack(side='right', fill='y')
        
        # Lesson controls
        controls_frame = tk.Frame(right_pane)
        controls_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Quiz button
        self.quiz_btn = tk.Button(controls_frame, text="📝 Take Quiz", 
                                 command=self.start_quiz, state='disabled',
                                 font=('Segoe UI', 10), bg=config.LIME_GREEN, fg='white')
        self.quiz_btn.pack(side='left', padx=(0, 10))
        
        # Review button  
        self.review_btn = tk.Button(controls_frame, text="🔄 Mark for Review",
                                   command=self.mark_for_review, state='disabled',
                                   font=('Segoe UI', 10))
        self.review_btn.pack(side='left', padx=(0, 10))
        
        # Settings gear icon
        settings_btn = tk.Button(controls_frame, text="⚙️ Settings",
                               command=self.show_settings, 
                               font=('Segoe UI', 10))
        settings_btn.pack(side='right')
        
        # Store widgets for theme updates
        self.widgets_to_style = [
            self, title_frame, title_label, desc_label, main_frame,
            left_pane, right_pane, selector_header, self.lesson_header,
            content_frame, self.lesson_text, controls_frame,
            self.quiz_btn, self.review_btn, settings_btn, listbox_frame,
            self.topic_listbox
        ]
    
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