'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Toaster, toast } from 'react-hot-toast'
import axios from 'axios'
import { 
  KeyboardIcon, BrainIcon, BarChart3Icon, SettingsIcon,
  ChevronRightIcon, WifiIcon, WifiOffIcon, ZapIcon, 
  BookOpenIcon, LayersIcon, HeartIcon,
  CrownIcon, GiftIcon, SparklesIcon, UserIcon
} from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://slywriterapp.onrender.com'

export default function Page() {
  const [activeTab, setActiveTab] = useState('typing')
  const [connected, setConnected] = useState(false)
  const [showOverlay, setShowOverlay] = useState(false)
  const [text, setText] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  // Check backend connection
  useEffect(() => {
    const checkConnection = async () => {
      try {
        await axios.get(`${API_URL}/api/health`)
        setConnected(true)
      } catch {
        setConnected(false)
      }
    }
    
    checkConnection()
    const interval = setInterval(checkConnection, 5000)
    return () => clearInterval(interval)
  }, [])

  const navItems = [
    { id: 'typing', label: 'Auto-Type', icon: KeyboardIcon, description: 'Types for you', badge: 'MAIN' },
    { id: 'humanizer', label: 'AI Humanizer', icon: SparklesIcon, description: 'Natural typing', badge: 'HOT' },
    { id: 'ai-hub', label: 'AI Writer', icon: BrainIcon, description: 'Generate essays' },
    { id: 'hotkeys', label: 'Hotkeys', icon: KeyboardIcon, description: 'Configure shortcuts' },
    { id: 'learning', label: 'Smart Learn', icon: BookOpenIcon, description: 'AI explains topics' },
    { id: 'statistics', label: 'Analytics', icon: BarChart3Icon, description: 'Track usage' },
    { id: 'mission', label: 'Mission', icon: HeartIcon, description: 'Our cause & rewards', badge: 'NEW' },
    { id: 'settings', label: 'Settings', icon: SettingsIcon, description: 'Customize' },
  ]

  const handleStartTyping = () => {
    if (!text.trim()) {
      toast.error('Please enter some text to type')
      return
    }
    setIsTyping(true)
    toast.success('Typing started!')
    // Simulate typing
    setTimeout(() => {
      setIsTyping(false)
      toast.success('Typing completed!')
    }, 3000)
  }

  return (
    <>
      <style jsx global>{`
        body {
          margin: 0;
          padding: 0;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
        }
      `}</style>
      
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
        {/* Animated background */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '2s' }} />
          <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '4s' }} />
        </div>

        <div className="relative flex h-screen">
          {/* Sidebar */}
          <motion.aside 
            initial={{ x: -100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="w-72 bg-black/40 backdrop-blur-2xl border-r border-white/10 flex flex-col"
          >
            {/* Logo */}
            <div className="p-6 border-b border-white/10">
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="flex items-center gap-3"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center shadow-lg relative">
                  <ZapIcon className="w-7 h-7 text-white" />
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                    SlyWriter
                  </h1>
                  <p className="text-xs text-gray-400">AI Types For You • Undetectable</p>
                </div>
              </motion.div>
            </div>

            {/* User Section */}
            <div className="px-6 py-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  <UserIcon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">Guest User</p>
                  <p className="text-xs text-gray-400">Free Plan</p>
                </div>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
              {navItems.map((item, index) => {
                const Icon = item.icon
                return (
                  <motion.button
                    key={item.id}
                    initial={{ x: -50, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                    whileHover={{ x: 4 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setActiveTab(item.id)}
                    className={`
                      w-full flex items-center gap-3 px-4 py-3 rounded-xl
                      transition-all duration-200 group relative overflow-hidden
                      ${activeTab === item.id 
                        ? 'bg-purple-500/20 text-white shadow-lg' 
                        : 'hover:bg-purple-500/10 text-gray-400 hover:text-white'
                      }
                    `}
                  >
                    {activeTab === item.id && (
                      <motion.div
                        layoutId="nav-indicator"
                        className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-xl"
                      />
                    )}
                    <Icon className={`w-5 h-5 relative z-10 flex-shrink-0 ${
                      activeTab === item.id ? 'text-purple-400' : ''
                    }`} />
                    <div className="flex-1 relative z-10">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{item.label}</span>
                        {item.badge && (
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                            item.badge === 'HOT' ? 'bg-red-500/20 text-red-400' :
                            item.badge === 'MAIN' ? 'bg-purple-500/20 text-purple-400' :
                            item.badge === 'NEW' ? 'bg-blue-500/20 text-blue-400' :
                            'bg-gray-500/20 text-gray-400'
                          }`}>
                            {item.badge}
                          </span>
                        )}
                      </div>
                      {item.description && (
                        <div className="text-xs text-gray-400 mt-0.5">{item.description}</div>
                      )}
                    </div>
                    {activeTab === item.id && (
                      <ChevronRightIcon className="w-4 h-4 ml-auto relative z-10" />
                    )}
                  </motion.button>
                )
              })}
            </nav>

            {/* Footer */}
            <div className="p-6 border-t border-white/10 space-y-4">
              {/* Connection Status */}
              <motion.div 
                animate={{ scale: connected ? 1 : [1, 1.05, 1] }}
                transition={{ repeat: connected ? 0 : Infinity, duration: 2 }}
                className={`
                  flex items-center justify-between px-4 py-3 rounded-xl
                  ${connected 
                    ? 'bg-green-500/10 border border-green-500/20' 
                    : 'bg-red-500/10 border border-red-500/20'
                  }
                `}
              >
                <span className="text-xs font-medium text-gray-300">Backend</span>
                <div className="flex items-center gap-2">
                  {connected ? (
                    <>
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                      <span className="text-xs font-medium text-green-400">Online</span>
                    </>
                  ) : (
                    <>
                      <WifiOffIcon className="w-4 h-4 text-red-400" />
                      <span className="text-xs font-medium text-red-400">Offline</span>
                    </>
                  )}
                </div>
              </motion.div>
              
              {/* Upgrade Banner */}
              <div className="bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-900/20 backdrop-blur rounded-full flex items-center justify-center">
                    <CrownIcon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">Go Premium</p>
                    <p className="text-xs text-white/70">Unlimited AI automation</p>
                  </div>
                </div>
              </div>
            </div>
          </motion.aside>

          {/* Main Content */}
          <main className="flex-1 overflow-hidden">
            <AnimatePresence mode="wait">
              {activeTab === 'typing' && (
                <motion.div
                  key="typing"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="h-full overflow-y-auto p-8"
                >
                  <div className="max-w-4xl mx-auto">
                    <h2 className="text-3xl font-bold text-white mb-6">Auto-Type</h2>
                    <p className="text-gray-300 mb-8">AI-powered typing automation</p>
                    
                    <div className="bg-black/20 backdrop-blur rounded-xl p-6 mb-6">
                      <div className="flex justify-between items-center mb-4">
                        <span className="text-sm text-gray-400">
                          {connected ? '✅ Connected' : '❌ Disconnected'}
                        </span>
                        <span className="text-sm text-gray-400">
                          {text.length} chars | {text.split(/\s+/).filter(w => w).length} words
                        </span>
                      </div>
                      
                      <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Enter or paste your text here..."
                        className="w-full h-64 bg-gray-900/50 text-white rounded-lg p-4 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                        disabled={isTyping}
                      />
                      
                      <button
                        onClick={handleStartTyping}
                        disabled={isTyping || !text.trim()}
                        className={`
                          w-full mt-4 py-3 rounded-lg font-medium transition-all
                          ${isTyping || !text.trim()
                            ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                            : 'bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600'
                          }
                        `}
                      >
                        {isTyping ? 'Typing...' : 'Start Typing (Ctrl+Shift+S)'}
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
              
              {activeTab !== 'typing' && (
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="h-full overflow-y-auto p-8"
                >
                  <div className="max-w-4xl mx-auto">
                    <h2 className="text-3xl font-bold text-white mb-6 capitalize">{activeTab}</h2>
                    <div className="bg-black/20 backdrop-blur rounded-xl p-8">
                      <p className="text-gray-300">
                        This is the {activeTab} section. Content coming soon...
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </main>
        </div>
      </div>
      
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1f2937',
            color: '#fff',
            border: '1px solid rgba(139, 92, 246, 0.3)',
          },
        }}
      />
    </>
  )
}