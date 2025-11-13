'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { useHotkeys } from 'react-hotkeys-hook'
import { useHotkeys as useCustomHotkeys } from '../hooks/useHotkeys'
import { FirstTimeHelper, FeatureTooltip, QuickTip } from './FeatureTooltips'
import OutOfWordsModal from './OutOfWordsModal'
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

// Import centralized API configuration
import { API_ENDPOINTS, getWebSocketUrl, AI_API_URL } from '../config/api'
import telemetry from '../services/telemetry'
import soundService from '../services/sound'

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
  pendingAIText?: string | null
  onAITextProcessed?: () => void
}

export default function TypingTabWithWPM({ connected, initialProfile, shouldOpenWpmTest, onWpmTestOpened, pendingAIText, onAITextProcessed }: TypingTabProps) {
  const { user, isPremium, canType, wordsRemaining, trackWordUsage } = useAuth()
  const hotkeys = useCustomHotkeys()
  
  // Core state
  const [inputText, setInputText] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isTyping, setIsTyping] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [status, setStatus] = useState('Ready to type')
  const [progress, setProgress] = useState(0)
  const [wpm, setWpm] = useState(0)
  const [accuracy, setAccuracy] = useState(100)
  const [charsTyped, setCharsTyped] = useState(0)
  const [totalChars, setTotalChars] = useState(0)
  const [countdown, setCountdown] = useState<number | undefined>(undefined)
  const [previewMode, setPreviewMode] = useState(false)
  
  // Profile state - don't initialize from localStorage to avoid hydration issues
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [selectedProfile, setSelectedProfile] = useState('Medium')
  const [loadingProfiles, setLoadingProfiles] = useState(true)
  const [profileLoaded, setProfileLoaded] = useState(false)
  
  // Premium features state
  const [typosMade, setTyposMade] = useState(0)
  const [pausesTaken, setPausesTaken] = useState(0)
  
  // Delayed correction settings (like autocorrect tools)
  const [grammarlyCorrectionEnabled, setGrammarlyCorrectionEnabled] = useState(false)
  const [grammarlyCorrectionDelay, setGrammarlyCorrectionDelay] = useState(3) // 3 seconds default
  const [typoRate, setTypoRate] = useState(3) // 3% typo rate
  const [humanMode, setHumanMode] = useState(true)
  const [pasteMode, setPasteMode] = useState(false)
  const [autoClearTextbox, setAutoClearTextbox] = useState(true)
  const [aiFillerEnabled, setAiFillerEnabled] = useState(false) // Premium feature
  const [microHesitations, setMicroHesitations] = useState(0)
  const [aiFillers, setAiFillers] = useState(0)
  const [zoneOutActive, setZoneOutActive] = useState(false)
  
  // UI state
  const [showStats, setShowStats] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [copied, setCopied] = useState(false)
  const [showOutOfWordsModal, setShowOutOfWordsModal] = useState(false)
  
  // WPM Test state
  const [showWpmTest, setShowWpmTest] = useState(false)
  const [testText] = useState('The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs. How vexingly quick daft zebras jump! Sphinx of black quartz, judge my vow.')
  const [testInput, setTestInput] = useState('')
  const [testStartTime, setTestStartTime] = useState<number | undefined>(undefined)
  // Initialize testWpm to undefined, then load from localStorage in useEffect
  const [testWpm, setTestWpm] = useState<number | undefined>(undefined)
  const [isTestActive, setIsTestActive] = useState(false)
  const [testErrors, setTestErrors] = useState(0)
  const [isClient, setIsClient] = useState(false)
  
  const wsRef = useRef<WebSocket | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const testInputRef = useRef<HTMLTextAreaElement>(null)
  
  // Function to reload settings from localStorage
  const reloadSettings = (forceReloadProfile = false) => {
    if (typeof window !== 'undefined') {
      // Only load profile if not already loaded or forced
      if (!profileLoaded || forceReloadProfile) {
        const savedProfile = localStorage.getItem('slywriter-selected-profile')
        if (savedProfile) {
          console.log('Loading saved profile:', savedProfile)
          setSelectedProfile(savedProfile)
          setProfileLoaded(true)

          // Only load custom WPM if the saved profile is Custom
          if (savedProfile === 'Custom') {
            const savedWpm = localStorage.getItem('slywriter-custom-wpm')
            if (savedWpm) {
              const wpm = parseInt(savedWpm)
              setTestWpm(wpm)
              console.log('Loaded custom WPM from localStorage:', wpm)
            }
          }
        }
      }
      
      // Load paste mode preference
      const savedPasteMode = localStorage.getItem('slywriter-paste-mode')
      if (savedPasteMode === 'true') {
        setPasteMode(true)
      }
      
      // Load profile settings from Settings tab
      const typosEnabled = localStorage.getItem('typosEnabled')
      if (typosEnabled !== null) {
        setHumanMode(typosEnabled === 'true')
      }
      
      const aiFillerEnabled = localStorage.getItem('aiFillerEnabled')
      if (aiFillerEnabled !== null) {
        setAiFillerEnabled(aiFillerEnabled === 'true')
      }
      
      // Load auto-clear setting
      const autoClear = localStorage.getItem('slywriter-auto-clear')
      if (autoClear !== null) {
        setAutoClearTextbox(autoClear === 'true')
      }
      
      // Load delayed correction mode setting
      const grammarlyMode = localStorage.getItem('slywriter-grammarly-mode')
      if (grammarlyMode !== null) {
        setGrammarlyCorrectionEnabled(grammarlyMode === 'true')
      }
      
      // Load correction delay setting
      const grammarlyDelay = localStorage.getItem('slywriter-grammarly-delay')
      if (grammarlyDelay !== null) {
        setGrammarlyCorrectionDelay(parseInt(grammarlyDelay))
      }
    }
  }
  
  // Load profiles and check for onboarding triggers
  useEffect(() => {
    loadProfiles()
    
    // Set client flag to prevent hydration mismatches
    setIsClient(true)
    
    // Load saved values from localStorage after mount (force profile reload on initial load)
    reloadSettings(true)
    
    // Check if we should open WPM test from onboarding
    if (shouldOpenWpmTest) {
      setShowWpmTest(true)
      if (onWpmTestOpened) {
        onWpmTestOpened()
      }
    }
  }, [shouldOpenWpmTest, onWpmTestOpened])

  // Reload settings when tab becomes visible or component gets focus
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        console.log('Tab became visible, reloading settings...')
        reloadSettings(true) // Force reload profile when tab becomes visible
      }
    }
    
    // Also reload when the window gets focus
    const handleFocus = () => {
      console.log('Window focused, reloading settings...')
      reloadSettings(true) // Force reload profile when window gets focus
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('focus', handleFocus)
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('focus', handleFocus)
    }
  }, [])

  // Handle pending AI text from app-level event listener
  useEffect(() => {
    if (pendingAIText) {
      console.log('TypingTab: Received pending AI text from app level:', pendingAIText.substring(0, 50))
      
      // Set the input text
      setInputText(pendingAIText)
      
      // Show popup immediately
      toast.success('🤖 AI Content Ready To Type!', { 
        duration: 3000,
        icon: '✨'
      })
      
      // Start typing immediately - no delay since AI Hub already did the countdown
      setTimeout(() => {
        console.log('TypingTab: Starting typing automatically for AI text')
        startTypingRef.current()
        
        // Clear the pending text
        if (onAITextProcessed) {
          onAITextProcessed()
        }
      }, 500) // Small delay to ensure UI is updated
    }
  }, [pendingAIText, onAITextProcessed])
  
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
  
  // Save WPM to localStorage ONLY when using Custom profile
  useEffect(() => {
    if (testWpm !== undefined && selectedProfile === 'Custom') {
      if (typeof window !== 'undefined') {
        localStorage.setItem('slywriter-custom-wpm', testWpm.toString())
        console.log('Saved custom WPM to localStorage:', testWpm)
      }
    }
  }, [testWpm, selectedProfile])
  
  // Save selected profile to localStorage whenever it changes (but not on initial load)
  useEffect(() => {
    // Only save after profile has been loaded from localStorage first
    if (typeof window !== 'undefined' && profileLoaded) {
      console.log('Saving profile to localStorage:', selectedProfile)
      localStorage.setItem('slywriter-selected-profile', selectedProfile)
    }
  }, [selectedProfile, profileLoaded])
  
  // Save typing settings to localStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined' && isClient) {
      localStorage.setItem('slywriter-auto-clear', autoClearTextbox.toString())
    }
  }, [autoClearTextbox, isClient])
  
  useEffect(() => {
    if (typeof window !== 'undefined' && isClient) {
      localStorage.setItem('slywriter-grammarly-mode', grammarlyCorrectionEnabled.toString())
    }
  }, [grammarlyCorrectionEnabled, isClient])
  
  useEffect(() => {
    if (typeof window !== 'undefined' && isClient) {
      localStorage.setItem('slywriter-grammarly-delay', grammarlyCorrectionDelay.toString())
    }
  }, [grammarlyCorrectionDelay, isClient])
  
  useEffect(() => {
    if (typeof window !== 'undefined' && isClient) {
      localStorage.setItem('typosEnabled', humanMode.toString())
    }
  }, [humanMode, isClient])
  
  useEffect(() => {
    if (typeof window !== 'undefined' && isClient) {
      localStorage.setItem('aiFillerEnabled', aiFillerEnabled.toString())
    }
  }, [aiFillerEnabled, isClient])
  
  useEffect(() => {
    if (typeof window !== 'undefined' && isClient) {
      localStorage.setItem('slywriter-paste-mode', pasteMode.toString())
    }
  }, [pasteMode, isClient])
  

  const loadProfiles = async () => {
    try {
      const response = await axios.get(API_ENDPOINTS.PROFILES_LIST)
      setProfiles(response.data.profiles)
      setLoadingProfiles(false)
    } catch (error) {
      // Use default profiles if API is not available
      const defaultProfiles: Profile[] = [
        { 
          name: 'Slow', 
          is_builtin: true, 
          settings: {
            min_delay: 150,
            max_delay: 200,
            typos_enabled: false,
            typo_chance: 0,
            pause_frequency: 5,
            ai_filler_enabled: false,
            micro_hesitations: false,
            zone_out_breaks: false,
            burst_variability: 0.1
          }
        },
        { 
          name: 'Medium', 
          is_builtin: true, 
          settings: {
            min_delay: 80,
            max_delay: 120,
            typos_enabled: false,
            typo_chance: 0,
            pause_frequency: 5,
            ai_filler_enabled: false,
            micro_hesitations: false,
            zone_out_breaks: false,
            burst_variability: 0.15
          }
        },
        { 
          name: 'Fast', 
          is_builtin: true, 
          settings: {
            min_delay: 40,
            max_delay: 80,
            typos_enabled: false,
            typo_chance: 0,
            pause_frequency: 5,
            ai_filler_enabled: false,
            micro_hesitations: false,
            zone_out_breaks: false,
            burst_variability: 0.2
          }
        },
        {
          name: 'Lightning',
          is_builtin: true,
          settings: {
            min_delay: 20,
            max_delay: 40,
            typos_enabled: false,
            typo_chance: 0,
            pause_frequency: 5,
            ai_filler_enabled: false,
            micro_hesitations: false,
            zone_out_breaks: false,
            burst_variability: 0.25
          }
        },
        {
          name: 'Custom',
          is_builtin: true,
          settings: {
            min_delay: 60,
            max_delay: 100,
            typos_enabled: false,
            typo_chance: 0,
            pause_frequency: 5,
            ai_filler_enabled: false,
            micro_hesitations: false,
            zone_out_breaks: false,
            burst_variability: 0.15
          }
        }
      ]
      setProfiles(defaultProfiles)
      setLoadingProfiles(false)
    }
  }
  
  // WebSocket connection
  useEffect(() => {
    if (!connected) return
    
    const userId = user?.email || 'anonymous'
    let ws: WebSocket | null = null
    
    try {
      ws = new WebSocket(getWebSocketUrl(userId))
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
          console.log('[TYPING TAB] WebSocket event received:', data.type, data)

          switch (data.type) {
        case 'countdown':
          setCountdown(data.data.count)
          setStatus(`Starting in ${data.data.count}...`)

          // Send to Electron overlay
          if (typeof window !== 'undefined' && (window as any).electron?.ipcRenderer) {
            const countdownData = {
              type: 'countdown',
              value: data.data.count
            }
            console.log('[TYPING TAB] Sending countdown to overlay:', countdownData)
            ;(window as any).electron.ipcRenderer.send('typing-status', countdownData)
          }
          break
          
        case 'typing_started':
          setCountdown(undefined)  // Clear countdown
          setStatus('⌨️ Typing...')

          // Show overlay when typing starts with initial stats
          if (typeof window !== 'undefined' && (window as any).electron) {
            if ((window as any).electron.showOverlay) {
              (window as any).electron.showOverlay()
            }
            // Send initial stats
            if ((window as any).electron.ipcRenderer) {
              const typingStartedData = {
                type: 'typing',
                progress: 0,
                wpm: 0,
                charsTyped: 0,
                status: '⌨️ Typing...'
              }
              console.log('[TYPING TAB] Sending typing_started to overlay:', typingStartedData)
              ;(window as any).electron.ipcRenderer.send('typing-status', typingStartedData)
            }
          }
          break
          
        case 'progress':
          // Ensure progress is a valid number
          const progressValue = data.data.progress || 0
          const currentWpm = data.data.wpm || 0
          const currentAccuracy = data.data.accuracy || 100
          const currentCharsTyped = data.data.chars_typed || 0
          const currentTotalChars = data.data.total_chars || 0
          
          setProgress(Math.min(100, Math.max(0, progressValue)))
          setWpm(currentWpm)
          setAccuracy(currentAccuracy)
          setCharsTyped(currentCharsTyped)
          setTotalChars(currentTotalChars)
          setStatus(data.data.status || '⌨️ Typing in progress')
          
          // Update overlay with current stats
          if (typeof window !== 'undefined' && (window as any).electron?.ipcRenderer) {
            (window as any).electron.ipcRenderer.send('typing-status', {
              type: 'progress',
              progress: progressValue,
              wpm: currentWpm,
              accuracy: currentAccuracy,
              charsTyped: currentCharsTyped,
              totalChars: currentTotalChars,
              status: data.data.status || 'Typing...'
            })
          }
          
          // Play key sound occasionally (every 10 chars)
          if (currentCharsTyped && currentCharsTyped % 10 === 0) {
            soundService.playKeySound()
          }
          
          console.log(`Progress update: ${progressValue}% (${currentCharsTyped}/${currentTotalChars} chars) - WPM: ${currentWpm}`)
          
          // Dispatch update event for overlay
          const updateEvent = new CustomEvent('typing-update', {
            detail: {
              status: data.data.status,
              wpm: data.data.wpm,
              progress: data.data.progress
            }
          })
          window.dispatchEvent(updateEvent)
          
          // Send to Electron overlay if available
          if (typeof window !== 'undefined' && window.electron?.ipcRenderer) {
            const progressData = {
              type: 'typing',
              status: data.data.status || '⌨️ Typing...',
              progress: progressValue,
              wpm: data.data.wpm || 0,
              charsTyped: data.data.chars_typed || 0
            }
            console.log('[TYPING TAB] Sending progress to overlay:', progressData)
            window.electron.ipcRenderer.send('typing-status', progressData)
          }
          break
          
        case 'typo':
          setTyposMade(data.data.typos_made)
          telemetry.trackTypingMetric('typo', data.data.typos_made)
          break
          
        case 'natural_pause':
          // Natural pauses are just delays, not actual pauses
          setPausesTaken(prev => {
            const newValue = prev + 1
            telemetry.trackTypingMetric('pause', newValue)
            return newValue
          })
          // Don't change isPaused state - these are automatic pauses
          break
          
        case 'pause':
          setPausesTaken(data.data.pauses_taken)
          telemetry.trackTypingMetric('pause', data.data.pauses_taken)
          setStatus(data.data.status)

          // Send to Electron overlay
          if (typeof window !== 'undefined' && (window as any).electron?.ipcRenderer) {
            const pauseData = {
              type: 'typing',
              status: data.data.status || '⏸️ Paused',
              progress: progress,
              wpm: wpm,
              charsTyped: charsTyped
            }
            console.log('[TYPING TAB] Sending pause to overlay:', pauseData)
            ;(window as any).electron.ipcRenderer.send('typing-status', pauseData)
          }
          break
          
        case 'zone_out':
          setZoneOutActive(true)
          setStatus(data.data.status)
          setTimeout(() => setZoneOutActive(false), data.data.duration * 1000)

          // Send to Electron overlay
          if (typeof window !== 'undefined' && (window as any).electron?.ipcRenderer) {
            const zoneOutData = {
              type: 'typing',
              status: data.data.status || '😴 Zoning out...',
              progress: progress,
              wpm: wpm,
              charsTyped: charsTyped
            }
            console.log('[TYPING TAB] Sending zone_out to overlay:', zoneOutData)
            ;(window as any).electron.ipcRenderer.send('typing-status', zoneOutData)
          }
          break
          
        case 'micro_hesitation':
          setMicroHesitations(prev => prev + 1)
          break
          
        case 'ai_filler':
          setAiFillers(data.data.fillers_used)
          setStatus('AI Filler...')

          // Send to Electron overlay
          if (typeof window !== 'undefined' && (window as any).electron?.ipcRenderer) {
            const aiFillerData = {
              type: 'typing',
              status: '🤖 AI Filler...',
              progress: progress,
              wpm: wpm,
              charsTyped: charsTyped
            }
            console.log('[TYPING TAB] Sending ai_filler to overlay:', aiFillerData)
            ;(window as any).electron.ipcRenderer.send('typing-status', aiFillerData)
          }
          break
          
        case 'complete':
          setIsTyping(false)
          setIsPaused(false)
          setStatus('✅ Finished!')
          setProgress(100)
          toast.success('Typing session complete!')
          setSessionId(null)

          // Track word usage
          const wordsTyped = Math.floor(charsTyped / 5)
          if (wordsTyped > 0 && trackWordUsage) {
            trackWordUsage(wordsTyped)
            console.log(`[USAGE TRACKING] Tracked ${wordsTyped} words typed`)
          }

          // Save typing session to database
          saveTypingSession(wpm, accuracy, charsTyped)

          // Send final stats to overlay
          if (typeof window !== 'undefined' && (window as any).electron?.ipcRenderer) {
            const completeData = {
              type: 'complete',
              progress: 100,
              wpm: wpm,
              accuracy: accuracy,
              charsTyped: charsTyped,
              totalChars: totalChars,
              status: '✅ Finished!'
            }
            console.log('[TYPING TAB] Sending complete to overlay:', completeData)
            ;(window as any).electron.ipcRenderer.send('typing-status', completeData)
          }
          
          // Reset typing state after a short delay
          setTimeout(() => {
            setProgress(0)
            setCharsTyped(0)
            setTotalChars(0)
            setStatus('Ready to type')
          }, 3000)
          
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

              // Send to Electron overlay
              if (typeof window !== 'undefined' && (window as any).electron?.ipcRenderer) {
                const errorData = {
                  type: 'complete',
                  status: '❌ Error: ' + (data.data.message || 'Unknown error'),
                  progress: progress,
                  wpm: wpm
                }
                console.log('[TYPING TAB] Sending error to overlay:', errorData)
                ;(window as any).electron.ipcRenderer.send('typing-status', errorData)
              }
              break
              
            case 'typing_complete':
            case 'typing_finished':
              console.log('Received typing_complete - setting isTyping to false')
              // Typing is complete, reset the UI
              setIsTyping(false)
              setIsPaused(false)
              setProgress(100)
              setStatus('✅ Finished!')
              setSessionId(null)

              // Track word usage
              const completedWords = Math.floor(charsTyped / 5)
              if (completedWords > 0 && trackWordUsage) {
                trackWordUsage(completedWords)
                console.log(`[USAGE TRACKING] Tracked ${completedWords} words typed (typing_complete event)`)
              }
              
              // Send final stats to overlay
              if (typeof window !== 'undefined' && (window as any).electron?.ipcRenderer) {
                (window as any).electron.ipcRenderer.send('typing-status', {
                  type: 'complete',
                  progress: 100,
                  wpm: wpm,
                  accuracy: accuracy,
                  charsTyped: charsTyped,
                  totalChars: totalChars,
                  status: '✅ Finished!'
                })
              }
              
              // Reset typing state after a short delay
              setTimeout(() => {
                setProgress(0)
                setCharsTyped(0)
                setTotalChars(0)
                setStatus('Ready to type')
              }, 3000)
              
              // Auto-clear textbox if enabled
              if (autoClearTextbox) {
                setTimeout(() => {
                  setInputText('')
                  toast.success('Textbox cleared - ready for next paste!', { icon: '🔄' })
                }, 1000) // Wait 1 second after completion before clearing
              }

              // Show success toast
              toast.success('✅ Typing completed successfully!', {
                duration: 3000,
                icon: '🎉'
              })
              
              // Clear session
              setSessionId(null)
              
              // Dispatch complete event for overlay with final WPM
              window.dispatchEvent(new CustomEvent('typing-complete', { 
                detail: { wpm: data.data.wpm || wpm } 
              }))
              
              // Send to Electron overlay
              if (window.electron?.ipcRenderer) {
                window.electron.ipcRenderer.send('typing-status', {
                  type: 'complete',
                  status: '✅ Finished!',
                  wpm: data.data.wpm || wpm,
                  progress: 100
                })
              }
              break
              
            case 'status':
              // Handle status updates from backend (especially AI filler updates)
              if (data.data) {
                const statusData = data.data
                setStatus(statusData.status || '⌨️ Typing in progress')

                if (statusData.progress !== undefined) {
                  setProgress(Math.min(100, Math.max(0, statusData.progress)))
                }

                // Send to Electron overlay
                if (window.electron?.ipcRenderer) {
                  const statusUpdateData = {
                    type: 'typing',
                    status: statusData.status || '⌨️ Typing in progress',
                    progress: statusData.progress,
                    wpm: statusData.wpm || wpm,
                    charsTyped: statusData.chars_typed
                  }
                  console.log('[TYPING TAB] Sending status update to overlay:', statusUpdateData)
                  window.electron.ipcRenderer.send('typing-status', statusUpdateData)
                }
                
                // Log AI filler events for debugging
                if (statusData.status?.includes('AI') || statusData.status?.includes('filler') || 
                    statusData.status?.includes('Generating') || statusData.status?.includes('Regretting')) {
                  console.log('[AI Filler Status]:', statusData.status)
                }
              }
              break
          }
        } catch (err) {
          console.warn('Failed to parse WebSocket message:', err)
        }
      }
      
      ws.onclose = () => {
        console.log('WebSocket disconnected - will reconnect on next typing session')
        wsRef.current = null
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
      const newWpm = Math.min(500, currentWpm + 10)
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
    // Allow updating WPM during pause as well
    if (!sessionId || (!isTyping && !isPaused)) return
    
    try {
      // Auth handled via cookies, no need for manual token
      
      await axios.post(API_ENDPOINTS.TYPING_UPDATE_WPM, {
        session_id: sessionId,
        wpm: newWpm
      })
      
      setWpm(newWpm)
    } catch (error) {
      console.error('Failed to update WPM:', error)
    }
  }

  const startTyping = useCallback(async () => {
    let textToType = inputText.trim()
    
    // Check if this is being called from AI auto-output
    const isFromAI = (window as any).isProcessingAIText
    
    // If no text entered and NOT from AI, try to read from clipboard
    if (!textToType && !isFromAI) {
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
      setShowOutOfWordsModal(true)
      return
    }
    
    try {
      // Auth handled via cookies, no need for manual token
      
      // Calculate the actual WPM to use - either custom or from profile
      const actualWpm = selectedProfile === 'Custom' && testWpm ? testWpm : getProfileWpm(selectedProfile, testWpm)
      const customWpm = actualWpm  // Always send the actual WPM value

      // EXTREMELY VISIBLE DEBUG - User MUST see this
      console.error('🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥')
      console.error('🚨 TYPING START - VERSION 2.5.5 🚨')
      console.error('🔥 Selected Profile:', selectedProfile)
      console.error('🔥 Test WPM (from state):', testWpm)
      console.error('🔥 Calculated WPM to send to backend:', customWpm)
      console.error('🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥')

      console.log('========== TYPING START DEBUG ==========')
      console.log('[TypingTab] Selected Profile:', selectedProfile)
      console.log('[TypingTab] Test WPM:', testWpm)
      console.log('[TypingTab] Profile Default WPM:', getProfileWpm(selectedProfile))
      console.log('[TypingTab] Actual WPM (will be sent):', actualWpm)
      console.log('[TypingTab] Custom WPM parameter:', customWpm)

      // Get profile settings from localStorage
      const typingSpeed = localStorage.getItem('typingSpeed') || '5'
      const pauseFrequency = localStorage.getItem('pauseFrequency') || '5'
      
      const requestData = {
        text: textToType,
        profile: selectedProfile,
        preview_mode: previewMode,
        custom_wpm: customWpm,
        ai_filler_enabled: aiFillerEnabled, // Pass premium AI filler setting
        typos_enabled: humanMode, // Enable typos when in human mode
        grammarly_mode: grammarlyCorrectionEnabled, // Enable delayed corrections
        grammarly_delay: grammarlyCorrectionDelay, // Delay before corrections
        typo_rate: typoRate, // Percentage chance of typos
        typing_speed: parseInt(typingSpeed), // Use profile speed setting
        pause_frequency: parseInt(pauseFrequency) // Use profile pause frequency
      }
      
      console.log('[TypingTab] Request Data:', JSON.stringify(requestData, null, 2))
      console.log('========================================')

      const response = await axios.post(API_ENDPOINTS.TYPING_START, requestData)

      console.log('[TypingTab] Typing started successfully')
      console.log('[TypingTab] Response:', response.data)
      
      setSessionId(response.data.session_id)
      setIsTyping(true)
      setIsPaused(false)
      setProgress(0)
      setCharsTyped(0)
      setTotalChars(textToType.length)
      console.log(`Typing started - isTyping set to true, text length: ${textToType.length} chars`)
      // ALWAYS set WPM based on selected profile when starting typing
      setWpm(selectedProfile === 'Custom' && testWpm ? testWpm : getProfileWpm(selectedProfile, testWpm))
      setAccuracy(100)
      setTyposMade(0)
      setPausesTaken(0)
      setMicroHesitations(0)
      setAiFillers(0)
      setStatus('Typing...')
      
      // Track typing session start
      telemetry.startTypingSession(textToType.length, selectedProfile, aiFillerEnabled)
      telemetry.trackEvent('typing_started', {
        profile: selectedProfile,
        textLength: textToType.length,
        aiFillerEnabled,
        humanMode,
        grammarlyCorrectionEnabled
      })
      
      // Dispatch start event for overlay
      window.dispatchEvent(new CustomEvent('typing-start'))
      
      // Send to Electron overlay
      if (window.electron?.ipcRenderer) {
        window.electron.ipcRenderer.send('typing-status', {
          type: 'typing',
          status: 'Starting...',
          wpm: 0,
          progress: 0,
          charsTyped: 0
        })
      }
      
      // Show immediate feedback
      toast.success('🚀 Starting typing engine...', { 
        duration: 2000,
        icon: '⚡'
      })
      
      // Show additional feedback based on settings
      if (aiFillerEnabled) {
        setTimeout(() => {
          toast('🎭 Premium AI Filler activated!', {
            icon: '👑',
            duration: 3000,
            style: {
              background: 'linear-gradient(135deg, #9333ea 0%, #ec4899 100%)',
              color: 'white',
            }
          })
        }, 500)
      }
      
      if (humanMode) {
        setTimeout(() => {
          toast('🎯 Human mode patterns enabled', {
            icon: '✨',
            duration: 2000
          })
        }, 300)
      }
      
      if (grammarlyCorrectionEnabled) {
        setTimeout(() => {
          toast('✏️ Delayed corrections active', {
            icon: '📝',
            duration: 2000
          })
        }, 600)
      }
      
      // Show typing speed after a moment
      const wpmValue = getProfileWpm(selectedProfile, testWpm)
      
      setTimeout(() => {
        toast.success(`✍️ Now typing at ${wpmValue} WPM!`, {
          duration: 4000,
          style: {
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
          }
        })
      }, 1500)
    } catch (error: any) {
      console.error('Typing start error:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to start typing'
      toast.error(errorMsg)
    }
  }, [inputText, connected, user, canType, wordsRemaining, selectedProfile, humanMode, 
     grammarlyCorrectionEnabled, grammarlyCorrectionDelay, typoRate, aiFillerEnabled, 
     pasteMode, autoClearTextbox, testWpm, isPremium])
  
  const pauseTyping = async () => {
    if (!isTyping) {
      console.log('Not typing, cannot pause')
      return
    }
    
    // Immediately update UI for responsiveness
    const newPausedState = !isPaused
    setIsPaused(newPausedState)
    setStatus(newPausedState ? '⏸️ Paused' : '⌨️ Typing in progress')
    
    try {
      if (sessionId) {
        // Try session-specific endpoint first
        if (newPausedState) {
          await axios.post(`${API_ENDPOINTS.TYPING_PAUSE}/${sessionId}`)
        } else {
          await axios.post(`${API_ENDPOINTS.TYPING_RESUME}/${sessionId}`)
        }
      } else {
        // Fallback to global pause endpoint
        await axios.post(API_ENDPOINTS.TYPING_PAUSE)
      }
      toast(newPausedState ? '⏸️ Typing paused - Press SPACE to resume' : '▶️ Typing resumed')
    } catch (error) {
      // If session endpoint fails, try global endpoint
      console.error('Pause/resume error, trying global endpoint:', error)
      try {
        await axios.post(API_ENDPOINTS.TYPING_PAUSE)
        toast(newPausedState ? '⏸️ Paused (global)' : '▶️ Resumed (global)')
      } catch (globalError) {
        console.error('Global pause failed:', globalError)
        toast(newPausedState ? '⏸️ Paused locally' : '▶️ Resumed locally')
      }
    }
  }
  
  // Store startTyping in a ref to avoid stale closures
  const startTypingRef = useRef(startTyping)
  useEffect(() => {
    startTypingRef.current = startTyping
  }, [startTyping])
  
  // Listen for background typing sessions and sync UI
  useEffect(() => {
    const checkBackgroundTyping = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.TYPING_STATUS)
        if (response.ok) {
          const data = await response.json()
          if (data.is_typing) {
            setIsTyping(true)
            setSessionId(data.session_id || 'active')
            setProgress(data.progress || 0)
            setStatus(data.status || '⌨️ Typing in progress')
          }
        }
      } catch (error) {
        // Ignore errors - backend might not be running
      }
    }
    
    // Check immediately and then periodically
    checkBackgroundTyping()
    const interval = setInterval(checkBackgroundTyping, 1000)
    
    return () => clearInterval(interval)
  }, [])
  
  // Handle pending AI text from parent
  useEffect(() => {
    if (pendingAIText) {
      console.log('TypingTab: Received pendingAIText from parent:', pendingAIText.substring(0, 50))
      
      // Set the text in the input
      setInputText(pendingAIText)
      
      // Force update the textarea
      setTimeout(() => {
        const textarea = document.querySelector('textarea[placeholder*="Type Mode"]') as HTMLTextAreaElement
        if (textarea) {
          textarea.value = pendingAIText
          textarea.dispatchEvent(new Event('input', { bubbles: true }))
        }
        
        // Start typing immediately
        console.log('TypingTab: Starting typing with pending AI text')
        if (typeof startTypingRef.current === 'function') {
          startTypingRef.current()
        } else {
          console.error('startTypingRef.current is not a function:', startTypingRef.current)
          // Fallback: call startTyping directly
          startTyping()
        }
        
        // Notify parent that text has been processed
        if (onAITextProcessed) {
          onAITextProcessed()
        }
      }, 100)
      
      toast.success('🤖 AI content ready to type!', { duration: 2000 })
    }
  }, [pendingAIText, onAITextProcessed, startTyping])
  
  // Listen for AI auto-output events
  // DISABLED: This is now handled at the app level in page.tsx to prevent duplicates
  /*
  useEffect(() => {
    const handleStartTyping = (event: CustomEvent) => {
      console.log('TypingTab received startTyping event:', event.detail)
      const { text, fromAI } = event.detail
      
      if (text && fromAI) {
        console.log('Setting input text and starting typing...')
        
        // Set flag to prevent clipboard usage
        if (typeof window !== 'undefined') {
          (window as any).isProcessingAIText = true
        }
        
        // Set the text in the input
        setInputText(text)
        
        // Force update the textarea to ensure text is visible
        setTimeout(() => {
          const textarea = document.querySelector('textarea[placeholder*="Type Mode"]') as HTMLTextAreaElement
          if (textarea) {
            textarea.value = text
            textarea.dispatchEvent(new Event('input', { bubbles: true }))
            console.log('Forced textarea update with AI text from event')
          }
          
          // Start typing immediately - AI Hub already did the countdown
          console.log('Starting typing immediately')
          if (typeof startTypingRef.current === 'function') {
            startTypingRef.current()
          } else {
            console.error('startTypingRef.current is not a function:', startTypingRef.current)
            // Fallback: call startTyping directly
            startTyping()
          }
          
          // Clear the flag after a short delay
          setTimeout(() => {
            if (typeof window !== 'undefined') {
              delete (window as any).isProcessingAIText
            }
          }, 1000)
        }, 100)
        
        toast.success('🤖 AI content ready to type!', { duration: 2000 })
      }
    }
    
    // Also check for backup method periodically
    const checkPendingText = setInterval(() => {
      if ((window as any).pendingAIText) {
        console.log('Found pending AI text via backup method')
        const text = (window as any).pendingAIText
        delete (window as any).pendingAIText
        
        // Set flag to prevent clipboard usage
        if (typeof window !== 'undefined') {
          (window as any).isProcessingAIText = true
        }
        
        // Set the text and force a re-render
        setInputText(text)
        
        // Use setTimeout to ensure state has updated
        setTimeout(() => {
          // Force the textarea to update its value
          const textarea = document.querySelector('textarea[placeholder*="Type Mode"]') as HTMLTextAreaElement
          if (textarea) {
            textarea.value = text
            textarea.dispatchEvent(new Event('input', { bubbles: true }))
            console.log('Forced textarea update with AI text')
          }
          
          // Start typing immediately - no delay since AI Hub already waited 5 seconds
          console.log('Starting typing immediately from backup method')
          
          // Force typing to start immediately
          console.log('Force starting typing immediately')

          // Calculate the actual WPM to use - either custom or from profile
          const actualWpm = selectedProfile === 'Custom' && testWpm ? testWpm : getProfileWpm(selectedProfile, testWpm)

          // Get profile settings from localStorage
          const typingSpeed = localStorage.getItem('typingSpeed') || '5'
          const pauseFrequency = localStorage.getItem('pauseFrequency') || '5'

          // Send typing request directly to backend with complete settings
          axios.post(API_ENDPOINTS.TYPING_START, {
            text: text,
            profile: selectedProfile || 'Medium',
            preview_mode: false,
            custom_wpm: actualWpm,
            ai_filler_enabled: aiFillerEnabled,
            typos_enabled: humanMode,
            grammarly_mode: grammarlyCorrectionEnabled,
            grammarly_delay: grammarlyCorrectionDelay,
            typo_rate: typoRate,
            typing_speed: parseInt(typingSpeed),
            pause_frequency: parseInt(pauseFrequency)
          }).then(response => {
            console.log('Typing started via direct API call:', response.data)
            console.log('🔥 Backup method used WPM:', actualWpm)
            setIsTyping(true)
            setSessionId(response.data.session_id || 'active')
            // Set WPM in UI to match what was sent
            setWpm(actualWpm)
          }).catch(error => {
            console.error('Failed to start typing:', error)
            // Fallback to button click
            const startButton = document.querySelector('button[data-testid="start-typing"]') as HTMLButtonElement
            if (startButton) {
              startButton.click()
            }
          })
          
          // Clear the flag after a short delay
          setTimeout(() => {
            if (typeof window !== 'undefined') {
              delete (window as any).isProcessingAIText
            }
          }, 1000)
        }, 100)
        
        toast.success('🤖 AI content ready to type!', { duration: 2000 })
      }
    }, 500) // Check more frequently for faster response
    
    window.addEventListener('startTyping', handleStartTyping as EventListener)
    console.log('TypingTab: startTyping event listener registered')
    
    return () => {
      window.removeEventListener('startTyping', handleStartTyping as EventListener)
      clearInterval(checkPendingText)
      console.log('TypingTab: startTyping event listener removed')
    }
  }, [setInputText, startTyping, selectedProfile]) // Include all dependencies to avoid stale closures
  */

  // Helper function to save typing session to database
  const saveTypingSession = async (finalWpm: number, finalAccuracy: number, finalCharsTyped: number) => {
    if (!user?.email) return

    try {
      const wordsTyped = Math.floor(finalCharsTyped / 5)

      await axios.post(`${AI_API_URL}/api/typing/session/complete`, {
        user_email: user.email,
        words_typed: wordsTyped,
        characters_typed: finalCharsTyped,
        average_wpm: finalWpm,
        accuracy: finalAccuracy,
        profile_used: selectedProfile,
        input_text: inputText.substring(0, 500), // Save first 500 chars
        typos_made: typosMade,
        pauses_taken: pausesTaken,
        ai_generated: false, // TODO: Track if content was AI-generated
        humanized: false // TODO: Track if content was humanized
      })

      console.log(`✅ Typing session saved: ${wordsTyped} words, ${finalWpm} WPM`)
    } catch (error) {
      console.error('Failed to save typing session:', error)
      // Don't throw - session tracking is optional
    }
  }

  const stopTyping = async () => {
    console.log('STOP TYPING CALLED - sessionId:', sessionId, 'isTyping:', isTyping)

    // If not typing, don't do anything
    if (!isTyping) {
      console.log('Not typing, nothing to stop')
      return
    }
    
    // Immediately update UI for better responsiveness
    setIsTyping(false)
    setIsPaused(false)
    setStatus('Stopped')
    
    // Only call API if actually typing
    try {
      if (sessionId) {
        // Try session-specific endpoint first
        try {
          await axios.post(`${API_ENDPOINTS.TYPING_STOP}/${sessionId}`)
          console.log('Session stop successful')
        } catch (sessionError) {
          console.error('Session stop failed, trying global:', sessionError)
          // If session stop fails, try global stop
          await axios.post(API_ENDPOINTS.TYPING_STOP)
        }
      } else {
        // No session ID, use global stop
        await axios.post(API_ENDPOINTS.TYPING_STOP)
        console.log('Global stop successful')
      }
      
      toast.success('✋ Typing stopped successfully!')
    } catch (error) {
      console.error('All stop attempts failed:', error)
      // Even if API fails, ensure UI is stopped
      toast.error('Stop signal sent (forcing local stop)')
    }
    
    // Track typing session end
    telemetry.endTypingSession(wpm, accuracy)
    telemetry.trackEvent('typing_stopped', {
      profile: selectedProfile,
      progress,
      wordsTyped: Math.floor(charsTyped / 5),
      typosMade,
      pausesTaken
    })

    // Save typing session to database
    await saveTypingSession(wpm, accuracy, charsTyped)
    
    // Always clear session and dispatch event
    setSessionId(null)
    window.dispatchEvent(new CustomEvent('typing-stop'))
    
    // Send to Electron overlay
    if (window.electron?.ipcRenderer) {
      window.electron.ipcRenderer.send('typing-status', {
        type: 'complete',
        status: 'Stopped'
      })
    }
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
      const response = await axios.post(API_ENDPOINTS.PROFILES_GENERATE_FROM_WPM, { wpm })
      toast.success(`✨ Custom profile calibrated for ${wpm} WPM!`)
      setSelectedProfile('Custom')
      await loadProfiles() // Reload to get updated custom profile
      
      // Close test panel
      setTimeout(() => setShowWpmTest(false), 2000)
    } catch (error) {
      // Fallback: Just set the custom WPM locally
      setTestWpm(wpm)
      setSelectedProfile('Custom')
      toast.success(`✨ Custom profile set to ${wpm} WPM!`)
      localStorage.setItem('slywriter-custom-wpm', wpm.toString())
      
      // Close test panel
      setTimeout(() => setShowWpmTest(false), 2000)
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
                        const newWpm = Math.min(500, currentWpm + 10)
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
                  {showWpmTest ? 'Hide Test' : 'Calibrate Speed'}
                </span>
                {isClient && testWpm && (
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
                {isClient && testWpm && (
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
                  
                  {isClient && testWpm && (
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
              
              {isClient && testWpm && (
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
          
          {isClient && selectedProfile === 'Custom' && testWpm && (
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
            {profiles.filter(profile => profile).map((profile) => (
              <motion.button
                key={profile.name}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  setSelectedProfile(profile.name)
                  // Set custom WPM to the profile's WPM value (makes profiles work like shortcuts)
                  const profileWpm = getProfileWpm(profile.name)
                  setTestWpm(profileWpm)
                  if (typeof window !== 'undefined') {
                    localStorage.setItem('slywriter-custom-wpm', profileWpm.toString())
                  }
                  console.log(`[Profile Change] Set ${profile.name} profile WPM to ${profileWpm}`)
                }}
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
                  {profile.name === 'Slow' && '~40 WPM'}
                  {profile.name === 'Medium' && '~70 WPM'}
                  {profile.name === 'Fast' && '~100 WPM'}
                  {profile.name === 'Lightning' && '~250 WPM ⚡'}
                  {profile.name === 'Custom' && (testWpm ? `${testWpm} WPM` : 'Up to 500 WPM')}
                </div>
                
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
          Click "Calibrate Speed" above to create a profile matched to your typing speed!
        </div>
      </div>
      
      {/* Text Input & Preview Section */}
      <div className={`bg-gray-900/50 rounded-2xl p-6 backdrop-blur-sm border transition-all duration-300 ${
        !inputText && !previewMode
          ? 'border-purple-500/40 shadow-lg shadow-purple-500/20'
          : 'border-gray-800 border-purple-500/20'
      }`}>
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-3">
            <FileTextIcon className={`w-5 h-5 transition-all ${!inputText && !previewMode ? 'text-purple-400' : 'text-blue-400'}`} />
            <div>
              <h3 className={`font-semibold uppercase tracking-wider flex items-center gap-2 transition-all ${
                !inputText && !previewMode ? 'text-base text-purple-300' : 'text-sm text-gray-300'
              }`}>
                {previewMode ? 'Preview Output' : '1. Paste Your Text Here'}
              </h3>
              {!inputText && !previewMode && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-xs text-gray-400 mt-1"
                >
                  Copy any text, paste it here, and click Start below ⬇️
                </motion.p>
              )}
            </div>
            {!inputText && !previewMode && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="ml-2 px-2 py-0.5 bg-purple-500/20 rounded-full text-xs text-purple-300"
              >
                📋 Clipboard fallback enabled
              </motion.span>
            )}
          </div>
          
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
          <div className="relative">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={pasteMode
                ? "📋 Paste Mode: AI answers will be instantly pasted (Ctrl+V or right-click → Paste)"
                : "📝 Paste or type any text here... (Ctrl+V to paste from clipboard)"
              }
              className={`w-full h-[200px] bg-gray-800 rounded-lg p-4 text-white resize-none focus:outline-none transition-all ${
                !inputText
                  ? 'placeholder-gray-400 text-base focus:ring-2 focus:ring-purple-500 focus:shadow-lg focus:shadow-purple-500/20'
                  : 'placeholder-gray-600 focus:ring-2 focus:ring-purple-500/50'
              }`}
              disabled={isTyping}
            />
            {!inputText && !isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute inset-0 pointer-events-none flex items-center justify-center"
              >
                <div className="text-center space-y-3 p-6">
                  <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                    className="text-6xl opacity-20"
                  >
                    📋
                  </motion.div>
                  <div className="text-sm text-gray-500 font-medium">
                    Click here to paste or type your text
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        )}
        
        {/* Quick Tips */}
        {!inputText && !isTyping && (
          <div className="mt-4 space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <QuickTip text="📋 Copy any text + Click Start = Instant typing!" />
              <QuickTip text="🎯 Or use Ctrl+Enter with clipboard" />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <QuickTip text={`Press ${hotkeys.ai_generation} on any highlighted text for AI magic`} />
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
                <kbd className="px-2 py-1 bg-gray-800 rounded text-red-400 font-mono">{hotkeys.stop}</kbd>
              </div>
            </div>
          </motion.div>
        )}
      </div>
      
      {/* Controls */}
      <div className={`bg-gray-900/50 rounded-2xl p-6 backdrop-blur-sm border transition-all duration-300 ${
        inputText && !isTyping
          ? 'border-green-500/40 shadow-lg shadow-green-500/20'
          : 'border-gray-800 border-purple-500/20'
      }`}>
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-3">
            <PlayIcon className={`w-5 h-5 transition-all ${inputText && !isTyping ? 'text-green-400' : 'text-gray-400'}`} />
            <div>
              <h3 className={`font-semibold uppercase tracking-wider transition-all ${
                inputText && !isTyping ? 'text-base text-green-300' : 'text-sm text-gray-300'
              }`}>
                2. Click Start to Begin
              </h3>
              {inputText && !isTyping && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-xs text-gray-400 mt-1"
                >
                  Ready to type your text automatically! 🚀
                </motion.p>
              )}
            </div>
          </div>
          
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
              data-testid="start-typing"
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
              status.includes('Typing') ? 'text-green-400' :
              status.includes('Paused') ? 'text-yellow-400' :
              status.includes('Stopped') ? 'text-red-400' :
              status.includes('Finished') ? 'text-blue-400' :
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

      {/* Out of Words Modal */}
      <OutOfWordsModal
        isOpen={showOutOfWordsModal}
        onClose={() => setShowOutOfWordsModal(false)}
        wordsRemaining={wordsRemaining}
        userEmail={user?.email || ''}
        referralCode={user?.referralCode || ''}
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
    'Slow': 40,
    'Medium': 70,
    'Fast': 100,
    'Lightning': 250,
    'Custom': 85,  // Default for custom if no test taken
    'Essay': 45
  }

  return wpmMap[profileName || 'Medium'] || 100
}      {/* Advanced Typing Settings */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <SlidersIcon className="w-4 h-4 text-purple-400" />
            Advanced Settings
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Typo Rate - controls natural typo frequency */}
          <div>
            <label className="flex items-center justify-between text-sm font-medium text-gray-300 mb-2">
              <span>Natural Typo Rate</span>
              <span className="text-purple-400 font-mono">{typoRate}%</span>
            </label>
            <input
              type="range"
              min="0"
              max="5"
              step="0.5"
              value={typoRate}
              onChange={(e) => setTypoRate(parseFloat(e.target.value))}
              className="w-full accent-purple-500"
              disabled={isTyping}
            />
          </div>
        </div>
        
        {/* Toggle Options */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <label className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-700/50 transition-colors group relative">
            <input
              type="checkbox"
              checked={humanMode}
              onChange={(e) => {
                setHumanMode(e.target.checked)
                if (e.target.checked) {
                  toast.success('🎭 Human mode activated!')
                }
              }}
              className="w-5 h-5 text-purple-500 rounded"
              disabled={isTyping}
            />
            <div className="flex-1">
              <span className="text-white font-medium text-sm">Natural Typos</span>
              <p className="text-xs text-gray-400">2% instant fixes</p>
            </div>
            {/* Human Mode Tooltip */}
            <div className="absolute bottom-full left-0 mb-2 w-72 p-3 bg-gray-900 rounded-lg shadow-xl border border-blue-500/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              <p className="text-xs text-gray-200">
                <span className="text-blue-300 font-semibold">🎭 Natural Typing Patterns:</span><br/>
                • Makes occasional typos (2% chance)<br/>
                • Immediately corrects them (like real typing)<br/>
                • Keyboard proximity errors (hit adjacent keys)<br/>
                • Works WITH delayed corrections (reduced rate)<br/>
                • Natural pauses and speed variations<br/>
                <span className="text-green-300 mt-1 inline-block">Makes typing look genuinely human!</span>
              </p>
            </div>
          </label>
          
          <label className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-700/50 transition-colors group relative">
            <input
              type="checkbox"
              checked={grammarlyCorrectionEnabled}
              onChange={(e) => {
                setGrammarlyCorrectionEnabled(e.target.checked)
                if (e.target.checked) {
                  toast.success('✏️ Delayed corrections enabled!')
                }
              }}
              className="w-5 h-5 text-purple-500 rounded"
              disabled={isTyping}
            />
            <div className="flex-1">
              <span className="text-white font-medium text-sm">Delayed Correction</span>
              <p className="text-xs text-gray-400">Makes typos then fixes them</p>
            </div>
            {/* Delayed Correction Tooltip */}
            <div className="absolute bottom-full left-0 mb-2 w-72 p-3 bg-gray-900 rounded-lg shadow-xl border border-green-500/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              <p className="text-xs text-gray-200">
                <span className="text-green-300 font-semibold">✏️ Simulates autocorrect tools:</span><br/>
                • Makes word typos (teh, taht, etc.)<br/>
                • Continues typing 20-40 chars<br/>
                • Then goes back to fix mistakes<br/>
                • Configurable delay (1-5 seconds)<br/>
                • Max 2 pending corrections at once<br/>
                • Works WITH natural typos (smart balance)<br/>
                • Shows you're using "writing assistance"<br/>
                <span className="text-yellow-300 mt-1 inline-block">Perfect for making AI text look human!</span>
              </p>
            </div>
          </label>
          
          {/* Correction Delay Slider - only show when enabled */}
          {grammarlyCorrectionEnabled && (
            <div className="ml-8 mt-2 p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-400">Correction Delay</span>
                <span className="text-xs font-medium text-purple-400">{grammarlyCorrectionDelay}s</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="0.5"
                value={grammarlyCorrectionDelay}
                onChange={(e) => setGrammarlyCorrectionDelay(parseFloat(e.target.value))}
                className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                disabled={isTyping}
              />
              <div className="flex justify-between text-[10px] text-gray-500 mt-1">
                <span>Quick</span>
                <span>Natural</span>
                <span>Slow</span>
              </div>
            </div>
          )}
          
          <label className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-700/50 transition-colors group relative">
            <input
              type="checkbox"
              checked={pasteMode}
              onChange={(e) => {
                setPasteMode(e.target.checked)
                localStorage.setItem('slywriter-paste-mode', e.target.checked.toString())
                toast.success(e.target.checked ? '⚡ Paste mode ON - Instant answers!' : '⌨️ Typing mode ON - Natural typing!')
              }}
              className="w-5 h-5 text-purple-500 rounded"
              disabled={isTyping}
            />
            <div className="flex-1">
              <span className="text-white font-medium text-sm">Paste Mode</span>
              <p className="text-xs text-gray-400">Instant paste</p>
            </div>
            {/* Enhanced Paste Mode Tooltip */}
            <div className="absolute bottom-full left-0 mb-2 w-80 p-3 bg-gray-900 rounded-lg shadow-xl border border-purple-500/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              <p className="text-xs text-gray-200">
                <span className="text-purple-300 font-semibold">⚡ Instant Paste vs Natural Typing:</span><br/>
                <span className="text-green-300">ON (Paste):</span> Instant paste for unmonitored work<br/>
                • Homework, personal projects<br/>
                • No screen recording<br/>
                <span className="text-blue-300">OFF (Type):</span> Natural typing for monitored tests<br/>
                • Online exams with proctoring<br/>
                • Screen-recorded assessments<br/>
                <span className="text-yellow-300 mt-1 inline-block">Toggle based on your situation!</span>
              </p>
            </div>
          </label>
          
          <label className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-700/50 transition-colors group relative">
            <input
              type="checkbox"
              checked={autoClearTextbox}
              onChange={(e) => {
                setAutoClearTextbox(e.target.checked)
                if (e.target.checked) {
                  toast.success('🧹 Auto-clear enabled for rapid Q&A!')
                }
              }}
              className="w-5 h-5 text-purple-500 rounded"
              disabled={isTyping}
            />
            <div className="flex-1">
              <span className="text-white font-medium text-sm">Auto-Clear</span>
              <p className="text-xs text-gray-400">After typing</p>
            </div>
            {/* Enhanced Auto-Clear Tooltip */}
            <div className="absolute bottom-full right-0 mb-2 w-72 p-3 bg-gray-900 rounded-lg shadow-xl border border-cyan-500/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              <p className="text-xs text-gray-200">
                <span className="text-cyan-300 font-semibold">🧹 Rapid-Fire Q&A Mode:</span><br/>
                • Auto-clears textbox after each answer<br/>
                • Perfect for multiple choice tests<br/>
                • No manual clearing needed<br/>
                <span className="text-yellow-300">Workflow:</span><br/>
                1. Paste question → Get answer<br/>
                2. Textbox auto-clears<br/>
                3. Paste next question → Repeat!<br/>
                <span className="text-green-300 mt-1 inline-block">10x faster for quiz sequences!</span>
              </p>
            </div>
          </label>
          
          {/* AI Filler - PRO FEATURE */}
          <label className={`flex items-center gap-3 p-3 bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-lg transition-all group relative border border-purple-500/30 ${!isPremium ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:from-purple-900/40 hover:to-pink-900/40'}`}>
            <input
              type="checkbox"
              checked={aiFillerEnabled && isPremium}
              onChange={(e) => {
                if (!isPremium) {
                  toast.error('AI Filler requires Pro or Premium plan', { icon: '🔒' })
                  return
                }
                setAiFillerEnabled(e.target.checked)
                localStorage.setItem('slywriter-ai-filler', e.target.checked.toString())
                if (e.target.checked) {
                  toast.success('🎭 AI Filler activated!', { icon: '✨' })
                }
              }}
              className="w-5 h-5 text-purple-500 rounded"
              disabled={isTyping || !isPremium}
            />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className={`font-medium text-sm ${!isPremium ? 'text-gray-400' : 'text-white'}`}>AI Filler</span>
                <span className="text-xs bg-gradient-to-r from-blue-500 to-purple-500 px-2 py-0.5 rounded-full text-white font-bold">PRO</span>
              </div>
              <p className="text-xs text-gray-400">Realistic drafts{!isPremium ? ' - Requires Pro or Premium' : ''}</p>
            </div>
            {/* Premium Tooltip */}
            <div className="absolute bottom-full right-0 mb-2 w-80 p-3 bg-gradient-to-br from-purple-900 to-pink-900 rounded-lg shadow-xl border border-purple-500/40 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              <p className="text-xs text-gray-200">
                <span className="text-yellow-300 font-bold">👑 PREMIUM ONLY - Ultimate Realism</span><br/>
                <span className="text-purple-300 font-semibold">🎭 How it works:</span><br/>
                • Types a "draft thought" (contextual)<br/>
                • Pauses like "hmm, that's not right"<br/>
                • Deletes the draft<br/>
                • Types the real answer<br/>
                <span className="text-cyan-300">Example:</span> Types "The answer is..." → deletes → types actual answer<br/>
                <span className="text-pink-300 font-bold mt-1 inline-block">🔥 Most realistic feature - 100% undetectable!</span>
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
                  <span className="text-sm font-semibold text-purple-300">⚡ Paste Mode Active (Instant):</span>
                  <p className="text-xs text-gray-400 mt-1">
                    <span className="text-yellow-400 font-semibold">The Workflow:</span><br/>
                    1️⃣ Highlight question text<br/>
                    2️⃣ Press <kbd className="px-1 py-0.5 bg-gray-800 rounded text-purple-300">{hotkeys.ai_generation}</kbd> (AI generates answer)<br/>
                    3️⃣ Answer is humanized (if enabled)<br/>
                    4️⃣ Review popup shows (if enabled)<br/>
                    5️⃣ Answer is <span className="text-green-400 font-bold">INSTANTLY PASTED</span> - no typing animation!
                  </p>
                  <p className="text-xs text-gray-300 mt-2 bg-gray-800/50 p-2 rounded">
                    💡 <span className="font-semibold">Use when:</span> Not being monitored, need speed over realism
                  </p>
                </div>
              )}
              {!pasteMode && (
                <div>
                  <span className="text-sm font-semibold text-blue-300">🎭 Typing Mode Active (Realistic):</span>
                  <p className="text-xs text-gray-400 mt-1">
                    Same workflow but answer is <span className="text-blue-400 font-bold">TYPED OUT</span> with human-like patterns, typos, and pauses.
                  </p>
                  <p className="text-xs text-gray-300 mt-2 bg-gray-800/50 p-2 rounded">
                    💡 <span className="font-semibold">Use when:</span> Being monitored, need realistic typing
                  </p>
                </div>
              )}
              {autoClearTextbox && (
                <div>
                  <span className="text-sm font-semibold text-blue-300">🔄 Auto-Clear Active:</span>
                  <p className="text-xs text-gray-400 mt-1">
                    After paste/type completes, textbox clears automatically. Perfect for multiple questions!
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
