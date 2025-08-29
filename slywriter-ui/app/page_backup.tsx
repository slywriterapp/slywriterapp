'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  SparklesIcon, KeyboardIcon, BarChart3Icon,
  SettingsIcon, ChevronRightIcon,
  WifiIcon, WifiOffIcon, ZapIcon, AwardIcon, BrainIcon
} from 'lucide-react'
import TypingTab from './components/TypingTab'
import AIHubTab from './components/AIHubTab'
import StatisticsTab from './components/StatisticsTab'
import SettingsTab from './components/SettingsTab'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

export default function SlyWriterApp() {
  const [activeTab, setActiveTab] = useState('typing')
  const [connected, setConnected] = useState(false)

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
    { id: 'typing', label: 'Typing', icon: KeyboardIcon, color: 'from-purple-500 to-blue-500' },
    { id: 'ai-hub', label: 'AI Hub', icon: BrainIcon, color: 'from-purple-400 to-pink-400' },
    { id: 'statistics', label: 'Statistics', icon: BarChart3Icon, color: 'from-blue-400 to-purple-400' },
    { id: 'settings', label: 'Settings', icon: SettingsIcon, color: 'from-indigo-400 to-purple-400' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Animated background particles */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse animation-delay-2000" />
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse animation-delay-4000" />
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
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center shadow-lg">
                <ZapIcon className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                  SlyWriter
                </h1>
                <p className="text-xs text-gray-400">Premium Typing Assistant</p>
              </div>
            </motion.div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            <AnimatePresence>
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
                        ? 'bg-gray-900/10 text-white shadow-lg' 
                        : 'hover:bg-gray-900/5 text-gray-400 hover:text-white'
                      }
                    `}
                  >
                    {activeTab === item.id && (
                      <motion.div
                        layoutId="nav-indicator"
                        className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-xl"
                      />
                    )}
                    <Icon className={`w-5 h-5 relative z-10 ${
                      activeTab === item.id ? 'text-purple-400' : ''
                    }`} />
                    <span className="text-sm font-medium relative z-10">{item.label}</span>
                    {activeTab === item.id && (
                      <ChevronRightIcon className="w-4 h-4 ml-auto relative z-10" />
                    )}
                  </motion.button>
                )
              })}
            </AnimatePresence>
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
            
            {/* User Badge */}
            <div className="bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-900/20 backdrop-blur rounded-full flex items-center justify-center">
                  <AwardIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">Premium Plan</p>
                  <p className="text-xs text-white/70">Unlimited Access</p>
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
                <TypingTab connected={connected} />
              </motion.div>
            )}
            
            {activeTab === 'ai-hub' && (
              <motion.div
                key="ai-hub"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="h-full overflow-y-auto p-8"
              >
                <AIHubTab />
              </motion.div>
            )}
            
            {activeTab === 'statistics' && (
              <motion.div
                key="statistics"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="h-full overflow-y-auto p-8"
              >
                <StatisticsTab />
              </motion.div>
            )}
            
            {activeTab === 'settings' && (
              <motion.div
                key="settings"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="h-full overflow-y-auto p-8"
              >
                <SettingsTab />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}