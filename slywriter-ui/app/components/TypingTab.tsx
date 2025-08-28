'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { 
  PlayIcon, PauseIcon, StopCircleIcon, 
  FileTextIcon, CopyIcon, TrashIcon, CheckIcon,
  ClockIcon, TrendingUpIcon, TargetIcon, SparklesIcon,
  DownloadIcon, UploadIcon, SaveIcon, RotateCcwIcon
} from 'lucide-react'

const API_URL = 'http://localhost:8000'

interface TypingTabProps {
  connected: boolean
}

export default function TypingTab({ connected }: TypingTabProps) {
  // Core state
  const [inputText, setInputText] = useState('')
  const [previewText, setPreviewText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [typingStatus, setTypingStatus] = useState('Ready')
  const [progress, setProgress] = useState(0)
  const [wpm, setWpm] = useState(0)
  const [charCount, setCharCount] = useState(0)
  const [timeElapsed, setTimeElapsed] = useState(0)
  const [copied, setCopied] = useState(false)
  const [saved, setSaved] = useState(false)
  
  // Settings with profiles
  const [currentProfile, setCurrentProfile] = useState('default')
  const [profiles] = useState({
    default: { speed: 5, typosEnabled: false, aiFiller: false, pauseFrequency: 5 },
    fast: { speed: 8, typosEnabled: false, aiFiller: false, pauseFrequency: 10 },
    natural: { speed: 5, typosEnabled: true, aiFiller: false, pauseFrequency: 3 },
    essay: { speed: 4, typosEnabled: true, aiFiller: true, pauseFrequency: 2 },
  })
  const [settings, setSettings] = useState(profiles.default)

  // Saved templates
  const [templates, setTemplates] = useState<{[key: string]: string}>({})
  const [templateName, setTemplateName] = useState('')
  const [showSaveDialog, setShowSaveDialog] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  // Load saved data from localStorage
  useEffect(() => {
    const savedTemplates = localStorage.getItem('slywriter_templates')
    if (savedTemplates) {
      setTemplates(JSON.parse(savedTemplates))
    }
    const lastText = localStorage.getItem('slywriter_last_text')
    if (lastText) {
      setInputText(lastText)
    }
  }, [])

  // Save text to localStorage
  useEffect(() => {
    if (inputText) {
      localStorage.setItem('slywriter_last_text', inputText)
    }
  }, [inputText])

  // Timer
  useEffect(() => {
    let interval: NodeJS.Timeout
    if (isTyping && !isPaused) {
      interval = setInterval(() => {
        setTimeElapsed(prev => prev + 1)
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [isTyping, isPaused])

  // WebSocket
  useEffect(() => {
    if (!connected) return

    const ws = new WebSocket('ws://localhost:8000/ws')
    wsRef.current = ws
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'status') {
        const progressValue = (data.data.chars_typed / Math.max(1, data.data.total_chars)) * 100
        setProgress(progressValue)
        setWpm(data.data.wpm || 0)
        setCharCount(data.data.chars_typed || 0)
        setPreviewText(inputText.substring(0, data.data.chars_typed))
        
        if (progressValue >= 100) {
          setIsTyping(false)
          setTypingStatus('Complete! 🎉')
        } else if (data.data.status) {
          setTypingStatus(data.data.status)
        }
      }
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [connected, inputText])

  // Typing controls
  const startTyping = async () => {
    if (!inputText.trim() || !connected) return
    
    try {
      await axios.post(`${API_URL}/api/typing/start`, {
        text: inputText,
        min_delay: 0.5 - (settings.speed * 0.05),
        max_delay: 0.5 - (settings.speed * 0.045),
        typos_enabled: settings.typosEnabled,
        ai_filler_enabled: settings.aiFiller,
        pause_frequency: settings.pauseFrequency
      })
      setIsTyping(true)
      setIsPaused(false)
      setTypingStatus('Typing...')
      setProgress(0)
      setCharCount(0)
      setTimeElapsed(0)
    } catch (err) {
      console.error('Failed to start:', err)
      setTypingStatus('Error - Check connection')
    }
  }

  const pauseTyping = async () => {
    try {
      await axios.post(`${API_URL}/api/typing/pause`)
      setIsPaused(!isPaused)
      setTypingStatus(isPaused ? 'Resuming...' : 'Paused')
    } catch (err) {
      console.error('Failed to pause:', err)
    }
  }

  const stopTyping = async () => {
    try {
      await axios.post(`${API_URL}/api/typing/stop`)
      setIsTyping(false)
      setIsPaused(false)
      setProgress(0)
      setPreviewText('')
      setCharCount(0)
      setTypingStatus('Stopped')
      setTimeElapsed(0)
    } catch (err) {
      console.error('Failed to stop:', err)
    }
  }

  // File operations
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
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
    a.download = `slywriter_${Date.now()}.txt`
    a.click()
  }

  const copyToClipboard = useCallback(() => {
    navigator.clipboard.writeText(inputText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [inputText])

  const saveAsTemplate = () => {
    if (templateName && inputText) {
      const newTemplates = { ...templates, [templateName]: inputText }
      setTemplates(newTemplates)
      localStorage.setItem('slywriter_templates', JSON.stringify(newTemplates))
      setSaved(true)
      setShowSaveDialog(false)
      setTemplateName('')
      setTimeout(() => setSaved(false), 2000)
    }
  }

  const loadTemplate = (name: string) => {
    setInputText(templates[name] || '')
  }

  const switchProfile = (profileName: string) => {
    setCurrentProfile(profileName)
    setSettings(profiles[profileName as keyof typeof profiles])
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const stats = [
    { label: 'Progress', value: `${Math.round(progress)}%`, icon: TargetIcon },
    { label: 'Speed', value: `${wpm} WPM`, icon: TrendingUpIcon },
    { label: 'Time', value: formatTime(timeElapsed), icon: ClockIcon },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="flex flex-col h-full"
    >
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-xl border-b border-white/10">
        <div className="flex items-center justify-between px-8 py-5">
          {/* Status */}
          <motion.div 
            className="flex items-center gap-3"
            animate={{ scale: isTyping ? [1, 1.05, 1] : 1 }}
            transition={{ repeat: isTyping ? Infinity : 0, duration: 2 }}
          >
            <div className={`
              w-3 h-3 rounded-full transition-colors
              ${isTyping ? 'bg-green-400 animate-pulse' : 
                typingStatus.includes('Complete') ? 'bg-blue-400' : 'bg-gray-400'}
            `} />
            <span className="text-sm font-medium">{typingStatus}</span>
          </motion.div>

          {/* Profile Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">Profile:</span>
            <select 
              value={currentProfile}
              onChange={(e) => switchProfile(e.target.value)}
              className="bg-gray-900/10 border border-white/20 rounded-lg px-3 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              disabled={isTyping}
            >
              <option value="default">Default</option>
              <option value="fast">Fast</option>
              <option value="natural">Natural</option>
              <option value="essay">Essay</option>
            </select>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-6">
            {stats.map((stat, index) => {
              const Icon = stat.icon
              return (
                <motion.div 
                  key={stat.label}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="text-center"
                >
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                    <Icon className="w-3 h-3" />
                    <span>{stat.label}</span>
                  </div>
                  <p className="text-lg font-bold text-white">{stat.value}</p>
                </motion.div>
              )
            })}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="h-1 bg-black/50 relative overflow-hidden">
          <motion.div 
            className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
          {isTyping && (
            <motion.div
              className="absolute top-0 h-full w-20 bg-gray-900/20"
              animate={{ x: ['-100%', '500%'] }}
              transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}
            />
          )}
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 p-8 overflow-y-auto">
        {/* Quick Actions */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-gray-900/10 rounded-lg text-sm text-white hover:bg-gray-900/20 transition-colors flex items-center gap-2"
            >
              <UploadIcon className="w-4 h-4" />
              Import
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={downloadText}
              className="px-4 py-2 bg-gray-900/10 rounded-lg text-sm text-white hover:bg-gray-900/20 transition-colors flex items-center gap-2"
            >
              <DownloadIcon className="w-4 h-4" />
              Export
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowSaveDialog(true)}
              className="px-4 py-2 bg-gray-900/10 rounded-lg text-sm text-white hover:bg-gray-900/20 transition-colors flex items-center gap-2"
            >
              <SaveIcon className="w-4 h-4" />
              Save Template
              {saved && <CheckIcon className="w-4 h-4 text-green-400" />}
            </motion.button>
          </div>

          {/* Templates */}
          {Object.keys(templates).length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">Templates:</span>
              {Object.keys(templates).map(name => (
                <button
                  key={name}
                  onClick={() => loadTemplate(name)}
                  className="px-3 py-1 bg-purple-500/20 rounded-lg text-xs text-purple-300 hover:bg-purple-500/30 transition-colors"
                >
                  {name}
                </button>
              ))}
            </div>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.md"
          onChange={handleFileUpload}
          className="hidden"
        />

        {/* Text Areas */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Input Card */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-black/30 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden"
          >
            <div className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 px-6 py-4 border-b border-white/10">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
                  <FileTextIcon className="w-4 h-4 text-purple-400" />
                  Input Text
                </h3>
                <div className="flex items-center gap-2">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={copyToClipboard}
                    className="p-2 hover:bg-gray-900/10 rounded-lg transition-colors group"
                  >
                    {copied ? (
                      <CheckIcon className="w-4 h-4 text-green-400" />
                    ) : (
                      <CopyIcon className="w-4 h-4 text-gray-400 group-hover:text-white" />
                    )}
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => {
                      setInputText('')
                      setPreviewText('')
                      setProgress(0)
                    }}
                    className="p-2 hover:bg-gray-900/10 rounded-lg transition-colors group"
                  >
                    <RotateCcwIcon className="w-4 h-4 text-gray-400 group-hover:text-white" />
                  </motion.button>
                </div>
              </div>
            </div>
            <div className="p-6">
              <textarea 
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                className="w-full h-64 bg-black/40 border border-white/10 rounded-xl p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all font-mono text-sm"
                placeholder="Enter or paste your text here... (Ctrl+Enter to start)"
                disabled={isTyping}
              />
              <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
                <span>{inputText.length} characters</span>
                <span>{inputText.split(/\s+/).filter(Boolean).length} words</span>
              </div>
            </div>
          </motion.div>

          {/* Preview Card */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-black/30 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden"
          >
            <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 px-6 py-4 border-b border-white/10">
              <h3 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
                <span className="text-lg">👁️</span>
                Live Preview
              </h3>
            </div>
            <div className="p-6">
              <div className="w-full h-64 bg-black/40 border border-white/10 rounded-xl p-4 overflow-y-auto">
                {previewText ? (
                  <p className="text-white font-mono text-sm whitespace-pre-wrap">
                    {previewText}
                    {isTyping && (
                      <motion.span
                        animate={{ opacity: [1, 0] }}
                        transition={{ repeat: Infinity, duration: 0.8 }}
                        className="inline-block w-0.5 h-4 bg-purple-400 ml-0.5"
                      />
                    )}
                  </p>
                ) : (
                  <p className="text-gray-400 italic">
                    Preview will appear here as you type...
                  </p>
                )}
              </div>
              <div className="flex items-center justify-between mt-3">
                <span className="text-xs text-gray-400">
                  {charCount} / {inputText.length} characters
                </span>
                <div className="flex gap-1">
                  {[...Array(10)].map((_, i) => (
                    <motion.div 
                      key={i}
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: i * 0.05 }}
                      className={`
                        h-1.5 w-8 rounded-full transition-all duration-500
                        ${i < Math.floor(progress / 10) 
                          ? 'bg-gradient-to-r from-purple-400 to-blue-400' 
                          : 'bg-gray-900/10'
                        }
                      `}
                    />
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Controls */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-black/30 backdrop-blur-xl rounded-2xl border border-white/10 p-6"
        >
          <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
            {/* Action Buttons */}
            <div className="flex items-center gap-3">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={startTyping}
                disabled={isTyping || !inputText.trim() || !connected}
                className={`
                  px-6 py-3 rounded-xl font-medium flex items-center gap-2 
                  transition-all shadow-lg
                  ${isTyping || !inputText.trim() || !connected
                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed opacity-50'
                    : 'bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:shadow-purple-500/25'
                  }
                `}
              >
                <PlayIcon className="w-5 h-5" />
                Start Typing
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={pauseTyping}
                disabled={!isTyping}
                className={`
                  px-6 py-3 rounded-xl font-medium flex items-center gap-2 
                  transition-all border
                  ${!isTyping
                    ? 'border-gray-700 text-gray-400 cursor-not-allowed opacity-50'
                    : 'border-white/20 text-white hover:bg-gray-900/10'
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
                disabled={!isTyping}
                className={`
                  px-6 py-3 rounded-xl font-medium flex items-center gap-2 
                  transition-all
                  ${!isTyping
                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed opacity-50'
                    : 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30'
                  }
                `}
              >
                <StopCircleIcon className="w-5 h-5" />
                Stop
              </motion.button>
            </div>

            {/* Settings */}
            <div className="flex items-center gap-6">
              {/* Speed Control */}
              <div className="flex items-center gap-3">
                <span className="text-xs uppercase tracking-wider text-gray-400">Speed</span>
                <input 
                  type="range" 
                  min="1" 
                  max="10" 
                  value={settings.speed}
                  onChange={(e) => setSettings({...settings, speed: parseInt(e.target.value)})}
                  className="w-24 h-2 bg-gray-900/10 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-purple-500 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-lg"
                  disabled={isTyping}
                />
                <span className="text-sm font-bold text-purple-400 min-w-[2ch]">
                  {settings.speed}
                </span>
              </div>

              <div className="h-6 w-px bg-gray-900/10" />

              {/* Options */}
              <label className="flex items-center gap-2 cursor-pointer group">
                <input 
                  type="checkbox"
                  checked={settings.typosEnabled}
                  onChange={(e) => setSettings({...settings, typosEnabled: e.target.checked})}
                  disabled={isTyping}
                  className="w-4 h-4 rounded accent-purple-500"
                />
                <span className="text-sm text-gray-300 group-hover:text-white transition-colors">
                  Typos
                </span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer group">
                <input 
                  type="checkbox"
                  checked={settings.aiFiller}
                  onChange={(e) => setSettings({...settings, aiFiller: e.target.checked})}
                  disabled={isTyping}
                  className="w-4 h-4 rounded accent-purple-500"
                />
                <span className="text-sm text-gray-300 group-hover:text-white transition-colors flex items-center gap-1">
                  <SparklesIcon className="w-4 h-4 text-yellow-400" />
                  AI Filler
                </span>
                <span className="text-xs px-2 py-0.5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full text-white font-bold">
                  PRO
                </span>
              </label>
            </div>
          </div>
        </motion.div>

        {/* Save Template Dialog */}
        <AnimatePresence>
          {showSaveDialog && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
              onClick={() => setShowSaveDialog(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-black/80 backdrop-blur-xl rounded-2xl border border-white/20 p-6 max-w-md w-full mx-4"
                onClick={(e) => e.stopPropagation()}
              >
                <h3 className="text-lg font-semibold text-white mb-4">Save as Template</h3>
                <input
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  placeholder="Template name..."
                  className="w-full bg-gray-900/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                  autoFocus
                />
                <div className="flex justify-end gap-3 mt-4">
                  <button
                    onClick={() => setShowSaveDialog(false)}
                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveAsTemplate}
                    className="px-4 py-2 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg font-medium hover:shadow-lg transition-all"
                  >
                    Save
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}