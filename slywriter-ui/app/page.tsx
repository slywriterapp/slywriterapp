'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Toaster } from 'react-hot-toast'
import { toast } from '@/lib/toast'
import { LocalStorageMonitor } from './utils/localStorage-monitor'
import { AuthProvider } from './context/AuthContext'
import UserDashboard from './components/UserDashboard'
import TypingTabWithWPM from './components/TypingTabWithWPM'
import AIHubTab from './components/AIHubTab'
import StatisticsTab from './components/StatisticsTab'
import SettingsTabComplete from './components/SettingsTabComplete'
import EnhancedLearningTab from './components/EnhancedLearningTab'
// Old overlay removed - using Electron overlay only
import HumanizerTab from './components/HumanizerTab'
import MissionTab from './components/MissionTab'
import GlobalHotkeys from './components/GlobalHotkeys'
import GlobalHotkeyListener from './components/GlobalHotkeyListener'
import OnboardingFlow from './components/OnboardingFlow'
import SplashScreen from './components/SplashScreen'
import BetaDisclosure from './components/BetaDisclosure'
import UserProfile from './components/UserProfile'
import axios from 'axios'
import { 
  KeyboardIcon, BrainIcon, BarChart3Icon, SettingsIcon,
  ChevronRightIcon, WifiIcon, WifiOffIcon, ZapIcon, 
  AwardIcon, BookOpenIcon, GaugeIcon, LayersIcon,
  CrownIcon, GiftIcon, SparklesIcon
} from 'lucide-react'

// Use local server in development, Render in production
const API_URL = typeof window !== 'undefined' && window.location.hostname === 'localhost' 
  ? 'http://localhost:5000' 
  : 'https://slywriterapp.onrender.com'

