'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { useHotkeys } from 'react-hotkeys-hook'
import { FirstTimeHelper, FeatureTooltip, QuickTip } from './FeatureTooltips'
import { 
  PlayIcon, PauseIcon, StopCircleIcon, SparklesIcon,
  FileTextIcon, CopyIcon, TrashIcon, CheckIcon,
  ClockIcon, TrendingUpIcon, TargetIcon, EyeIcon,
  DownloadIcon, UploadIcon, SaveIcon, RotateCcwIcon,
  ZapIcon, BrainIcon, ShieldIcon, TimerIcon, 
  KeyboardIcon, GaugeIcon, AlertCircleIcon, CrownIcon,
  RefreshCwIcon, ActivityIcon, ChevronUpIcon, ChevronDownIcon,
  SlidersIcon
} from 'lucide-react'

const API_URL = 'https://slywriterapp.onrender.com'

interface Profile {
  name: string
  is_builtin: boolean
  settings: {
    min_delay: number
    max_delay: number
    typos_enabled: boolean
    typo_chance: number
    pause_frequency: number
    ai_filler_enabled: boolean
    micro_hesitations: boolean
    zone_out_breaks: boolean
    burst_variability: number
  }
}

interface TypingTabProps {
  connected: boolean
  initialProfile?: string
  shouldOpenWpmTest?: boolean
  onWpmTestOpened?: () => void
}

