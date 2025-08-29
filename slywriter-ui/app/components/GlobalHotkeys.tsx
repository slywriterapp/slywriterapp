'use client'

import { useEffect, useState } from 'react'
import { useHotkeys } from 'react-hotkeys-hook'
import axios from 'axios'
import toast from 'react-hot-toast'
import ReviewPopup from './ReviewPopup'
import { addLearningTopic } from './LearningHub'

const API_URL = 'https://slywriterapp.onrender.com'

interface HotkeyConfig {
  start: string
  stop: string
  pause: string
  overlay: string
  ai_generation: string
}

export default function GlobalHotkeys() {
  // Initialize hotkeys from localStorage on component mount
  const [hotkeys, setHotkeys] = useState<HotkeyConfig>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('slywriter-hotkeys')
      if (saved) {
        try {
          return JSON.parse(saved)
        } catch {
          // If parse fails, return defaults
        }
      }
    }
    return {
      start: 'ctrl+alt+s',
      stop: 'ctrl+alt+q',
      pause: 'ctrl+alt+p',
      overlay: 'ctrl+alt+o',
      ai_generation: 'ctrl+alt+g'
    }
  })
  
  const [clipboardText, setClipboardText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [overlayVisible, setOverlayVisible] = useState(false)
  const [reviewPopup, setReviewPopup] = useState<{open: boolean, text: string, question: string}>({
    open: false,
    text: '',
    question: ''
  })
  
  // Start typing hotkey
  useHotkeys(hotkeys.start, async () => {
    if (isTyping) {
      toast.error('Already typing!')
      return
    }
    
    try {
      // Get text from clipboard
      const text = await navigator.clipboard.readText()
      if (!text) {
        toast.error('No text in clipboard!')
        return
      }
      
      // Start typing
      await axios.post(`${API_URL}/api/typing/start`, {
        text,
        profile: 'Medium',
        preview_mode: false
      })
      
      setIsTyping(true)
      toast.success('Typing started!')
    } catch (error) {
      toast.error('Failed to start typing')
    }
  }, [isTyping])
  
  // Stop typing hotkey (Panic Stop) - MUST WORK ALWAYS
  useHotkeys(hotkeys.stop, async () => {
    console.log('GLOBAL STOP HOTKEY TRIGGERED!')
    
    // Dispatch a custom event that the typing component will hear
    window.dispatchEvent(new CustomEvent('global-stop-typing'))
    
    // Call the global stop endpoint - this stops ALL sessions
    try {
      const response = await axios.post(`${API_URL}/api/typing/stop`)
      console.log('Global stop response:', response.data)
    } catch (error) {
      console.error('Global stop API error:', error)
    }
    
    setIsTyping(false)
    setIsPaused(false)
    toast.success('🛑 EMERGENCY STOP ACTIVATED!')
  }, { enabled: true, enableOnFormTags: true, preventDefault: true })
  
  // Pause/Resume hotkey
  useHotkeys(hotkeys.pause, async () => {
    console.log('GLOBAL PAUSE HOTKEY TRIGGERED!')
    
    try {
      // Use global pause endpoint which toggles pause state for all sessions
      const response = await axios.post(`${API_URL}/api/typing/pause`)
      console.log('Global pause response:', response.data)
      
      if (response.data.status === 'paused') {
        setIsPaused(true)
        toast.success('⏸️ Typing paused!')
      } else if (response.data.status === 'resumed') {
        setIsPaused(false)
        toast.success('▶️ Typing resumed!')
      } else {
        toast('No active typing session', { icon: 'ℹ️' })
      }
    } catch (error) {
      console.error('Global pause API error:', error)
      toast.error('Failed to pause/resume')
    }
  }, { enabled: true, preventDefault: true })
  
  // Toggle overlay hotkey
  useHotkeys(hotkeys.overlay, () => {
    setOverlayVisible(!overlayVisible)
    
    // Send message to overlay window
    if (window.parent !== window) {
      window.parent.postMessage({ 
        type: 'toggle-overlay',
        visible: !overlayVisible 
      }, '*')
    }
    
    toast.success(overlayVisible ? 'Overlay hidden' : 'Overlay shown')
  }, [overlayVisible])
  
  // AI Generation hotkey (MOST IMPORTANT)
  useHotkeys(hotkeys.ai_generation, async () => {
    try {
      // Get highlighted/clipboard text
      let text = ''
      
      // Try to get selected text first
      const selection = window.getSelection()
      if (selection && selection.toString()) {
        text = selection.toString()
      } else {
        // Fallback to clipboard
        text = await navigator.clipboard.readText()
      }
      
      if (!text) {
        toast.error('No text selected or in clipboard!')
        return
      }
      
      toast.success('🤖 Processing with AI...')
      
      // Get AI generation settings
      const settings = JSON.parse(localStorage.getItem('slywriter-ai-settings') || '{}')
      
      // Build prompt
      const prompt = buildAIPrompt(text, settings)
      
      // Generate with AI
      const response = await axios.post(`${API_URL}/api/ai/generate`, {
        prompt,
        settings,
        ai_filler_enabled: settings.ai_filler_enabled || false // Pass AI filler setting
      })
      
      let generatedText = response.data.text
      
      // Apply humanizer if enabled
      if (settings.humanizer_enabled) {
        const humanizeResponse = await axios.post(`${API_URL}/api/ai/humanize`, {
          text: generatedText,
          grade_level: settings.grade_level || 11,
          tone: settings.tone || 'Neutral',
          style: settings.rewrite_style || 'Clear'
        })
        generatedText = humanizeResponse.data.text
      }
      
      // Auto-save to learning (track what they're using AI for)
      if (settings.learning_mode !== false) { // Default to true
        addLearningTopic(text, generatedText)
      }
      
      // Check review mode
      if (settings.review_mode) {
        // Show review popup
        setReviewPopup({
          open: true,
          text: generatedText,
          question: text
        })
      } else {
        // Check if paste mode is enabled
        const pasteMode = localStorage.getItem('slywriter-paste-mode') === 'true'
        
        if (pasteMode) {
          // PASTE MODE: Instantly paste the answer
          try {
            await navigator.clipboard.writeText(generatedText)
            
            // Simulate paste event to paste into active field
            const activeElement = document.activeElement as HTMLTextAreaElement | HTMLInputElement
            if (activeElement && (activeElement.tagName === 'TEXTAREA' || activeElement.tagName === 'INPUT')) {
              const start = activeElement.selectionStart || 0
              const end = activeElement.selectionEnd || 0
              const currentValue = activeElement.value
              
              // Insert text at cursor position
              activeElement.value = currentValue.substring(0, start) + generatedText + currentValue.substring(end)
              
              // Update cursor position
              activeElement.selectionStart = activeElement.selectionEnd = start + generatedText.length
              
              // Trigger input event
              activeElement.dispatchEvent(new Event('input', { bubbles: true }))
              
              toast.success('⚡ Answer pasted instantly!', { icon: '📋' })
            } else {
              // Just copy to clipboard if no active field
              toast.success('✨ Answer copied to clipboard! Paste anywhere.', { icon: '📋' })
            }
          } catch (err) {
            toast.error('Failed to paste - answer copied to clipboard')
          }
        } else {
          // TYPING MODE: Type out with human patterns
          await axios.post(`${API_URL}/api/typing/start`, {
            text: generatedText,
            profile: 'Medium',
            preview_mode: false
          })
          
          setIsTyping(true)
          toast.success('✨ AI generated and typing started!')
        }
      }
      
      // Create lesson if learning mode
      if (settings.learning_mode) {
        await axios.post(`${API_URL}/api/learning/create-lesson`, {
          topic: text.substring(0, 100),
          content: generatedText,
          method: 'ai_generated'
        })
        toast.success('📚 Lesson created!')
      }
      
    } catch (error) {
      console.error('AI generation failed:', error)
      toast.error('Failed to generate with AI')
    }
  }, [])
  
  const buildAIPrompt = (text: string, settings: any): string => {
    const { response_type = 'short_response', response_length = 3, academic_format = 'None', 
            required_pages = 1, grade_level = 11, tone = 'Neutral', depth = 3, 
            rewrite_style = 'Clear', use_of_evidence = 'Optional' } = settings
    
    let prompt = `Process this text: "${text}"\n\n`
    
    if (response_type === 'short_response') {
      const lengths = {
        1: 'very brief (1-2 sentences)',
        2: 'short (2-4 sentences)', 
        3: 'medium (4-8 sentences)',
        4: 'long (8-15 sentences)',
        5: 'very detailed (15+ sentences)'
      }
      prompt += `Create a ${lengths[response_length as keyof typeof lengths] || lengths[3]} response.\n`
    } else {
      const wordsPerPage = academic_format === 'MLA' ? 275 : 
                          academic_format === 'APA' ? 260 :
                          academic_format === 'Chicago' ? 250 : 250
      prompt += `Create a ${required_pages} page ${academic_format !== 'None' ? academic_format : ''} essay (approximately ${required_pages * wordsPerPage} words).\n`
    }
    
    // Add style parameters
    prompt += `\nWriting parameters:\n`
    prompt += `- Grade level: ${grade_level}${grade_level <= 12 ? 'th grade' : ' (college)'}\n`
    prompt += `- Tone: ${tone.toLowerCase()}\n`
    prompt += `- Depth: ${['shallow', 'basic', 'moderate', 'deep', 'comprehensive'][depth - 1] || 'moderate'}\n`
    prompt += `- Style: ${rewrite_style.toLowerCase()}\n`
    
    if (use_of_evidence !== 'None') {
      prompt += `- Evidence/examples are ${use_of_evidence.toLowerCase()}\n`
    }
    
    return prompt
  }
  
  // Listen for overlay toggle from parent
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'toggle-overlay') {
        setOverlayVisible(event.data.visible)
      }
    }
    
    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [])
  
  const handleReviewConfirm = async (finalText: string) => {
    // Check if paste mode is enabled
    const pasteMode = localStorage.getItem('slywriter-paste-mode') === 'true'
    
    if (pasteMode) {
      // PASTE MODE: Instantly paste the answer
      try {
        await navigator.clipboard.writeText(finalText)
        
        // Simulate paste event to paste into active field
        const activeElement = document.activeElement as HTMLTextAreaElement | HTMLInputElement
        if (activeElement && (activeElement.tagName === 'TEXTAREA' || activeElement.tagName === 'INPUT')) {
          const start = activeElement.selectionStart || 0
          const end = activeElement.selectionEnd || 0
          const currentValue = activeElement.value
          
          // Insert text at cursor position
          activeElement.value = currentValue.substring(0, start) + finalText + currentValue.substring(end)
          
          // Update cursor position
          activeElement.selectionStart = activeElement.selectionEnd = start + finalText.length
          
          // Trigger input event
          activeElement.dispatchEvent(new Event('input', { bubbles: true }))
          
          toast.success('⚡ Answer pasted!', { icon: '📋' })
        } else {
          // Just copy to clipboard if no active field
          toast.success('✨ Answer copied to clipboard!', { icon: '📋' })
        }
      } catch (err) {
        toast.error('Failed to paste - answer copied to clipboard')
      }
    } else {
      // TYPING MODE: Type out with human patterns
      await axios.post(`${API_URL}/api/typing/start`, {
        text: finalText,
        profile: 'Medium',
        preview_mode: false
      })
      
      setIsTyping(true)
      toast.success('✨ Typing started!')
    }
    
    setReviewPopup({ open: false, text: '', question: '' })
  }
  
  return (
    <>
      <ReviewPopup
        isOpen={reviewPopup.open}
        onClose={() => setReviewPopup({ open: false, text: '', question: '' })}
        text={reviewPopup.text}
        question={reviewPopup.question}
        onConfirm={handleReviewConfirm}
        onSaveToLearning={addLearningTopic}
      />
    </>
  ) // Review popup component
}