function SlyWriterApp() {
  const [activeTab, setActiveTab] = useState('typing')
  const activeTabRef = useRef(activeTab)
  const [connected, setConnected] = useState(false)
  const [overlayVisible, setOverlayVisible] = useState(false)
  const [aiReviewData, setAiReviewData] = useState<any>(null)
  const aiReviewHandlerRef = useRef<(data: any) => void>(() => {})
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const [showDashboard, setShowDashboard] = useState(false)
  
  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      console.log('=== MAIN PAGE AUTH CHECK START ===')
      console.log('[MAIN-1] Current URL:', window.location.href)
      console.log('[MAIN-2] Referrer:', document.referrer)
      console.log('[MAIN-3] Query params:', window.location.search)
      console.log('[MAIN-4] Hash:', window.location.hash)
      console.log('[MAIN-4.1] Window.electron exists?', !!(window as any).electron)
      console.log('[MAIN-4.2] Current time:', new Date().toISOString())
      console.log('[MAIN-4.3] Document ready state:', document.readyState)

      // Start localStorage monitoring
      LocalStorageMonitor.start()
      console.log('[MAIN-5] Initial localStorage state:')
      console.log('[MAIN-5.1] localStorage length:', localStorage.length)
      console.log('[MAIN-5.2] All localStorage keys:', Object.keys(localStorage))
      LocalStorageMonitor.logCurrentState()

      try {
        // IMMEDIATE synchronous check - no delays first
        console.log('[MAIN-5.3] SYNCHRONOUS AUTH CHECK')
        const immediateToken = localStorage.getItem('auth_token')
        const immediateUserData = localStorage.getItem('user_data')
        console.log('[MAIN-5.4] Immediate token exists:', !!immediateToken)
        console.log('[MAIN-5.5] Immediate user data exists:', !!immediateUserData)

        if (immediateToken && immediateUserData) {
          // Found auth immediately - set state and return
          console.log('[MAIN-5.6] ✅ IMMEDIATE AUTH SUCCESS - Setting authenticated true')
          setIsAuthenticated(true)
          setIsCheckingAuth(false)
          console.log('[MAIN-5.7] States set, returning early')
          console.log('=== MAIN PAGE AUTH CHECK END (IMMEDIATE SUCCESS) ===')
          return
        }

        // Check if we're coming from login page
        const referrer = document.referrer
        const isFromLogin = referrer && (referrer.includes('/login') || referrer.includes('slywriter-ui.onrender.com'))

        if (isFromLogin) {
          console.log('[MAIN-5.8] Coming from login, waiting for auth to settle...')
          await new Promise(resolve => setTimeout(resolve, 1000)) // Increased wait time
        } else {
          // Not from login, still give a small delay for localStorage
          console.log('[MAIN-6] Waiting 200ms before secondary auth check...')
          await new Promise(resolve => setTimeout(resolve, 200))
        }

        console.log('[MAIN-7] After wait - checking localStorage again:')
        LocalStorageMonitor.logCurrentState()

        // Secondary check after delay
        console.log('[MAIN-7.5] Secondary localStorage check...')
        const token = localStorage.getItem('auth_token')
        const userData = localStorage.getItem('user_data')
        console.log('[MAIN-7.6] Read complete. Token type:', typeof token, 'UserData type:', typeof userData)

        console.log('[MAIN-8] localStorage check results:')
        console.log('  - Token exists:', !!token)
        console.log('  - User data exists:', !!userData)
        if (token) {
          console.log('  - Token preview:', token.substring(0, 20) + '...')
          console.log('  - Token length:', token.length)
        }
        if (userData) {
          try {
            const parsed = JSON.parse(userData)
            console.log('  - User email:', parsed.email)
            console.log('  - User ID:', parsed.user_id)
          } catch (e) {
            console.log('  - Failed to parse user data:', e)
          }
        }

        if (token && userData) {
          // We have auth data, set authenticated immediately
          console.log('[MAIN-9] ✅ Authentication successful - token found on secondary check!')
          console.log('[MAIN-10] Setting isAuthenticated to true')
          setIsAuthenticated(true)
          setIsCheckingAuth(false)
          console.log('[MAIN-10.3] States set successfully')
          console.log('=== MAIN PAGE AUTH CHECK END (SECONDARY SUCCESS) ===')

          // Then check with Electron for additional validation if available
          if (typeof window !== 'undefined' && (window as any).electron) {
            const result = await (window as any).electron.ipcRenderer.invoke('check-auth')
            console.log('Electron auth check result:', result)
            // Don't redirect even if Electron says not authenticated - trust localStorage
          }

          return // Exit early, we're authenticated
        }
        
        // Final retry for login redirects
        if (isFromLogin) {
          console.log('[MAIN-11] Final retry for login redirect...')
          await new Promise(resolve => setTimeout(resolve, 500))

          const retryToken = localStorage.getItem('auth_token')
          const retryUserData = localStorage.getItem('user_data')

          if (retryToken && retryUserData) {
            console.log('[MAIN-11.1] ✅ Found auth on final retry!')
            setIsAuthenticated(true)
            setIsCheckingAuth(false)
            console.log('=== MAIN PAGE AUTH CHECK END (RETRY SUCCESS) ===')
            return
          }
          console.log('[MAIN-11.2] ❌ No auth found on final retry')
        }
        
        // No token in localStorage, check Electron
        console.log('[MAIN-12] No token found in localStorage after all retries')
        console.log('[MAIN-13] All localStorage keys:', Object.keys(localStorage))
        
        if (typeof window !== 'undefined' && (window as any).electron) {
          console.log('[MAIN-14] Checking Electron auth...')
          const result = await (window as any).electron.ipcRenderer.invoke('check-auth')
          console.log('[MAIN-15] Electron auth check result:', result)

          if (result.authenticated) {
            console.log('[MAIN-16] Electron has auth, setting authenticated')
            setIsAuthenticated(true)
            setIsCheckingAuth(false)
            console.log('=== MAIN PAGE AUTH CHECK END (ELECTRON SUCCESS) ===')
            return
          } else {
            // No auth anywhere, redirect to login (with loop protection)
            const urlParams = new URLSearchParams(window.location.search)
            const redirectCount = parseInt(urlParams.get('auth_attempt') || '0')

            if (redirectCount >= 2) {
              console.log('[MAIN-17] Redirect loop detected! Staying on page without auth')
              console.log('[MAIN-17.1] This prevents infinite loops')
              setIsAuthenticated(false)
              setIsCheckingAuth(false)
            } else {
              console.log('[MAIN-18] No auth in Electron either, redirecting to login...')
              console.log('[MAIN-18.1] Redirect attempt:', redirectCount + 1)
              setIsCheckingAuth(false) // Set this before redirect
              console.log('=== MAIN PAGE AUTH CHECK END (REDIRECT TO LOGIN) ===')
              window.location.href = `${window.location.origin}/login?from=main&auth_attempt=${redirectCount + 1}`
            }
          }
        } else {
          // Browser environment, no Electron
          // No token found, redirect to login
          console.log('[MAIN-19] Browser environment (no Electron)')
          console.log('[MAIN-20] No auth found, redirecting to login...')
          setIsCheckingAuth(false) // Set this before redirect
          console.log('=== MAIN PAGE AUTH CHECK END (REDIRECT TO LOGIN) ===')
          window.location.href = window.location.origin + '/login'
        }
      } catch (error) {
        console.error('[MAIN-ERROR] Auth check failed:', error)
        console.error('[MAIN-ERROR] Error stack:', (error as Error).stack)
        setIsAuthenticated(false)
        setIsCheckingAuth(false)
        console.log('[MAIN-ERROR] Will redirect to login due to error')
        window.location.href = window.location.origin + '/login'
      }
    }
    
    console.log('[MAIN-INIT] Starting auth check...')
    checkAuth()
  }, [])

  // Log when auth state changes
  useEffect(() => {
    console.log('[MAIN-STATE] isAuthenticated changed to:', isAuthenticated)
  }, [isAuthenticated])

  useEffect(() => {
    console.log('[MAIN-STATE] isCheckingAuth changed to:', isCheckingAuth)
  }, [isCheckingAuth])
  
  // Update ref when activeTab changes
  useEffect(() => {
    activeTabRef.current = activeTab
  }, [activeTab])
  
  // Listen for overlay visibility changes and AI review from main process
  useEffect(() => {
    if (window.electron?.ipcRenderer) {
      const handleOverlayVisibilityChange = (isVisible: boolean) => {
        console.log('Overlay visibility changed:', isVisible)
        setOverlayVisible(isVisible)
      }
      
      const handleAiReview = (data: any) => {
        console.log('🎯 [PAGE.TSX] Received AI review IPC event from electron!')
        console.log('🎯 [PAGE.TSX] Full data object:', data)
        console.log('🎯 [PAGE.TSX] Review text:', data?.text?.substring(0, 50) + '...')
        console.log('🎯 [PAGE.TSX] Learning mode from IPC:', data?.learningMode)
        console.log('🎯 [PAGE.TSX] Original text from IPC:', data?.originalText?.substring(0, 50) + '...')
        console.log('🎯 [PAGE.TSX] Current active tab:', activeTab)
        console.log('🎯 [PAGE.TSX] Data properties:', Object.keys(data || {}))

        // Switch to AI Hub tab (where the review modal is)
        setActiveTab('ai-hub')

        // Dispatch event to show review modal after tab switch
        setTimeout(() => {
          console.log('🎯 [PAGE.TSX] Dispatching showAIReview DOM event to AIHubTab')
          console.log('🎯 [PAGE.TSX] Event detail - passing all data:', data)
          // FIXED: Pass all data from IPC, not just text (includes learningMode, originalText, etc.)
          const reviewEvent = new CustomEvent('showAIReview', {
            detail: data  // Pass entire data object
          })
          window.dispatchEvent(reviewEvent)
          console.log('🎯 [PAGE.TSX] showAIReview event dispatched with all properties!')
        }, 500) // Give time for tab to mount
      }
      
      // Auto-update event handlers
      const handleUpdateChecking = () => {
        console.log('🔄 [AUTO-UPDATE] Checking for updates...')
        toast.loading('Checking for updates...', { id: 'update-check', duration: 3000 })
      }

      const handleUpdateAvailable = (data: { version: string; currentVersion: string }) => {
        console.log(`✅ [AUTO-UPDATE] Update available: v${data.version} (current: v${data.currentVersion})`)
        toast.success(`Update v${data.version} available! Downloading...`, { id: 'update-check', duration: 5000 })
      }

      const handleUpdateNotAvailable = (data: { version: string }) => {
        console.log(`ℹ️ [AUTO-UPDATE] You're on the latest version (${data.version})`)
        toast.success(`You're up to date! (v${data.version})`, { id: 'update-check', duration: 3000 })
      }

      window.electron.ipcRenderer.on('overlay-visibility-changed', handleOverlayVisibilityChange)
      window.electron.ipcRenderer.on('show-ai-review', handleAiReview)
      window.electron.ipcRenderer.on('update-checking', handleUpdateChecking)
      window.electron.ipcRenderer.on('update-available', handleUpdateAvailable)
      window.electron.ipcRenderer.on('update-not-available', handleUpdateNotAvailable)
      console.log('🎧 [PAGE.TSX] IPC listeners registered for show-ai-review')

      return () => {
        if (window.electron?.ipcRenderer) {
          window.electron.ipcRenderer.removeListener('overlay-visibility-changed', handleOverlayVisibilityChange)
          window.electron.ipcRenderer.removeListener('show-ai-review', handleAiReview)
          window.electron.ipcRenderer.removeListener('update-checking', handleUpdateChecking)
          window.electron.ipcRenderer.removeListener('update-available', handleUpdateAvailable)
          window.electron.ipcRenderer.removeListener('update-not-available', handleUpdateNotAvailable)
        }
      }
    }
  }, [])
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
  
  // Listen for overlay toggle from Electron
  useEffect(() => {
    if (typeof window !== 'undefined' && window.electron?.ipcRenderer) {
      // Overlay toggle removed - handled entirely by Electron
    }
  }, [])

  // Global event listener for tab switching
  useEffect(() => {
    const handleSwitchTab = (event: CustomEvent) => {
      if (event.detail?.tab) {
        console.log('App-level: Switching to tab:', event.detail.tab)
        setActiveTab(event.detail.tab)
      }
    }
    
    window.addEventListener('switchTab', handleSwitchTab as EventListener)
    
    return () => {
      window.removeEventListener('switchTab', handleSwitchTab as EventListener)
    }
  }, [])
  
  // Global event listener for AI auto-typing (always active)
  useEffect(() => {
    const handleStartTyping = (event: CustomEvent) => {
      console.log('App-level: startTyping event received:', event.detail)
      
      // Ensure event.detail exists and has the expected properties
      if (!event.detail || typeof event.detail !== 'object') {
        console.error('Invalid event detail:', event.detail)
        return
      }
      
      const aiText = event.detail.text
      const isFromAI = event.detail.fromAI
      
      // Type check to ensure text is a string
      if (typeof aiText !== 'string') {
        console.error('Text is not a string:', typeof aiText, aiText)
        return
      }
      
      if (aiText && isFromAI) {
        console.log('App-level: Processing AI text from hotkey/overlay')
        
        // Check if review mode is enabled
        const aiHubSettings = localStorage.getItem('slywriter-ai-hub-settings')
        let reviewMode = false
        
        if (aiHubSettings) {
          try {
            const settings = JSON.parse(aiHubSettings)
            reviewMode = settings.review_mode === true
            console.log('App-level: Review mode enabled:', reviewMode)
          } catch (e) {
            console.error('Failed to parse AI hub settings:', e)
          }
        }
        
        if (reviewMode) {
          console.log('App-level: Switching to AI Hub tab for review')
          // Switch to AI Hub tab and trigger review modal
          setActiveTab('ai-hub')

          // Dispatch event to trigger review modal in AIHubTab with a longer delay to ensure component is ready
          setTimeout(() => {
            console.log('App-level: Dispatching showAIReview event with text:', aiText.substring(0, 50) + '...')
            const reviewEvent = new CustomEvent('showAIReview', {
              detail: event.detail  // Pass entire event detail (includes text, learningMode, etc.)
            })
            window.dispatchEvent(reviewEvent)
          }, 500) // Increased delay to ensure AIHubTab is mounted and ready
        } else {
          // Start typing in background without review
          const startBackgroundTyping = async () => {
            try {
              // Get the current typing profile and WPM from localStorage
              const savedProfile = localStorage.getItem('slywriter-selected-profile') || 'Medium'
              const savedWpm = localStorage.getItem('slywriter-custom-wpm')
              
              const response = await fetch('http://127.0.0.1:8000/api/typing/start', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  text: aiText,
                  profile: savedProfile,
                  custom_wpm: savedProfile === 'Custom' ? parseInt(savedWpm || '70') : null,
                  preview_mode: false,
                  typos_enabled: true,
                  grammarly_mode: false
                })
              })
              
              if (response.ok) {
                const data = await response.json()
                console.log('Background typing started:', data)
                toast.success('🤖 Typing AI content in background...', { duration: 2000 })
              } else {
                console.error('Failed to start background typing:', response.status)
              }
            } catch (error) {
              console.error('Error starting background typing:', error)
            }
          }
          
          startBackgroundTyping()
        }
      }
    }
    
    window.addEventListener('startTyping', handleStartTyping as EventListener)
    console.log('App-level: startTyping event listener registered (always active)')
    
    // No need for periodic checks or tab switching anymore
    
    return () => {
      window.removeEventListener('startTyping', handleStartTyping as EventListener)
      console.log('App-level: startTyping event listener removed')
    }
  }, []) // Remove activeTab dependency to prevent re-registration

  const navItems = [
    { id: 'typing', label: 'Auto-Type', icon: KeyboardIcon, color: 'from-indigo-500 to-blue-600', description: 'Types for you', badge: 'MAIN' },
    { id: 'humanizer', label: 'AI Humanizer', icon: SparklesIcon, color: 'from-violet-500 to-indigo-500', description: 'Bypass AI detectors', badge: 'HOT' },
    { id: 'ai-hub', label: 'AI Writer', icon: BrainIcon, color: 'from-blue-500 to-indigo-500', description: 'Generate essays' },
    { id: 'learning', label: 'Smart Learn', icon: BookOpenIcon, color: 'from-emerald-600 to-teal-600', description: 'AI explains topics' },
    { id: 'mission', label: 'Referrals', icon: AwardIcon, color: 'from-amber-600 to-orange-600', description: 'Our cause & rewards', badge: 'NEW' },
    { id: 'statistics', label: 'Analytics', icon: BarChart3Icon, color: 'from-slate-600 to-slate-700', description: 'Track usage' },
    { id: 'settings', label: 'Settings', icon: SettingsIcon, color: 'from-indigo-400 to-purple-400', description: 'Customize' },
  ]

  // Show loading screen while checking authentication
  if (isCheckingAuth) {
    return (
      <>
        <style jsx>{`
          @keyframes breathe {
            0%, 100% {
              box-shadow:
                0 20px 40px rgba(0, 0, 0, 0.6),
                0 0 0 1px rgba(139, 92, 246, 0.3),
                0 0 20px rgba(139, 92, 246, 0.15);
            }
            50% {
              box-shadow:
                0 20px 40px rgba(0, 0, 0, 0.6),
                0 0 0 1px rgba(139, 92, 246, 0.6),
                0 0 40px rgba(139, 92, 246, 0.4);
            }
          }

          .breathe-border {
            animation: breathe 3s ease-in-out infinite;
          }

          @keyframes shimmer {
            0% { background-position: -1000px 0; }
            100% { background-position: 1000px 0; }
          }

          .shimmer {
            background: linear-gradient(
              90deg,
              rgba(139, 92, 246, 0) 0%,
              rgba(139, 92, 246, 0.3) 50%,
              rgba(139, 92, 246, 0) 100%
            );
            background-size: 1000px 100%;
            animation: shimmer 2s infinite;
          }
        `}</style>

        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
          <div className="relative">
            <div className="bg-gradient-to-br from-gray-900/95 to-gray-800/95 backdrop-blur-xl p-12 rounded-2xl border border-purple-500/30 breathe-border">
              <div className="text-center">
                <div className="relative mb-6">
                  <div className="absolute inset-0 shimmer rounded-full" />
                  <div className="w-16 h-16 border-4 border-purple-400 border-t-transparent rounded-full animate-spin mx-auto relative z-10"></div>
                </div>
                <p className="text-white text-xl font-medium mb-2">Loading SlyWriter</p>
                <p className="text-gray-400 text-sm">Checking authentication...</p>
              </div>
            </div>
          </div>
        </div>
      </>
    )
  }
  
  // Don't redirect here - already handled in useEffect
  // This was causing redirect loops
  /*
  if (!isAuthenticated && typeof window !== 'undefined') {
    window.location.href = window.location.origin + '/login'
    return null
  }
  */

  return (
    <div className="min-h-screen bg-black">
      {/* Splash Screen */}
      <SplashScreen />
      
      {/* Beta Testing Disclosure */}
      <BetaDisclosure />
      
      {/* Global hotkey listener for Electron */}
      <GlobalHotkeyListener />
      
      {/* Subtle gradient effects around the edges */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Top subtle gradient */}
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[200%] h-64 bg-indigo-600/10 blur-[100px] animate-pulse" />
        {/* Bottom subtle gradient */}
        <div className="absolute -bottom-32 left-1/2 -translate-x-1/2 w-[200%] h-64 bg-indigo-600/10 blur-[100px] animate-pulse animation-delay-2000" />
        {/* Left subtle accent */}
        <div className="absolute top-1/2 -left-32 -translate-y-1/2 w-64 h-[200%] bg-blue-600/10 blur-[80px] animate-pulse animation-delay-4000" />
        {/* Right subtle accent */}
        <div className="absolute top-1/2 -right-32 -translate-y-1/2 w-64 h-[200%] bg-blue-600/10 blur-[80px] animate-pulse" />
      </div>

      <div className="relative flex h-screen">
        {/* Sidebar */}
        <motion.aside 
          initial={{ x: -100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="w-72 bg-black/40 backdrop-blur-2xl border-r border-gray-900 flex flex-col"
        >
          {/* Logo */}
          <div className="p-6 border-b border-gray-900">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="flex items-center gap-3"
            >
              <img
                src="/for_topleft_logo.png"
                alt="SlyWriter Logo"
                className="w-[60px] h-[67px] object-contain"
              />
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-blue-500 bg-clip-text text-transparent">
                  SlyWriter
                </h1>
                <p className="text-xs text-gray-400">AI Types For You • Undetectable</p>
              </div>
            </motion.div>
          </div>

          {/* User Section */}
          <div className="px-6 py-4 border-b border-gray-900">
            <UserProfile onShowDashboard={() => setShowDashboard(true)} />
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
                        className="absolute inset-0 bg-gradient-to-r from-indigo-500/15 to-blue-500/15 rounded-xl"
                      />
                    )}
                    <Icon className={`w-5 h-5 relative z-10 flex-shrink-0 ${
                      activeTab === item.id ? 'text-indigo-400' : ''
                    }`} />
                    <div className="flex-1 relative z-10">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{item.label}</span>
                        {item.badge && (
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                            item.badge === 'HOT' ? 'bg-red-500/20 text-red-400' :
                            item.badge === 'MAIN' ? 'bg-indigo-500/20 text-indigo-400' :
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

            {/* Features Section */}
            <div className="mt-6 pt-6 border-t border-gray-900">
              <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-3 px-2">Features</h3>

              <button
                onClick={() => {
                  // Toggle Electron overlay - state will be updated by visibility-changed event
                  if (window.electron?.ipcRenderer) {
                    window.electron.ipcRenderer.send('toggle-electron-overlay')
                    // Don't update state here - wait for the visibility-changed event
                  }
                }}
                className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-900/5 text-gray-400 hover:text-white transition-all"
              >
                <LayersIcon className="w-4 h-4" />
                <span className="text-sm">Overlay Window</span>
                <span className={`ml-auto w-2 h-2 rounded-full transition-colors ${overlayVisible ? 'bg-green-400' : 'bg-gray-600'}`} />
              </button>
            </div>
          </nav>

          {/* Footer */}
          <div className="p-6 border-t border-gray-900 space-y-4">
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
            <div className="bg-gradient-to-r from-indigo-600 to-blue-600 rounded-xl p-4">
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
          <AnimatePresence>
            {activeTab === 'typing' && (
              <motion.div
                key="typing"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="h-full overflow-y-auto p-8"
              >
                <TypingTabWithWPM 
                  connected={connected} 
                />
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
                <HumanizerTab onNavigateToDashboard={() => setShowDashboard(true)} />
              </motion.div>
            )}
            
            <motion.div
              key="ai-hub"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`h-full overflow-y-auto p-8 ${activeTab === 'ai-hub' ? 'block' : 'hidden'}`}
            >
              <AIHubTab />
            </motion.div>
            
            {activeTab === 'learning' && (
              <motion.div
                key="learning"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="h-full overflow-y-auto p-8"
              >
                <EnhancedLearningTab />
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
      
      {/* User Dashboard Modal */}
      {showDashboard && (
        <UserDashboard onClose={() => setShowDashboard(false)} />
      )}
      
      {/* Old React overlay removed - using Electron overlay only */}
    </div>
  )
}

export default function Page() {
  return (
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
  )
}