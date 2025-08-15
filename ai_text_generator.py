# ai_text_generator.py - AI Text Generation with ChatGPT and AIUndetect Integration

import os
import json
import time
import requests
import threading
import ttkbootstrap as tb
from tkinter import messagebox, scrolledtext
import tkinter as tk
from ai_clipboard_handler import clipboard_handler
import typing_engine


class AITextGenerator:
    """Handles the complete AI text generation workflow"""
    
    def __init__(self, app):
        self.app = app
        self.is_processing = False
        self.review_window = None
        self.lesson_generated = False  # Track if lesson was generated this session
        self.generated_text = None
        
    def trigger_generation(self):
        """Main entry point for AI text generation hotkey"""
        if self.is_processing:
            print("[AI GEN] Already processing, ignoring hotkey")
            return
            
        # Start async workflow
        thread = threading.Thread(target=self._generation_workflow, daemon=True)
        thread.start()
    
    def _generation_workflow(self):
        """Complete workflow: clipboard -> ChatGPT -> Humanizer -> typing"""
        try:
            self.is_processing = True
            self.lesson_generated = False  # Reset lesson flag
            
            # Update overlay status
            self._update_status("Initializing AI Generation...")
            
            # Step 1: Capture highlighted text
            print("[AI GEN] Capturing highlighted text...")
            self._update_status("Capturing highlighted text...")
            captured_text = clipboard_handler.capture_highlighted_text()
            
            if not captured_text:
                self._update_status("Ready")
                self._show_error("No text selected", 
                               "Please highlight some text and try again.")
                return
            
            # Step 2: Validate text length
            char_count = len(captured_text)
            if char_count > 10000:
                self._update_status("Ready")
                self._show_error("Text too long", 
                               f"Selected text is {char_count} characters. Maximum is 10,000 characters.")
                return
                
            # Step 3: Process through ChatGPT
            print("[AI GEN] Processing with ChatGPT...")
            self._update_status(f"Generating AI text ({char_count} chars)...")
            chatgpt_response = self._call_chatgpt(captured_text)
            
            if not chatgpt_response:
                self._update_status("Ready")
                return  # Error already shown
            
            # Step 4: Check if humanizer is enabled
            humanizer_enabled = self.app.cfg.get('settings', {}).get('humanizer_enabled', True)
            
            final_text = chatgpt_response
            if humanizer_enabled:
                print("[AI GEN] Processing with AIUndetect humanizer...")
                self._update_status("Humanizing text with AI...")
                humanized_text = self._call_humanizer(chatgpt_response)
                if humanized_text:
                    final_text = humanized_text
                else:
                    # Humanizer failed - ask user what to do
                    self._update_status("Humanizer failed - awaiting user choice")
                    # Show humanizer failure dialog on main thread
                    self.app.after_idle(lambda: self._handle_humanizer_failure(chatgpt_response))
                    return
            
            # Step 5: Check if learning mode is enabled and generate lesson
            learning_mode = self.app.cfg.get('settings', {}).get('learning_mode', False)
            
            if learning_mode:
                print("[AI GEN] Generating educational lesson...")
                self._update_status("Generating educational lesson...")
                # Generate lesson but don't switch tabs yet - let user finish typing first
                self._generate_lesson_async(captured_text, switch_tab=False)
            
            # Step 6: Check review mode
            review_mode = self.app.cfg.get('settings', {}).get('review_mode', False)
            
            if review_mode:
                self._update_status("Review required - awaiting user approval")
                self._show_review_dialog(final_text, humanizer_enabled)
            else:
                self._update_status("Starting typing simulation...")
                self._start_typing(final_text)
                
        except Exception as e:
            print(f"[AI GEN] Unexpected error: {e}")
            self._update_status("Ready")
            self._show_error("Unexpected Error", f"An error occurred: {str(e)}")
        finally:
            self.is_processing = False
            # Restore clipboard
            clipboard_handler.restore_clipboard()
    
    def _call_chatgpt(self, input_text):
        """Generate text using ChatGPT with user's settings"""
        try:
            # Get humanizer settings for prompt construction
            settings = self.app.cfg.get('settings', {}).get('humanizer', {})
            
            # Construct prompt based on user settings
            prompt = self._build_chatgpt_prompt(input_text, settings)
            
            # Make API call through your server (which has the OPENAI_API_KEY environment variable)
            data = {
                'prompt': prompt,
                'user_id': getattr(self.app, 'user_id', None)
            }
            
            response = requests.post(
                'https://slywriterapp.onrender.com/ai_generate_text',
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    generated_text = result.get('text', '').strip()
                    
                    # Update word usage tracking
                    self._update_usage_tracking(generated_text)
                    
                    return generated_text
                else:
                    error_msg = result.get('error', 'Unknown server error')
                    self._show_error("AI Generation Error", error_msg)
                    return None
                
            else:
                error_msg = f"Server error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                self._show_error("Server Error", error_msg)
                return None
                
        except requests.exceptions.Timeout:
            self._show_error("Request Timeout", "ChatGPT API request timed out. Please try again.")
            return None
        except Exception as e:
            self._show_error("ChatGPT Error", f"Error calling ChatGPT API: {str(e)}")
            return None
    
    def _build_chatgpt_prompt(self, input_text, settings):
        """Build detailed prompt based on user's humanizer settings"""
        
        # Get response length setting (will be added in Stage 3)
        response_length = settings.get('response_length', 3)  # Default to medium
        
        # Map response length to descriptive terms - ensure all lengths are substantial
        length_mapping = {
            1: "concise but detailed (3-5 sentences, minimum 150 words)",
            2: "moderate length (5-8 sentences, minimum 200 words)", 
            3: "comprehensive (8-12 sentences, minimum 300 words)",
            4: "extensive (12-20 sentences, minimum 500 words)",
            5: "very detailed and thorough (20+ sentences, minimum 700 words)"
        }
        
        length_instruction = length_mapping.get(response_length, "medium length")
        
        # Base prompt construction
        prompt_parts = []
        prompt_parts.append(f"Based on this input text: '{input_text}'")
        prompt_parts.append(f"Generate a {length_instruction} response that:")
        
        # Tone setting
        tone = settings.get('tone', 'Neutral')
        if tone == 'Formal':
            prompt_parts.append("- Uses formal, professional language")
        elif tone == 'Casual':
            prompt_parts.append("- Uses casual, conversational language")
        elif tone == 'Witty':
            prompt_parts.append("- Uses witty, clever language with humor when appropriate")
        else:
            prompt_parts.append("- Uses neutral, balanced language")
        
        # Depth setting
        depth = settings.get('depth', 3)
        if depth <= 2:
            prompt_parts.append("- Provides a brief, surface-level treatment")
        elif depth >= 4:
            prompt_parts.append("- Provides deep, comprehensive analysis with examples")
        else:
            prompt_parts.append("- Provides moderate depth and detail")
        
        # Rewrite style
        rewrite_style = settings.get('rewrite_style', 'Clear')
        if rewrite_style == 'Concise':
            prompt_parts.append("- Is concise and direct")
        elif rewrite_style == 'Creative':
            prompt_parts.append("- Uses creative, engaging language")
        else:
            prompt_parts.append("- Is clear and well-structured")
        
        # Use of evidence
        evidence = settings.get('use_of_evidence', 'Optional')
        if evidence == 'Required':
            prompt_parts.append("- Includes specific examples, facts, or evidence")
        elif evidence == 'None':
            prompt_parts.append("- Focuses on general concepts without specific evidence")
        else:
            prompt_parts.append("- May include examples where helpful")
        
        # Academic format (will be enhanced in Stage 3)
        academic_format = settings.get('academic_format', None)
        if academic_format:
            prompt_parts.append(f"- Follows {academic_format} formatting guidelines")
        
        # Ensure adequate length based on setting
        min_words = {1: 150, 2: 200, 3: 300, 4: 500, 5: 700}.get(response_length, 300)
        prompt_parts.append(f"- CRITICAL: Ensure the response is at least {min_words} words long with substantial detail and depth")
        prompt_parts.append("- Never provide brief, short, or summary responses")
        prompt_parts.append("- Always expand with examples, explanations, and thorough coverage")
        
        return "\n".join(prompt_parts)
    
    def _call_humanizer(self, text):
        """Process text through AIUndetect humanizer via server"""
        try:
            # Map user settings to AIUndetect model
            humanizer_settings = self.app.cfg.get('settings', {}).get('humanizer', {})
            depth = humanizer_settings.get('depth', 3)
            
            # Map depth to AIUndetect model (0: quality, 1: balance, 2: human)
            if depth <= 2:
                model = "2"  # More human for shallow depth
            elif depth >= 4: 
                model = "0"  # More quality for deep depth
            else:
                model = "1"  # Balanced
            
            data = {
                'text': text,
                'model': model,
                'user_id': getattr(self.app, 'user_id', None)
            }
            
            response = requests.post(
                'https://slywriterapp.onrender.com/ai_humanize_text',
                json=data,
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('humanized_text')
                else:
                    error_msg = result.get('error', 'Unknown humanizer error')
                    raise Exception(f"AIUndetect error: {error_msg}")
            else:
                raise Exception(f"Server error: {response.status_code}")
                
        except Exception as e:
            print(f"[AI GEN] Humanizer error: {e}")
            return None
    
    def _handle_humanizer_failure(self, original_text):
        """Handle case where humanizer fails - show warning and let user choose"""
        try:
            # Ensure we're on the main thread
            if not self.app.winfo_exists():
                print("[AI GEN] App window destroyed, cannot show humanizer failure dialog")
                return
                
            def on_proceed():
                try:
                    dialog.destroy()
                    self._update_status("Starting typing simulation...")
                    self._start_typing(original_text)
                except Exception as e:
                    print(f"[AI GEN] Error in proceed handler: {e}")
            
            def on_cancel():
                try:
                    dialog.destroy()
                    self._update_status("Ready")
                    # Still charge for the words since API was used
                    self._update_usage_tracking(original_text)
                    messagebox.showinfo("Words Deducted", 
                                      "Your word count has been updated since we used AI services. "
                                      "This helps cover our costs for the API calls.")
                except Exception as e:
                    print(f"[AI GEN] Error in cancel handler: {e}")
            
            def on_close():
                try:
                    dialog.destroy()
                    self._update_status("Ready")
                except Exception as e:
                    print(f"[AI GEN] Error in close handler: {e}")
            
            dialog = tk.Toplevel(self.app)
            dialog.title("Humanizer Failed")
            dialog.geometry("450x250")
            dialog.resizable(False, False)
            dialog.grab_set()
            dialog.focus_force()
            
            # Make sure dialog stays on top and handles close properly
            dialog.protocol("WM_DELETE_WINDOW", on_close)
            dialog.transient(self.app)
            
            # Content
            tk.Label(dialog, text="⚠️ Humanizer Service Failed", 
                    font=('Segoe UI', 14, 'bold'), fg='red').pack(pady=15)
            
            tk.Label(dialog, text="The AI Humanizer service encountered an error or returned text that was too short.\n\n"
                                "You can proceed with the unhumanized text or cancel this operation.",
                    wraplength=400, justify='center', font=('Segoe UI', 10)).pack(pady=10)
            
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=20)
            
            # Make buttons more visible
            proceed_btn = tk.Button(button_frame, text="Proceed (NOT Humanized)", 
                                   command=on_proceed, bg='#ff6b35', fg='white', 
                                   font=('Segoe UI', 10, 'bold'), width=20)
            proceed_btn.pack(side='left', padx=10)
            
            cancel_btn = tk.Button(button_frame, text="Cancel", 
                                  command=on_cancel, bg='#666', fg='white',
                                  font=('Segoe UI', 10), width=10)
            cancel_btn.pack(side='left', padx=10)
            
            # Center the dialog
            dialog.update_idletasks()
            x = (self.app.winfo_x() + (self.app.winfo_width() // 2)) - (dialog.winfo_width() // 2)
            y = (self.app.winfo_y() + (self.app.winfo_height() // 2)) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            # Ensure dialog is visible
            dialog.lift()
            dialog.attributes('-topmost', True)
            dialog.after(100, lambda: dialog.attributes('-topmost', False))
            
        except Exception as e:
            print(f"[AI GEN] Error creating humanizer failure dialog: {e}")
            # Fallback: just proceed without humanization
            self._update_status("Starting typing simulation...")
            self._start_typing(original_text)
    
    def _show_review_dialog(self, text, was_humanized):
        """Show review dialog for user approval before typing"""
        if self.review_window:
            self.review_window.destroy()
        
        def on_accept():
            self.review_window.destroy()
            self.review_window = None
            self._update_status("Starting typing simulation...")
            self._start_typing(text)
        
        def on_decline():
            self.review_window.destroy()
            self.review_window = None
            self._update_status("Ready")
            # Still charge for the words
            messagebox.showinfo("Words Deducted", 
                              "Your word count has been updated since we used AI services. "
                              "This helps cover our costs for the API calls.")
        
        # Create polished review window matching app theme
        self.review_window = tk.Toplevel(self.app)
        self.review_window.title("Review AI Generated Text")
        self.review_window.geometry("600x500")
        self.review_window.grab_set()
        
        # Apply theme
        dark_mode = self.app.cfg.get('settings', {}).get('dark_mode', False)
        bg_color = "#2b2b2b" if dark_mode else "#ffffff"
        fg_color = "#ffffff" if dark_mode else "#000000"
        entry_bg = "#3c3c3c" if dark_mode else "#f0f0f0"
        
        self.review_window.configure(bg=bg_color)
        
        # Header
        header_frame = tk.Frame(self.review_window, bg=bg_color)
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        status_text = "✅ Humanized" if was_humanized else "⚠️ NOT Humanized"
        color = "#10B981" if was_humanized else "#F59E0B"
        
        tk.Label(header_frame, text="Review Generated Text", 
                font=('Segoe UI', 14, 'bold'), bg=bg_color, fg=fg_color).pack()
        tk.Label(header_frame, text=status_text, 
                font=('Segoe UI', 10, 'bold'), bg=bg_color, fg=color).pack()
        
        # Warning about word charges
        warning_frame = tk.Frame(self.review_window, bg=bg_color)
        warning_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        tk.Label(warning_frame, 
                text="⚠️ Words will be deducted from your account even if you decline",
                font=('Segoe UI', 9, 'italic'), bg=bg_color, fg="#F59E0B").pack()
        
        # Text display with scrollbar
        text_frame = tk.Frame(self.review_window, bg=bg_color)
        text_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))
        
        text_widget = scrolledtext.ScrolledText(text_frame, wrap='word', 
                                               font=('Segoe UI', 11),
                                               bg=entry_bg, fg=fg_color,
                                               height=15)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', text)
        text_widget.configure(state='disabled')  # Read-only
        
        # Buttons
        button_frame = tk.Frame(self.review_window, bg=bg_color)
        button_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        tk.Button(button_frame, text="✅ Accept & Type", 
                 command=on_accept, bg='#10B981', fg='white',
                 font=('Segoe UI', 10, 'bold'), width=15).pack(side='right', padx=(5, 0))
        tk.Button(button_frame, text="❌ Decline", 
                 command=on_decline, bg='#EF4444', fg='white',
                 font=('Segoe UI', 10, 'bold'), width=15).pack(side='right')
        
        # Center on parent
        self.review_window.transient(self.app)
        self.review_window.update_idletasks()
        x = (self.app.winfo_x() + (self.app.winfo_width() // 2)) - (self.review_window.winfo_width() // 2)
        y = (self.app.winfo_y() + (self.app.winfo_height() // 2)) - (self.review_window.winfo_height() // 2)
        self.review_window.geometry(f"+{x}+{y}")
    
    def _start_typing(self, text):
        """Start the typing simulation with the generated text"""
        try:
            # Set the text in the typing tab
            self.app.typing_tab.text_input.delete('1.0', 'end')
            self.app.typing_tab.text_input.insert('1.0', text)
            
            # Start typing (this will handle its own overlay updates)
            self.app.typing_tab.start_typing()
            
            print(f"[AI GEN] Started typing {len(text)} characters")
            
            # If lesson was generated, switch to Learn tab after a delay
            if self.lesson_generated:
                # Wait 3 seconds then switch to Learn tab
                self.app.after(3000, self._switch_to_learn_tab)
            
        except Exception as e:
            print(f"[AI GEN] Error starting typing: {e}")
            self._update_status("Ready")
            self._show_error("Typing Error", f"Error starting typing simulation: {str(e)}")
    
    def _update_usage_tracking(self, text):
        """Update word usage tracking"""
        try:
            word_count = len(text.split())
            print(f"[AI GEN] Updating usage: {word_count} words")
            
            # Update local usage tracking (fallback)
            if hasattr(self.app, 'account_tab'):
                try:
                    self.app.account_tab.update_local_usage(word_count)
                except:
                    pass
            
            # Update server usage tracking
            user_id = getattr(self.app, 'user_id', None)
            if user_id:
                try:
                    requests.post(
                        "https://slywriterapp.onrender.com/update_usage",
                        json={"user_id": user_id, "words": word_count},
                        timeout=10
                    )
                except:
                    print("[AI GEN] Failed to update server usage - using local fallback")
                    
        except Exception as e:
            print(f"[AI GEN] Error updating usage: {e}")
    
    def _update_status(self, status_text):
        """Update overlay status (thread-safe)"""
        try:
            # Use tkinter's after method for thread-safe UI updates
            if hasattr(self.app, 'overlay_tab') and self.app.overlay_tab:
                self.app.after_idle(lambda: self.app.overlay_tab.update_overlay_text(status_text))
        except Exception as e:
            print(f"[AI GEN] Error updating status: {e}")
    
    def _generate_lesson_async(self, original_question, switch_tab=True):
        """Generate educational lesson in background thread"""
        def lesson_worker():
            try:
                # Get learning preferences from config
                learning_prefs = self.app.cfg.get('settings', {}).get('learning_preferences', {})
                explanation_style = learning_prefs.get('explanation_style', 'casual')
                difficulty_level = learning_prefs.get('difficulty_level', 'intermediate')
                
                # Make API call to generate lesson
                lesson_data = self._call_lesson_api(original_question, explanation_style, difficulty_level)
                
                if lesson_data:
                    # Add lesson to Learn tab (thread-safe)
                    self.app.after_idle(lambda: self._add_lesson_to_tab(lesson_data))
                    # Mark that lesson was generated for later tab switch
                    self.lesson_generated = True
                    # Switch to Learn tab if requested (thread-safe)  
                    if switch_tab:
                        self.app.after_idle(lambda: self._switch_to_learn_tab())
                    print("[AI GEN] Lesson generated and added to Learn tab")
                else:
                    print("[AI GEN] Failed to generate lesson")
                    
            except Exception as e:
                print(f"[AI GEN] Error generating lesson: {e}")
        
        # Start background thread for lesson generation
        lesson_thread = threading.Thread(target=lesson_worker, daemon=True)
        lesson_thread.start()
    
    def _call_lesson_api(self, original_question, explanation_style, difficulty_level):
        """Call server endpoint to generate educational lesson"""
        try:
            data = {
                'original_question': original_question,
                'explanation_style': explanation_style,
                'difficulty_level': difficulty_level,
                'user_id': getattr(self.app, 'user_id', None)
            }
            
            response = requests.post(
                'https://slywriterapp.onrender.com/ai_generate_lesson',
                json=data,
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('lesson')
                else:
                    print(f"[AI GEN] Lesson API error: {result.get('error', 'Unknown error')}")
                    return None
            else:
                print(f"[AI GEN] Lesson API HTTP error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[AI GEN] Exception calling lesson API: {e}")
            return None
    
    def _add_lesson_to_tab(self, lesson_data):
        """Add lesson to Learn tab (must be called from main thread)"""
        try:
            if hasattr(self.app, 'learn_tab') and self.app.learn_tab:
                self.app.learn_tab.add_new_lesson(lesson_data)
        except Exception as e:
            print(f"[AI GEN] Error adding lesson to tab: {e}")
    
    def _switch_to_learn_tab(self):
        """Switch to Learn tab (must be called from main thread)"""
        try:
            if hasattr(self.app, 'notebook') and hasattr(self.app, 'tabs'):
                # Find the Learn tab index
                for i in range(self.app.notebook.index('end')):
                    tab_text = self.app.notebook.tab(i, 'text')
                    if 'Learn' in tab_text:
                        self.app.notebook.select(i)
                        break
        except Exception as e:
            print(f"[AI GEN] Error switching to Learn tab: {e}")
    
    def _show_error(self, title, message):
        """Show error dialog to user"""
        messagebox.showerror(title, message)


# Global instance
_ai_generator = None

def trigger_ai_text_generation(app):
    """Entry point called by hotkey system"""
    global _ai_generator
    
    if not _ai_generator:
        _ai_generator = AITextGenerator(app)
    
    _ai_generator.trigger_generation()