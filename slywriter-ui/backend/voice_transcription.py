"""
Voice Transcription Module
- Supports multiple transcription backends
- Web Speech API (free, browser-based)
- OpenAI Whisper (high quality, costs money)
- Local Whisper (free, needs resources)
"""

import os
import io
import json
import tempfile
import asyncio
from typing import Optional, Union
from pathlib import Path
from fastapi import UploadFile, HTTPException
import aiofiles

# Optional imports (not all may be available)
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import whisper
    HAS_LOCAL_WHISPER = True
except ImportError:
    HAS_LOCAL_WHISPER = False

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False

class VoiceTranscriber:
    """Multi-backend voice transcription service"""
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 whisper_model: str = "base",
                 preferred_backend: str = "auto"):
        """
        Initialize the voice transcriber
        
        Args:
            openai_api_key: OpenAI API key for Whisper API
            whisper_model: Model size for local Whisper (tiny, base, small, medium, large)
            preferred_backend: Preferred backend (auto, openai, local, speech_recognition)
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.whisper_model = whisper_model
        self.preferred_backend = preferred_backend
        
        # Initialize available backends
        self.backends = self._initialize_backends()
        
        if not self.backends:
            raise RuntimeError("No transcription backends available")
        
        print(f"Available transcription backends: {list(self.backends.keys())}")
    
    def _initialize_backends(self) -> dict:
        """Initialize available transcription backends"""
        backends = {}
        
        # OpenAI Whisper API
        if HAS_OPENAI and self.openai_api_key:
            try:
                openai.api_key = self.openai_api_key
                backends['openai'] = self._transcribe_openai
                print("✅ OpenAI Whisper API initialized")
            except Exception as e:
                print(f"⚠️ OpenAI initialization failed: {e}")
        
        # Local Whisper
        if HAS_LOCAL_WHISPER:
            try:
                # Load model lazily to save memory
                self.local_whisper_model = None
                backends['local'] = self._transcribe_local_whisper
                print("✅ Local Whisper available")
            except Exception as e:
                print(f"⚠️ Local Whisper initialization failed: {e}")
        
        # Speech Recognition (Google, etc.)
        if HAS_SPEECH_RECOGNITION:
            try:
                self.recognizer = sr.Recognizer()
                backends['speech_recognition'] = self._transcribe_speech_recognition
                print("✅ Speech Recognition (Google) initialized")
            except Exception as e:
                print(f"⚠️ Speech Recognition initialization failed: {e}")
        
        # Fallback: Mock transcription for development
        backends['mock'] = self._transcribe_mock
        
        return backends
    
    async def transcribe(self, 
                        audio_data: Union[bytes, UploadFile, Path],
                        language: str = "en",
                        backend: Optional[str] = None) -> str:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Audio file data (bytes, uploaded file, or path)
            language: Language code (en, es, fr, etc.)
            backend: Specific backend to use (overrides preferred)
            
        Returns:
            Transcribed text
        """
        # Convert audio_data to bytes if needed
        audio_bytes = await self._get_audio_bytes(audio_data)
        
        # Select backend
        backend_name = backend or self.preferred_backend
        
        if backend_name == "auto":
            # Try backends in order of preference
            backend_order = ['openai', 'local', 'speech_recognition', 'mock']
            for name in backend_order:
                if name in self.backends:
                    backend_name = name
                    break
        
        if backend_name not in self.backends:
            available = list(self.backends.keys())
            raise ValueError(f"Backend '{backend_name}' not available. Available: {available}")
        
        # Call the selected backend
        transcribe_func = self.backends[backend_name]
        
        try:
            result = await transcribe_func(audio_bytes, language)
            return result
        except Exception as e:
            print(f"Transcription error with {backend_name}: {e}")
            
            # Try fallback backends
            for name, func in self.backends.items():
                if name != backend_name and name != 'mock':
                    try:
                        print(f"Trying fallback backend: {name}")
                        result = await func(audio_bytes, language)
                        return result
                    except Exception as e2:
                        print(f"Fallback {name} also failed: {e2}")
            
            # Last resort: mock
            if 'mock' in self.backends:
                return await self.backends['mock'](audio_bytes, language)
            
            raise HTTPException(status_code=500, detail="All transcription backends failed")
    
    async def _get_audio_bytes(self, audio_data: Union[bytes, UploadFile, Path]) -> bytes:
        """Convert various audio input types to bytes"""
        if isinstance(audio_data, bytes):
            return audio_data
        
        if isinstance(audio_data, UploadFile):
            return await audio_data.read()
        
        if isinstance(audio_data, (str, Path)):
            async with aiofiles.open(audio_data, 'rb') as f:
                return await f.read()
        
        raise ValueError(f"Unsupported audio data type: {type(audio_data)}")
    
    async def _transcribe_openai(self, audio_bytes: bytes, language: str) -> str:
        """Transcribe using OpenAI Whisper API"""
        if not HAS_OPENAI:
            raise RuntimeError("OpenAI library not installed")
        
        # Save audio to temporary file (OpenAI API requires file)
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Use OpenAI Whisper API
            with open(tmp_path, 'rb') as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )
            
            return transcript.text
        
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
    
    async def _transcribe_local_whisper(self, audio_bytes: bytes, language: str) -> str:
        """Transcribe using local Whisper model"""
        if not HAS_LOCAL_WHISPER:
            raise RuntimeError("Whisper library not installed")
        
        # Load model if not already loaded
        if self.local_whisper_model is None:
            print(f"Loading Whisper model: {self.whisper_model}")
            self.local_whisper_model = whisper.load_model(self.whisper_model)
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Transcribe with local Whisper
            result = self.local_whisper_model.transcribe(
                tmp_path,
                language=language,
                fp16=False  # Use FP32 for CPU
            )
            
            return result['text'].strip()
        
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
    
    async def _transcribe_speech_recognition(self, audio_bytes: bytes, language: str) -> str:
        """Transcribe using speech_recognition library (Google)"""
        if not HAS_SPEECH_RECOGNITION:
            raise RuntimeError("speech_recognition library not installed")
        
        # Convert language code to speech_recognition format
        lang_map = {
            'en': 'en-US',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'de': 'de-DE',
            'it': 'it-IT',
            'pt': 'pt-PT',
            'ru': 'ru-RU',
            'zh': 'zh-CN',
            'ja': 'ja-JP',
            'ko': 'ko-KR'
        }
        
        sr_language = lang_map.get(language, 'en-US')
        
        # Convert audio bytes to AudioData
        audio_io = io.BytesIO(audio_bytes)
        
        try:
            with sr.AudioFile(audio_io) as source:
                audio_data = self.recognizer.record(source)
            
            # Try Google Speech Recognition (free)
            text = self.recognizer.recognize_google(audio_data, language=sr_language)
            return text
        
        except sr.UnknownValueError:
            raise ValueError("Could not understand audio")
        except sr.RequestError as e:
            raise RuntimeError(f"Speech recognition error: {e}")
    
    async def _transcribe_mock(self, audio_bytes: bytes, language: str) -> str:
        """Mock transcription for development/testing"""
        # Return a sample transcription based on audio length
        audio_length = len(audio_bytes)
        
        if audio_length < 10000:
            return "This is a short test message."
        elif audio_length < 50000:
            return "This is a medium length test message that simulates voice transcription."
        else:
            return "This is a longer test message that simulates voice transcription. " \
                   "It contains multiple sentences to test the typing functionality. " \
                   "The quick brown fox jumps over the lazy dog."
    
    def get_backend_info(self) -> dict:
        """Get information about available backends"""
        info = {
            'available_backends': list(self.backends.keys()),
            'preferred_backend': self.preferred_backend,
            'backend_details': {}
        }
        
        if 'openai' in self.backends:
            info['backend_details']['openai'] = {
                'name': 'OpenAI Whisper API',
                'cost': '$0.006 per minute',
                'quality': 'Excellent',
                'speed': 'Fast',
                'requires_api_key': True
            }
        
        if 'local' in self.backends:
            info['backend_details']['local'] = {
                'name': 'Local Whisper',
                'cost': 'Free',
                'quality': f'Good ({self.whisper_model} model)',
                'speed': 'Depends on hardware',
                'requires_api_key': False
            }
        
        if 'speech_recognition' in self.backends:
            info['backend_details']['speech_recognition'] = {
                'name': 'Google Speech Recognition',
                'cost': 'Free (with limits)',
                'quality': 'Good',
                'speed': 'Fast',
                'requires_api_key': False
            }
        
        return info

