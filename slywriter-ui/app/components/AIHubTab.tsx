'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Wand2, RefreshCw, Copy, Check, Brain, Zap, BookOpen, Briefcase, Heart, Gamepad2, Code, Palette, AlertCircleIcon, XCircleIcon, BrainIcon, SparklesIcon, X, Lightbulb, Info, TrendingUp, MessageSquare, CheckCircle2, Target, Rocket } from 'lucide-react'
import { FirstTimeHelper } from './FeatureTooltips'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useHotkeys } from '../hooks/useHotkeys'

// Use direct Render URL with proper error handling - for beta testing with 20 users
const API_URL = 'https://slywriterapp.onrender.com'
const LOCAL_API_URL = 'http://127.0.0.1:8000'  // Local typing server

interface AITemplate {
  id: string
  name: string
  icon: any
  prompt: string
  description: string
}

const templates: AITemplate[] = [
  { id: 'creative', name: 'Creative Writing', icon: Palette, prompt: 'Write a creative and engaging', description: 'Stories, narratives, and creative content' },
  { id: 'professional', name: 'Professional', icon: Briefcase, prompt: 'Write a professional and formal', description: 'Business emails, reports, and documents' },
  { id: 'academic', name: 'Academic', icon: BookOpen, prompt: 'Write an academic and scholarly', description: 'Essays, research papers, and studies' },
  { id: 'casual', name: 'Casual', icon: Heart, prompt: 'Write a casual and friendly', description: 'Personal messages and informal content' },
  { id: 'technical', name: 'Technical', icon: Code, prompt: 'Write a technical and detailed', description: 'Documentation, guides, and tutorials' },
  { id: 'gaming', name: 'Gaming', icon: Gamepad2, prompt: 'Write gaming-related', description: 'Game reviews, guides, and discussions' },
]

interface AIGenerationSettings {
  // Template
  selectedTemplate: string
  
  // Response Configuration
  response_type: 'short_response' | 'essay'
  response_length: number // 1-5 for short, pages for essay
  academic_format: string
  required_pages: number
  
  // Writing Style Settings
  grade_level: number
  tone: string
  
  // Processing Modes
  humanizer_enabled: boolean  // Whether to humanize after generation
  review_mode: boolean        // Whether to review before output
  learning_mode: boolean      // Whether to save as lesson
  auto_output: boolean        // Whether to auto-type/paste after generation
  auto_output_delay: number   // Seconds to wait before auto-output (1-10)
}