export function HotkeySettings() {
  const [hotkeys, setHotkeys] = useState<HotkeyConfig>(() => {
    // Load saved hotkeys on mount
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('slywriter-hotkeys')
      if (saved) {
        try {
          return JSON.parse(saved)
        } catch {
          // If parse fails, return defaults
        }
      }
    }
    return {
      start: 'ctrl+alt+s',
      stop: 'ctrl+alt+q',
      pause: 'ctrl+alt+p',
      overlay: 'ctrl+alt+o',
      ai_generation: 'ctrl+alt+g'
    }
  })
  
  const [editing, setEditing] = useState<string | null>(null)
  
  const saveHotkeys = () => {
    localStorage.setItem('slywriter-hotkeys', JSON.stringify(hotkeys))
    toast.success('Hotkeys saved!')
    
    // Reload the page to apply new hotkeys
    setTimeout(() => window.location.reload(), 1000)
  }
  
  const recordHotkey = (key: string) => {
    setEditing(key)
    toast('Press your desired key combination...', { icon: '⌨️' })
    
    const handler = (e: KeyboardEvent) => {
      e.preventDefault()
      
      const parts = []
      if (e.ctrlKey) parts.push('ctrl')
      if (e.altKey) parts.push('alt')
      if (e.shiftKey) parts.push('shift')
      if (e.metaKey) parts.push('cmd')
      
      // Get the actual key
      if (e.key && e.key !== 'Control' && e.key !== 'Alt' && e.key !== 'Shift' && e.key !== 'Meta') {
        parts.push(e.key.toLowerCase())
      }
      
      if (parts.length > 1) {
        const combo = parts.join('+')
        const newHotkeys = {...hotkeys, [key]: combo}
        setHotkeys(newHotkeys)
        setEditing(null)
        document.removeEventListener('keydown', handler)
        
        // Auto-save the new hotkey immediately
        localStorage.setItem('slywriter-hotkeys', JSON.stringify(newHotkeys))
        toast.success(`Hotkey set to ${combo} and saved!`)
      }
    }
    
    document.addEventListener('keydown', handler)
    
    // Remove listener after 5 seconds
    setTimeout(() => {
      document.removeEventListener('keydown', handler)
      if (editing === key) {
        setEditing(null)
        toast.error('Hotkey recording timeout')
      }
    }, 5000)
  }
  
  const hotkeyDescriptions: Record<string, string> = {
    start: 'Start typing from clipboard',
    stop: 'Emergency stop (Panic button)', 
    pause: 'Pause/Resume typing',
    overlay: 'Toggle overlay window',
    ai_generation: 'AI generate from highlighted text'
  }
  
  return (
    <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50 border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-6">Global Hotkeys</h3>
      
      <div className="space-y-4">
        {Object.entries(hotkeys).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
            <div>
              <div className="text-sm font-medium text-white capitalize">
                {key.replace('_', ' ')}
              </div>
              <div className="text-xs text-gray-400">
                {hotkeyDescriptions[key]}
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <kbd className="px-3 py-1 bg-gray-800 rounded text-sm text-white font-mono">
                {editing === key ? 'Recording...' : value}
              </kbd>
              <button
                onClick={() => recordHotkey(key)}
                disabled={editing !== null}
                className="px-3 py-1 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-600 rounded text-sm text-white transition-colors"
              >
                {editing === key ? 'Press keys...' : 'Change'}
              </button>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-6 flex justify-end gap-3">
        <button
          onClick={() => {
            const defaultHotkeys = {
              start: 'ctrl+alt+s',
              stop: 'ctrl+alt+q',
              pause: 'ctrl+alt+p',
              overlay: 'ctrl+alt+o',
              ai_generation: 'ctrl+alt+g'
            }
            setHotkeys(defaultHotkeys)
            localStorage.setItem('slywriter-hotkeys', JSON.stringify(defaultHotkeys))
            toast.success('Reset to default hotkeys!')
          }}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition-colors"
        >
          Reset to Defaults
        </button>
        <button
          onClick={saveHotkeys}
          className="px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg text-white transition-colors"
        >
          Save Hotkeys
        </button>
      </div>
      
      <div className="mt-4 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
        <p className="text-xs text-yellow-300">
          <strong>Important:</strong> The AI Generation hotkey (Ctrl+Alt+G) is the most powerful feature. 
          Highlight any text and press it to instantly enhance with AI and auto-type!
        </p>
      </div>
    </div>
  )
}