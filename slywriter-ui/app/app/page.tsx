'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Toaster } from 'react-hot-toast'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { AuthProvider } from '../context/AuthContext'
import { ThemeProvider } from '../context/ThemeContext'
import { ThemeToggleCompact } from '../components/ThemeToggle'
import GoogleLoginEnhanced from '../components/GoogleLoginEnhanced'
import TypingTabModern from '../components/TypingTabModern'
import AIHubTab from '../components/AIHubTab'
import StatisticsTab from '../components/StatisticsTab'
import SettingsTabComplete from '../components/SettingsTabComplete'
import LearningTabEnhanced from '../components/LearningTabEnhanced'
import OverlayWindowOptimized from '../components/OverlayWindowOptimized'
import HumanizerTab from '../components/HumanizerTab'
import HotkeysTabEnhanced from '../components/HotkeysTabEnhanced'
import EnhancedOverlay from '../components/EnhancedOverlay'
import GlobalHotkeys from '../components/GlobalHotkeys'
import OnboardingFlow from '../components/OnboardingFlow'
import MissionTab from '../components/MissionTab'
import axios from 'axios'
import { 
  KeyboardIcon, BrainIcon, BarChart3Icon, SettingsIcon,
  ChevronRightIcon, WifiIcon, WifiOffIcon, ZapIcon, 
  AwardIcon, BookOpenIcon, GaugeIcon, LayersIcon,
  CrownIcon, GiftIcon, SparklesIcon, HeartIcon
} from 'lucide-react'

const API_URL = 'http://localhost:8000'