export default function AIHubTab() {
  const hotkeys = useHotkeys()
  const [input, setInput] = useState('')
  const [output, setOutput] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [history, setHistory] = useState<Array<{input: string, output: string, timestamp: string}>>([])
  const [countdown, setCountdown] = useState<number | null>(null)
  const [countdownInterval, setCountdownInterval] = useState<NodeJS.Timeout | null>(null)
  const [showReviewModal, setShowReviewModal] = useState(false)
  const [reviewText, setReviewText] = useState('')
  const hasLoadedSettings = useRef(false)
  
  // Debug review modal state
  useEffect(() => {
    console.log('[AIHub] Review modal state changed:', showReviewModal)
    if (showReviewModal) {
      console.log('[AIHub] Review text:', reviewText.substring(0, 50) + '...')
    }
  }, [showReviewModal, reviewText])
  
  // ALL settings in one state object with defaults
  const [settings, setSettings] = useState<AIGenerationSettings>({
    selectedTemplate: 'creative',
    response_type: 'short_response',
    response_length: 3,
    academic_format: 'None',
    required_pages: 1,
    grade_level: 11,
    tone: 'Neutral',
    humanizer_enabled: true,
    review_mode: false,
    learning_mode: false,
    auto_output: false,
    auto_output_delay: 5
  })

  // Load settings ONCE on mount
  useEffect(() => {
    if (hasLoadedSettings.current) return
    hasLoadedSettings.current = true
    
    console.log('[AIHub] Loading settings on mount...')
    
    // Load history
    const savedHistory = localStorage.getItem('aiHistory')
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory))
      } catch (e) {
        console.error('Failed to parse history:', e)
      }
    }
    
    // Load all settings
    const savedSettings = localStorage.getItem('slywriter-ai-hub-settings')
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings)
        console.log('[AIHub] Loaded saved settings:', parsed)
        console.log('[AIHub] Review mode in saved settings:', parsed.review_mode)
        
        // Ensure all properties exist (for backward compatibility)
        const defaultSettings: AIGenerationSettings = {
          selectedTemplate: 'creative',
          response_type: 'short_response',
          response_length: 3,
          academic_format: 'None',
          required_pages: 1,
          grade_level: 11,
          tone: 'Neutral',
          humanizer_enabled: true,
          review_mode: false,
          learning_mode: false,
          auto_output: false,
          auto_output_delay: 5
        }
        
        const mergedSettings = {
          ...defaultSettings, // default values
          ...parsed          // saved values override defaults
        }
        console.log('[AIHub] Merged settings with defaults:', mergedSettings)
        console.log('[AIHub] Review mode after merge:', mergedSettings.review_mode)
        setSettings(mergedSettings)
      } catch (e) {
        console.error('Failed to parse settings:', e)
      }
    } else {
      console.log('[AIHub] No saved settings found, using defaults')
    }
    
    // Sync with global auto-humanize setting
    const autoHumanize = localStorage.getItem('slywriter-auto-humanize')
    if (autoHumanize !== null) {
      setSettings(prev => ({
        ...prev,
        humanizer_enabled: autoHumanize === 'true'
      }))
    }
  }, [])
  
  // Listen for external review requests (from overlay/hotkey) - no dependencies to ensure it stays registered
  useEffect(() => {
    const handleShowReview = (event: CustomEvent) => {
      console.log('🎉🎉🎉 [AIHub] External review requested from hotkey/overlay!')
      console.log('🎉 [AIHub] Event detail:', event.detail)
      console.log('🎉 [AIHub] Text received:', event.detail?.text?.substring(0, 50) + '...')
      console.log('🎉 [AIHub] Current showReviewModal state:', showReviewModal)
      
      if (event.detail?.text) {
        console.log('🎉 [AIHub] Setting review text and showing modal!')
        setOutput(event.detail.text)
        setReviewText(event.detail.text)
        setShowReviewModal(true)
      } else {
        console.log('❌ [AIHub] No text in event detail!')
      }
    }
    
    window.addEventListener('showAIReview', handleShowReview as EventListener)
    console.log('[AIHub] Listening for showAIReview events')
    
    return () => {
      window.removeEventListener('showAIReview', handleShowReview as EventListener)
    }
  }, []) // Empty dependency array - register once
  
  // Listen for external AI generation requests (from overlay/hotkey)
  useEffect(() => {
    const handleGenerateAI = async (event: CustomEvent) => {
      console.log('[AIHub] External AI generation requested:', event.detail)
      
      if (event.detail?.text) {
        setInput(event.detail.text)
        
        // Wait a tick for state to update
        setTimeout(() => {
          generateAI()
        }, 100)
      }
    }
    
    window.addEventListener('generateAI', handleGenerateAI as any)
    
    // Also expose the function globally for direct access
    ;(window as any).aiHubGenerateAI = (text: string) => {
      console.log('[AIHub] Direct AI generation requested:', text)
      setInput(text)
      setTimeout(() => {
        generateAI()
      }, 100)
    }
    
    return () => {
      window.removeEventListener('generateAI', handleGenerateAI as any)
      delete (window as any).aiHubGenerateAI
    }
  }, [input, settings]) // Include dependencies
  
  // Save settings whenever they change (after initial load)
  useEffect(() => {
    if (!hasLoadedSettings.current) return
    
    console.log('[AIHub] Saving settings:', settings)
    localStorage.setItem('slywriter-ai-hub-settings', JSON.stringify(settings))
    
    // Also sync humanizer setting globally
    localStorage.setItem('slywriter-auto-humanize', settings.humanizer_enabled.toString())
  }, [settings])
  
  // Listen for humanize changes from other tabs
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'slywriter-auto-humanize' && e.newValue !== null) {
        console.log('[AIHub] Auto-humanize changed from another tab:', e.newValue)
        setSettings(prev => ({
          ...prev,
          humanizer_enabled: e.newValue === 'true'
        }))
      }
    }
    
    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  // Save history whenever it changes
  useEffect(() => {
    if (history.length > 0) {
      localStorage.setItem('aiHistory', JSON.stringify(history))
    }
  }, [history])

  // Auto-output countdown function
  const startAutoOutputCountdown = (text: string) => {
    const delay = settings.auto_output_delay
    setCountdown(delay)
    
    const interval = setInterval(() => {
      setCountdown(prev => {
        if (prev === null || prev <= 1) {
          clearInterval(interval)
          autoOutput(text)
          return null
        }
        return prev - 1
      })
    }, 1000)
    
    setCountdownInterval(interval)
  }

  const cancelCountdown = () => {
    if (countdownInterval) {
      clearInterval(countdownInterval)
      setCountdownInterval(null)
    }
    setCountdown(null)
    toast.success('Auto-output cancelled')
  }

  const autoOutput = async (text: string) => {
    const pasteMode = localStorage.getItem('slywriter-paste-mode') === 'true'
    
    if (pasteMode) {
      navigator.clipboard.writeText(text)
      toast.success('📋 Text copied to clipboard!')
    } else {
      try {
        // Get the current typing profile and WPM from localStorage
        const savedProfile = localStorage.getItem('slywriter-selected-profile') || 'Medium'
        const savedWpm = localStorage.getItem('slywriter-custom-wpm')
        
        console.log('[AIHub] Starting auto-output with profile:', savedProfile, 'WPM:', savedWpm)
        
        const response = await fetch(`${LOCAL_API_URL}/api/typing/start`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text,
            profile: savedProfile,
            custom_wpm: savedProfile === 'Custom' ? parseInt(savedWpm || '70') : null,
            preview_mode: false
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.success) {
            toast.success('⌨️ Typing started!')
          }
        } else {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
      } catch (error) {
        console.error('Failed to start typing:', error)
        toast.error('Failed to start typing')
      }
    }
  }

  const generateAI = async () => {
    console.log('[AIHub] generateAI function called!')
    console.log('[AIHub] Input value:', input)
    
    if (!input.trim()) {
      console.log('[AIHub] No input text, showing error')
      toast.error('Please enter some text')
      return
    }
    
    console.log('[AIHub] Starting generation with settings:', settings)
    console.log('[AIHub] Review mode enabled?', settings.review_mode)

    setIsGenerating(true)
    
    try {
      // Build the prompt
      const template = templates.find(t => t.id === settings.selectedTemplate)
      let prompt = `${template?.prompt || 'Write'} response about: ${input}\n\n`
      
      if (settings.response_type === 'short_response') {
        const lengths = {
          1: '1-2 sentences',
          2: '2-4 sentences',
          3: '4-8 sentences',
          4: '8-15 sentences',
          5: '15+ sentences'
        }
        prompt += `Length: ${lengths[settings.response_length as keyof typeof lengths]}\n`
      } else {
        prompt += `Format: ${settings.required_pages} page ${settings.academic_format} essay\n`
      }
      
      prompt += `Grade level: ${settings.grade_level}\n`
      prompt += `Tone: ${settings.tone}\n`
      
      // Make API call using axios (works better with CORS on Render)
      console.log('[AIHub] Making API call to:', `${API_URL}/api/ai/generate`)
      console.log('[AIHub] With prompt:', prompt)
      
      let response
      let generatedText
      
      // Use axios directly since it works properly with CORS
      console.log('[AIHub] Using axios for API call')
      
      try {
        response = await axios.post(`${API_URL}/api/ai/generate`, {
          prompt,
          settings
        }, {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          timeout: 30000,
          withCredentials: false  // Important for CORS
        })
        
        console.log('[AIHub] Axios response received:', response.data)
        generatedText = response.data.text || response.data.content || 'Generated content'
        
      } catch (axiosError: any) {
        console.error('[AIHub] Axios error details:', axiosError)
        
        // If Render server is sleeping, provide mock response for testing
        if (axiosError.code === 'ERR_NETWORK' || axiosError.response?.status === 503) {
          console.log('[AIHub] Server appears to be sleeping, using mock response')
          
          // Provide a mock response based on template
          const mockResponses: any = {
            'creative': 'The canvas of imagination stretches before us, inviting exploration of ideas both profound and whimsical. Each word becomes a brushstroke, painting narratives that dance between reality and dreams.',
            'professional': 'I am writing to present a comprehensive analysis of the matter at hand. After careful consideration of all relevant factors, I have prepared this detailed assessment for your review.',
            'academic': 'This analysis examines the fundamental principles underlying the subject matter. Through systematic evaluation of empirical evidence and theoretical frameworks, we establish a foundation for further discourse.',
            'casual': 'Hey! So I was thinking about this topic and it\'s actually pretty interesting. There are so many different angles to consider, and each one brings something unique to the table.',
            'technical': 'The implementation architecture consists of modular components designed for scalability and maintainability. Each module interfaces through well-defined APIs, ensuring loose coupling and high cohesion.',
            'gaming': 'The gameplay mechanics create an immersive experience that challenges players while maintaining accessibility. Level design encourages exploration and rewards strategic thinking.'
          }
          
          generatedText = mockResponses[settings.selectedTemplate] || mockResponses['creative']
          
          // Adjust length if needed
          if (settings.response_type === 'essay') {
            generatedText = generatedText + ' ' + generatedText + ' ' + generatedText // Triple for essay length
          }
          
          toast('AI server is waking up. Using sample text for now. Try again in 30 seconds for real AI generation.', { 
            icon: '⚠️',
            duration: 6000 
          })
        } else {
          throw axiosError
        }
      }
      
      console.log('[AIHub] Generated text:', generatedText?.substring(0, 100) + '...')
      
      // Apply humanizer if enabled
      if (settings.humanizer_enabled && generatedText) {
        try {
          // Try axios for humanizer
          const humanizeResponse = await axios.post(`${API_URL}/api/ai/humanize`, {
            text: generatedText,
            settings: {
              grade_level: settings.grade_level,
              tone: settings.tone,
              style: 'Natural'
            }
          }, {
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            },
            timeout: 15000,
            withCredentials: false
          })
          
          if (humanizeResponse.data?.text) {
            generatedText = humanizeResponse.data.text
            console.log('[AIHub] Text humanized successfully')
          }
        } catch (humanizeError: any) {
          console.log('[AIHub] Humanizer failed, using original text:', humanizeError.message)
          // Use original text if humanizer fails - this is fine
        }
      }
      
      setOutput(generatedText)
      
      // Add to history
      const newEntry = {
        input,
        output: generatedText,
        timestamp: new Date().toISOString()
      }
      setHistory(prev => [newEntry, ...prev.slice(0, 9)])
      
      // Handle output modes
      console.log('[AIHub] Output mode check:', {
        review_mode: settings.review_mode,
        auto_output: settings.auto_output,
        generatedText: generatedText.substring(0, 50) + '...'
      })
      
      if (settings.review_mode) {
        // Show review modal
        console.log('[AIHub] Review mode is ON - showing modal')
        setReviewText(generatedText)
        setShowReviewModal(true)
        toast.success('✅ Generated! Review the output before proceeding.')
      } else if (settings.auto_output) {
        console.log('[AIHub] Auto-output mode is ON - starting countdown')
        startAutoOutputCountdown(generatedText)
      } else {
        console.log('[AIHub] Standard mode - just showing toast')
        toast.success('✨ AI response generated!')
      }
      
      // Create lesson if learning mode is on
      if (settings.learning_mode && generatedText) {
        try {
          const lessonResponse = await axios.post(`${API_URL}/api/learning/create-lesson`, {
            topic: input.substring(0, 100),
            content: generatedText,
            method: 'ai_generated'
          }, {
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            },
            timeout: 5000,
            withCredentials: false
          })
          
          if (lessonResponse.data?.success) {
            console.log('[AIHub] Lesson created successfully:', lessonResponse.data.lesson_id)
            toast.success('📚 Lesson saved! View it in the Smart Learn tab', { 
              duration: 4000,
              icon: '🎓'
            })
          }
        } catch (error: any) {
          console.error('[AIHub] Failed to create lesson:', error)
          // Show user-friendly error but don't block the main flow
          if (error.response?.status === 404) {
            console.log('[AIHub] Learning endpoint not found - server may need update')
          } else if (error.code === 'ERR_NETWORK') {
            console.log('[AIHub] Learning service unavailable - server may be down')
          }
          // Don't show error toast - learning is a bonus feature
        }
      }
      
    } catch (error: any) {
      console.error('[AIHub] Generation failed:', error)
      console.error('[AIHub] Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      })
      
      // Provide user-friendly error messages
      if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
        toast.error('⚠️ AI server is starting up. Please try again in 30 seconds.', { duration: 5000 })
      } else if (error.response?.status === 500) {
        toast.error('Server error: The AI service encountered an issue. Please try again.', { duration: 4000 })
      } else if (error.response?.status === 429) {
        toast.error('Rate limit reached. Please wait a moment before trying again.', { duration: 4000 })
      } else if (error.message?.includes('timeout')) {
        toast.error('Request timed out. The server may be busy. Please try again.', { duration: 4000 })
      } else {
        toast.error('Failed to generate content. Please check your connection and try again.', { duration: 4000 })
      }
    } finally {
      console.log('[AIHub] Generation complete, isGenerating = false')
      setIsGenerating(false)
    }
  }

  const copyOutput = () => {
    if (output) {
      navigator.clipboard.writeText(output)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      toast.success('Copied to clipboard!')
    }
  }

  const startTyping = async () => {
    if (!output) {
      toast.error('No output to type')
      return
    }
    
    try {
      // Get the current typing profile and WPM from localStorage
      const savedProfile = localStorage.getItem('slywriter-selected-profile') || 'Medium'
      const savedWpm = localStorage.getItem('slywriter-custom-wpm')
      
      console.log('[AIHub] Starting manual typing with profile:', savedProfile, 'WPM:', savedWpm)
      
      const response = await fetch(`${LOCAL_API_URL}/api/typing/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: output,
          profile: savedProfile,
          custom_wpm: savedProfile === 'Custom' ? parseInt(savedWpm || '70') : null,
          preview_mode: false
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          toast.success('⌨️ Typing started!')
        }
      } else {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
    } catch (error) {
      console.error('Failed to start typing:', error)
      toast.error('Failed to start typing')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-2xl p-8 backdrop-blur-sm border border-blue-500/20"
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="p-3 bg-blue-500/20 rounded-xl">
            <Brain className="w-8 h-8 text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              AI Content Writer
            </h2>
            <p className="text-gray-400 mt-1">Generate high-quality content with advanced AI</p>
          </div>
        </div>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-3 mt-6">
          <div className="bg-gray-800/50 rounded-lg p-3 text-center">
            <Zap className="w-4 h-4 text-yellow-400 mx-auto mb-1" />
            <p className="text-[10px] text-gray-400">Instant</p>
            <p className="text-xs font-semibold text-white">Generation</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3 text-center">
            <TrendingUp className="w-4 h-4 text-green-400 mx-auto mb-1" />
            <p className="text-[10px] text-gray-400">6 Styles</p>
            <p className="text-xs font-semibold text-white">Templates</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3 text-center">
            <MessageSquare className="w-4 h-4 text-blue-400 mx-auto mb-1" />
            <p className="text-[10px] text-gray-400">Natural</p>
            <p className="text-xs font-semibold text-white">Output</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3 text-center">
            <SparklesIcon className="w-4 h-4 text-purple-400 mx-auto mb-1" />
            <p className="text-[10px] text-gray-400">Auto</p>
            <p className="text-xs font-semibold text-white">Humanize</p>
          </div>
        </div>
      </motion.div>

      {/* Content Templates */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider">Content Templates</h3>
          <div className="text-xs text-gray-500">
            <Target className="w-3 h-3 inline mr-1" />
            {templates.find(t => t.id === settings.selectedTemplate)?.name || 'None'} selected
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {templates.map(template => (
            <motion.button
              key={template.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                setSettings(prev => ({
                  ...prev,
                  selectedTemplate: template.id
                }))
              }}
              className={`p-4 rounded-lg border transition-all ${
                settings.selectedTemplate === template.id
                  ? 'bg-gradient-to-br from-purple-500/20 to-blue-500/20 border-purple-500 shadow-lg shadow-purple-500/20'
                  : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'
              }`}
            >
              <template.icon className={`w-5 h-5 mx-auto mb-2 ${
                settings.selectedTemplate === template.id ? 'text-purple-400' : 'text-gray-400'
              }`} />
              <div className="text-xs font-medium">{template.name}</div>
              <div className="text-[10px] text-gray-400 mt-1">{template.description}</div>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* AI Generation Settings */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider">AI Generation Settings</h3>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Info className="w-3 h-3" />
            All settings auto-save
          </div>
        </div>
        
        <div className="space-y-4">
          {/* Response Type */}
          <div>
            <label className="block text-sm font-medium mb-2">Response Type</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setSettings(prev => ({...prev, response_type: 'short_response'}))}
                className={`px-4 py-2 rounded-lg border transition-all ${
                  settings.response_type === 'short_response'
                    ? 'bg-purple-500/20 border-purple-500'
                    : 'bg-gray-800 border-gray-600'
                }`}
              >
                Short Response
              </button>
              <button
                onClick={() => setSettings(prev => ({...prev, response_type: 'essay'}))}
                className={`px-4 py-2 rounded-lg border transition-all ${
                  settings.response_type === 'essay'
                    ? 'bg-purple-500/20 border-purple-500'
                    : 'bg-gray-800 border-gray-600'
                }`}
              >
                Essay
              </button>
            </div>
          </div>
          
          {/* Length Control */}
          {settings.response_type === 'short_response' ? (
            <div>
              <label className="flex items-center justify-between text-sm font-medium mb-2">
                <span>Response Length</span>
                <span className="text-purple-400">
                  {settings.response_length === 1 && '1-2 sentences'}
                  {settings.response_length === 2 && '2-4 sentences'}
                  {settings.response_length === 3 && '4-8 sentences'}
                  {settings.response_length === 4 && '8-15 sentences'}
                  {settings.response_length === 5 && '15+ sentences'}
                </span>
              </label>
              <input
                type="range"
                min="1"
                max="5"
                value={settings.response_length}
                onChange={(e) => setSettings(prev => ({...prev, response_length: Number(e.target.value)}))}
                className="w-full accent-purple-500"
              />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Pages</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={settings.required_pages}
                  onChange={(e) => setSettings(prev => ({...prev, required_pages: Number(e.target.value)}))}
                  className="w-full bg-gray-800 rounded-lg px-3 py-2 border border-gray-600 focus:border-purple-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Format</label>
                <select
                  value={settings.academic_format}
                  onChange={(e) => setSettings(prev => ({...prev, academic_format: e.target.value}))}
                  className="w-full bg-gray-800 rounded-lg px-3 py-2 border border-gray-600 focus:border-purple-500 focus:outline-none"
                >
                  <option value="None">None</option>
                  <option value="MLA">MLA</option>
                  <option value="APA">APA</option>
                  <option value="Chicago">Chicago</option>
                </select>
              </div>
            </div>
          )}
          
          {/* Writing Parameters */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Grade Level</label>
              <select
                value={settings.grade_level}
                onChange={(e) => setSettings(prev => ({...prev, grade_level: Number(e.target.value)}))}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 border border-gray-600 focus:border-purple-500 focus:outline-none"
              >
                {[6,7,8,9,10,11,12,13,14,15,16].map(level => (
                  <option key={level} value={level}>
                    {level <= 12 ? `Grade ${level}` : `College (${level - 12} year)`}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Tone</label>
              <select
                value={settings.tone}
                onChange={(e) => setSettings(prev => ({...prev, tone: e.target.value}))}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 border border-gray-600 focus:border-purple-500 focus:outline-none"
              >
                <option value="Neutral">Neutral</option>
                <option value="Formal">Formal</option>
                <option value="Casual">Casual</option>
                <option value="Academic">Academic</option>
                <option value="Professional">Professional</option>
                <option value="Creative">Creative</option>
                <option value="Humorous">Humorous</option>
              </select>
            </div>
          </div>
          
          {/* Mode Toggles */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-4 border-t border-gray-700">
            <label className={`flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-all ${
              settings.humanizer_enabled 
                ? 'bg-purple-500/20 border border-purple-500/50' 
                : 'bg-gray-800/50 hover:bg-gray-700/50'
            }`}>
              <input
                type="checkbox"
                checked={settings.humanizer_enabled}
                onChange={(e) => {
                  console.log('[AIHub] Auto-Humanize toggled:', e.target.checked)
                  setSettings(prev => ({...prev, humanizer_enabled: e.target.checked}))
                }}
                className="w-4 h-4 text-purple-500 rounded"
              />
              <div>
                <div className="text-xs font-medium">✨ Auto-Humanize</div>
                <div className="text-[10px] text-gray-400">Natural output</div>
              </div>
            </label>
            
            <label className={`flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-all ${
              settings.review_mode
                ? 'bg-green-500/20 border border-green-500/50'
                : 'bg-gray-800/50 hover:bg-gray-700/50'
            }`}>
              <input
                type="checkbox"
                checked={settings.review_mode}
                onChange={(e) => {
                  console.log('[AIHub] Review checkbox clicked, new value:', e.target.checked)
                  setSettings(prev => {
                    const newSettings = {...prev, review_mode: e.target.checked}
                    console.log('[AIHub] New settings after review toggle:', newSettings)
                    return newSettings
                  })
                }}
                className="w-4 h-4 text-purple-500 rounded"
              />
              <div>
                <div className="text-xs font-medium">👁️ Review</div>
                <div className="text-[10px] text-gray-400">Preview first</div>
              </div>
            </label>
            
            <label className={`flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-all ${
              settings.auto_output
                ? 'bg-blue-500/20 border border-blue-500/50'
                : 'bg-gray-800/50 hover:bg-gray-700/50'
            }`}>
              <input
                type="checkbox"
                checked={settings.auto_output}
                onChange={(e) => {
                  console.log('[AIHub] Auto-Output toggled:', e.target.checked)
                  setSettings(prev => ({...prev, auto_output: e.target.checked}))
                }}
                className="w-4 h-4 text-purple-500 rounded"
              />
              <div>
                <div className="text-xs font-medium">🚀 Auto-Output</div>
                <div className="text-[10px] text-gray-400">After {settings.auto_output_delay}s</div>
              </div>
            </label>
            
            <label className={`flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-all ${
              settings.learning_mode
                ? 'bg-yellow-500/20 border border-yellow-500/50'
                : 'bg-gray-800/50 hover:bg-gray-700/50'
            }`}>
              <input
                type="checkbox"
                checked={settings.learning_mode}
                onChange={(e) => {
                  console.log('[AIHub] Auto-Learn toggled:', e.target.checked)
                  setSettings(prev => ({...prev, learning_mode: e.target.checked}))
                }}
                className="w-4 h-4 text-purple-500 rounded"
              />
              <div>
                <div className="text-xs font-medium">🧠 Auto-Learn</div>
                <div className="text-[10px] text-gray-400">Save to Smart Learn tab</div>
              </div>
            </label>
          </div>
          
          {/* Auto-output delay slider (only show when auto-output is enabled) */}
          {settings.auto_output && (
            <div className="pt-2">
              <label className="flex items-center justify-between text-xs font-medium mb-2">
                <span>Auto-output delay</span>
                <span className="text-purple-400">{settings.auto_output_delay}s</span>
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={settings.auto_output_delay}
                onChange={(e) => setSettings(prev => ({...prev, auto_output_delay: Number(e.target.value)}))}
                className="w-full h-1 accent-purple-500"
              />
            </div>
          )}
        </div>
      </motion.div>

      {/* Input/Output Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50"
      >
        <div className="space-y-4">
          {/* Input */}
          <div>
            <label className="block text-sm font-medium mb-2">Input</label>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter your text or question..."
              className="w-full h-32 bg-gray-800 rounded-lg p-3 text-white placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          
          {/* Generate Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={generateAI}
            disabled={isGenerating || !input.trim()}
            className="w-full px-4 py-3 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-all flex items-center justify-center gap-2"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate AI Response
              </>
            )}
          </motion.button>
          
          {/* Countdown */}
          {countdown !== null && (
            <div className="flex items-center justify-between p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <span className="text-sm text-yellow-300">
                Auto-typing starts in {countdown} seconds...
              </span>
              <button
                onClick={cancelCountdown}
                className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 rounded text-red-300 text-sm"
              >
                Cancel
              </button>
            </div>
          )}
          
          {/* Output */}
          {output && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium">Output</label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={copyOutput}
                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs flex items-center gap-1"
                  >
                    {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                  <button
                    onClick={startTyping}
                    className="px-3 py-1 bg-green-500/20 hover:bg-green-500/30 border border-green-500/50 rounded text-green-300 text-xs"
                  >
                    Start Typing
                  </button>
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-4 max-h-64 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm text-gray-300">{output}</pre>
              </div>
            </div>
          )}
        </div>
      </motion.div>
      
      {/* Debug Button - TEMPORARY */}
      <button
        onClick={() => {
          console.log('[AIHub] DEBUG: Button clicked!')
          console.log('[AIHub] Current showReviewModal state before:', showReviewModal)
          console.log('[AIHub] Current reviewText before:', reviewText)
          
          const testText = 'This is a test review text to verify the modal is working correctly. If you can see this, the modal is rendering properly.'
          setReviewText(testText)
          setShowReviewModal(true)
          
          console.log('[AIHub] Called setReviewText with:', testText)
          console.log('[AIHub] Called setShowReviewModal(true)')
          
          // Force a re-check after state update
          setTimeout(() => {
            console.log('[AIHub] After timeout - showReviewModal state:', showReviewModal)
          }, 100)
        }}
        className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-white font-medium"
      >
        🔧 DEBUG: Test Review Modal
      </button>
      
      {/* Tips Section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-xl p-6 border border-purple-500/20"
      >
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb className="w-5 h-5 text-yellow-400" />
          <h3 className="text-lg font-semibold text-white">Pro Tips</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-300">
              <span className="font-semibold">Quick Start:</span> Select a template, enter your topic, and click generate for instant content
            </p>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-300">
              <span className="font-semibold">Auto-Humanize:</span> Enable to make AI content undetectable automatically
            </p>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-300">
              <span className="font-semibold">Smart Output:</span> Use Auto-Output to start typing immediately after generation
            </p>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-300">
              <span className="font-semibold">Essay Mode:</span> Switch to essay type for longer, structured academic content
            </p>
          </div>
          <div className="flex items-start gap-2">
            <Rocket className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-300">
              <span className="font-semibold">Power User:</span> Combine templates with custom prompts for best results
            </p>
          </div>
          <div className="flex items-start gap-2">
            <Rocket className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-300">
              <span className="font-semibold">Settings Persist:</span> All your preferences are saved automatically
            </p>
          </div>
        </div>
      </motion.div>
      
      {/* Review Modal */}
      <AnimatePresence mode="wait">
        {showReviewModal && (
          <motion.div
            key="review-modal"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowReviewModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-gray-900 rounded-2xl p-6 max-w-3xl w-full max-h-[80vh] overflow-hidden border border-purple-500/30 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <CheckCircle2 className="w-6 h-6 text-green-400" />
                  Review Generated Content
                </h2>
                <button
                  onClick={() => setShowReviewModal(false)}
                  className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              </div>
              
              <div className="bg-gray-800/50 rounded-lg p-4 mb-4 max-h-[50vh] overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm text-white/90">{reviewText}</pre>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="text-xs text-gray-400">
                  {reviewText.split(/\s+/).filter(w => w).length} words • {reviewText.length} characters
                </div>
                
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setShowReviewModal(false)
                      setOutput('')
                      setReviewText('')
                    }}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition-colors"
                  >
                    Discard
                  </button>
                  
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(reviewText)
                      toast.success('📋 Copied to clipboard!')
                    }}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white transition-colors flex items-center gap-2"
                  >
                    <Copy className="w-4 h-4" />
                    Copy
                  </button>
                  
                  <button
                    onClick={() => {
                      setShowReviewModal(false)
                      if (settings.auto_output) {
                        startAutoOutputCountdown(reviewText)
                      } else {
                        toast.success('✅ Content approved! Use the output buttons below to type or copy.')
                      }
                    }}
                    className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-lg text-white font-medium transition-all flex items-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Approve & Use
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}