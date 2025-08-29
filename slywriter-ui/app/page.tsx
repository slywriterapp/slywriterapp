'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Toaster } from 'react-hot-toast'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { AuthProvider } from './context/AuthContext'
import GoogleLogin from './components/GoogleLogin'
import TypingTabWithWPM from './components/TypingTabWithWPM'
import AIHubTab from './components/AIHubTab'
import StatisticsTab from './components/StatisticsTab'
import SettingsTabComplete from './components/SettingsTabComplete'
import LearningHub from './components/LearningHub'
import OverlayWindowEnhanced from './components/OverlayWindowEnhanced'
import HumanizerTabSimple from './components/HumanizerTabSimple'
import MissionTab from './components/MissionTab'
import GlobalHotkeys from './components/GlobalHotkeys'
import OnboardingFlow from './components/OnboardingFlow'
import axios from 'axios'
import { 
  KeyboardIcon, BrainIcon, BarChart3Icon, SettingsIcon,
  ChevronRightIcon, WifiIcon, WifiOffIcon, ZapIcon, 
  AwardIcon, BookOpenIcon, GaugeIcon, LayersIcon,
  CrownIcon, GiftIcon, SparklesIcon
} from 'lucide-react'

const API_URL = 'https://slywriterapp.onrender.com'

function SlyWriterApp() {
  const [activeTab, setActiveTab] = useState('typing')
  const [connected, setConnected] = useState(false)
  const [showOverlay, setShowOverlay] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(true)
  const [typingStatus, setTypingStatus] = useState({
    isTyping: false,
    status: 'Ready',
    wpm: 0,
    progress: 0
  })

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
    { id: 'typing', label: 'Auto-Type', icon: KeyboardIcon, color: 'from-purple-500 to-blue-500', description: 'Types for you', badge: 'MAIN' },
    { id: 'humanizer', label: 'AI Humanizer', icon: SparklesIcon, color: 'from-purple-400 to-pink-400', description: 'Bypass AI detectors', badge: 'HOT' },
    { id: 'ai-hub', label: 'AI Writer', icon: BrainIcon, color: 'from-pink-400 to-red-400', description: 'Generate essays' },
    { id: 'learning', label: 'Smart Learn', icon: BookOpenIcon, color: 'from-green-400 to-blue-400', description: 'AI explains topics' },
    { id: 'statistics', label: 'Analytics', icon: BarChart3Icon, color: 'from-blue-400 to-purple-400', description: 'Track usage' },
    { id: 'mission', label: 'Mission', icon: AwardIcon, color: 'from-yellow-400 to-orange-400', description: 'Our cause & rewards', badge: 'NEW' },
    { id: 'settings', label: 'Settings', icon: SettingsIcon, color: 'from-indigo-400 to-purple-400', description: 'Customize' },
  ]

  return (
    <div className="min-h-screen bg-black">
      {/* Purple wave effects around the edges */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Top purple wave */}
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[200%] h-64 bg-purple-600/20 blur-[100px] animate-pulse" />
        {/* Bottom purple wave */}
        <div className="absolute -bottom-32 left-1/2 -translate-x-1/2 w-[200%] h-64 bg-purple-600/20 blur-[100px] animate-pulse animation-delay-2000" />
        {/* Left purple accent */}
        <div className="absolute top-1/2 -left-32 -translate-y-1/2 w-64 h-[200%] bg-purple-500/15 blur-[80px] animate-pulse animation-delay-4000" />
        {/* Right purple accent */}
        <div className="absolute top-1/2 -right-32 -translate-y-1/2 w-64 h-[200%] bg-purple-500/15 blur-[80px] animate-pulse" />
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
            <GoogleLogin />
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            <AnimatePresence>
              {navItems.map((item, index) => {
                const Icon = item.icon
                return (
                  <motion.button
                    key={item.id}
                    data-tab={item.id}
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
                            'bg-blue-500/20 text-blue-400'
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
            </AnimatePresence>

            {/* Premium Features Section */}
            <div className="mt-6 pt-6 border-t border-white/10">
              <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-3 px-2">Premium Features</h3>
              
              <button
                onClick={() => setShowOverlay(!showOverlay)}
                className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-900/5 text-gray-400 hover:text-white transition-all"
              >
                <LayersIcon className="w-4 h-4" />
                <span className="text-sm">Overlay Window</span>
                <span className={`ml-auto w-2 h-2 rounded-full ${showOverlay ? 'bg-green-400' : 'bg-gray-600'}`} />
              </button>

              <button className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-900/5 text-gray-400 hover:text-white transition-all">
                <GiftIcon className="w-4 h-4" />
                <span className="text-sm">Referral Program</span>
              </button>
            </div>
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
                <TypingTabWithWPM connected={connected} />
              </motion.div>
            )}
            
            {activeTab === 'humanizer' && (
              <motion.div
                key="humanizer"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="h-full overflow-y-auto p-8"
              >
                <HumanizerTabSimple />
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
            
            {activeTab === 'learning' && (
              <motion.div
                key="learning"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="h-full overflow-y-auto p-8"
              >
                <LearningHub />
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
            
            {activeTab === 'mission' && (
              <motion.div
                key="mission"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="h-full overflow-y-auto p-8"
              >
                <MissionTab />
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
                <SettingsTabComplete />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>

      {/* Onboarding Flow */}
      <OnboardingFlow
        isVisible={showOnboarding}
        onComplete={() => setShowOnboarding(false)}
      />
      
      {/* Global Hotkeys */}
      <GlobalHotkeys />
      
      {/* Overlay Window */}
      <OverlayWindowEnhanced
        isVisible={showOverlay}
        onClose={() => setShowOverlay(false)}
      />
    </div>
  )
}

export default function Page() {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '670659562469-i3i49sdl2b7qdp8jsh5dp7upb0g6k9kk.apps.googleusercontent.com'
  
  return (
    <GoogleOAuthProvider clientId={clientId}>
      <AuthProvider>
        <SlyWriterApp />
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
      </AuthProvider>
    </GoogleOAuthProvider>
  )
}