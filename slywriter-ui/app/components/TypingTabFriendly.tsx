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

interface Profile {
  name: string
  is_builtin: boolean
  settings: {
    min_delay: number
    max_delay: number
    typos_enabled: boolean
    typo_chance: number
    pause_frequency: number
  }
}

interface TypingTabProps {
  connected: boolean
  initialProfile?: string
  shouldOpenWpmTest?: boolean
  onWpmTestOpened?: () => void
}

export default function TypingTabFriendly({ connected, initialProfile, shouldOpenWpmTest, onWpmTestOpened }: TypingTabProps) {
  const { user, isPremium, canType, wordsRemaining } = useAuth()
  
  // Core state
  const [inputText, setInputText] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isTyping, setIsTyping] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [status, setStatus] = useState('Ready')
  const [progress, setProgress] = useState(0)
  const [wpm, setWpm] = useState(0)
  const [accuracy, setAccuracy] = useState(100)
  const [charsTyped, setCharsTyped] = useState(0)
  const [totalChars, setTotalChars] = useState(0)
  const [countdown, setCountdown] = useState<number | null>(null)
  const [previewMode, setPreviewMode] = useState(false)
  const [isFromClipboard, setIsFromClipboard] = useState(false)
  
  // Profile state
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [selectedProfile, setSelectedProfile] = useState(initialProfile || 'Medium')
  const [loadingProfiles, setLoadingProfiles] = useState(true)
  const [customWpm, setCustomWpm] = useState<number | null>(null)
  const [showCustomWpm, setShowCustomWpm] = useState(false)
  
  // Enhanced features state (hidden by default)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [settings, setSettings] = useState({
    pasteMode: false,
    pasteModeTimer: 5,
    autoClearAfterClipboard: true,
    delayedTypoCorrection: false,
    typoCorrectionDelay: 3,
    voiceInputEnabled: false
  })
  
  // Paste Mode state
  const [isPasteModeActive, setIsPasteModeActive] = useState(false)
  const [pasteCountdown, setPasteCountdown] = useState<number | null>(null)
  
  // Voice Input state
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTimer, setRecordingTimer] = useState(0)
  
  // UI state
  const [showStats, setShowStats] = useState(false)
  const [copied, setCopied] = useState(false)
  
  // WPM Test state
  const [showWpmTest, setShowWpmTest] = useState(false)
  const [testText] = useState('The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.')
  const [testInput, setTestInput] = useState('')
  const [testStartTime, setTestStartTime] = useState<number | null>(null)
  const [testWpm, setTestWpm] = useState<number | null>(null)
  const [isTestActive, setIsTestActive] = useState(false)
  
  const wsRef = useRef<WebSocket | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
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
      
      const savedProfile = localStorage.getItem('slywriter-selected-profile')
      if (savedProfile) {
        setSelectedProfile(savedProfile)
      }
      
      const savedWpm = localStorage.getItem('slywriter-custom-wpm')
      if (savedWpm) {
        setCustomWpm(parseInt(savedWpm))
      }
    }
  }, [])
  
  // Save settings
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('slywriter-typing-settings', JSON.stringify(settings))
    }
  }, [settings])
  
  // Save profile selection
  useEffect(() => {
    if (typeof window !== 'undefined' && selectedProfile) {
      localStorage.setItem('slywriter-selected-profile', selectedProfile)
    }
  }, [selectedProfile])
  
  // Save custom WPM
  useEffect(() => {
    if (typeof window !== 'undefined' && customWpm) {
      localStorage.setItem('slywriter-custom-wpm', customWpm.toString())
    }
  }, [customWpm])
  
  // Load profiles
  const loadProfiles = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/profiles`)
      setProfiles(response.data.profiles || [])
    } catch (error) {
      console.error('Failed to load profiles:', error)
    } finally {
      setLoadingProfiles(false)
    }
  }
  
  useEffect(() => {
    loadProfiles()
    
    if (shouldOpenWpmTest) {
      setShowWpmTest(true)
      onWpmTestOpened?.()
    }
  }, [shouldOpenWpmTest])
  
  // WebSocket connection
  useEffect(() => {
    if (!connected) return
    
    const userId = user?.email || 'anonymous'
    const ws = new WebSocket(`ws://localhost:8000/ws/${userId}`)
    
    ws.onopen = () => {
      console.log('WebSocket connected')
      setStatus('Connected')
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      switch(data.type) {
        case 'typing_progress':
          setProgress(data.progress || 0)
          setWpm(data.wpm || 0)
          setAccuracy(data.accuracy || 100)
          setCharsTyped(data.chars_typed || 0)
          setTotalChars(data.total_chars || 0)
          break
          
        case 'typing_complete':
          handleTypingComplete()
          break
          
        case 'countdown':
          setCountdown(data.count)
          if (data.count === 0) {
            setCountdown(null)
            setStatus('Typing in progress...')
          }
          break
          
        case 'typing_started':
          setIsTyping(true)
          setStatus('Typing in progress...')
          break
          
        case 'error':
          toast.error(data.message || 'An error occurred')
          setIsTyping(false)
          setStatus('Error')
          break
      }
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setStatus('Disconnected')
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
    toast.success('✨ Typing complete!')
    
    // Auto-clear if from clipboard and setting is enabled
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
    if (!canType) {
      toast.error('Daily word limit reached. Upgrade to Premium for unlimited typing!')
      return
    }
    
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
        toast.success('📋 Text pasted from clipboard!')
        
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
      
      toast.success('🎤 Recording... Click again to stop')
      
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
        toast.success('✅ Voice transcribed successfully!')
      }
    } catch (error) {
      console.error('Transcription failed:', error)
      toast.error('Voice transcription failed')
    }
  }
  
  // Main handlers
  const handleStart = async () => {
    if (!canType) {
      toast.error('Daily word limit reached. Upgrade to Premium for unlimited typing!')
      return
    }
    
    if (isTyping) return
    
    let textToType = inputText.trim()
    
    // If no text, try clipboard
    if (!textToType) {
      try {
        const clipboardText = await navigator.clipboard.readText()
        if (clipboardText && clipboardText.trim()) {
          textToType = clipboardText.trim()
          setInputText(textToType)
          setIsFromClipboard(true)
          toast.success('📋 Using text from clipboard!')
        } else {
          toast.error('No text in input box or clipboard. Please enter or copy some text.')
          return
        }
      } catch (err) {
        toast.error('Please enter text or copy text to clipboard first')
        return
      }
    }
    
    setStatus('Starting...')
    setProgress(0)
    setCharsTyped(0)
    setTotalChars(textToType.length)
    
    try {
      const response = await axios.post(`${API_URL}/api/typing/start`, {
        text: textToType,
        profile: selectedProfile === 'Custom' ? 'Custom' : selectedProfile,
        custom_wpm: selectedProfile === 'Custom' ? customWpm : null,
        preview_mode: previewMode,
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
  
  const copyToClipboard = () => {
    navigator.clipboard.writeText(inputText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    toast.success('Copied to clipboard')
  }
  
  const loadFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setInputText(e.target?.result as string)
        toast.success('File loaded')
      }
      reader.readAsText(file)
    }
  }
  
  // WPM Test handlers
  const startWpmTest = () => {
    setTestInput('')
    setTestStartTime(Date.now())
    setTestWpm(null)
    setIsTestActive(true)
  }
  
  const handleTestInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const input = e.target.value
    setTestInput(input)
    
    if (!testStartTime || !isTestActive) return
    
    const words = input.trim().split(/\s+/).length
    const minutes = (Date.now() - testStartTime) / 60000
    const currentWpm = Math.round(words / minutes)
    setTestWpm(currentWpm)
    
    if (input.length >= testText.length) {
      setIsTestActive(false)
      toast.success(`Test complete! Your typing speed: ${currentWpm} WPM`)
    }
  }
  
  // Dynamic hotkey display - fixed for SSR
  const [userHotkeys, setUserHotkeys] = useState<Record<string, string>>({
    start: 'Ctrl+Shift+S',
    stop: 'Ctrl+Shift+X',
    pause: 'Ctrl+Shift+P'
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
  
  // Hotkey bindings
  useHotkeys('ctrl+enter', () => handleStart(), { enabled: !isTyping })
  
  return (
    <div className="space-y-6">
      {/* Header - Clean and Simple */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <KeyboardIcon className="text-purple-400" size={28} />
            Typing Assistant
          </h2>
          
          {/* Advanced Features Toggle */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="px-4 py-2 bg-purple-600/20 hover:bg-purple-600/30 rounded-lg text-purple-400 font-semibold transition-all flex items-center gap-2"
          >
            <SettingsIcon size={18} />
            Advanced Features
          </motion.button>
        </div>
        
        {/* Status Bar */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-4">
            <span className={`px-3 py-1 rounded-full ${
              connected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
            }`}>
              {connected ? '● Connected' : '● Disconnected'}
            </span>
            <span className="text-gray-400">Status: {status}</span>
          </div>
          
          <div className="flex items-center gap-4 text-gray-400">
            {canType ? (
              <span>{wordsRemaining?.toLocaleString() || '∞'} words remaining</span>
            ) : (
              <span className="text-red-400">Daily limit reached</span>
            )}
          </div>
        </div>
      </div>
      
      {/* Advanced Features Panel - Hidden by Default */}
      <AnimatePresence>
        {showAdvanced && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Voice Input */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => isRecording ? stopVoiceRecording() : startVoiceRecording()}
                disabled={!settings.voiceInputEnabled}
                className={`p-4 rounded-lg transition-all flex flex-col items-center gap-2 ${
                  isRecording 
                    ? 'bg-red-500 text-white animate-pulse' 
                    : settings.voiceInputEnabled
                      ? 'bg-purple-600/20 hover:bg-purple-600/30 text-purple-400'
                      : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                }`}
              >
                <MicIcon size={24} />
                <span className="font-semibold">
                  {isRecording ? `Recording ${recordingTimer}s` : 'Voice Input'}
                </span>
              </motion.button>
              
              {/* Paste Mode */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handlePasteMode}
                disabled={!settings.pasteMode || isTyping || isPasteModeActive}
                className={`p-4 rounded-lg transition-all flex flex-col items-center gap-2 ${
                  isPasteModeActive
                    ? 'bg-yellow-500 text-black animate-pulse'
                    : settings.pasteMode
                      ? 'bg-green-600/20 hover:bg-green-600/30 text-green-400'
                      : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                }`}
              >
                <ClipboardIcon size={24} />
                <span className="font-semibold">
                  {isPasteModeActive ? `Pasting in ${pasteCountdown}...` : 'Paste Mode'}
                </span>
              </motion.button>
              
              {/* WPM Test */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowWpmTest(!showWpmTest)}
                className="p-4 bg-blue-600/20 hover:bg-blue-600/30 rounded-lg text-blue-400 transition-all flex flex-col items-center gap-2"
              >
                <GaugeIcon size={24} />
                <span className="font-semibold">WPM Test</span>
              </motion.button>
            </div>
            
            {/* Settings */}
            <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.voiceInputEnabled}
                  onChange={(e) => setSettings({...settings, voiceInputEnabled: e.target.checked})}
                  className="w-4 h-4 text-purple-600 rounded"
                />
                <span className="text-sm text-gray-300">Voice Input</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.pasteMode}
                  onChange={(e) => setSettings({...settings, pasteMode: e.target.checked})}
                  className="w-4 h-4 text-purple-600 rounded"
                />
                <span className="text-sm text-gray-300">Paste Mode</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.autoClearAfterClipboard}
                  onChange={(e) => setSettings({...settings, autoClearAfterClipboard: e.target.checked})}
                  className="w-4 h-4 text-purple-600 rounded"
                />
                <span className="text-sm text-gray-300">Auto-clear</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.delayedTypoCorrection}
                  onChange={(e) => setSettings({...settings, delayedTypoCorrection: e.target.checked})}
                  className="w-4 h-4 text-purple-600 rounded"
                />
                <span className="text-sm text-gray-300">Grammarly Mode</span>
              </label>
            </div>
            
            <div className="mt-4 p-3 bg-gray-800 rounded-lg">
              <p className="text-xs text-gray-400">
                <strong>Hotkeys:</strong> {getUserHotkey('start')} to start • {getUserHotkey('stop')} to stop • {getUserHotkey('pause')} to pause
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Main Input Area */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
        <div className="space-y-4">
          {/* Text Input */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-lg font-semibold text-white">Your Text</label>
              <div className="flex gap-2">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={copyToClipboard}
                  className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  {copied ? <CheckIcon size={18} className="text-green-400" /> : <CopyIcon size={18} className="text-gray-400" />}
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <UploadIcon size={18} className="text-gray-400" />
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
              placeholder="Paste or type your text here... Or just copy text and press Start - SlyWriter will use your clipboard!"
              className="w-full h-[200px] bg-gray-800 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
              disabled={isTyping}
            />
            
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt"
              onChange={loadFile}
              className="hidden"
            />
          </div>
          
          {/* Speed Selection */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-gray-400">Speed:</span>
              <div className="flex gap-2">
                {['Slow', 'Medium', 'Fast', 'Custom'].map((profile) => (
                  <button
                    key={profile}
                    onClick={() => {
                      setSelectedProfile(profile)
                      if (profile === 'Custom') setShowCustomWpm(true)
                    }}
                    className={`px-4 py-2 rounded-lg transition-all font-semibold ${
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
                  className="w-20 px-3 py-2 bg-gray-800 rounded-lg text-white"
                />
              )}
            </div>
            
            <div className="text-sm text-gray-400">
              Press {getUserHotkey('start')} or click Start
            </div>
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
              {wpm > 0 && (
                <div className="text-center text-sm text-purple-400">
                  Current speed: {wpm} WPM
                </div>
              )}
            </div>
          )}
          
          {/* Countdown */}
          <AnimatePresence>
            {countdown !== null && (
              <motion.div
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 1.5, opacity: 0 }}
                className="text-center"
              >
                <div className="text-6xl font-bold text-purple-400">
                  {countdown}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Control Buttons */}
          <div className="flex gap-4 justify-center pt-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleStart}
              disabled={isTyping || !connected}
              className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-700 disabled:to-gray-800 rounded-lg font-semibold text-white transition-all flex items-center gap-2 shadow-lg"
            >
              <PlayIcon size={20} />
              Start Typing
            </motion.button>
            
            {isTyping && (
              <>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handlePause}
                  className="px-6 py-3 bg-yellow-600 hover:bg-yellow-700 rounded-lg font-semibold text-white transition-all flex items-center gap-2"
                >
                  <PauseIcon size={20} />
                  {isPaused ? 'Resume' : 'Pause'}
                </motion.button>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleStop}
                  className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-semibold text-white transition-all flex items-center gap-2"
                >
                  <StopCircleIcon size={20} />
                  Stop
                </motion.button>
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* WPM Test Modal */}
      <AnimatePresence>
        {showWpmTest && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowWpmTest(false)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-gray-900 rounded-xl p-6 max-w-2xl w-full mx-4 border border-purple-500/20"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-xl font-bold text-white mb-4">WPM Speed Test</h3>
              <p className="text-gray-400 mb-4">Type the following text as fast as you can:</p>
              <div className="bg-gray-800 rounded-lg p-4 mb-4">
                <p className="text-white">{testText}</p>
              </div>
              <textarea
                value={testInput}
                onChange={handleTestInput}
                placeholder="Start typing here..."
                className="w-full h-32 bg-gray-800 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                disabled={!isTestActive}
              />
              <div className="flex items-center justify-between mt-4">
                <div className="text-gray-400">
                  {testWpm !== null && <span>Current speed: {testWpm} WPM</span>}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={startWpmTest}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold text-white"
                  >
                    Start Test
                  </button>
                  <button
                    onClick={() => setShowWpmTest(false)}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold text-white"
                  >
                    Close
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}