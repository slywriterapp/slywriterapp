'use client'

import { useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { API_ENDPOINTS, AI_API_URL, TYPING_API_URL } from '../config/api'
import { addLearningTopic } from './LearningHub'

export default function GlobalHotkeyListener() {
  useEffect(() => {
    const handleGlobalHotkey = async (action: string) => {
      console.log('🔥 [GlobalHotkeyListener] Global hotkey received:', action)
      console.log('🔥 [GlobalHotkeyListener] Action type:', typeof action)
      console.log('🔥 [GlobalHotkeyListener] Action matches ai_generation?', action === 'ai_generation')
      console.log('🔥 [GlobalHotkeyListener] Action matches ai-generation?', action === 'ai-generation')
      
      switch (action) {
        case 'start':
          await handleStart()
          break
        case 'stop':
          await handleStop()
          break
        case 'pause':
          await handlePause()
          break
        case 'ai_generation':
        case 'ai-generation':
        case 'generate':
        case 'ai':
          console.log('🔥 [GlobalHotkeyListener] AI Generation case matched!')
          await handleAIGeneration()
          break
      }
    }
    
    const handleHotkeySuccess = (message: string) => {
      toast.success(message)
    }
    
    const handleHotkeyError = (message: string) => {
      toast.error(message)
    }
    
    const handleHotkeyWithText = async (data: { action: string, text: string }) => {
      console.log('Global hotkey with text received:', data.action)
      
      // AI generation is now handled entirely in main process
      // This is kept for potential future use
    }
    
    const handleOverlayCommand = async (command: string) => {
      console.log('Overlay command received:', command)
      
      if (command === 'toggle-paste-mode') {
        const current = localStorage.getItem('slywriter-paste-mode') === 'true'
        localStorage.setItem('slywriter-paste-mode', (!current).toString())
        toast.success(current ? '⌨️ Typing mode enabled' : '📋 Paste mode enabled')
      } else if (command === 'humanize') {
        // Get last generated text and humanize it
        const lastText = localStorage.getItem('slywriter-last-generated') || ''
        if (!lastText) {
          toast.error('No text to humanize!')
          return
        }
        
        toast.success('✨ Humanizing text...')
        
        try {
          const settings = JSON.parse(localStorage.getItem('slywriter-ai-settings') || '{}')
          const response = await axios.post(`${AI_API_URL}/api/ai/humanize`, {
            text: lastText,
            grade_level: settings.grade_level || 11,
            tone: settings.tone || 'Neutral',
            style: settings.rewrite_style || 'Clear'
          })
          
          const humanizedText = response.data.text
          localStorage.setItem('slywriter-last-generated', humanizedText)
          
          // Check paste mode
          const pasteMode = localStorage.getItem('slywriter-paste-mode') === 'true'
          if (pasteMode) {
            await navigator.clipboard.writeText(humanizedText)
            toast.success('✨ Humanized and copied to clipboard!')
          } else {
            await axios.post(`${TYPING_API_URL}/api/typing/start`, {
              text: humanizedText,
              profile: 'Medium',
              preview_mode: false
            })
            toast.success('✨ Humanized and typing started!')
          }
        } catch (error) {
          toast.error('Failed to humanize text')
        }
      }
    }
    
    // Check if we're in Electron environment
    if (typeof window !== 'undefined' && window.electron?.ipcRenderer) {
      // Listen for global hotkey events from main process
      window.electron.ipcRenderer.on('global-hotkey', handleGlobalHotkey)
      window.electron.ipcRenderer.on('global-hotkey-success', handleHotkeySuccess)
      window.electron.ipcRenderer.on('global-hotkey-error', handleHotkeyError)
      window.electron.ipcRenderer.on('global-hotkey-with-text', handleHotkeyWithText)
      window.electron.ipcRenderer.on('overlay-command', handleOverlayCommand)
      console.log('GlobalHotkeyListener: Listening for IPC events')
      
      return () => {
        window.electron?.ipcRenderer?.removeListener('global-hotkey', handleGlobalHotkey)
        window.electron?.ipcRenderer?.removeListener('global-hotkey-success', handleHotkeySuccess)
        window.electron?.ipcRenderer?.removeListener('global-hotkey-error', handleHotkeyError)
        window.electron?.ipcRenderer?.removeListener('global-hotkey-with-text', handleHotkeyWithText)
        window.electron?.ipcRenderer?.removeListener('overlay-command', handleOverlayCommand)
      }
    } else {
      console.log('GlobalHotkeyListener: Not in Electron environment')
    }
  }, [])
  
  const handleStart = async () => {
    try {
      let text = ''
      
      // First, check if there's text in the "Type Here" input box
      // Try multiple selectors to find the textarea
      const typeHereInput = document.querySelector('textarea[placeholder*="Type or paste"]') as HTMLTextAreaElement ||
                           document.querySelector('textarea[placeholder*="Type here"]') as HTMLTextAreaElement ||
                           document.querySelector('#typing-input') as HTMLTextAreaElement
      
      console.log('Type Here input found:', !!typeHereInput)
      console.log('Type Here value:', typeHereInput?.value?.substring(0, 50))
      
      if (typeHereInput && typeHereInput.value.trim()) {
        text = typeHereInput.value.trim()
        console.log('✅ Using text from Type Here box:', text.substring(0, 50) + '...')
        toast.success('Using text from Type Here box', { icon: '📝' })
      } else {
        // Fallback to clipboard if Type Here is empty
        console.log('Type Here is empty, checking clipboard...')
        text = await navigator.clipboard.readText()
        console.log('📋 Using text from clipboard:', text.substring(0, 50) + '...')
        toast.success('Using text from clipboard', { icon: '📋' })
      }
      
      if (!text) {
        toast.error('No text in Type Here box or clipboard!')
        return
      }
      
      // Start typing using local backend
      await axios.post(`${TYPING_API_URL}/api/typing/start`, {
        text,
        profile: localStorage.getItem('slywriter-selected-profile') || 'Medium',
        preview_mode: false
      })
      
      toast.success('Typing started!')
    } catch (error) {
      toast.error('Failed to start typing')
    }
  }
  
  const handleStop = async () => {
    console.log('GLOBAL STOP HOTKEY TRIGGERED!')
    
    // Dispatch a custom event that the typing component will hear
    window.dispatchEvent(new CustomEvent('global-stop-typing'))
    
    // Call the global stop endpoint - this stops ALL sessions
    try {
      const response = await axios.post(`${TYPING_API_URL}/api/typing/stop`)
      console.log('Global stop response:', response.data)
    } catch (error) {
      console.error('Global stop API error:', error)
    }
    
    toast.success('🛑 EMERGENCY STOP ACTIVATED!')
  }
  
  const handlePause = async () => {
    console.log('GLOBAL PAUSE HOTKEY TRIGGERED!')
    
    try {
      // Use global pause endpoint which toggles pause state for all sessions
      const response = await axios.post(`${TYPING_API_URL}/api/typing/pause`)
      console.log('Global pause response:', response.data)
      
      if (response.data.status === 'paused') {
        toast.success('⏸️ Typing paused!')
      } else if (response.data.status === 'resumed') {
        toast.success('▶️ Typing resumed!')
      } else {
        toast('No active typing session', { icon: 'ℹ️' })
      }
    } catch (error) {
      console.error('Global pause API error:', error)
      toast.error('Failed to pause/resume')
    }
  }
  
  const handleAIGenerationWithText = async (text: string) => {
    try {
      if (!text) {
        toast.error('No text provided for AI generation!')
        return
      }
      
      toast.success('🤖 Processing with AI...')
      
      // Simple fallback if AI service is down
      const fallbackGeneration = () => {
        const fallbackText = `Based on your input: "${text.substring(0, 50)}...", here's a generated response:\n\n` +
          `This is a fallback response while the AI service is unavailable. ` +
          `The text you provided has been processed and would normally generate a detailed response. ` +
          `Please check your AI settings or try again later when the service is available.`
        return fallbackText
      }
      
      // Get AI generation settings
      const aiHubSettings = localStorage.getItem('slywriter-ai-hub-settings')
      const aiSettings = localStorage.getItem('slywriter-ai-settings')
      console.log('🎯 [GlobalHotkeyListener] AI Hub Settings from storage:', aiHubSettings)
      console.log('🎯 [GlobalHotkeyListener] AI Settings from storage:', aiSettings)
      
      // Try AI Hub settings first, fall back to AI settings
      const settings = JSON.parse(aiHubSettings || aiSettings || '{}')
      console.log('🎯 [GlobalHotkeyListener] Parsed settings:', settings)
      console.log('🎯 [GlobalHotkeyListener] Review mode value:', settings.review_mode)
      console.log('🎯 [GlobalHotkeyListener] Review mode type:', typeof settings.review_mode)
      
      // Build prompt
      const prompt = buildAIPrompt(text, settings)
      
      // Generate with AI
      console.log('AI Generation request:', {
        url: `${AI_API_URL}/api/ai/generate`,
        prompt: prompt.substring(0, 100) + '...',
        settings
      })
      
      let response
      try {
        response = await axios.post(`${AI_API_URL}/api/ai/generate`, {
          prompt,
          settings,
          ai_filler_enabled: settings.ai_filler_enabled || false
        })
      } catch (error: any) {
        console.error('AI Generation error:', error)
        if (error.response) {
          console.error('Error response:', error.response.data)
          console.error('Error status:', error.response.status)
          
          // Handle specific error cases
          if (error.response.status === 500) {
            toast.error('AI service error. The server may be down or the API key may be invalid.')
          } else if (error.response.status === 429) {
            toast.error('Rate limit exceeded. Please wait a moment and try again.')
          } else {
            toast.error(`AI error: ${error.response.data?.error || 'Unknown error'}`)
          }
        } else {
          toast.error('Failed to connect to AI service')
        }
        return
      }
      
      let generatedText = response.data.text || response.data.response || response.data.content
      
      // Apply humanizer if enabled
      if (settings.humanizer_enabled) {
        const humanizeResponse = await axios.post(`${AI_API_URL}/api/ai/humanize`, {
          text: generatedText,
          grade_level: settings.grade_level || 11,
          tone: settings.tone || 'Neutral',
          style: settings.rewrite_style || 'Clear'
        })
        generatedText = humanizeResponse.data.text
      }
      
      // Auto-save to learning (track what they're using AI for)
      if (settings.learning_mode !== false) {
        addLearningTopic(text, generatedText)
      }
      
      // Check if paste mode is enabled
      const pasteMode = localStorage.getItem('slywriter-paste-mode') === 'true'
      
      if (pasteMode) {
        // PASTE MODE: Instantly paste the answer
        try {
          await navigator.clipboard.writeText(generatedText)
          toast.success('⚡ Answer copied to clipboard! Paste anywhere.', { icon: '📋' })
        } catch (err) {
          // Use Electron IPC to set clipboard
          if (window.electron?.ipcRenderer) {
            window.electron.ipcRenderer.send('set-clipboard', generatedText)
            toast.success('⚡ Answer copied to clipboard! Paste anywhere.', { icon: '📋' })
          } else {
            toast.error('Failed to copy to clipboard')
          }
        }
      } else {
        // TYPING MODE: Check if review mode is enabled
        const reviewMode = settings.review_mode || false
        
        if (reviewMode) {
          // Dispatch event to show review modal
          console.log('GlobalHotkeyListener: Review mode enabled, dispatching showAIReview')
          const reviewEvent = new CustomEvent('showAIReview', {
            detail: { text: generatedText }
          })
          window.dispatchEvent(reviewEvent)
          
          // Also switch to AI Hub tab
          const tabSwitchEvent = new CustomEvent('switchTab', {
            detail: { tab: 'ai-hub' }
          })
          window.dispatchEvent(tabSwitchEvent)
          
          toast.success('✨ AI generated - Review before sending!')
        } else {
          // Type out with human patterns
          await axios.post(`${TYPING_API_URL}/api/typing/start`, {
            text: generatedText,
            profile: 'Medium',
            preview_mode: false
          })
          
          toast.success('✨ AI generated and typing started!')
        }
      }
      
      // Create lesson if learning mode
      if (settings.learning_mode) {
        await axios.post(`${AI_API_URL}/api/learning/create-lesson`, {
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
  }
  
  const handleAIGeneration = async () => {
    console.log('🎯 [GlobalHotkeyListener] handleAIGeneration called!')
    console.log('🎯 [GlobalHotkeyListener] Stack trace:', new Error().stack)
    
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
      const aiHubSettings = localStorage.getItem('slywriter-ai-hub-settings')
      const aiSettings = localStorage.getItem('slywriter-ai-settings')
      console.log('🎯 [GlobalHotkeyListener] AI Hub Settings from storage:', aiHubSettings)
      console.log('🎯 [GlobalHotkeyListener] AI Settings from storage:', aiSettings)
      
      // Try AI Hub settings first, fall back to AI settings
      const settings = JSON.parse(aiHubSettings || aiSettings || '{}')
      console.log('🎯 [GlobalHotkeyListener] Parsed settings:', settings)
      console.log('🎯 [GlobalHotkeyListener] Review mode value:', settings.review_mode)
      console.log('🎯 [GlobalHotkeyListener] Review mode type:', typeof settings.review_mode)
      
      // Build prompt
      const prompt = buildAIPrompt(text, settings)
      
      // Generate with AI
      console.log('AI Generation request:', {
        url: `${AI_API_URL}/api/ai/generate`,
        prompt: prompt.substring(0, 100) + '...',
        settings
      })
      
      let response
      try {
        response = await axios.post(`${AI_API_URL}/api/ai/generate`, {
          prompt,
          settings,
          ai_filler_enabled: settings.ai_filler_enabled || false
        })
      } catch (error: any) {
        console.error('AI Generation error:', error)
        if (error.response) {
          console.error('Error response:', error.response.data)
          console.error('Error status:', error.response.status)
          
          // Handle specific error cases
          if (error.response.status === 500) {
            toast.error('AI service error. The server may be down or the API key may be invalid.')
          } else if (error.response.status === 429) {
            toast.error('Rate limit exceeded. Please wait a moment and try again.')
          } else {
            toast.error(`AI error: ${error.response.data?.error || 'Unknown error'}`)
          }
        } else {
          toast.error('Failed to connect to AI service')
        }
        return
      }
      
      let generatedText = response.data.text || response.data.response || response.data.content
      
      // Apply humanizer if enabled
      if (settings.humanizer_enabled) {
        const humanizeResponse = await axios.post(`${AI_API_URL}/api/ai/humanize`, {
          text: generatedText,
          grade_level: settings.grade_level || 11,
          tone: settings.tone || 'Neutral',
          style: settings.rewrite_style || 'Clear'
        })
        generatedText = humanizeResponse.data.text
      }
      
      // Auto-save to learning (track what they're using AI for)
      if (settings.learning_mode !== false) {
        addLearningTopic(text, generatedText)
      }
      
      // Check if paste mode is enabled
      const pasteMode = localStorage.getItem('slywriter-paste-mode') === 'true'
      
      if (pasteMode) {
        // PASTE MODE: Instantly paste the answer
        try {
          await navigator.clipboard.writeText(generatedText)
          toast.success('⚡ Answer copied to clipboard! Paste anywhere.', { icon: '📋' })
        } catch (err) {
          toast.error('Failed to copy to clipboard')
        }
      } else {
        // TYPING MODE: Check if review mode is enabled
        const reviewMode = settings.review_mode || false
        
        if (reviewMode) {
          // Dispatch event to show review modal
          console.log('GlobalHotkeyListener: Review mode enabled, dispatching showAIReview')
          const reviewEvent = new CustomEvent('showAIReview', {
            detail: { text: generatedText }
          })
          window.dispatchEvent(reviewEvent)
          
          // Also switch to AI Hub tab
          const tabSwitchEvent = new CustomEvent('switchTab', {
            detail: { tab: 'ai-hub' }
          })
          window.dispatchEvent(tabSwitchEvent)
          
          toast.success('✨ AI generated - Review before sending!')
        } else {
          // Type out with human patterns
          await axios.post(`${TYPING_API_URL}/api/typing/start`, {
            text: generatedText,
            profile: 'Medium',
            preview_mode: false
          })
          
          toast.success('✨ AI generated and typing started!')
        }
      }
      
      // Create lesson if learning mode
      if (settings.learning_mode) {
        await axios.post(`${AI_API_URL}/api/learning/create-lesson`, {
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
  }
  
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
  
  return null // This is a listener component, doesn't render anything
}

// Also export a preload script helper for Electron
declare global {
  interface Window {
    electron?: {
      ipcRenderer: {
        on: (channel: string, callback: Function) => void
        removeListener: (channel: string, callback: Function) => void
        send: (channel: string, ...args: any[]) => void
      }
    }
  }
}