"""
AI Integration Module for SlyWriter
Handles ChatGPT/OpenAI API integration for text generation and learning
"""

import os
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
import asyncio
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AIGenerator:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("No OpenAI API key found. AI features will be limited.")
    
    def is_available(self) -> bool:
        """Check if AI generation is available"""
        return self.client is not None
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        model: str = "gpt-3.5-turbo",
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate text using OpenAI API"""
        
        if not self.client:
            return {
                "success": False,
                "text": self._generate_mock_response(prompt),
                "mock": True,
                "error": "OpenAI API not configured"
            }
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            )
            
            generated_text = response.choices[0].message.content
            
            return {
                "success": True,
                "text": generated_text,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return {
                "success": False,
                "text": self._generate_mock_response(prompt),
                "mock": True,
                "error": str(e)
            }
    
    async def generate_essay(
        self,
        topic: str,
        word_count: int = 500,
        tone: str = "neutral",
        academic_level: str = "college",
        include_citations: bool = False
    ) -> Dict[str, Any]:
        """Generate an essay on a specific topic"""
        
        system_prompt = f"""You are an expert academic writer. Write a {word_count}-word essay 
        at a {academic_level} level with a {tone} tone. 
        {'Include proper citations in APA format.' if include_citations else ''}
        Structure the essay with clear introduction, body paragraphs, and conclusion."""
        
        prompt = f"Write an essay about: {topic}"
        
        # Calculate tokens (roughly 1.3 tokens per word)
        max_tokens = int(word_count * 1.3)
        
        result = await self.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            system_prompt=system_prompt
        )
        
        return result
    
    async def humanize_text(
        self,
        text: str,
        style: str = "natural",
        preserve_meaning: bool = True
    ) -> Dict[str, Any]:
        """Humanize AI-generated text to make it more natural"""
        
        system_prompt = """You are an expert at rewriting text to sound more human and natural.
        Maintain the original meaning while:
        - Varying sentence structure
        - Adding personal touches
        - Using more colloquial language where appropriate
        - Fixing any robotic or repetitive patterns
        - Making the text flow naturally"""
        
        prompt = f"Rewrite the following text to sound more human and {style}:\n\n{text}"
        
        result = await self.generate_text(
            prompt=prompt,
            max_tokens=len(text.split()) * 2,  # Allow for expansion
            temperature=0.8,
            system_prompt=system_prompt
        )
        
        return result
    
    async def explain_topic(
        self,
        topic: str,
        learning_style: str = "visual",
        complexity: str = "intermediate"
    ) -> Dict[str, Any]:
        """Generate educational explanation of a topic"""
        
        style_prompts = {
            "visual": "Use vivid descriptions and visual analogies",
            "auditory": "Explain as if speaking, with rhythm and flow",
            "kinesthetic": "Use hands-on examples and action-oriented language",
            "analytical": "Break down into logical steps with clear reasoning"
        }
        
        system_prompt = f"""You are an expert educator who adapts to different learning styles.
        Explain topics at an {complexity} level.
        {style_prompts.get(learning_style, 'Use clear, engaging explanations')}.
        Include examples and make the content memorable."""
        
        prompt = f"Explain this topic in an engaging way: {topic}"
        
        result = await self.generate_text(
            prompt=prompt,
            max_tokens=800,
            temperature=0.7,
            system_prompt=system_prompt
        )
        
        return result
    
    async def generate_study_questions(
        self,
        topic: str,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """Generate study questions for a topic"""
        
        system_prompt = f"""Generate {num_questions} thought-provoking study questions 
        at a {difficulty} difficulty level. Include a mix of:
        - Comprehension questions
        - Application questions  
        - Analysis questions
        - Synthesis questions
        Format each question clearly and provide brief answer guidelines."""
        
        prompt = f"Create study questions for: {topic}"
        
        result = await self.generate_text(
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
            system_prompt=system_prompt
        )
        
        return result
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate a mock response when API is not available"""
        
        # Simple mock responses based on keywords
        if "essay" in prompt.lower():
            return """This is a mock essay response. In a production environment with a valid OpenAI API key, 
            this would generate a full essay on your requested topic. The essay would include:
            
            Introduction: Setting up the main argument and thesis statement.
            
            Body Paragraphs: Multiple paragraphs developing the main points with evidence and examples.
            
            Conclusion: Summarizing the key arguments and providing final thoughts.
            
            To enable real AI generation, please add your OpenAI API key to the environment variables."""
        
        elif "explain" in prompt.lower():
            return """This is a mock explanation. With a valid OpenAI API key, this would provide 
            a detailed, educational explanation tailored to your learning style. The explanation would 
            break down complex concepts into understandable parts with relevant examples."""
        
        else:
            return f"""This is a simulated response to: "{prompt[:100]}..."
            
            To enable real AI generation:
            1. Get an API key from OpenAI (https://platform.openai.com/api-keys)
            2. Set the OPENAI_API_KEY environment variable
            3. Restart the application
            
            Real AI generation would provide contextual, intelligent responses based on your input."""

# Singleton instance
ai_generator = AIGenerator()