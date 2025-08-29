'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { 
  PlayIcon, PauseIcon, StopCircleIcon, 
  SparklesIcon, KeyboardIcon, BarChart3Icon,
  SettingsIcon, UserCircleIcon, ChevronRightIcon,
  FileTextIcon, CopyIcon, TrashIcon, WifiOffIcon
} from 'lucide-react'

const API_URL = 'http://localhost:8000'

export default function SlyWriterApp() {
  // State management
  const [activeTab, setActiveTab] = useState('typing')
  const [inputText, setInputText] = useState('')
  const [previewText, setPreviewText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [typingStatus, setTypingStatus] = useState('Ready')
  const [progress, setProgress] = useState(0)
  const [wpm, setWpm] = useState(0)
  const [settings, setSettings] = useState({
    minDelay: 0.05,
    maxDelay: 0.15,
    typosEnabled: false,
    aiFiller: false,
    pauseFreq: 5
  })
  const [connected, setConnected] = useState(false)

  // Check backend connection
  useEffect(() => {
    checkConnection()
    const interval = setInterval(checkConnection, 5000)
    return () => clearInterval(interval)
  }, [])

  const checkConnection = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/health`)
      setConnected(true)
    } catch {
      setConnected(false)
    }
  }

  // WebSocket for real-time updates
  useEffect(() => {
    if (!connected) return

    const ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'status') {
        setTypingStatus(data.data.status)
        setProgress((data.data.chars_typed / Math.max(1, data.data.total_chars)) * 100)
        setWpm(data.data.wpm || 0)
        setPreviewText(inputText.substring(0, data.data.chars_typed))
      }
    }

    return () => ws.close()
  }, [connected, inputText])

  // Typing controls
  const startTyping = async () => {
    if (!inputText.trim()) return
    
    try {
      await axios.post(`${API_URL}/api/typing/start`, {
        text: inputText,
        min_delay: settings.minDelay,
        max_delay: settings.maxDelay,
        typos_enabled: settings.typosEnabled,
        ai_filler_enabled: settings.aiFiller,
        pause_frequency: settings.pauseFreq
      })
      setIsTyping(true)
      setIsPaused(false)
    } catch (err) {
      console.error('Failed to start typing:', err)
    }
  }

  const pauseTyping = async () => {
    try {
      await axios.post(`${API_URL}/api/typing/pause`)
      setIsPaused(!isPaused)
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
    } catch (err) {
      console.error('Failed to stop:', err)
    }
  }

  // Navigation items
  const navItems = [
    { id: 'typing', label: 'Typing', icon: KeyboardIcon },
    { id: 'ai-hub', label: 'AI Hub', icon: SparklesIcon },
    { id: 'stats', label: 'Statistics', icon: BarChart3Icon },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ]

  return (
    <div className="flex h-screen text-white">
      {/* Sidebar */}
      <motion.div 
        initial={{ x: -300 }}
        animate={{ x: 0 }}
        className="glass-darker w-72 p-6 flex flex-col"
      >
        <div className="mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
            SlyWriter
          </h1>
          <p className="text-gray-400 text-sm mt-1">Premium Typing Assistant</p>
        </div>

        {/* Navigation */}
        <nav className="space-y-2 flex-1">
          {navItems.map((item) => (
            <motion.button
              key={item.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center space-x-3 p-3 rounded-xl glass transition-all ${
                activeTab === item.id ? 'bg-purple-600/20 border-purple-500/50' : 'hover:bg-white/5'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
              {activeTab === item.id && (
                <ChevronRightIcon className="w-4 h-4 ml-auto" />
              )}
            </motion.button>
          ))}
        </nav>

        {/* Connection Status */}
        <div className={`glass p-4 rounded-xl ${connected ? 'border-green-500/30' : 'border-red-500/30'}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm">Backend</span>
            {connected ? (
              <span className="flex items-center text-green-400 text-sm">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                Connected
              </span>
            ) : (
              <span className="flex items-center text-red-400 text-sm">
                <WifiOffIcon className="w-4 h-4 mr-1" />
                Offline
              </span>
            )}
          </div>
        </div>

        {/* User Profile */}
        <div className="glass p-4 rounded-xl mt-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center">
              <UserCircleIcon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium">Premium User</p>
              <p className="text-xs text-gray-400">Unlimited typing</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {activeTab === 'typing' && (
            <motion.div
              key="typing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="h-full p-8 overflow-y-auto custom-scrollbar"
            >
              {/* Status Bar */}
              <motion.div 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass p-4 rounded-2xl mb-6"
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center space-x-4">
                    <div className={`w-3 h-3 rounded-full ${
                      isTyping ? 'bg-green-400 animate-pulse' : 'bg-gray-400'
                    }`} />
                    <span className="font-medium">{typingStatus}</span>
                  </div>
                  <div className="flex space-x-8 text-sm">
                    <span>Progress: <span className="text-purple-400 font-bold">{Math.round(progress)}%</span></span>
                    <span>WPM: <span className="text-blue-400 font-bold">{wpm}</span></span>
                    <span>Words: <span className="text-green-400 font-bold">{inputText.split(' ').length}</span></span>
                  </div>
                </div>
                
                {/* Progress Bar */}
                <div className="mt-4 h-1.5 bg-black/30 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </motion.div>

              {/* Main Typing Area */}
              <div className="grid grid-cols-2 gap-6 mb-6">
                {/* Input Section */}
                <motion.div 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="glass p-6 rounded-2xl"
                >
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-semibold flex items-center">
                      <FileTextIcon className="w-5 h-5 mr-2" />
                      Input Text
                    </h2>
                    <div className="flex space-x-2">
                      <button className="p-2 glass rounded-lg hover:bg-white/10">
                        <CopyIcon className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => setInputText('')}
                        className="p-2 glass rounded-lg hover:bg-white/10"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <textarea 
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    className="w-full h-72 bg-black/20 rounded-xl p-4 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none custom-scrollbar"
                    placeholder="Start typing or paste your text here..."
                    disabled={isTyping}
                  />
                  <div className="mt-4 flex justify-between text-sm text-gray-400">
                    <span>Characters: {inputText.length}</span>
                    <span>Words: {inputText.split(/\s+/).filter(Boolean).length}</span>
                  </div>
                </motion.div>

                {/* Preview Section */}
                <motion.div 
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="glass p-6 rounded-2xl"
                >
                  <h2 className="text-lg font-semibold mb-4 flex items-center">
                    <span className="mr-2">👁️</span>
                    Live Preview
                  </h2>
                  <div className="w-full h-72 bg-black/20 rounded-xl p-4 overflow-y-auto custom-scrollbar">
                    {previewText ? (
                      <motion.p 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-gray-100 whitespace-pre-wrap"
                      >
                        {previewText}
                        <span className="animate-pulse">|</span>
                      </motion.p>
                    ) : (
                      <p className="text-gray-500">Preview will appear here as you type...</p>
                    )}
                  </div>
                  <div className="mt-4">
                    <div className="text-sm text-gray-400 mb-2">Typing Progress</div>
                    <div className="flex space-x-2">
                      {[...Array(10)].map((_, i) => (
                        <div 
                          key={i}
                          className={`h-2 flex-1 rounded-full transition-all ${
                            i < Math.floor(progress / 10) 
                              ? 'bg-gradient-to-r from-purple-500 to-blue-500' 
                              : 'bg-black/20'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                </motion.div>
              </div>

              {/* Controls */}
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass p-6 rounded-2xl"
              >
                <div className="flex justify-between items-center">
                  {/* Action Buttons */}
                  <div className="flex space-x-3">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={startTyping}
                      disabled={isTyping || !inputText.trim() || !connected}
                      className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <PlayIcon className="w-5 h-5" />
                      <span>Start Typing</span>
                    </motion.button>
                    
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={pauseTyping}
                      disabled={!isTyping}
                      className="btn-secondary flex items-center space-x-2 disabled:opacity-50"
                    >
                      <PauseIcon className="w-5 h-5" />
                      <span>{isPaused ? 'Resume' : 'Pause'}</span>
                    </motion.button>
                    
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={stopTyping}
                      disabled={!isTyping}
                      className="btn-danger flex items-center space-x-2 disabled:opacity-50"
                    >
                      <StopCircleIcon className="w-5 h-5" />
                      <span>Stop</span>
                    </motion.button>
                  </div>

                  {/* Settings Controls */}
                  <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-3">
                      <span className="text-sm text-gray-400">Speed:</span>
                      <input 
                        type="range" 
                        min="1" 
                        max="10" 
                        value={(0.5 - settings.maxDelay) * 20}
                        onChange={(e) => {
                          const speed = parseInt(e.target.value)
                          setSettings({
                            ...settings,
                            maxDelay: 0.5 - (speed * 0.05)
                          })
                        }}
                        className="w-32"
                        disabled={isTyping}
                      />
                      <span className="text-sm font-bold w-8">{Math.round((0.5 - settings.maxDelay) * 20)}</span>
                    </div>

                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input 
                        type="checkbox"
                        checked={settings.typosEnabled}
                        onChange={(e) => setSettings({...settings, typosEnabled: e.target.checked})}
                        disabled={isTyping}
                        className="w-4 h-4 rounded"
                      />
                      <span className="text-sm">Typos</span>
                    </label>

                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input 
                        type="checkbox"
                        checked={settings.aiFiller}
                        onChange={(e) => setSettings({...settings, aiFiller: e.target.checked})}
                        disabled={isTyping}
                        className="w-4 h-4 rounded"
                      />
                      <span className="text-sm flex items-center">
                        <SparklesIcon className="w-4 h-4 mr-1" />
                        AI Filler
                      </span>
                      <span className="text-xs px-2 py-0.5 bg-purple-500/30 rounded-full ml-1">PRO</span>
                    </label>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}

          {activeTab !== 'typing' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="h-full flex items-center justify-center"
            >
              <div className="text-center">
                <div className="text-6xl mb-4">🚧</div>
                <h2 className="text-2xl font-bold mb-2">Coming Soon</h2>
                <p className="text-gray-400">This section is under development</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}