export default function TypingTabWithWPM({ connected, initialProfile, shouldOpenWpmTest, onWpmTestOpened }: TypingTabProps) {
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
  const [countdown, setCountdown] = useState<number | undefined>(undefined)
  const [previewMode, setPreviewMode] = useState(false)
  
  // Profile state
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [selectedProfile, setSelectedProfile] = useState(initialProfile || 'Medium')
  const [loadingProfiles, setLoadingProfiles] = useState(true)
  
  // Premium features state
  const [typosMade, setTyposMade] = useState(0)
  const [pausesTaken, setPausesTaken] = useState(0)
  
  // Grammarly-style settings
  const [grammarlyCorrectionEnabled, setGrammarlyCorrectionEnabled] = useState(false)
  const [grammarlyCorrectionDelay, setGrammarlyCorrectionDelay] = useState(2)
  const [typoRate, setTypoRate] = useState(2)
  const [humanMode, setHumanMode] = useState(true)
  const [pasteMode, setPasteMode] = useState(false)
  const [autoClearTextbox, setAutoClearTextbox] = useState(true)
  const [zoneOutActive, setZoneOutActive] = useState(false)
  const [microHesitations, setMicroHesitations] = useState(0)
  const [aiFillers, setAiFillers] = useState(0)
  
  // UI state
  const [showStats, setShowStats] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [copied, setCopied] = useState(false)
  
  // WPM Test state
  const [showWpmTest, setShowWpmTest] = useState(false)
  const [testText] = useState('The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs. How vexingly quick daft zebras jump! Sphinx of black quartz, judge my vow.')
  const [testInput, setTestInput] = useState('')
  const [testStartTime, setTestStartTime] = useState<number | undefined>(undefined)
  const [testWpm, setTestWpm] = useState<number | undefined>(undefined)
  const [isTestActive, setIsTestActive] = useState(false)
  const [testErrors, setTestErrors] = useState(0)
  
  const wsRef = useRef<WebSocket | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const testInputRef = useRef<HTMLTextAreaElement>(null)
  
  // Load profiles and check for onboarding triggers
  useEffect(() => {
    loadProfiles()
    
    // Load saved values from localStorage after mount to avoid hydration mismatch
    if (typeof window !== 'undefined') {
      const savedProfile = localStorage.getItem('slywriter-selected-profile')
      if (savedProfile) {
        setSelectedProfile(savedProfile)
      }
      
      const savedWpm = localStorage.getItem('slywriter-custom-wpm')
      if (savedWpm) {
        setTestWpm(parseInt(savedWpm))
      }
    }
    
    // Check if we should open WPM test from onboarding
    if (shouldOpenWpmTest) {
      setShowWpmTest(true)
      if (onWpmTestOpened) {
        onWpmTestOpened()
      }
    }
  }, [shouldOpenWpmTest, onWpmTestOpened])
  
  // Listen for global stop event from GlobalHotkeys component
  useEffect(() => {
    const handleGlobalStop = () => {
      console.log('GLOBAL STOP EVENT RECEIVED!')
      stopTyping()
    }
    
    window.addEventListener('global-stop-typing', handleGlobalStop)
    
    return () => {
      window.removeEventListener('global-stop-typing', handleGlobalStop)
    }
  }, [])
  
  // Save WPM to localStorage whenever it changes
  useEffect(() => {
    if (testWpm !== undefined) {
      if (typeof window !== 'undefined') {
        localStorage.setItem('slywriter-custom-wpm', testWpm.toString())
      }
    }
  }, [testWpm])
  
  // Save selected profile to localStorage whenever it changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('slywriter-selected-profile', selectedProfile)
    }
  }, [selectedProfile])
  
  const loadProfiles = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/profiles`)
      setProfiles(response.data.profiles)
      setLoadingProfiles(false)
    } catch (error) {
      console.error('Failed to load profiles:', error)
      setLoadingProfiles(false)
    }
  }
  
  // WebSocket connection
  useEffect(() => {
    if (!connected) return
    
    const userId = user?.email || 'anonymous'
    let ws: WebSocket | null = null
    
    try {
      ws = new WebSocket(`ws://localhost:8000/ws/${userId}`)
      wsRef.current = ws
      
      ws.onopen = () => {
        console.log('WebSocket connected for typing updates')
      }
      
      ws.onerror = (error) => {
        console.warn('WebSocket connection error - this is normal if not actively typing')
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          switch (data.type) {
        case 'countdown':
          setCountdown(data.data.count)
          setStatus(`Starting in ${data.data.count}...`)
          break
          
        case 'typing_started':
          setCountdown(undefined)  // Clear countdown
          setStatus('Typing...')
          break
          
        case 'progress':
          setProgress(data.data.progress)
          setWpm(data.data.wpm)
          setAccuracy(data.data.accuracy)
          setCharsTyped(data.data.chars_typed)
          setTotalChars(data.data.total_chars)
          setStatus(data.data.status)
          
          // Dispatch update event for overlay
          const updateEvent = new CustomEvent('typing-update', {
            detail: {
              status: data.data.status,
              wpm: data.data.wpm,
              progress: data.data.progress
            }
          })
          window.dispatchEvent(updateEvent)
          break
          
        case 'typo':
          setTyposMade(data.data.typos_made)
          break
          
        case 'natural_pause':
          // Natural pauses are just delays, not actual pauses
          setPausesTaken(prev => prev + 1)
          // Don't change isPaused state - these are automatic pauses
          break
          
        case 'pause':
          setPausesTaken(data.data.pauses_taken)
          setStatus(data.data.status)
          break
          
        case 'zone_out':
          setZoneOutActive(true)
          setStatus(data.data.status)
          setTimeout(() => setZoneOutActive(false), data.data.duration * 1000)
          break
          
        case 'micro_hesitation':
          setMicroHesitations(prev => prev + 1)
          break
          
        case 'ai_filler':
          setAiFillers(data.data.fillers_used)
          setStatus('AI Filler...')
          break
          
        case 'complete':
          setIsTyping(false)
          setStatus('Complete!')
          toast.success('Typing session complete!')
          setSessionId(null)
          
          // Auto-clear textbox if enabled
          if (autoClearTextbox) {
            setTimeout(() => {
              setInputText('')
              toast.success('Textbox cleared - ready for next paste!', { icon: '🔄' })
            }, 1000) // Wait 1 second after completion before clearing
          }
          
          // Dispatch event for statistics tracking
          const words = inputText.trim().split(/\s+/).length
          const typingEvent = new CustomEvent('typing-complete', {
            detail: {
              words,
              characters: inputText.length,
              wpm: wpm || getProfileWpm(selectedProfile, testWpm)
            }
          })
          window.dispatchEvent(typingEvent)
          break
          
            case 'error':
              toast.error(data.data.message)
              setIsTyping(false)
              setStatus('Error')
              break
          }
        } catch (err) {
          console.warn('Failed to parse WebSocket message:', err)
        }
      }
      
      ws.onclose = () => {
        console.log('WebSocket disconnected')
      }
      
    } catch (error) {
      console.warn('WebSocket setup error - this is normal if backend is starting up')
    }
    
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
      wsRef.current = null
    }
  }, [connected, user])
  
  // Other hotkeys
  useHotkeys('ctrl+enter', () => !isTyping && startTyping())
  useHotkeys('ctrl+shift+p', () => setPreviewMode(!previewMode))
  useHotkeys('ctrl+t', () => setShowWpmTest(!showWpmTest))
  
  // WPM adjustment hotkeys
  useHotkeys('ctrl+up', () => {
    if (!isTyping) {
      const currentWpm = selectedProfile === 'Custom' && testWpm ? testWpm : getProfileWpm(selectedProfile, testWpm)
      const newWpm = Math.min(200, currentWpm + 10)
      setSelectedProfile('Custom')
      setTestWpm(newWpm)
      toast.success(`Speed increased to ${newWpm} WPM`)
    }
  }, [isTyping, selectedProfile, testWpm])
  
  useHotkeys('ctrl+down', () => {
    if (!isTyping) {
      const currentWpm = selectedProfile === 'Custom' && testWpm ? testWpm : getProfileWpm(selectedProfile, testWpm)
      const newWpm = Math.max(20, currentWpm - 10)
      setSelectedProfile('Custom')
      setTestWpm(newWpm)
      toast.success(`Speed decreased to ${newWpm} WPM`)
    }
  }, [isTyping, selectedProfile, testWpm])
  
  // Update WPM while typing (for arrow controls)
  const updateTypingWpm = async (newWpm: number) => {
    if (!sessionId || !isTyping) return
    
    try {
      // Auth handled via cookies, no need for manual token
      
      await axios.post(`${API_URL}/api/typing/update_wpm`, {
        session_id: sessionId,
        wpm: newWpm
      })
      
      setWpm(newWpm)
    } catch (error) {
      console.error('Failed to update WPM:', error)
    }
  }

  const startTyping = async () => {
    let textToType = inputText.trim()
    
    // If no text entered, try to read from clipboard
    if (!textToType) {
      try {
        const clipboardText = await navigator.clipboard.readText()
        if (clipboardText && clipboardText.trim()) {
          textToType = clipboardText.trim()
          setInputText(textToType)
          toast.success('📋 Using text from clipboard!')
        } else {
          toast.error('No text in input box or clipboard. Please enter or copy some text.')
          return
        }
      } catch (err) {
        toast.error('Please enter text or copy text to clipboard first (clipboard access denied)')
        return
      }
    }
    
    if (!connected) {
      toast.error('Backend connection required. Please check if the server is running.')
      return
    }
    
    // Check word limit for authenticated users
    const wordCount = textToType.split(/\s+/).length
    if (user && (!canType || wordCount > wordsRemaining)) {
      toast.error(`Word limit exceeded! ${wordsRemaining} words remaining today`)
      return
    }
    
    try {
      // Auth handled via cookies, no need for manual token
      
      // Calculate custom WPM if using Custom profile or arrows
      const customWpm = selectedProfile === 'Custom' && testWpm ? testWpm : undefined
      
      const response = await axios.post(`${API_URL}/api/typing/start`, {
        text: textToType,
        profile: selectedProfile,
        preview_mode: previewMode,
        custom_wpm: customWpm
      })
      
      setSessionId(response.data.session_id)
      setIsTyping(true)
      setIsPaused(false)
      setProgress(0)
      setWpm(selectedProfile === 'Custom' && testWpm ? testWpm : getProfileWpm(selectedProfile, testWpm)) // Set initial WPM based on profile
      setAccuracy(100)
      setCharsTyped(0)
      setTotalChars(textToType.length)
      setTyposMade(0)
      setPausesTaken(0)
      setMicroHesitations(0)
      setAiFillers(0)
      setStatus('Typing...')
      
      // Dispatch start event for overlay
      window.dispatchEvent(new CustomEvent('typing-start'))
      
      toast.success('✨ Automation started! SlyWriter is typing for you...')
    } catch (error: any) {
      console.error('Typing start error:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to start typing'
      toast.error(errorMsg)
    }
  }
  
  const pauseTyping = async () => {
    if (!isTyping) {
      console.log('Not typing, cannot pause')
      return
    }
    
    // Immediately update UI for responsiveness
    const newPausedState = !isPaused
    setIsPaused(newPausedState)
    setStatus(newPausedState ? 'Paused' : 'Typing...')
    
    try {
      if (sessionId) {
        // Try session-specific endpoint first
        if (newPausedState) {
          await axios.post(`${API_URL}/api/typing/pause/${sessionId}`)
        } else {
          await axios.post(`${API_URL}/api/typing/resume/${sessionId}`)
        }
      } else {
        // Fallback to global pause endpoint
        await axios.post(`${API_URL}/api/typing/pause`)
      }
      toast(newPausedState ? '⏸️ Typing paused - Press SPACE to resume' : '▶️ Typing resumed')
    } catch (error) {
      // If session endpoint fails, try global endpoint
      console.error('Pause/resume error, trying global endpoint:', error)
      try {
        await axios.post(`${API_URL}/api/typing/pause`)
        toast(newPausedState ? '⏸️ Paused (global)' : '▶️ Resumed (global)')
      } catch (globalError) {
        console.error('Global pause failed:', globalError)
        toast(newPausedState ? '⏸️ Paused locally' : '▶️ Resumed locally')
      }
    }
  }
  
  const stopTyping = async () => {
    console.log('STOP TYPING CALLED - sessionId:', sessionId, 'isTyping:', isTyping)
    
    // Immediately update UI for better responsiveness
    setIsTyping(false)
    setIsPaused(false)
    setStatus('Stopped')
    
    // Always try to stop, even without sessionId
    try {
      if (sessionId) {
        // Try session-specific endpoint first
        try {
          await axios.post(`${API_URL}/api/typing/stop/${sessionId}`)
          console.log('Session stop successful')
        } catch (sessionError) {
          console.error('Session stop failed, trying global:', sessionError)
          // If session stop fails, try global stop
          await axios.post(`${API_URL}/api/typing/stop`)
        }
      } else {
        // No session ID, use global stop
        await axios.post(`${API_URL}/api/typing/stop`)
        console.log('Global stop successful')
      }
      
      toast.success('✋ Typing stopped successfully!')
    } catch (error) {
      console.error('All stop attempts failed:', error)
      // Even if API fails, ensure UI is stopped
      toast.error('Stop signal sent (forcing local stop)')
    }
    
    // Always clear session and dispatch event
    setSessionId(null)
    window.dispatchEvent(new CustomEvent('typing-stop'))
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
      }
      reader.readAsText(file)
    }
  }
  
  const downloadText = () => {
    const blob = new Blob([inputText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'slywriter-text.txt'
    a.click()
  }
  
  // WPM Test Functions
  const startWpmTest = () => {
    setIsTestActive(true)
    setTestStartTime(Date.now())
    setTestInput('')
    setTestWpm(undefined)
    setTestErrors(0)
    setTimeout(() => testInputRef.current?.focus(), 100)
  }
  
  const handleTestInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setTestInput(value)
    
    // Calculate errors
    let errors = 0
    for (let i = 0; i < value.length; i++) {
      if (value[i] !== testText[i]) {
        errors++
      }
    }
    setTestErrors(errors)
    
    // Auto-complete if full text typed
    if (value.length >= testText.length) {
      completeWpmTest()
    }
  }
  
  const completeWpmTest = () => {
    if (!testStartTime || !isTestActive) return
    
    const timeInMinutes = (Date.now() - testStartTime) / 60000
    const wordsTyped = testInput.trim().split(/\s+/).length
    const calculatedWpm = Math.round(wordsTyped / timeInMinutes)
    const calculatedAccuracy = Math.round(((testText.length - testErrors) / testText.length) * 100)
    
    setTestWpm(calculatedWpm)
    setIsTestActive(false)
    
    // Auto-generate profile based on WPM
    if (calculatedWpm > 0) {
      generateCustomProfile(calculatedWpm)
    }
  }
  
  const generateCustomProfile = async (wpm: number) => {
    try {
      const response = await axios.post(`${API_URL}/api/profiles/generate-from-wpm`, { wpm })
      toast.success(`✨ Custom profile calibrated for ${wpm} WPM!`)
      setSelectedProfile('Custom')
      await loadProfiles() // Reload to get updated custom profile
      
      // Close test panel
      setTimeout(() => setShowWpmTest(false), 2000)
    } catch (error) {
      console.error('Failed to generate profile:', error)
      toast.error('Failed to generate custom profile')
    }
  }
  
  return (
    <div className="space-y-6 relative">
      {/* First Time Helper */}
      <FirstTimeHelper feature="typing" />
      
      {/* Header with WPM Test Integration */}
      <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 bg-gray-900 rounded-2xl p-6 backdrop-blur-sm border border-purple-500/20">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <KeyboardIcon className="w-8 h-8 text-purple-400" />
              <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent text-purple-400">
                Typing Automation Engine</h2>
              <span className="text-xs bg-purple-500/20 px-2 py-1 rounded-full text-purple-300 text-purple-400">
                Works FOR You
              </span>
              <FeatureTooltip 
                title="Auto-Typing" 
                content="Paste any text and SlyWriter will type it automatically with human-like patterns. No manual typing needed!"
              />
            </div>
            <p className="text-gray-400 mb-4">AI-powered automation that types like you would</p>
            
            {/* Integrated WPM Display & Test */}
            <div className="flex items-center gap-4">
              <div className="bg-gray-900/50 rounded-lg px-4 py-2 flex items-center gap-3 border border-purple-500/20">
                <GaugeIcon className="w-5 h-5 text-purple-400" />
                <div>
                  <span className="text-xs text-gray-400">Target Speed</span>
                  <div className="flex items-center gap-1">
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={async () => {
                        const currentWpm = selectedProfile === 'Custom' && testWpm ? testWpm : getProfileWpm(selectedProfile, testWpm)
                        const newWpm = Math.max(20, currentWpm - 10)
                        setSelectedProfile('Custom')
                        setTestWpm(newWpm)
                        toast(`Speed: ${newWpm} WPM`, { icon: '⬇️' })
                        
                        // Update backend if typing is active
                        if (isTyping) {
                          await updateTypingWpm(newWpm)
                        }
                      }}
                      className="p-1.5 bg-gray-800 hover:bg-purple-500/30 rounded-lg transition-all"
                      title="Decrease speed (Ctrl+Down)"
                    >
                      <ChevronDownIcon className="w-5 h-5 text-purple-400" />
                    </motion.button>
                    
                    <div className="px-3 py-1 bg-gray-800 rounded-lg min-w-[100px]">
                      <div className="text-xl font-bold text-white text-purple-400 text-center">
                        {isTyping ? wpm : (selectedProfile === 'Custom' && testWpm ? testWpm : getProfileWpm(selectedProfile, testWpm))} 
                        <span className="text-xs text-gray-400 ml-1">WPM</span>
                      </div>
                      <div className="text-[10px] text-gray-500 text-center">
                        ±20% variance
                      </div>
                    </div>
                    
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={async () => {
                        const currentWpm = selectedProfile === 'Custom' && testWpm ? testWpm : getProfileWpm(selectedProfile, testWpm)
                        const newWpm = Math.min(200, currentWpm + 10)
                        setSelectedProfile('Custom')
                        setTestWpm(newWpm)
                        toast(`Speed: ${newWpm} WPM`, { icon: '⬆️' })
                        
                        // Update backend if typing is active
                        if (isTyping) {
                          await updateTypingWpm(newWpm)
                        }
                      }}
                      className="p-1.5 bg-gray-800 hover:bg-purple-500/30 rounded-lg transition-all"
                      title="Increase speed (Ctrl+Up)"
                    >
                      <ChevronUpIcon className="w-5 h-5 text-purple-400" />
                    </motion.button>
                  </div>
                  <div className="text-[10px] text-gray-500 mt-1">
                    <span className="text-purple-400">Realistic range:</span> {Math.round((selectedProfile === 'Custom' && testWpm ? testWpm : getProfileWpm(selectedProfile, testWpm)) * 0.8)}-{Math.round((selectedProfile === 'Custom' && testWpm ? testWpm : getProfileWpm(selectedProfile, testWpm)) * 1.2)} WPM with natural variance
                  </div>
                </div>
              </div>
              
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowWpmTest(!showWpmTest)}
                className="px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 rounded-lg flex items-center gap-2 transition-all"
              >
                <ActivityIcon className="w-4 h-4" />
                <span className="text-sm font-medium">
                  {showWpmTest ? 'Hide Test' : testWpm ? 'Retake Test' : 'Calibrate Speed'}
                </span>
                {testWpm && (
                  <span className="text-xs bg-green-500/20 px-2 py-0.5 rounded-full text-green-400">
                    {testWpm} WPM
                  </span>
                )}
              </motion.button>
            </div>
          </div>
          
          {user && (
            <div className="text-right">
              <div className="flex items-center gap-2 justify-end mb-2">
                {isPremium && <CrownIcon className="w-5 h-5 text-yellow-400" />}
                <span className="text-sm font-medium bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent text-purple-400">
                  {(user.plan || 'FREE').toUpperCase()} PLAN
                </span>
              </div>
              <div className="text-xs text-gray-400">
                {wordsRemaining === Infinity ? (
                  'Unlimited words'
                ) : (
                  <>{wordsRemaining.toLocaleString()} words remaining</>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* WPM Test Panel */}
      <AnimatePresence>
        {showWpmTest && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-purple-500/20"
          >
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <GaugeIcon className="w-5 h-5 text-purple-400" />
                  Speed Calibration Test
                </h3>
                {testWpm && (
                  <div className="text-right">
                    <div className="text-2xl font-bold text-purple-400">{testWpm} WPM</div>
                    <div className="text-xs text-gray-400">Your typing speed</div>
                  </div>
                )}
              </div>
              
              {/* Test Text Display */}
              <div className="bg-gray-800 rounded-lg p-4 font-mono text-sm">
                {testText.split('').map((char, idx) => {
                  const isTyped = idx < testInput.length
                  const isCorrect = isTyped && testInput[idx] === char
                  const isWrong = isTyped && testInput[idx] !== char
                  
                  return (
                    <span
                      key={idx}
                      className={`
                        ${isCorrect ? 'text-green-400' : ''}
                        ${isWrong ? 'text-red-400 bg-red-900/30' : ''}
                        ${!isTyped ? 'text-gray-400' : ''}
                      `}
                    >
                      {char}
                    </span>
                  )
                })}
              </div>
              
              {/* Test Input */}
              <div className="relative">
                <textarea
                  ref={testInputRef}
                  value={testInput}
                  onChange={handleTestInput}
                  disabled={!isTestActive}
                  placeholder={isTestActive ? "Start typing the text above..." : "Click 'Start Test' to begin"}
                  className="w-full h-32 bg-gray-800 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all font-mono text-sm"
                />
                {isTestActive && testStartTime && (
                  <div className="absolute top-2 right-2 text-xs text-gray-400">
                    Time: {Math.floor((Date.now() - testStartTime) / 1000)}s
                  </div>
                )}
              </div>
              
              {/* Test Controls */}
              <div className="flex justify-between items-center">
                <div className="text-xs text-gray-400">
                  {testInput.length}/{testText.length} characters • {testErrors} errors
                </div>
                
                <div className="flex gap-2">
                  {!isTestActive ? (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={startWpmTest}
                      className="px-4 py-2 bg-purple-500 hover:bg-purple-600 bg-purple-500 hover:bg-purple-500-dark rounded-lg flex items-center gap-2 transition-colors text-white"
                    >
                      <PlayIcon className="w-4 h-4" />
                      Start Test
                    </motion.button>
                  ) : (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={completeWpmTest}
                      className="px-4 py-2 bg-green-500 hover:bg-green-600 rounded-lg flex items-center gap-2 transition-colors"
                    >
                      <CheckIcon className="w-4 h-4" />
                      Complete
                    </motion.button>
                  )}
                  
                  {testWpm && (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => generateCustomProfile(testWpm)}
                      className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg flex items-center gap-2 transition-colors"
                    >
                      <RefreshCwIcon className="w-4 h-4" />
                      Apply to Profile
                    </motion.button>
                  )}
                </div>
              </div>
              
              {testWpm && (
                <div className="bg-purple-500/10 rounded-lg p-4 border border-purple-500/20">
                  <p className="text-sm text-purple-300 text-purple-400">
                    ✨ Based on your {testWpm} WPM typing speed, we've calibrated a custom profile that will make automated typing look natural for you.
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Profile Selection */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <ZapIcon className="w-4 h-4 text-yellow-400" />
            Typing Profile
          </h3>
          
          {selectedProfile === 'Custom' && testWpm && (
            <span className="text-xs bg-purple-500/20 px-2 py-1 rounded-full text-purple-300 text-purple-400">
              Calibrated for {testWpm} WPM
            </span>
          )}
        </div>
        
        {loadingProfiles ? (
          <div className="flex justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-purple-400 border-t-transparent" />
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {profiles.map((profile) => (
              <motion.button
                key={profile.name}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setSelectedProfile(profile.name)}
                disabled={isTyping}
                className={`
                  relative p-3 rounded-lg border transition-all
                  ${selectedProfile === profile.name 
                    ? 'bg-purple-500/20 bg-purple-500/10 border-purple-500 border-purple-500 shadow-lg shadow-purple-500/20 shadow-brand-purple/20' 
                    : 'bg-gray-800/50 bg-gray-900/50 border-gray-700 hover:border-purple-500/50'
                  }
                  ${isTyping ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                <div className="text-sm font-medium text-white mb-1">
                  {profile.name}
                </div>
                <div className="text-xs text-gray-400">
                  {profile.name === 'Slow' && '~50-60 WPM'}
                  {profile.name === 'Medium' && '~100-140 WPM'}
                  {profile.name === 'Fast' && '~350-450 WPM (Lightning!)'}
                  {profile.name === 'Essay' && 'AI Enhanced (~65 WPM)'}
                  {profile.name === 'Custom' && (testWpm ? `${testWpm} WPM` : 'Calibrate First')}
                </div>
                
                {profile.settings.ai_filler_enabled && (
                  <div className="absolute top-1 right-1">
                    <SparklesIcon className="w-3 h-3 text-yellow-400" />
                  </div>
                )}
                
                {selectedProfile === profile.name && (
                  <motion.div
                    layoutId="selected-profile"
                    className="absolute inset-0 border-2 border-purple-400 rounded-lg pointer-events-none"
                  />
                )}
              </motion.button>
            ))}
          </div>
        )}
        
        <div className="mt-4 text-xs text-gray-400">
          <span className="text-yellow-400">Tip:</span> All profiles have typos enabled by default for realistic typing. 
          {!testWpm && ' Click "Calibrate Speed" above to create a profile matched to your typing speed!'}
        </div>
      </div>
      
      {/* Advanced Typing Settings */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <SlidersIcon className="w-4 h-4 text-purple-400" />
            Advanced Settings
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
              step="1"
              value={typoRate}
              onChange={(e) => setTypoRate(parseInt(e.target.value))}
              className="w-full accent-purple-500"
              disabled={isTyping}
            />
          </div>
          
          {/* Grammarly Correction Delay */}
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
              disabled={!grammarlyCorrectionEnabled || isTyping}
            />
          </div>
        </div>
        
        {/* Toggle Options */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <label className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-700/50 transition-colors group">
            <input
              type="checkbox"
              checked={humanMode}
              onChange={(e) => setHumanMode(e.target.checked)}
              className="w-5 h-5 text-purple-500 rounded"
              disabled={isTyping}
            />
            <div>
              <span className="text-white font-medium text-sm">Human Mode</span>
              <p className="text-xs text-gray-400">Natural patterns</p>
            </div>
          </label>
          
          <label className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-700/50 transition-colors group">
            <input
              type="checkbox"
              checked={grammarlyCorrectionEnabled}
              onChange={(e) => setGrammarlyCorrectionEnabled(e.target.checked)}
              className="w-5 h-5 text-purple-500 rounded"
              disabled={isTyping}
            />
            <div>
              <span className="text-white font-medium text-sm">Grammarly-Style</span>
              <p className="text-xs text-gray-400">Delayed fixes</p>
            </div>
          </label>
          
          <label className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-700/50 transition-colors group relative">
            <input
              type="checkbox"
              checked={pasteMode}
              onChange={(e) => setPasteMode(e.target.checked)}
              className="w-5 h-5 text-purple-500 rounded"
              disabled={isTyping}
            />
            <div className="flex-1">
              <span className="text-white font-medium text-sm">Paste Mode</span>
              <p className="text-xs text-gray-400">5s delay</p>
            </div>
            {/* Tooltip explanation */}
            <div className="absolute bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 rounded-lg shadow-xl border border-purple-500/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              <p className="text-xs text-gray-300">
                <span className="text-purple-400 font-semibold">Why use this?</span><br/>
                Perfect for quick copy-paste workflows. Highlight question → paste → auto-types answer after 5s. No clicking needed!
              </p>
            </div>
          </label>
          
          <label className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-700/50 transition-colors group relative">
            <input
              type="checkbox"
              checked={autoClearTextbox}
              onChange={(e) => setAutoClearTextbox(e.target.checked)}
              className="w-5 h-5 text-purple-500 rounded"
              disabled={isTyping}
            />
            <div className="flex-1">
              <span className="text-white font-medium text-sm">Auto-Clear</span>
              <p className="text-xs text-gray-400">After typing</p>
            </div>
            {/* Tooltip explanation */}
            <div className="absolute bottom-full right-0 mb-2 w-64 p-3 bg-gray-900 rounded-lg shadow-xl border border-purple-500/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              <p className="text-xs text-gray-300">
                <span className="text-purple-400 font-semibold">Why use this?</span><br/>
                Clears textbox after typing completes. Great for multiple questions - just highlight next Q, paste, repeat. No manual clearing!
              </p>
            </div>
          </label>
        </div>
      </div>
      
      {/* Quick Tips for Power Users */}
      {(pasteMode || autoClearTextbox) && (
        <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-xl p-4 border border-purple-500/20">
          <div className="flex items-start gap-3">
            <SparklesIcon className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-2">
              {pasteMode && (
                <div>
                  <span className="text-sm font-semibold text-purple-300">🚀 Paste Mode Active:</span>
                  <p className="text-xs text-gray-400 mt-1">
                    Copy any question → Paste here → Wait 5 seconds → Auto-types! Perfect for rapid Q&A sessions. 
                    No need to click start button.
                  </p>
                </div>
              )}
              {autoClearTextbox && (
                <div>
                  <span className="text-sm font-semibold text-blue-300">🔄 Auto-Clear Active:</span>
                  <p className="text-xs text-gray-400 mt-1">
                    Textbox clears automatically after typing completes. Chain multiple answers: 
                    Copy Q1 → Paste → Types → Copy Q2 → Paste → Repeat!
                  </p>
                </div>
              )}
              {pasteMode && autoClearTextbox && (
                <div className="pt-2 border-t border-gray-700/50">
                  <span className="text-xs font-bold text-yellow-400">⚡ POWER MODE:</span>
                  <p className="text-xs text-gray-300 mt-1">
                    Both features combined = Ultimate workflow! Just keep copying questions and pasting. 
                    SlyWriter handles everything else automatically.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Text Input & Preview Section */}
      <div className="bg-gray-900/50 rounded-2xl p-6 backdrop-blur-sm border border-gray-800 border-purple-500/20">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <FileTextIcon className="w-4 h-4 text-blue-400" />
            {previewMode ? 'Preview Output' : 'Text Input'}
            {!inputText && !previewMode && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="ml-2 px-2 py-0.5 bg-purple-500/20 rounded-full text-xs text-purple-300"
              >
                📋 Clipboard fallback enabled
              </motion.span>
            )}
          </h3>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPreviewMode(!previewMode)}
              className="px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 rounded-lg flex items-center gap-2 transition-all text-sm"
            >
              <EyeIcon className="w-4 h-4" />
              {previewMode ? 'Edit' : 'Preview'}
            </button>
            
            {inputText && (
              <button
                onClick={() => {
                  navigator.clipboard.writeText(inputText)
                  setCopied(true)
                  setTimeout(() => setCopied(false), 2000)
                }}
                className="px-3 py-1.5 bg-gray-700 bg-gray-800 hover:bg-gray-600 rounded-lg flex items-center gap-2 transition-all text-sm"
              >
                {copied ? <CheckIcon className="w-4 h-4" /> : <CopyIcon className="w-4 h-4" />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            )}
            
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-3 py-1.5 bg-gray-700 bg-gray-800 hover:bg-gray-600 rounded-lg flex items-center gap-2 transition-all text-sm"
            >
              <UploadIcon className="w-4 h-4" />
              Load File
            </button>
            
            {inputText && (
              <button
                onClick={() => setInputText('')}
                className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 rounded-lg flex items-center gap-2 transition-all text-sm text-red-400"
              >
                <TrashIcon className="w-4 h-4" />
                Clear
              </button>
            )}
          </div>
        </div>
        
        {previewMode ? (
          <div className="bg-gray-800 rounded-lg p-4 min-h-[200px] max-h-[400px] overflow-y-auto">
            <div className="font-mono text-sm text-green-400 whitespace-pre-wrap">
              {inputText || (
                <span className="text-gray-400">
                  Enter text to see how it will be typed out with human-like patterns...
                </span>
              )}
            </div>
            {inputText && (
              <div className="mt-4 pt-4 border-t border-gray-700 flex items-center justify-between text-xs text-gray-400">
                <span>Characters: {inputText.length}</span>
                <span>Words: {inputText.trim().split(/\s+/).length}</span>
                <span>Est. Time: {Math.round(inputText.length / (wpm * 5) * 60)}s @ {wpm || getProfileWpm(selectedProfile, testWpm)} WPM</span>
              </div>
            )}
          </div>
        ) : (
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onPaste={(e) => {
              if (pasteMode && !isTyping) {
                // In paste mode, automatically start typing after 5 seconds
                const pastedText = e.clipboardData.getData('text')
                setInputText(pastedText)
                setCountdown(5)
                
                // Countdown timer
                let count = 5
                const timer = setInterval(() => {
                  count--
                  setCountdown(count)
                  if (count <= 0) {
                    clearInterval(timer)
                    setCountdown(undefined)
                    startTyping()
                  }
                }, 1000)
              }
            }}
            placeholder="Paste or type your text here... Or just copy text and press Start - SlyWriter will use your clipboard!"
            className="w-full h-[200px] bg-gray-800 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
            disabled={isTyping}
          />
        )}
        
        {/* Paste Mode Countdown */}
        {countdown !== undefined && countdown > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-4 p-4 bg-purple-500/20 border border-purple-500/50 rounded-lg"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-500/30 rounded-full flex items-center justify-center">
                  <span className="text-lg font-bold text-purple-300">{countdown}</span>
                </div>
                <div>
                  <p className="text-sm font-semibold text-purple-300">Paste Mode Active</p>
                  <p className="text-xs text-gray-400">Starting in {countdown} seconds...</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setCountdown(undefined)
                  toast('Paste mode cancelled', { icon: '❌' })
                }}
                className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-400 text-sm"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        )}
        
        {/* Quick Tips */}
        {!inputText && !isTyping && (
          <div className="mt-4 space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <QuickTip text="📋 Copy any text + Click Start = Instant typing!" />
              <QuickTip text="🎯 Or use Ctrl+Enter with clipboard" />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <QuickTip text="Free users get 4,000 words daily" />
              <QuickTip text="Press Ctrl+Alt+G on any highlighted text for AI magic" />
            </div>
          </div>
        )}
        
        {/* Active Typing Indicators */}
        {isTyping && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span className="text-sm text-green-400 font-medium">Typing in progress...</span>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="text-gray-400">Stop with hotkey:</span>
                <kbd className="px-2 py-1 bg-gray-800 rounded text-red-400 font-mono">Ctrl+Alt+Q</kbd>
              </div>
            </div>
          </motion.div>
        )}
      </div>
      
      {/* Controls */}
      <div className="bg-gray-900/50 rounded-2xl p-6 backdrop-blur-sm border border-gray-800 border-purple-500/20">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <PlayIcon className="w-4 h-4 text-green-400" />
            Controls
          </h3>
          
          {countdown !== null && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="text-3xl font-bold text-purple-400"
            >
              {countdown}
            </motion.div>
          )}
        </div>
        
        <div className="flex flex-wrap gap-3">
          {!isTyping ? (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={startTyping}
              disabled={!connected || !canType}
              className={`
                w-full py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all
                ${connected && canType
                  ? 'bg-gradient-to-r from-green-500 to-emerald-500 bg-green-500 text-white hover:shadow-lg hover:shadow-green-500/30 hover:shadow-green-500/20'
                  : 'bg-gray-700 bg-gray-800 text-gray-400 cursor-not-allowed'
                }
              `}
            >
              <PlayIcon className="w-5 h-5" />
              {inputText ? 'Start Typing' : 'Start (Uses Clipboard)'}
            </motion.button>
          ) : (
            <>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={pauseTyping}
                className={`
                  flex-1 py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all
                  ${isPaused
                    ? 'bg-yellow-500 text-white hover:bg-yellow-600'
                    : 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30'
                  }
                `}
              >
                <PauseIcon className="w-5 h-5" />
                {isPaused ? 'Resume' : 'Pause'}
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={stopTyping}
                className="flex-1 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-medium hover:from-red-600 hover:to-red-700 flex items-center justify-center gap-2 transition-all shadow-lg shadow-red-500/30"
              >
                <StopCircleIcon className="w-5 h-5" />
                Stop
              </motion.button>
            </>
          )}
        </div>
        
        {/* Status Bar */}
        <div className="mt-4 p-3 bg-gray-800 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Status</span>
            <span className={`text-sm font-medium ${
              status === 'Typing...' ? 'text-green-400' :
              status === 'Paused' ? 'text-yellow-400' :
              status === 'Stopped' ? 'text-red-400' :
              'text-gray-400'
            }`}>
              {status}
            </span>
          </div>
          
          {progress > 0 && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-gray-400">
                <span>Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-700 bg-gray-800 rounded-full h-2">
                <motion.div
                  className="bg-gradient-to-r from-purple-500 to-blue-500 bg-purple-500 h-2 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Live Stats */}
      {(isTyping || progress > 0) && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="bg-gray-900/50 rounded-2xl p-6 backdrop-blur-sm border border-gray-800 border-purple-500/20"
        >
          <h3 className="text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            <ActivityIcon className="w-4 h-4 text-purple-400" />
            Live Statistics
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 rounded-lg p-3">
              <div className="text-2xl font-bold text-white">{wpm}</div>
              <div className="text-xs text-gray-400">Current WPM</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-3">
              <div className="text-2xl font-bold text-white">{accuracy}%</div>
              <div className="text-xs text-gray-400">Accuracy</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-3">
              <div className="text-2xl font-bold text-white">{charsTyped}/{totalChars}</div>
              <div className="text-xs text-gray-400">Characters</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-3">
              <div className="text-2xl font-bold text-white">{typosMade}</div>
              <div className="text-xs text-gray-400">Typos Made</div>
            </div>
          </div>
          
          {isPremium && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-purple-500/10 rounded-lg p-3 border border-purple-500/30">
                <div className="text-lg font-bold text-purple-400">{pausesTaken}</div>
                <div className="text-xs text-gray-400">Natural Pauses</div>
              </div>
              <div className="bg-purple-500/10 rounded-lg p-3 border border-purple-500/30">
                <div className="text-lg font-bold text-purple-400">{microHesitations}</div>
                <div className="text-xs text-gray-400">Micro-Hesitations</div>
              </div>
              <div className="bg-purple-500/10 rounded-lg p-3 border border-purple-500/30">
                <div className="text-lg font-bold text-purple-400">{aiFillers}</div>
                <div className="text-xs text-gray-400">AI Fillers</div>
              </div>
              <div className="bg-purple-500/10 rounded-lg p-3 border border-purple-500/30">
                <div className="text-lg font-bold text-purple-400">{zoneOutActive ? 'Yes' : 'No'}</div>
                <div className="text-xs text-gray-400">Zone Out Active</div>
              </div>
            </div>
          )}
        </motion.div>
      )}
      
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt"
        onChange={loadFile}
        className="hidden"
      />
    </div>
  )
}

// Helper function to get WPM for current profile
function getProfileWpm(profileName?: string, customWpm?: number): number {
  // If it's a custom profile and we have a custom WPM value, use it
  if (profileName === 'Custom' && customWpm) {
    return customWpm
  }
  
  const wpmMap: Record<string, number> = {
    'Slow': 30,
    'Medium': 60,
    'Fast': 120,
    'Essay': 45,
    'Custom': 80  // Default for custom if no test taken
  }
  
  return wpmMap[profileName || 'Medium'] || 100
}