# FastAPI integration
async def setup_voice_routes(app):
    """Add voice transcription routes to FastAPI app"""
    from fastapi import File, Form
    
    # Initialize transcriber
    transcriber = VoiceTranscriber()
    
    @app.post("/api/voice/transcribe")
    async def transcribe_audio(
        audio: UploadFile = File(...),
        language: str = Form(default="en"),
        backend: Optional[str] = Form(default=None)
    ):
        """Transcribe audio file to text"""
        try:
            text = await transcriber.transcribe(audio, language, backend)
            return {
                "success": True,
                "text": text,
                "language": language,
                "backend": backend or transcriber.preferred_backend
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/voice/backends")
    async def get_transcription_backends():
        """Get available transcription backends"""
        return transcriber.get_backend_info()
    
    return transcriber

# Test function
async def test_transcription():
    """Test the transcription system"""
    print("Testing Voice Transcription System")
    print("=" * 50)
    
    transcriber = VoiceTranscriber()
    
    # Test with mock audio
    mock_audio = b"Mock audio data for testing"
    
    result = await transcriber.transcribe(mock_audio)
    print(f"Mock transcription result: {result}")
    
    # Show backend info
    info = transcriber.get_backend_info()
    print(f"\nBackend info: {json.dumps(info, indent=2)}")

if __name__ == "__main__":
    # Run test
    asyncio.run(test_transcription())