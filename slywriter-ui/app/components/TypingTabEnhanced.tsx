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
  KeyboardIcon, GaugeIcon, AlertCircleIcon, CrownIcon
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
    ai_filler_enabled: boolean
    micro_hesitations: boolean
    zone_out_breaks: boolean
    burst_variability: number
  }
}

interface TypingTabProps {
  connected: boolean
}

export default function TypingTabEnhanced({ connected }: TypingTabProps) {
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
  
  // Profile state
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [selectedProfile, setSelectedProfile] = useState('Default')
  const [loadingProfiles, setLoadingProfiles] = useState(true)
  
  // Premium features state
  const [typosMade, setTyposMade] = useState(0)
  const [pausesTaken, setPausesTaken] = useState(0)
  const [zoneOutActive, setZoneOutActive] = useState(false)
  const [microHesitations, setMicroHesitations] = useState(0)
  const [aiFillers, setAiFillers] = useState(0)
  
  // UI state
  const [showStats, setShowStats] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [copied, setCopied] = useState(false)
  
  const wsRef = useRef<WebSocket | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Load profiles
  useEffect(() => {
    loadProfiles()
  }, [])
  
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
    const ws = new WebSocket(`ws://localhost:8000/ws/${userId}`)
    wsRef.current = ws
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      switch(data.type) {
        case 'connected':
          console.log('WebSocket connected:', data.data.message)
          break
          
        case 'countdown':
          setCountdown(data.data.count)
          setStatus(data.data.status)
          break
          
        case 'progress':
          setProgress(data.data.progress)
          setWpm(data.data.wpm)
          setAccuracy(data.data.accuracy)
          setCharsTyped(data.data.chars_typed)
          setTotalChars(data.data.total_chars)
          setStatus(data.data.status)
          setTyposMade(data.data.typos_made || 0)
          setPausesTaken(data.data.pauses_taken || 0)
          break
          
        case 'pause':
          setStatus(data.data.status)
          break
          
        case 'zone_out':
          setZoneOutActive(true)
          setStatus(`Zone out: ${Math.round(data.data.duration)}s`)
          setTimeout(() => setZoneOutActive(false), data.data.duration * 1000)
          break
          
        case 'complete':
          setIsTyping(false)
          setStatus('Complete!')
          setWpm(data.data.final_wpm)
          setTyposMade(data.data.typos_made)
          setPausesTaken(data.data.pauses_taken)
          
          if (data.data.premium_stats) {
            setMicroHesitations(data.data.premium_stats.micro_hesitations)
            setAiFillers(data.data.premium_stats.ai_fillers)
          }
          
          toast.success(`Typing complete! ${data.data.final_wpm} WPM`)
          break
      }
    }
    
    ws.onerror = () => {
      console.error('WebSocket error')
    }
    
    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [connected, user])
  
  // Hotkeys
  useHotkeys('ctrl+enter', () => !isTyping && startTyping(), [isTyping, inputText])
  useHotkeys('escape', () => isTyping && stopTyping(), [isTyping])
  useHotkeys('space', () => isTyping && pauseTyping(), { preventDefault: true }, [isTyping, isPaused])
  useHotkeys('ctrl+shift+p', () => setPreviewMode(!previewMode), [previewMode])
  
  const startTyping = async () => {
    if (!inputText.trim() || !connected) {
      toast.error('Please enter text and ensure connection')
      return
    }
    
    // Check word limit
    const wordCount = inputText.split(/\s+/).length
    if (!canType || wordCount > wordsRemaining) {
      toast.error(`Not enough words remaining. You have ${wordsRemaining} words left today.`)
      return
    }
    
    try {
      const response = await axios.post(`${API_URL}/api/typing/start`, {
        text: inputText,
        profile: selectedProfile,
        preview_mode: previewMode,
        session_id: sessionId
      })
      
      setSessionId(response.data.session_id)
      setIsTyping(true)
      setIsPaused(false)
      setProgress(0)
      setCharsTyped(0)
      setTotalChars(inputText.length)
      setCountdown(5)
      
      // Reset stats
      setTyposMade(0)
      setPausesTaken(0)
      setMicroHesitations(0)
      setAiFillers(0)
      
    } catch (error: any) {
      console.error('Failed to start typing:', error)
      toast.error(error.response?.data?.detail || 'Failed to start typing')
    }
  }
  
  const pauseTyping = async () => {
    if (!sessionId) return
    
    try {
      const response = await axios.post(`${API_URL}/api/typing/pause/${sessionId}`)
      setIsPaused(response.data.status === 'paused')
      setStatus(response.data.message)
    } catch (error) {
      console.error('Failed to pause:', error)
    }
  }
  
  const stopTyping = async () => {
    if (!sessionId) return
    
    try {
      await axios.post(`${API_URL}/api/typing/stop/${sessionId}`)
      setIsTyping(false)
      setIsPaused(false)
      setProgress(0)
      setCountdown(null)
      setStatus('Stopped')
      setSessionId(null)
    } catch (error) {
      console.error('Failed to stop:', error)
    }
  }
  
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target?.result as string
        setInputText(text)
        toast.success(`Loaded ${text.split(/\s+/).length} words`)
      }
      reader.readAsText(file)
    }
  }
  
  const copyToClipboard = () => {
    navigator.clipboard.writeText(inputText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    toast.success('Copied to clipboard')
  }
  
  const downloadText = () => {
    const blob = new Blob([inputText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `slywriter_${Date.now()}.txt`
    a.click()
  }
  
  const currentProfile = profiles.find(p => p.name === selectedProfile)
  
  return (
    <div className="space-y-6">
      {/* Header with User Info */}
      <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-2xl p-6 backdrop-blur-sm border border-purple-500/20">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <KeyboardIcon className="w-8 h-8 text-purple-400" />
              <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                Advanced Typing Engine
              </h2>
            </div>
            <p className="text-gray-400">Professional typing automation with human-like patterns</p>
          </div>
          
          {user && (
            <div className="text-right">
              <div className="flex items-center gap-2 justify-end mb-2">
                {isPremium && <CrownIcon className="w-5 h-5 text-yellow-400" />}
                <span className="text-sm font-medium bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  {user.plan.toUpperCase()} PLAN
                </span>
              </div>
              <div className="text-sm text-gray-400">
                {wordsRemaining === Infinity ? (
                  <span>Unlimited words</span>
                ) : (
                  <span>{wordsRemaining.toLocaleString()} words remaining today</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Profile Selector */}
      <div className="bg-gray-900/50 rounded-xl p-4 backdrop-blur-sm border border-gray-700/50">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <ZapIcon className="w-4 h-4 text-yellow-400" />
            Typing Profile
          </h3>
          {currentProfile && !currentProfile.is_builtin && (
            <span className="text-xs px-2 py-1 bg-purple-500/20 rounded-full">Custom</span>
          )}
        </div>
        
        {loadingProfiles ? (
          <div className="animate-pulse bg-gray-800 h-10 rounded-lg" />
        ) : (
          <div className="flex gap-2 flex-wrap">
            {profiles.map((profile) => (
              <motion.button
                key={profile.name}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setSelectedProfile(profile.name)}
                disabled={isTyping}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  selectedProfile === profile.name
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg shadow-purple-500/25'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
                } ${isTyping ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {profile.name}
                {profile.settings.ai_filler_enabled && (
                  <SparklesIcon className="w-4 h-4 inline ml-2 text-yellow-400" />
                )}
              </motion.button>
            ))}
          </div>
        )}
        
        {currentProfile && (
          <div className="mt-3 p-3 bg-gray-800/50 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-gray-400">Speed:</span>
                <span className="ml-2 text-purple-400">
                  {Math.round((1 - currentProfile.settings.min_delay) * 100)}%
                </span>
              </div>
              <div>
                <span className="text-gray-400">Typos:</span>
                <span className="ml-2">
                  {currentProfile.settings.typos_enabled ? 'ON' : 'OFF'}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Pauses:</span>
                <span className="ml-2">
                  Every {currentProfile.settings.pause_frequency} sentences
                </span>
              </div>
              {isPremium && (
                <div>
                  <span className="text-gray-400">Premium:</span>
                  <span className="ml-2 text-yellow-400">
                    {[
                      currentProfile.settings.ai_filler_enabled && 'AI',
                      currentProfile.settings.micro_hesitations && 'MH',
                      currentProfile.settings.zone_out_breaks && 'ZO'
                    ].filter(Boolean).join(', ') || 'OFF'}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* Countdown Display */}
      <AnimatePresence>
        {countdown !== null && countdown > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none"
          >
            <div className="bg-black/80 backdrop-blur-xl rounded-full w-32 h-32 flex items-center justify-center">
              <motion.div
                key={countdown}
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 1.5, opacity: 0 }}
                transition={{ duration: 0.5 }}
                className="text-6xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent"
              >
                {countdown}
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Status Bar */}
      {isTyping && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-900/50 rounded-xl p-4 backdrop-blur-sm border border-gray-700/50"
        >
          <div className="flex justify-between items-center mb-3">
            <div className="flex items-center gap-4">
              <div className={`w-3 h-3 rounded-full ${
                isTyping ? (isPaused ? 'bg-yellow-400' : 'bg-green-400 animate-pulse') : 'bg-gray-400'
              }`} />
              <span className="text-sm font-medium">{status}</span>
              {zoneOutActive && (
                <span className="px-2 py-1 bg-purple-500/20 rounded-full text-xs text-purple-400">
                  Zone Out Active
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-6">
              <div className="text-center">
                <div className="text-xs text-gray-400">WPM</div>
                <div className="text-xl font-bold text-purple-400">{wpm}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-gray-400">Accuracy</div>
                <div className="text-xl font-bold text-green-400">{accuracy.toFixed(1)}%</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-gray-400">Progress</div>
                <div className="text-xl font-bold text-blue-400">{Math.round(progress)}%</div>
              </div>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              className="h-full bg-gradient-to-r from-purple-500 to-blue-500 relative"
            >
              {isTyping && !isPaused && (
                <motion.div
                  className="absolute right-0 top-0 h-full w-8 bg-gray-900/30"
                  animate={{ x: [-32, 8] }}
                  transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                />
              )}
            </motion.div>
          </div>
          
          {/* Premium Stats */}
          {isPremium && showStats && (
            <div className="mt-3 pt-3 border-t border-gray-700 grid grid-cols-5 gap-4 text-xs">
              <div>
                <span className="text-gray-400">Typos:</span>
                <span className="ml-2 text-orange-400">{typosMade}</span>
              </div>
              <div>
                <span className="text-gray-400">Pauses:</span>
                <span className="ml-2 text-blue-400">{pausesTaken}</span>
              </div>
              <div>
                <span className="text-gray-400">Hesitations:</span>
                <span className="ml-2 text-purple-400">{microHesitations}</span>
              </div>
              <div>
                <span className="text-gray-400">AI Fillers:</span>
                <span className="ml-2 text-yellow-400">{aiFillers}</span>
              </div>
              <div>
                <span className="text-gray-400">Chars:</span>
                <span className="ml-2">{charsTyped}/{totalChars}</span>
              </div>
            </div>
          )}
          
          <button
            onClick={() => setShowStats(!showStats)}
            className="mt-2 text-xs text-gray-400 hover:text-gray-400"
          >
            {showStats ? 'Hide' : 'Show'} detailed stats
          </button>
        </motion.div>
      )}
      
      {/* Text Input */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <FileTextIcon className="w-4 h-4 text-purple-400" />
            Input Text
          </h3>
          
          <div className="flex items-center gap-2">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => fileInputRef.current?.click()}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <UploadIcon className="w-4 h-4" />
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={downloadText}
              disabled={!inputText}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
            >
              <DownloadIcon className="w-4 h-4" />
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={copyToClipboard}
              disabled={!inputText}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
            >
              {copied ? (
                <CheckIcon className="w-4 h-4 text-green-400" />
              ) : (
                <CopyIcon className="w-4 h-4" />
              )}
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setInputText('')}
              disabled={!inputText || isTyping}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
            >
              <TrashIcon className="w-4 h-4" />
            </motion.button>
          </div>
        </div>
        
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Enter or paste your text here... (Ctrl+Enter to start)"
          disabled={isTyping}
          className="w-full h-64 bg-gray-800/50 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all font-mono text-sm"
        />
        
        <div className="flex justify-between items-center mt-3">
          <div className="text-xs text-gray-400">
            {inputText.length} characters • {inputText.split(/\s+/).filter(Boolean).length} words
          </div>
          
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={previewMode}
              onChange={(e) => setPreviewMode(e.target.checked)}
              disabled={isTyping}
              className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
            />
            <span className="text-sm text-gray-400">
              <EyeIcon className="w-4 h-4 inline mr-1" />
              Preview Mode
            </span>
          </label>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt"
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>
      
      {/* Controls */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <div className="flex flex-wrap gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={startTyping}
            disabled={isTyping || !inputText.trim() || !connected}
            className={`px-6 py-3 rounded-xl font-medium flex items-center gap-2 transition-all shadow-lg ${
              isTyping || !inputText.trim() || !connected
                ? 'bg-gray-700 text-gray-400 cursor-not-allowed opacity-50'
                : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:shadow-purple-500/25'
            }`}
          >
            <PlayIcon className="w-5 h-5" />
            Start Typing
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={pauseTyping}
            disabled={!isTyping}
            className={`px-6 py-3 rounded-xl font-medium flex items-center gap-2 transition-all border ${
              !isTyping
                ? 'border-gray-700 text-gray-400 cursor-not-allowed opacity-50'
                : 'border-white/20 text-white hover:bg-gray-900/10'
            }`}
          >
            <PauseIcon className="w-5 h-5" />
            {isPaused ? 'Resume' : 'Pause'}
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={stopTyping}
            disabled={!isTyping}
            className={`px-6 py-3 rounded-xl font-medium flex items-center gap-2 transition-all ${
              !isTyping
                ? 'bg-gray-700 text-gray-400 cursor-not-allowed opacity-50'
                : 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30'
            }`}
          >
            <StopCircleIcon className="w-5 h-5" />
            Stop
          </motion.button>
        </div>
        
        {/* Keyboard Shortcuts */}
        <div className="mt-6 pt-6 border-t border-gray-700 flex flex-wrap items-center gap-4 text-xs text-gray-400">
          <span className="flex items-center gap-2">
            <kbd className="px-2 py-1 bg-gray-800 rounded">Ctrl</kbd>+
            <kbd className="px-2 py-1 bg-gray-800 rounded">Enter</kbd>
            Start
          </span>
          <span className="flex items-center gap-2">
            <kbd className="px-2 py-1 bg-gray-800 rounded">Space</kbd>
            Pause
          </span>
          <span className="flex items-center gap-2">
            <kbd className="px-2 py-1 bg-gray-800 rounded">Esc</kbd>
            Stop
          </span>
          <span className="flex items-center gap-2">
            <kbd className="px-2 py-1 bg-gray-800 rounded">Ctrl</kbd>+
            <kbd className="px-2 py-1 bg-gray-800 rounded">Shift</kbd>+
            <kbd className="px-2 py-1 bg-gray-800 rounded">P</kbd>
            Preview
          </span>
        </div>
      </div>
      
      {/* Premium Features Indicator */}
      {!isPremium && (
        <div className="bg-gradient-to-r from-yellow-900/20 to-orange-900/20 rounded-xl p-4 backdrop-blur-sm border border-yellow-500/20">
          <div className="flex items-center gap-3">
            <CrownIcon className="w-6 h-6 text-yellow-400" />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-400">Unlock Premium Features</h3>
              <p className="text-sm text-gray-400 mt-1">
                Get AI filler text, micro-hesitations, zone-out breaks, and more advanced anti-detection features.
              </p>
            </div>
            <button className="px-4 py-2 bg-gradient-to-r from-yellow-600 to-orange-600 rounded-lg font-medium">
              Upgrade
            </button>
          </div>
        </div>
      )}
    </div>
  )
}