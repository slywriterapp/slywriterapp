'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { useHotkeys } from 'react-hotkeys-hook'
import { 
  PlayIcon, PauseIcon, StopCircleIcon, SparklesIcon,
  FileTextIcon, CopyIcon, TrashIcon, CheckIcon,
  ClockIcon, TrendingUpIcon, TargetIcon, EyeIcon,
  DownloadIcon, UploadIcon, SaveIcon, RotateCcwIcon,
  ZapIcon, BrainIcon, ShieldIcon, TimerIcon, 
  KeyboardIcon, GaugeIcon, AlertCircleIcon, CrownIcon,
  RefreshCwIcon, ActivityIcon, ChevronUpIcon, ChevronDownIcon,
  ClipboardIcon, MicIcon, SettingsIcon, VolumeIcon,
  CircleIcon, XIcon
} from 'lucide-react'

const API_URL = 'http://localhost:8000'

interface TypingTabProps {
  connected: boolean
  initialProfile?: string
  shouldOpenWpmTest?: boolean
  onWpmTestOpened?: () => void
}

export default function TypingTabComplete({ connected, initialProfile }: TypingTabProps) {
  const { user, isPremium, canType, wordsRemaining } = useAuth()
  
  // Core state
  const [inputText, setInputText] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isTyping, setIsTyping] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [status, setStatus] = useState('Ready')
  const [progress, setProgress] = useState(0)
  const [wpm, setWpm] = useState(0)
  const [countdown, setCountdown] = useState<number | null>(null)
  const [isFromClipboard, setIsFromClipboard] = useState(false)
  
  // Enhanced Settings
  const [settings, setSettings] = useState({
    pasteMode: false,
    pasteModeTimer: 5,
    autoClearAfterClipboard: true,
    delayedTypoCorrection: false,
    typoCorrectionDelay: 3,
    voiceInputEnabled: true,
    showAdvanced: false
  })
  
  // Paste Mode state
  const [isPasteModeActive, setIsPasteModeActive] = useState(false)
  const [pasteCountdown, setPasteCountdown] = useState<number | null>(null)
  
  // Voice Input state
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTimer, setRecordingTimer] = useState(0)
  
  // Profile state
  const [selectedProfile, setSelectedProfile] = useState(initialProfile || 'Medium')
  const [customWpm, setCustomWpm] = useState<number | null>(null)
  const [showCustomWpm, setShowCustomWpm] = useState(false)
  
  const wsRef = useRef<WebSocket | null>(null)
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const recordingRef = useRef<MediaRecorder | null>(null)
  
  // Load settings from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedSettings = localStorage.getItem('slywriter-typing-settings')
      if (savedSettings) {
        try {
          setSettings(JSON.parse(savedSettings))
        } catch (e) {
          console.error('Failed to load settings:', e)
        }
      }
    }
  }, [])
  
  // Save settings
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('slywriter-typing-settings', JSON.stringify(settings))
    }
  }, [settings])
  
  // WebSocket connection
  useEffect(() => {
    if (!connected) return
    
    const userId = user?.email || 'anonymous'
    const ws = new WebSocket(`ws://localhost:8000/ws/${userId}`)
    
    ws.onopen = () => {
      console.log('WebSocket connected')
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      switch(data.type) {
        case 'typing_progress':
          setProgress(data.progress || 0)
          setWpm(data.wpm || 0)
          break
          
        case 'typing_complete':
          handleTypingComplete()
          break
          
        case 'countdown':
          setCountdown(data.count)
          if (data.count === 0) {
            setCountdown(null)
            setStatus('Typing...')
          }
          break
          
        case 'typing_started':
          setIsTyping(true)
          setStatus('Typing...')
          break
      }
    }
    
    wsRef.current = ws
    
    return () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
    }
  }, [connected, user])
  
  // Handle typing complete
  const handleTypingComplete = () => {
    setIsTyping(false)
    setIsPaused(false)
    setStatus('Complete')
    toast.success('Typing complete!')
    
    // Auto-clear if from clipboard
    if (isFromClipboard && settings.autoClearAfterClipboard) {
      setInputText('')
      setIsFromClipboard(false)
      toast.success('Input cleared (auto-clear enabled)')
    }
    
    setTimeout(() => {
      setProgress(0)
      setStatus('Ready')
    }, 3000)
  }
  
  // Paste Mode Handler
  const handlePasteMode = async () => {
    if (isTyping || isPasteModeActive) return
    
    setIsPasteModeActive(true)
    
    // Countdown
    for (let i = settings.pasteModeTimer; i > 0; i--) {
      setPasteCountdown(i)
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
    
    setPasteCountdown(null)
    setIsPasteModeActive(false)
    
    // Get text from clipboard
    try {
      const clipboardText = await navigator.clipboard.readText()
      if (clipboardText && clipboardText.trim()) {
        setInputText(clipboardText.trim())
        setIsFromClipboard(true)
        toast.success('Text pasted from clipboard!')
        
        // Auto-start typing
        setTimeout(() => handleStart(), 500)
      } else {
        toast.error('No text found in clipboard')
      }
    } catch (err) {
      toast.error('Clipboard access denied')
    }
  }
  
  // Voice Recording Handlers
  const startVoiceRecording = async () => {
    if (!settings.voiceInputEnabled || isRecording || isTyping) return
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      const chunks: Blob[] = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data)
        }
      }
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' })
        await transcribeAudio(audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }
      
      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTimer(0)
      
      // Start timer
      recordingIntervalRef.current = setInterval(() => {
        setRecordingTimer(prev => prev + 1)
      }, 1000)
      
      // Store recorder reference
      recordingRef.current = mediaRecorder
      
      toast.success('Recording... Click again to stop')
      
      // Auto-stop after 30 seconds
      setTimeout(() => {
        if (recordingRef.current) {
          stopVoiceRecording()
        }
      }, 30000)
      
    } catch (error) {
      console.error('Failed to start recording:', error)
      toast.error('Microphone access denied')
    }
  }
  
  const stopVoiceRecording = () => {
    if (!isRecording) return
    
    const recorder = recordingRef.current
    if (recorder && recorder.state !== 'inactive') {
      recorder.stop()
    }
    
    setIsRecording(false)
    setRecordingTimer(0)
    
    if (recordingIntervalRef.current) {
      clearInterval(recordingIntervalRef.current)
      recordingIntervalRef.current = null
    }
    
    recordingRef.current = null
    toast.success('Processing voice input...')
  }
  
  const transcribeAudio = async (audioBlob: Blob) => {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')
    formData.append('language', 'en')
    
    try {
      const response = await axios.post(`${API_URL}/api/voice/transcribe`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      if (response.data.text) {
        setInputText(response.data.text)
        toast.success('Voice transcribed successfully!')
      }
    } catch (error) {
      console.error('Transcription failed:', error)
      toast.error('Voice transcription failed')
    }
  }
  
  // Start typing
  const handleStart = async () => {
    if (isTyping) return
    
    let textToType = inputText.trim()
    
    if (!textToType) {
      try {
        const clipboardText = await navigator.clipboard.readText()
        if (clipboardText && clipboardText.trim()) {
          textToType = clipboardText.trim()
          setInputText(textToType)
          setIsFromClipboard(true)
          toast.success('Using text from clipboard!')
        } else {
          toast.error('No text to type')
          return
        }
      } catch (err) {
        toast.error('Please enter text or copy text to clipboard first')
        return
      }
    }
    
    setStatus('Starting...')
    setProgress(0)
    
    try {
      const response = await axios.post(`${API_URL}/api/typing/start`, {
        text: textToType,
        profile: selectedProfile === 'Custom' ? 'Custom' : selectedProfile,
        custom_wpm: selectedProfile === 'Custom' ? customWpm : null,
        user_id: user?.email || 'anonymous',
        delayed_typo_correction: settings.delayedTypoCorrection,
        typo_correction_delay: settings.typoCorrectionDelay,
        is_from_clipboard: isFromClipboard,
        paste_mode: settings.pasteMode,
        auto_clear_after_clipboard: settings.autoClearAfterClipboard
      })
      
      setSessionId(response.data.session_id)
      setIsTyping(true)
      setCountdown(3)
    } catch (error: any) {
      console.error('Failed to start typing:', error)
      toast.error(error.response?.data?.detail || 'Failed to start typing')
      setStatus('Error')
    }
  }
  
  const handleStop = async () => {
    if (!sessionId) return
    
    try {
      await axios.post(`${API_URL}/api/typing/stop`, { session_id: sessionId })
      setIsTyping(false)
      setIsPaused(false)
      setStatus('Stopped')
      setProgress(0)
      toast.success('Typing stopped')
    } catch (error) {
      console.error('Failed to stop typing:', error)
    }
  }
  
  const handlePause = async () => {
    if (!sessionId || !isTyping) return
    
    try {
      if (isPaused) {
        await axios.post(`${API_URL}/api/typing/resume`, { session_id: sessionId })
        setIsPaused(false)
        toast.success('Typing resumed')
      } else {
        await axios.post(`${API_URL}/api/typing/pause`, { session_id: sessionId })
        setIsPaused(true)
        toast.success('Typing paused')
      }
    } catch (error) {
      console.error('Failed to pause/resume:', error)
    }
  }
  
  // Dynamic hotkey display - fixed for SSR
  const [userHotkeys, setUserHotkeys] = useState<Record<string, string>>({
    start: 'Ctrl+Shift+S',
    stop: 'Ctrl+Shift+X',
    pause: 'Ctrl+Shift+P',
    voice: 'Ctrl+Shift+V'
  })
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const hotkeys = localStorage.getItem('slywriter-hotkeys')
      if (hotkeys) {
        try {
          setUserHotkeys(JSON.parse(hotkeys))
        } catch {
          // Keep defaults
        }
      }
    }
  }, [])
  
  const getUserHotkey = (action: string): string => {
    return userHotkeys[action] || 'Not set'
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <KeyboardIcon className="text-purple-400" size={28} />
            <h2 className="text-2xl font-bold text-white">Advanced Typing Assistant</h2>
            {isPremium && (
              <span className="px-3 py-1 bg-gradient-to-r from-yellow-500 to-amber-500 rounded-full text-xs font-semibold text-black">
                PREMIUM
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            {/* Voice Input Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => isRecording ? stopVoiceRecording() : startVoiceRecording()}
              className={`px-4 py-2 rounded-lg font-semibold transition-all flex items-center gap-2 ${
                isRecording 
                  ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse' 
                  : settings.voiceInputEnabled 
                    ? 'bg-purple-600 hover:bg-purple-700 text-white' 
                    : 'bg-gray-800 text-gray-500 cursor-not-allowed'
              }`}
              disabled={!settings.voiceInputEnabled}
            >
              {isRecording ? (
                <>
                  <CircleIcon size={18} className="animate-pulse fill-current" />
                  Recording {recordingTimer}s
                </>
              ) : (
                <>
                  <MicIcon size={18} />
                  Voice Input
                </>
              )}
            </motion.button>
            
            {/* Paste Mode Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handlePasteMode}
              disabled={!settings.pasteMode || isTyping || isPasteModeActive}
              className={`px-4 py-2 rounded-lg font-semibold transition-all flex items-center gap-2 ${
                isPasteModeActive
                  ? 'bg-yellow-500 text-black animate-pulse'
                  : settings.pasteMode 
                    ? 'bg-green-600 hover:bg-green-700 text-white' 
                    : 'bg-gray-800 text-gray-500 cursor-not-allowed'
              }`}
            >
              <ClipboardIcon size={18} />
              {isPasteModeActive ? `Pasting in ${pasteCountdown}...` : 'Paste Mode'}
            </motion.button>
            
            {/* Settings Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setSettings({...settings, showAdvanced: !settings.showAdvanced})}
              className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <SettingsIcon className="text-gray-400" size={20} />
            </motion.button>
          </div>
        </div>
        
        {/* Status Bar */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-4">
            <span className={`px-3 py-1 rounded-full ${
              connected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
            }`}>
              {connected ? 'Connected' : 'Disconnected'}
            </span>
            <span className="text-gray-400">Status: {status}</span>
            {isTyping && <span className="text-purple-400">WPM: {wpm}</span>}
          </div>
          
          <div className="text-gray-400">
            Profile: {selectedProfile}
            {selectedProfile === 'Custom' && customWpm && (
              <span className="text-purple-400 ml-2">{customWpm} WPM</span>
            )}
          </div>
        </div>
      </div>
      
      {/* Settings Panel */}
      <AnimatePresence>
        {settings.showAdvanced && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Advanced Settings</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Paste Mode Settings */}
              <div className="space-y-4">
                <h4 className="text-purple-400 font-semibold">Paste Mode</h4>
                
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={settings.pasteMode}
                    onChange={(e) => setSettings({...settings, pasteMode: e.target.checked})}
                    className="w-4 h-4 text-purple-600 rounded"
                  />
                  <span className="text-white">Enable Paste Mode</span>
                </label>
                
                {settings.pasteMode && (
                  <div className="ml-7">
                    <label className="text-sm text-gray-400">
                      Timer (seconds):
                      <input
                        type="number"
                        min="1"
                        max="10"
                        value={settings.pasteModeTimer}
                        onChange={(e) => setSettings({...settings, pasteModeTimer: parseInt(e.target.value) || 5})}
                        className="ml-2 w-16 px-2 py-1 bg-gray-800 rounded text-white"
                      />
                    </label>
                  </div>
                )}
                
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={settings.autoClearAfterClipboard}
                    onChange={(e) => setSettings({...settings, autoClearAfterClipboard: e.target.checked})}
                    className="w-4 h-4 text-purple-600 rounded"
                  />
                  <span className="text-white">Auto-clear after clipboard</span>
                </label>
              </div>
              
              {/* Voice & Typo Settings */}
              <div className="space-y-4">
                <h4 className="text-purple-400 font-semibold">Voice & Typos</h4>
                
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={settings.voiceInputEnabled}
                    onChange={(e) => setSettings({...settings, voiceInputEnabled: e.target.checked})}
                    className="w-4 h-4 text-purple-600 rounded"
                  />
                  <span className="text-white">Enable Voice Input</span>
                </label>
                
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={settings.delayedTypoCorrection}
                    onChange={(e) => setSettings({...settings, delayedTypoCorrection: e.target.checked})}
                    className="w-4 h-4 text-purple-600 rounded"
                  />
                  <span className="text-white">Grammarly-style typo correction</span>
                </label>
                
                {settings.delayedTypoCorrection && (
                  <div className="ml-7">
                    <label className="text-sm text-gray-400">
                      Correction delay:
                      <input
                        type="number"
                        min="1"
                        max="10"
                        value={settings.typoCorrectionDelay}
                        onChange={(e) => setSettings({...settings, typoCorrectionDelay: parseInt(e.target.value) || 3})}
                        className="ml-2 w-16 px-2 py-1 bg-gray-800 rounded text-white"
                      />
                      s
                    </label>
                  </div>
                )}
              </div>
            </div>
            
            <div className="mt-4 p-3 bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-400">
                <strong>Hotkeys:</strong> {getUserHotkey('start')} to start • {getUserHotkey('stop')} to stop • {getUserHotkey('pause')} to pause • {getUserHotkey('voice')} for voice
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Main Input Area */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-lg font-semibold text-white">Input Text</label>
            <div className="flex gap-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigator.clipboard.writeText(inputText)}
                className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <CopyIcon size={18} className="text-gray-400" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setInputText('')}
                className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <TrashIcon size={18} className="text-gray-400" />
              </motion.button>
            </div>
          </div>
          
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type, paste, or record your text here..."
            className="w-full h-[200px] bg-gray-800 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50"
            disabled={isTyping}
          />
          
          {/* Profile Selection */}
          <div className="flex items-center gap-4">
            <label className="text-gray-400">Speed:</label>
            <div className="flex gap-2">
              {['Slow', 'Medium', 'Fast', 'Custom'].map((profile) => (
                <button
                  key={profile}
                  onClick={() => {
                    setSelectedProfile(profile)
                    if (profile === 'Custom') setShowCustomWpm(true)
                  }}
                  className={`px-3 py-1 rounded-lg transition-colors ${
                    selectedProfile === profile
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  {profile}
                </button>
              ))}
            </div>
            
            {selectedProfile === 'Custom' && (
              <input
                type="number"
                min="30"
                max="200"
                value={customWpm || ''}
                onChange={(e) => setCustomWpm(parseInt(e.target.value) || null)}
                placeholder="WPM"
                className="w-20 px-2 py-1 bg-gray-800 rounded text-white"
              />
            )}
          </div>
          
          {/* Progress Bar */}
          {isTyping && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-400">
                <span>Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  className="bg-gradient-to-r from-purple-500 to-blue-500 h-full rounded-full"
                />
              </div>
            </div>
          )}
          
          {/* Countdown Display */}
          {countdown !== null && (
            <div className="text-center">
              <motion.div
                key={countdown}
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 1.5, opacity: 0 }}
                className="text-6xl font-bold text-purple-400"
              >
                {countdown}
              </motion.div>
            </div>
          )}
          
          {/* Control Buttons */}
          <div className="flex gap-4 justify-center">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleStart}
              disabled={isTyping || !connected}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-700 disabled:to-gray-800 rounded-lg font-semibold text-white transition-all flex items-center gap-2"
            >
              <PlayIcon size={20} />
              Start
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handlePause}
              disabled={!isTyping}
              className="px-6 py-3 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-700 rounded-lg font-semibold text-white transition-all flex items-center gap-2"
            >
              <PauseIcon size={20} />
              {isPaused ? 'Resume' : 'Pause'}
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleStop}
              disabled={!isTyping}
              className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 rounded-lg font-semibold text-white transition-all flex items-center gap-2"
            >
              <StopCircleIcon size={20} />
              Stop
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  )
}