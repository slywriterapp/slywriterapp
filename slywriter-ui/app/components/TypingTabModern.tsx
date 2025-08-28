'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import toast from 'react-hot-toast'
import { 
  KeyboardIcon, PlayIcon, StopCircleIcon, PauseIcon, 
  SettingsIcon, MicIcon, ClipboardIcon, ZapIcon,
  CheckIcon, XIcon, SparklesIcon, GaugeIcon,
  TrendingUpIcon, AlertCircleIcon, RefreshCwIcon,
  Volume2Icon, VolumeXIcon, TimerIcon, TypeIcon,
  ActivityIcon, BrainIcon
} from 'lucide-react'
// WPM Test Modal inline below

const API_URL = 'http://localhost:8000'

// WPM to delay conversion
const wpmToDelay = (wpm: number): number => {
  const baseCharsPerWord = 5
  const charsPerMinute = wpm * baseCharsPerWord
  const charsPerSecond = charsPerMinute / 60
  const delayPerChar = 1 / charsPerSecond
  return Math.max(0.01, Math.min(delayPerChar, 1.0))
}

interface TypingTabModernProps {
  connected?: boolean
  initialProfile?: string
  shouldOpenWpmTest?: boolean
  onWpmTestOpened?: () => void
}

export default function TypingTabModern({ 
  connected = false, 
  initialProfile = 'Medium',
  shouldOpenWpmTest = false,
  onWpmTestOpened
}: TypingTabModernProps) {
  // Core states
  const [text, setText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [progress, setProgress] = useState(0)
  const [charsTyped, setCharsTyped] = useState(0)
  const [totalChars, setTotalChars] = useState(0)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [startCountdown, setStartCountdown] = useState<number | null>(null)
  
  // Real-time stats
  const [currentWPM, setCurrentWPM] = useState(0)
  const [averageWPM, setAverageWPM] = useState(0)
  const [timeElapsed, setTimeElapsed] = useState(0)
  const [estimatedTimeLeft, setEstimatedTimeLeft] = useState(0)
  
  // Settings
  const [wpm, setWpm] = useState(60)
  const [typoRate, setTypoRate] = useState(2)
  const [pauseChance, setPauseChance] = useState(5)
  const [humanMode, setHumanMode] = useState(true)
  const [pasteMode, setPasteMode] = useState(false)
  const [autoClearClipboard, setAutoClearClipboard] = useState(true)
  const [grammarlyCorrectionEnabled, setGrammarlyCorrectionEnabled] = useState(false)
  const [grammarlyCorrectionDelay, setGrammarlyCorrectionDelay] = useState(2)
  
  // UI states
  const [showSettings, setShowSettings] = useState(false)
  const [showWPMTest, setShowWPMTest] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [countdown, setCountdown] = useState<number | null>(null)
  
  // Hotkeys
  const [userHotkeys, setUserHotkeys] = useState<Record<string, string>>({
    start: 'Ctrl+Shift+S',
    stop: 'Ctrl+Shift+X',
    pause: 'Ctrl+Shift+P',
    voice: 'Ctrl+Shift+V'
  })
  
  // Refs
  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const typingStartTimeRef = useRef<Date | null>(null)
  
  // Load hotkeys from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedHotkeys = localStorage.getItem('slywriter-hotkeys')
      if (savedHotkeys) {
        try {
          setUserHotkeys(JSON.parse(savedHotkeys))
        } catch (e) {
          console.error('Failed to load hotkeys:', e)
        }
      }
    }
  }, [])
  
  // WebSocket connection
  useEffect(() => {
    if (!connected) return
    
    const connectWebSocket = () => {
      const ws = new WebSocket(`ws://localhost:8000/ws/typing`)
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        wsRef.current = ws
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'typing_update') {
            setProgress(data.progress || 0)
            setCharsTyped(data.chars_typed || 0)
            setTotalChars(data.total_chars || 0)
            setIsTyping(data.status === 'typing')
            setIsPaused(data.status === 'paused')
            
            // Calculate real-time WPM
            if (data.chars_typed > 0 && typingStartTimeRef.current) {
              const elapsed = (Date.now() - typingStartTimeRef.current.getTime()) / 1000 / 60 // minutes
              const wordsTyped = data.chars_typed / 5
              const realTimeWPM = Math.round(wordsTyped / Math.max(elapsed, 0.01))
              setCurrentWPM(realTimeWPM)
              
              // Update average WPM
              setAverageWPM(prev => {
                if (prev === 0) return realTimeWPM
                return Math.round((prev * 0.9) + (realTimeWPM * 0.1)) // Weighted average
              })
              
              // Update time stats
              setTimeElapsed(Math.floor(elapsed * 60)) // seconds
              const remainingChars = data.total_chars - data.chars_typed
              const remainingTime = (remainingChars / 5) / wpm * 60 // seconds
              setEstimatedTimeLeft(Math.floor(remainingTime))
            }
            
            if (data.status === 'completed') {
              toast.success('Typing completed!')
              handleStop()
            }
          }
        } catch (error) {
          console.error('WebSocket message error:', error)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      
      ws.onclose = () => {
        console.log('WebSocket disconnected')
        wsRef.current = null
      }
      
      return ws
    }
    
    const ws = connectWebSocket()
    
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [connected, wpm])
  
  // Handle WPM test modal
  useEffect(() => {
    if (shouldOpenWpmTest) {
      setShowWPMTest(true)
      onWpmTestOpened?.()
    }
  }, [shouldOpenWpmTest, onWpmTestOpened])
  
  // Start typing
  const handleStart = async () => {
    if (!text.trim()) {
      toast.error('Please enter some text to type')
      return
    }
    
    // Show countdown
    setStartCountdown(5)
    
    const countdownInterval = setInterval(() => {
      setStartCountdown(prev => {
        if (prev === null || prev <= 1) {
          clearInterval(countdownInterval)
          return null
        }
        return prev - 1
      })
    }, 1000)
    
    // Wait for countdown
    setTimeout(async () => {
      try {
        typingStartTimeRef.current = new Date()
        setCurrentWPM(0)
        setAverageWPM(0)
        setTimeElapsed(0)
        setTotalChars(text.trim().length)
        
        const response = await axios.post(`${API_URL}/api/typing/start`, {
          text: text.trim(),
          profile: 'Custom',
          custom_wpm: wpm,
          preview_mode: false,
          session_id: sessionId,
          user_id: 'anonymous',
          delayed_typo_correction: grammarlyCorrectionEnabled,
          typo_correction_delay: grammarlyCorrectionDelay,
          is_from_clipboard: false,
          paste_mode: pasteMode,
          auto_clear_after_clipboard: autoClearClipboard
        })
        
        if (response.data.status === 'started') {
          setSessionId(response.data.session_id)
          setIsTyping(true)
          setIsPaused(false)
        }
      } catch (error: any) {
        toast.error(error.response?.data?.detail || 'Failed to start typing')
        setIsTyping(false)
      }
    }, 5000)
  }
  
  // Stop typing
  const handleStop = async () => {
    try {
      if (sessionId) {
        await axios.post(`${API_URL}/api/typing/stop`, {
          session_id: sessionId
        })
      }
      setIsTyping(false)
      setIsPaused(false)
      setProgress(0)
      setCharsTyped(0)
      setCurrentWPM(0)
      setSessionId(null)
      typingStartTimeRef.current = null
    } catch (error: any) {
      // Still stop on frontend even if backend fails
      setIsTyping(false)
      setIsPaused(false)
      setProgress(0)
      setCharsTyped(0)
      setCurrentWPM(0)
      setSessionId(null)
    }
  }
  
  // Pause/Resume typing
  const handlePauseResume = async () => {
    try {
      if (!sessionId) return
      
      const endpoint = isPaused ? 'resume' : 'pause'
      await axios.post(`${API_URL}/api/typing/${endpoint}`, {
        session_id: sessionId
      })
      setIsPaused(!isPaused)
    } catch (error: any) {
      console.error(`Failed to ${isPaused ? 'resume' : 'pause'}:`, error)
    }
  }
  
  // Handle paste mode
  const handlePasteMode = async () => {
    try {
      const clipboardText = await navigator.clipboard.readText()
      
      if (!clipboardText.trim()) {
        toast.error('Clipboard is empty')
        return
      }
      
      // Set countdown
      setCountdown(5)
      setPasteMode(true)
      
      const countdownInterval = setInterval(() => {
        setCountdown(prev => {
          if (prev === null || prev <= 1) {
            clearInterval(countdownInterval)
            return null
          }
          return prev - 1
        })
      }, 1000)
      
      // Start typing after countdown
      setTimeout(async () => {
        setText(clipboardText)
        
        // Auto clear clipboard if enabled
        if (autoClearClipboard) {
          await navigator.clipboard.writeText('')
          toast.success('Clipboard cleared')
        }
        
        // Start typing
        handleStart()
        setPasteMode(false)
      }, 5000)
      
    } catch (error) {
      toast.error('Failed to read clipboard')
      setPasteMode(false)
      setCountdown(null)
    }
  }
  
  // Voice recording
  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        const formData = new FormData()
        formData.append('audio', audioBlob, 'recording.webm')
        
        try {
          const response = await axios.post(`${API_URL}/api/voice/transcribe`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })
          
          if (response.data.text) {
            setText(prev => prev + ' ' + response.data.text)
            toast.success('Voice transcribed!')
          }
        } catch (error) {
          toast.error('Failed to transcribe voice')
        }
        
        stream.getTracks().forEach(track => track.stop())
      }
      
      mediaRecorder.start()
      setIsRecording(true)
      toast.success('Recording started...')
      
    } catch (error) {
      toast.error('Failed to access microphone')
    }
  }
  
  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      toast.success('Processing voice...')
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Header with Live Stats */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-purple-900/50 to-blue-900/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-500/20 rounded-xl">
              <KeyboardIcon className="w-8 h-8 text-purple-400" />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-white">Auto-Type</h2>
              <p className="text-gray-400">AI-powered typing automation</p>
            </div>
          </div>
          
          {/* Connection Status */}
          <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
            connected ? 'bg-green-500/20' : 'bg-red-500/20'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              connected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
            }`} />
            <span className={`text-sm font-medium ${
              connected ? 'text-green-400' : 'text-red-400'
            }`}>
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
        
        {/* Live Stats Display */}
        {isTyping && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="grid grid-cols-4 gap-4 mt-4"
          >
            {/* Current WPM */}
            <div className="bg-gray-900/50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <GaugeIcon className="w-4 h-4 text-purple-400" />
                <span className="text-xs text-gray-400">Current WPM</span>
              </div>
              <div className="text-3xl font-bold text-white">
                {currentWPM}
              </div>
            </div>
            
            {/* Average WPM */}
            <div className="bg-gray-900/50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUpIcon className="w-4 h-4 text-blue-400" />
                <span className="text-xs text-gray-400">Average WPM</span>
              </div>
              <div className="text-3xl font-bold text-white">
                {averageWPM}
              </div>
            </div>
            
            {/* Time Elapsed */}
            <div className="bg-gray-900/50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <TimerIcon className="w-4 h-4 text-green-400" />
                <span className="text-xs text-gray-400">Time Elapsed</span>
              </div>
              <div className="text-3xl font-bold text-white">
                {Math.floor(timeElapsed / 60)}:{(timeElapsed % 60).toString().padStart(2, '0')}
              </div>
            </div>
            
            {/* Est. Time Left */}
            <div className="bg-gray-900/50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <ActivityIcon className="w-4 h-4 text-orange-400" />
                <span className="text-xs text-gray-400">Est. Time Left</span>
              </div>
              <div className="text-3xl font-bold text-white">
                {Math.floor(estimatedTimeLeft / 60)}:{(estimatedTimeLeft % 60).toString().padStart(2, '0')}
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>
      
      {/* Main Controls */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
        {/* Text Input Area */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-300">Text to Type</label>
            <div className="flex items-center gap-2">
              {/* Voice Input */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
                className={`p-2 rounded-lg transition-colors ${
                  isRecording 
                    ? 'bg-red-500 hover:bg-red-600' 
                    : 'bg-gray-700 hover:bg-gray-600'
                }`}
                title={`Voice Input (${userHotkeys.voice})`}
              >
                <MicIcon className={`w-5 h-5 ${isRecording ? 'animate-pulse' : ''}`} />
              </motion.button>
              
              {/* Paste Mode */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handlePasteMode}
                disabled={isTyping || countdown !== null}
                className="p-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500 rounded-lg transition-colors"
                title="Paste Mode (5s delay)"
              >
                <ClipboardIcon className="w-5 h-5" />
              </motion.button>
              
              <span className="text-xs text-gray-500">
                {text.length} chars | {Math.ceil(text.split(' ').length)} words
              </span>
            </div>
          </div>
          
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter or paste your text here..."
            disabled={isTyping}
            className="w-full h-40 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed resize-none"
          />
          
          {/* Countdown Display for paste mode and start */}
          {(countdown !== null || startCountdown !== null) && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mt-4 text-center"
            >
              <div className="text-6xl font-bold text-purple-400">
                {countdown || startCountdown}
              </div>
              <p className="text-gray-400 mt-2">
                {countdown !== null ? 'Paste mode starting...' : 'Starting typing...'}
              </p>
            </motion.div>
          )}
        </div>
        
        {/* Progress Bar */}
        {(isTyping || progress > 0) && (
          <div className="mb-6">
            <div className="flex justify-between text-sm text-gray-400 mb-2">
              <span>{charsTyped} / {totalChars} characters</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full"
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        )}
        
        {/* Control Buttons */}
        <div className="flex items-center gap-3">
          {/* Start/Stop */}
          {!isTyping ? (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleStart}
              disabled={!connected || !text.trim() || countdown !== null || startCountdown !== null}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-700 disabled:to-gray-700 disabled:text-gray-500 rounded-xl font-semibold transition-all"
            >
              <PlayIcon className="w-5 h-5" />
              {startCountdown !== null ? `Starting in ${startCountdown}...` : `Start Typing (${userHotkeys.start})`}
            </motion.button>
          ) : (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleStop}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 rounded-xl font-semibold transition-colors"
            >
              <StopCircleIcon className="w-5 h-5" />
              Stop ({userHotkeys.stop})
            </motion.button>
          )}
          
          {/* Pause/Resume */}
          {isTyping && (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handlePauseResume}
              className={`flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold transition-colors ${
                isPaused 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-yellow-600 hover:bg-yellow-700'
              }`}
            >
              <PauseIcon className="w-5 h-5" />
              {isPaused ? 'Resume' : 'Pause'} ({userHotkeys.pause})
            </motion.button>
          )}
          
          {/* Settings */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowSettings(!showSettings)}
            className="p-3 bg-gray-700 hover:bg-gray-600 rounded-xl transition-colors"
          >
            <SettingsIcon className={`w-5 h-5 ${showSettings ? 'rotate-90' : ''} transition-transform`} />
          </motion.button>
          
          {/* WPM Test */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowWPMTest(true)}
            className="p-3 bg-purple-600 hover:bg-purple-700 rounded-xl transition-colors"
            title="Test Your WPM"
          >
            <ZapIcon className="w-5 h-5" />
          </motion.button>
        </div>
      </div>
      
      {/* Settings Panel */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20"
          >
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <BrainIcon className="w-6 h-6 text-purple-400" />
              Typing Settings
            </h3>
            
            <div className="grid md:grid-cols-2 gap-6">
              {/* Speed Control */}
              <div>
                <label className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
                  <span>Typing Speed (WPM)</span>
                  <span className="text-purple-400 font-mono">{wpm}</span>
                </label>
                <input
                  type="range"
                  min="20"
                  max="200"
                  value={wpm}
                  onChange={(e) => setWpm(parseInt(e.target.value))}
                  className="w-full accent-purple-500"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Slow (20)</span>
                  <span>Average (60)</span>
                  <span>Fast (120)</span>
                  <span>Pro (200)</span>
                </div>
              </div>
              
              {/* Typo Rate */}
              <div>
                <label className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
                  <span>Typo Rate</span>
                  <span className="text-purple-400 font-mono">{typoRate}%</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="10"
                  value={typoRate}
                  onChange={(e) => setTypoRate(parseInt(e.target.value))}
                  className="w-full accent-purple-500"
                />
              </div>
              
              {/* Pause Chance */}
              <div>
                <label className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
                  <span>Pause Chance</span>
                  <span className="text-purple-400 font-mono">{pauseChance}%</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="20"
                  value={pauseChance}
                  onChange={(e) => setPauseChance(parseInt(e.target.value))}
                  className="w-full accent-purple-500"
                />
              </div>
              
              {/* Grammarly Delay */}
              <div>
                <label className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
                  <span>Correction Delay</span>
                  <span className="text-purple-400 font-mono">{grammarlyCorrectionDelay}s</span>
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="5"
                  step="0.5"
                  value={grammarlyCorrectionDelay}
                  onChange={(e) => setGrammarlyCorrectionDelay(parseFloat(e.target.value))}
                  className="w-full accent-purple-500"
                  disabled={!grammarlyCorrectionEnabled}
                />
              </div>
            </div>
            
            {/* Toggle Options */}
            <div className="grid md:grid-cols-2 gap-4 mt-6">
              <label className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors">
                <input
                  type="checkbox"
                  checked={humanMode}
                  onChange={(e) => setHumanMode(e.target.checked)}
                  className="w-5 h-5 text-purple-500"
                />
                <div>
                  <span className="text-white font-medium">Human Mode</span>
                  <p className="text-xs text-gray-400">Natural typing patterns</p>
                </div>
              </label>
              
              <label className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors">
                <input
                  type="checkbox"
                  checked={grammarlyCorrectionEnabled}
                  onChange={(e) => setGrammarlyCorrectionEnabled(e.target.checked)}
                  className="w-5 h-5 text-purple-500"
                />
                <div>
                  <span className="text-white font-medium">Grammarly-Style Corrections</span>
                  <p className="text-xs text-gray-400">Delayed typo fixes</p>
                </div>
              </label>
              
              <label className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors">
                <input
                  type="checkbox"
                  checked={autoClearClipboard}
                  onChange={(e) => setAutoClearClipboard(e.target.checked)}
                  className="w-5 h-5 text-purple-500"
                />
                <div>
                  <span className="text-white font-medium">Auto-Clear Clipboard</span>
                  <p className="text-xs text-gray-400">Clear after paste mode</p>
                </div>
              </label>
              
              <label className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors opacity-50 cursor-not-allowed">
                <input
                  type="checkbox"
                  checked={pasteMode}
                  disabled
                  className="w-5 h-5 text-purple-500"
                />
                <div>
                  <span className="text-white font-medium">Paste Mode</span>
                  <p className="text-xs text-gray-400">Auto-enabled on paste</p>
                </div>
              </label>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* WPM Test Modal */}
      <AnimatePresence>
        {showWPMTest && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            onClick={() => setShowWPMTest(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-gray-900 rounded-2xl p-8 max-w-2xl w-full mx-4 border border-purple-500/20"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold text-white mb-4">WPM Speed Test</h3>
              <p className="text-gray-400 mb-6">
                Test your typing speed to find the perfect WPM setting that matches your natural typing pace.
              </p>
              
              <div className="grid grid-cols-3 gap-4 mb-6">
                <button
                  onClick={() => {
                    setWpm(40)
                    setShowWPMTest(false)
                    toast.success('WPM set to 40 (Beginner)')
                  }}
                  className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <div className="text-2xl font-bold text-purple-400 mb-1">40</div>
                  <div className="text-sm text-gray-400">Beginner</div>
                </button>
                
                <button
                  onClick={() => {
                    setWpm(60)
                    setShowWPMTest(false)
                    toast.success('WPM set to 60 (Average)')
                  }}
                  className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <div className="text-2xl font-bold text-purple-400 mb-1">60</div>
                  <div className="text-sm text-gray-400">Average</div>
                </button>
                
                <button
                  onClick={() => {
                    setWpm(80)
                    setShowWPMTest(false)
                    toast.success('WPM set to 80 (Fast)')
                  }}
                  className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <div className="text-2xl font-bold text-purple-400 mb-1">80</div>
                  <div className="text-sm text-gray-400">Fast</div>
                </button>
                
                <button
                  onClick={() => {
                    setWpm(100)
                    setShowWPMTest(false)
                    toast.success('WPM set to 100 (Professional)')
                  }}
                  className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <div className="text-2xl font-bold text-purple-400 mb-1">100</div>
                  <div className="text-sm text-gray-400">Professional</div>
                </button>
                
                <button
                  onClick={() => {
                    setWpm(120)
                    setShowWPMTest(false)
                    toast.success('WPM set to 120 (Expert)')
                  }}
                  className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <div className="text-2xl font-bold text-purple-400 mb-1">120</div>
                  <div className="text-sm text-gray-400">Expert</div>
                </button>
                
                <button
                  onClick={() => {
                    setWpm(150)
                    setShowWPMTest(false)
                    toast.success('WPM set to 150 (Pro)')
                  }}
                  className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <div className="text-2xl font-bold text-purple-400 mb-1">150</div>
                  <div className="text-sm text-gray-400">Pro</div>
                </button>
              </div>
              
              <button
                onClick={() => setShowWPMTest(false)}
                className="w-full py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold transition-colors"
              >
                Cancel
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}