function SlyWriterAppInner() {
  const [activeTab, setActiveTab] = useState('typing')
  const [connected, setConnected] = useState(false)
  const [showOverlay, setShowOverlay] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(true)
  const [selectedProfile, setSelectedProfile] = useState<string>('Medium')
  const [triggerWpmTest, setTriggerWpmTest] = useState(false)
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
    { id: 'humanizer', label: 'AI Humanizer', icon: SparklesIcon, color: 'from-purple-400 to-pink-400', description: 'Natural typing', badge: 'HOT' },
    { id: 'ai-hub', label: 'AI Writer', icon: BrainIcon, color: 'from-pink-400 to-red-400', description: 'Generate essays' },
    { id: 'hotkeys', label: 'Hotkeys', icon: KeyboardIcon, color: 'from-orange-400 to-red-400', description: 'Configure shortcuts' },
    { id: 'learning', label: 'Smart Learn', icon: BookOpenIcon, color: 'from-green-400 to-blue-400', description: 'AI explains topics' },
    { id: 'statistics', label: 'Analytics', icon: BarChart3Icon, color: 'from-blue-400 to-purple-400', description: 'Track usage' },
    { id: 'mission', label: 'Mission', icon: HeartIcon, color: 'from-red-400 to-pink-400', description: 'Our cause & rewards', badge: 'NEW' },
    { id: 'settings', label: 'Settings', icon: SettingsIcon, color: 'from-indigo-400 to-purple-400', description: 'Customize' },
  ]

  return (
    <div className="min-h-screen transition-colors duration-500 bg-black bg-gray-900">
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-600 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 opacity-10 animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 opacity-10 animate-pulse animation-delay-2000" />
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-purple-700 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 opacity-10 animate-pulse animation-delay-4000" />
      </div>

      <div className="relative flex h-screen">
        {/* Sidebar */}
        <motion.aside 
          initial={{ x: -100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="w-72 bg-black/40 bg-gray-900/95 backdrop-blur-2xl border-r border-white/10 border-purple-500/20 flex flex-col"
        >
          {/* Logo */}
          <div className="p-6 border-b border-white/10 border-purple-500/20">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 bg-purple-500 flex items-center justify-center shadow-lg relative">
                <ZapIcon className="w-7 h-7 text-white" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent text-white">
                  SlyWriter
                </h1>
                <p className="text-xs text-gray-400">AI Types For You • Undetectable</p>
              </div>
              </div>
              <ThemeToggleCompact />
            </motion.div>
          </div>

          {/* User Section */}
          <div className="px-6 py-4 border-b border-white/10 border-purple-500/20">
            <GoogleLoginEnhanced />
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
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
                        ? 'bg-gray-900/10 bg-purple-500/10 text-white text-purple-400 shadow-lg' 
                        : 'hover:bg-gray-900/5 hover:bg-purple-500/10 text-gray-400 hover:text-white hover:text-purple-400'
                      }
                    `}
                  >
                    {activeTab === item.id && (
                      <motion.div
                        layoutId="nav-indicator"
                        className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-blue-500/20 bg-purple-500/10 rounded-xl"
                      />
                    )}
                    <Icon className={`w-5 h-5 relative z-10 flex-shrink-0 ${
                      activeTab === item.id ? 'text-purple-400' : ''
                    }`} />
                    <div className="flex-1 relative z-10">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-inherit text-white">{item.label}</span>
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
            <div className="mt-6 pt-6 border-t border-white/10 border-purple-500/20">
              <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-3 px-2">Premium Features</h3>
              
              <button
                onClick={() => setShowOverlay(!showOverlay)}
                className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-900/5 hover:bg-purple-500/10 text-gray-400 hover:text-white hover:text-purple-400 transition-all"
              >
                <LayersIcon className="w-4 h-4" />
                <span className="text-sm">Overlay Window</span>
                <span className={`ml-auto w-2 h-2 rounded-full ${showOverlay ? 'bg-green-400' : 'bg-gray-600 bg-gray-800'}`} />
              </button>

              <button className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-900/5 hover:bg-purple-500/10 text-gray-400 hover:text-white hover:text-purple-400 transition-all">
                <GiftIcon className="w-4 h-4" />
                <span className="text-sm">Referral Program</span>
              </button>
            </div>
          </nav>

          {/* Footer */}
          <div className="p-6 border-t border-white/10 border-purple-500/20 space-y-4">
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
            <div className="bg-gradient-to-r from-purple-500 to-blue-500 bg-purple-500 rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-900/20 bg-gray-900/90 backdrop-blur rounded-full flex items-center justify-center">
                  <CrownIcon className="w-6 h-6 text-white text-purple-400" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">Go Premium</p>
                  <p className="text-xs text-white/70 text-white/90">Unlimited AI automation</p>
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
                <TypingTabModern 
                  connected={connected} 
                  initialProfile={selectedProfile}
                  shouldOpenWpmTest={triggerWpmTest}
                  onWpmTestOpened={() => setTriggerWpmTest(false)}
                />
              </motion.div>
            )}
            
            {activeTab === 'hotkeys' && (
              <motion.div
                key="hotkeys"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="h-full overflow-y-auto p-8"
              >
                <HotkeysTabEnhanced />
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
                <HumanizerTab />
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
                <LearningTabEnhanced />
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
                <SettingsTabComplete />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>

      {/* Onboarding Flow */}
      <OnboardingFlow
        isVisible={showOnboarding}
        onComplete={(profile, triggerTest) => {
          setShowOnboarding(false)
          if (profile) {
            setSelectedProfile(profile)
          }
          if (triggerTest) {
            setTriggerWpmTest(true)
          }
        }}
      />
      
      {/* Global Hotkeys */}
      <GlobalHotkeys />
      
      {/* Overlay Window */}
      <OverlayWindowOptimized
        isVisible={showOverlay}
        onClose={() => setShowOverlay(false)}
      />
    </div>
  )
}

function SlyWriterApp() {
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''
  
  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <ThemeProvider>
        <AuthProvider>
          <SlyWriterAppInner />
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              className: 'bg-gray-900 text-white border-purple-500/30 border',
            }}
          />
        </AuthProvider>
      </ThemeProvider>
    </GoogleOAuthProvider>
  )
}

export default function Page() {
  return <SlyWriterApp />
}