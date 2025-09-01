// Central API configuration
// All API endpoints should use these URLs

// Use environment variable if available, otherwise use production Render server
export const RENDER_API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://slywriterapp.onrender.com'

// Local typing backend (runs on user's machine for typing functionality)
// Use 127.0.0.1 instead of localhost to avoid IPv6 issues on Windows
export const LOCAL_TYPING_API = 'http://127.0.0.1:8000'
export const LOCAL_TYPING_WS = 'ws://127.0.0.1:8000'

// API endpoints configuration
export const API_ENDPOINTS = {
  // AI Generation (uses Render server with OpenAI key)
  AI_GENERATE: `${RENDER_API_URL}/api/ai/generate`,
  AI_HUMANIZE: `${RENDER_API_URL}/api/ai/humanize`,
  AI_FILLER: `${RENDER_API_URL}/generate_filler`,
  AI_EXPLAIN: `${RENDER_API_URL}/api/ai/explain`,
  AI_STUDY_QUESTIONS: `${RENDER_API_URL}/api/ai/study-questions`,
  
  // Learning endpoints (Render)
  LEARNING_CREATE_LESSON: `${RENDER_API_URL}/api/learning/create-lesson`,
  
  // Typing endpoints (Local backend)
  TYPING_START: `${LOCAL_TYPING_API}/api/typing/start`,
  TYPING_STOP: `${LOCAL_TYPING_API}/api/typing/stop`,
  TYPING_PAUSE: `${LOCAL_TYPING_API}/api/typing/pause`,
  TYPING_RESUME: `${LOCAL_TYPING_API}/api/typing/resume`,
  TYPING_STATUS: `${LOCAL_TYPING_API}/api/typing/status`,
  TYPING_UPDATE_WPM: `${LOCAL_TYPING_API}/api/typing/update_wpm`,
  
  // Profile endpoints (Local)
  PROFILES_LIST: `${LOCAL_TYPING_API}/api/profiles`,
  PROFILES_GENERATE_FROM_WPM: `${LOCAL_TYPING_API}/api/profiles/generate-from-wpm`,
  
  // WebSocket endpoints (Local)
  WS_TYPING: `${LOCAL_TYPING_WS}/ws`,
  
  // WPM Test (Local)
  WPM_TEST_CALCULATE: `${LOCAL_TYPING_API}/api/wpm-test/calculate`,
  
  // Voice transcription (if implemented)
  VOICE_TRANSCRIBE: `${LOCAL_TYPING_API}/api/voice/transcribe`,
  
  // Hotkeys (if implemented server-side)
  HOTKEYS_REGISTER: `${LOCAL_TYPING_API}/api/hotkeys/register`,
  HOTKEYS_RECORD: `${LOCAL_TYPING_API}/api/hotkeys/record`,
  HOTKEYS_RECORDING_STATUS: `${LOCAL_TYPING_API}/api/hotkeys/recording-status`,
}

// Helper function to get WebSocket URL with user ID
export const getWebSocketUrl = (userId: string) => {
  return `${LOCAL_TYPING_WS}/ws/${userId}`
}

// Export individual URLs for backward compatibility
export const API_URL = RENDER_API_URL
export const TYPING_API_URL = LOCAL_TYPING_API
export const AI_API_URL = RENDER_API_URL