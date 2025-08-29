'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Wand2, RefreshCw, Copy, Check, Brain, Zap, BookOpen, Briefcase, Heart, Gamepad2, Code, Palette, AlertCircleIcon, XCircleIcon, BrainIcon, SparklesIcon } from 'lucide-react'
import { FirstTimeHelper } from './FeatureTooltips'
import axios from 'axios'
import toast from 'react-hot-toast'

const API_URL = 'https://slywriterapp.onrender.com'

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
  // Response Configuration
  response_type: 'short_response' | 'essay'
  response_length: number // 1-5 for short, pages for essay
  academic_format: string
  required_pages: number
  
  // Writing Style Settings
  grade_level: number
  tone: string
  depth: number
  rewrite_style: string
  use_of_evidence: string
  
  // Processing Modes
  humanizer_enabled: boolean  // Whether to humanize after generation
  review_mode: boolean        // Whether to review before output
  learning_mode: boolean      // Whether to save as lesson
}

export default function AIHubTab() {
  const [input, setInput] = useState('')
  const [output, setOutput] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState('creative')
  const [isGenerating, setIsGenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [history, setHistory] = useState<Array<{input: string, output: string, timestamp: string}>>([])
  
  // Comprehensive AI generation settings
  const [settings, setSettings] = useState<AIGenerationSettings>({
    response_type: 'short_response',
    response_length: 3,
    academic_format: 'None',
    required_pages: 1,
    grade_level: 11,
    tone: 'Neutral',
    depth: 3,
    rewrite_style: 'Clear',
    use_of_evidence: 'Optional',
    humanizer_enabled: true,
    review_mode: false,
    learning_mode: false
  })

  // Load saved settings and history
  useEffect(() => {
    const savedHistory = localStorage.getItem('aiHistory')
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory))
    }
    
    const savedSettings = localStorage.getItem('slywriter-ai-settings')
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings))
    }
    
    // Load global humanize state
    const autoHumanize = localStorage.getItem('slywriter-auto-humanize')
    if (autoHumanize !== null) {
      setSettings(prev => ({ ...prev, humanizer_enabled: autoHumanize === 'true' }))
    }
  }, [])
  
  // Listen for humanize state changes from other tabs
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'slywriter-auto-humanize' && e.newValue !== null) {
        setSettings(prev => ({ ...prev, humanizer_enabled: e.newValue === 'true' }))
      }
    }
    
    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])
  
  // Save settings on change
  useEffect(() => {
    localStorage.setItem('slywriter-ai-settings', JSON.stringify(settings))
  }, [settings])

  const buildAIPrompt = (): string => {
    const template = templates.find(t => t.id === selectedTemplate)
    let prompt = `${template?.prompt}: ${input}\n\n`
    
    // Add AI filler context if enabled
    if (settings.ai_filler_enabled) {
      prompt += `Include natural transitions and thought processes as if the writer is thinking while typing. `
    }
    
    // Add response type specifics
    if (settings.response_type === 'short_response') {
      const lengths = {
        1: 'very brief (1-2 sentences)',
        2: 'short (2-4 sentences)', 
        3: 'medium (4-8 sentences)',
        4: 'long (8-15 sentences)',
        5: 'very detailed (15+ sentences)'
      }
      prompt += `Create a ${lengths[settings.response_length as keyof typeof lengths] || lengths[3]} response.\n`
    } else {
      const wordsPerPage = settings.academic_format === 'MLA' ? 275 : 
                          settings.academic_format === 'APA' ? 260 :
                          settings.academic_format === 'Chicago' ? 250 : 250
      prompt += `Create a ${settings.required_pages} page ${settings.academic_format !== 'None' ? settings.academic_format : ''} essay (approximately ${settings.required_pages * wordsPerPage} words).\n`
    }
    
    // Add style parameters
    prompt += `\nWriting parameters:\n`
    prompt += `- Grade level: ${settings.grade_level}${settings.grade_level <= 12 ? 'th grade' : ' (college)'}\n`
    prompt += `- Tone: ${settings.tone.toLowerCase()}\n`
    prompt += `- Depth: ${['shallow', 'basic', 'moderate', 'deep', 'comprehensive'][settings.depth - 1] || 'moderate'}\n`
    prompt += `- Style: ${settings.rewrite_style.toLowerCase()}\n`
    
    if (settings.use_of_evidence !== 'None') {
      prompt += `- Evidence/examples are ${settings.use_of_evidence.toLowerCase()}\n`
    }
    
    return prompt
  }

  const handleGenerate = async () => {
    if (!input.trim()) return
    
    setIsGenerating(true)
    
    // Track for learning if enabled
    if (settings.learning_mode) {
      const { addLearningTopic } = await import('./LearningHub')
      // Will save the Q&A after generation completes
    }
    
    try {
      const prompt = buildAIPrompt()
      const template = templates.find(t => t.id === selectedTemplate)
      const systemPrompt = `You are a ${template?.name} writer specializing in ${settings.grade_level <= 12 ? 'grade ' + settings.grade_level : 'college-level'} content.`
      
      const response = await axios.post(`${API_URL}/api/ai/generate`, {
        prompt,
        max_tokens: settings.response_type === 'essay' ? settings.required_pages * 400 : Math.round(settings.response_length * 50),
        temperature: settings.tone === 'Creative' || settings.tone === 'Humorous' ? 0.9 : 0.7,
        system_prompt: systemPrompt,
        settings,
        ai_filler_enabled: settings.ai_filler_enabled // Pass this to backend for special handling
      })
      
      if (response.data.success) {
        let generatedText = response.data.text
        
        // If humanizer is enabled, apply it automatically
        if (settings.humanizer_enabled) {
          const humanizeResponse = await axios.post(`${API_URL}/api/ai/humanize`, {
            text: generatedText,
            grade_level: settings.grade_level,
            tone: settings.tone,
            style: settings.rewrite_style,
            preserve_meaning: true
          })
          
          if (humanizeResponse.data.success) {
            generatedText = humanizeResponse.data.text
          }
        }
        
        setOutput(generatedText)
        
        // Save to learning if enabled
        if (settings.learning_mode) {
          const { addLearningTopic } = await import('./LearningHub')
          addLearningTopic(input, generatedText)
          toast.success('📚 Added to learning topics!', { duration: 2000 })
        }
        
        // Show review popup if enabled
        if (settings.review_mode) {
          // For now, just show a toast since review is handled by GlobalHotkeys
          toast('💡 Review mode is best used with Ctrl+Alt+G hotkey', { icon: 'ℹ️' })
        }
        
        const newEntry = {
          input,
          output: generatedText,
          timestamp: new Date().toLocaleString()
        }
        
        const updatedHistory = [newEntry, ...history].slice(0, 10)
        setHistory(updatedHistory)
        localStorage.setItem('aiHistory', JSON.stringify(updatedHistory))
        
        if (response.data.mock) {
          toast('Using mock response. Add OpenAI API key for real generation.', {
            icon: '⚠️',
            duration: 3000
          })
        }
      } else {
        toast.error(response.data.error || 'Generation failed')
      }
    } catch (error) {
      console.error('AI generation error:', error)
      toast.error('Failed to generate content')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleEnhance = async () => {
    if (!output) return
    
    setIsGenerating(true)
    
    try {
      // Only humanize if enabled
      if (!settings.humanizer_enabled) {
        toast('Humanizer is disabled. Enable it in settings to enhance text.', { icon: '⚠️' })
        setIsGenerating(false)
        return
      }
      
      const response = await axios.post(`${API_URL}/api/ai/humanize`, {
        text: output,
        grade_level: settings.grade_level,
        tone: settings.tone,
        style: settings.rewrite_style,
        preserve_meaning: true
      })
      
      if (response.data.success) {
        setOutput(response.data.text)
        
        if (response.data.mock) {
          toast('Using mock enhancement. Add OpenAI API key for real AI.', {
            icon: '⚠️',
            duration: 3000
          })
        } else {
          toast.success('Content enhanced successfully!')
        }
      } else {
        toast.error(response.data.error || 'Enhancement failed')
      }
    } catch (error) {
      console.error('Enhancement error:', error)
      toast.error('Failed to enhance content')
    } finally {
      setIsGenerating(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(output)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      {/* First Time Helper */}
      <FirstTimeHelper feature="ai-hub" />
      
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 rounded-2xl p-6 backdrop-blur-sm border border-purple-500/20">
        <div className="flex items-center gap-3 mb-3">
          <Brain className="w-8 h-8 text-purple-400" />
          <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            AI Content Hub
          </h2>
        </div>
        <p className="text-gray-400">Generate, enhance, and transform your text with AI assistance</p>
        <div className="mt-3 flex items-center gap-2">
          <kbd className="px-2 py-0.5 bg-gray-700 bg-gray-800 rounded text-xs">Ctrl+Alt+G</kbd>
          <span className="text-xs text-gray-400">Highlight any text and press this for instant AI magic!</span>
        </div>
      </div>

      {/* Template Selection */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-yellow-400" />
          Content Templates
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {templates.map((template) => {
            const Icon = template.icon
            return (
              <motion.button
                key={template.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setSelectedTemplate(template.id)}
                className={`p-4 rounded-lg border transition-all ${
                  selectedTemplate === template.id
                    ? 'bg-purple-500/20 bg-purple-500/10 border-purple-500 shadow-lg shadow-purple-500/20'
                    : 'bg-gray-800/50 bg-gray-900/50 border-gray-700 hover:border-gray-600'
                }`}
              >
                <Icon className={`w-6 h-6 mb-2 ${
                  selectedTemplate === template.id ? 'text-purple-400' : 'text-gray-400'
                }`} />
                <div className="text-sm font-medium">{template.name}</div>
                <div className="text-xs text-gray-400 mt-1">{template.description}</div>
              </motion.button>
            )
          })}
        </div>
      </div>

      {/* AI Generation Settings */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <BrainIcon className="w-5 h-5 text-purple-400" />
          AI Generation Settings
        </h3>
        
        <div className="space-y-4">
          {/* Response Type */}
          <div>
            <label className="block text-sm font-medium mb-2">Response Type</label>
            <div className="flex gap-3">
              <button
                onClick={() => setSettings({...settings, response_type: 'short_response'})}
                className={`flex-1 py-2 px-4 rounded-lg border transition-all ${
                  settings.response_type === 'short_response'
                    ? 'bg-purple-500/20 border-purple-500 text-purple-300'
                    : 'bg-gray-800/50 border-gray-600 hover:border-gray-500'
                }`}
              >
                Short Response
              </button>
              <button
                onClick={() => setSettings({...settings, response_type: 'essay'})}
                className={`flex-1 py-2 px-4 rounded-lg border transition-all ${
                  settings.response_type === 'essay'
                    ? 'bg-purple-500/20 border-purple-500 text-purple-300'
                    : 'bg-gray-800/50 border-gray-600 hover:border-gray-500'
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
                onChange={(e) => setSettings({...settings, response_length: Number(e.target.value)})}
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
                  onChange={(e) => setSettings({...settings, required_pages: Number(e.target.value)})}
                  className="w-full bg-gray-800 rounded-lg px-3 py-2 border border-gray-600 focus:border-purple-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Format</label>
                <select
                  value={settings.academic_format}
                  onChange={(e) => setSettings({...settings, academic_format: e.target.value})}
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
                onChange={(e) => setSettings({...settings, grade_level: Number(e.target.value)})}
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
                onChange={(e) => setSettings({...settings, tone: e.target.value})}
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
            <label className="flex items-center gap-2 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-700/50 group relative" title="Auto-humanize AI output">
              <input
                type="checkbox"
                checked={settings.humanizer_enabled}
                onChange={(e) => {
                  setSettings({...settings, humanizer_enabled: e.target.checked})
                  // Update global humanize state
                  localStorage.setItem('slywriter-auto-humanize', e.target.checked.toString())
                  if (e.target.checked) {
                    toast.success('✨ Auto-humanize enabled!', { duration: 2000 })
                  }
                }}
                className="w-5 h-5 text-purple-500 rounded"
              />
              <div>
                <span className="text-sm font-medium">Auto-Humanize</span>
                <p className="text-xs text-gray-400">Natural output</p>
              </div>
            </label>
            
            <label className="flex items-center gap-2 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-700/50 group" title="Preview and edit generated content before using">
              <input
                type="checkbox"
                checked={settings.review_mode}
                onChange={(e) => setSettings({...settings, review_mode: e.target.checked})}
                className="w-5 h-5 text-purple-500 rounded"
              />
              <div>
                <span className="text-sm font-medium">Review</span>
                <p className="text-xs text-gray-400">Preview first</p>
              </div>
            </label>
            
            <label className="flex items-center gap-2 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-700/50 group" title="Auto-save questions and answers to build your knowledge base">
              <input
                type="checkbox"
                checked={settings.learning_mode}
                onChange={(e) => setSettings({...settings, learning_mode: e.target.checked})}
                className="w-5 h-5 text-purple-500 rounded"
              />
              <div>
                <span className="text-sm font-medium">Auto-Learn</span>
                <p className="text-xs text-gray-400">Track topics</p>
              </div>
            </label>
          </div>
        </div>
      </div>
      
      {/* Humanize Status Banner */}
      {settings.humanizer_enabled && (
        <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-xl p-3 border border-purple-500/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SparklesIcon className="w-5 h-5 text-purple-400" />
              <span className="text-sm font-medium text-purple-300">✨ Auto-Humanize is ON</span>
              <span className="text-xs text-gray-400">All AI content will be humanized</span>
            </div>
            <button
              onClick={() => {
                // Navigate to Humanizer tab
                const humanizerTab = document.querySelector('[data-tab="humanizer"]') as HTMLElement
                if (humanizerTab) humanizerTab.click()
              }}
              className="text-xs text-purple-400 hover:text-purple-300 underline"
            >
              Go to Humanizer →
            </button>
          </div>
        </div>
      )}
      
      {/* Workflow Explanation */}
      <div className="space-y-3">
        {/* Highlight Workflow Tip */}
        <div className="bg-gradient-to-r from-yellow-900/20 to-orange-900/20 rounded-xl p-4 border border-yellow-500/20">
          <div className="flex items-start gap-3">
            <Zap className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-2">
              <span className="text-sm font-semibold text-yellow-300">⚡ Quick Workflow (Most Popular):</span>
              <p className="text-xs text-gray-400">
                <span className="text-yellow-300">Highlight any text</span> → Press <kbd className="px-2 py-0.5 bg-gray-700 rounded text-xs">Ctrl+Alt+G</kbd> → AI generates answer → Auto-types naturally!<br/>
                <span className="text-gray-500 mt-1 inline-block">Perfect for: Online tests, chat responses, quick answers</span>
              </p>
            </div>
          </div>
        </div>
        
        {/* Active Settings */}
        {(settings.humanizer_enabled || settings.review_mode || settings.learning_mode) && (
          <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-xl p-4 border border-purple-500/20">
            <div className="flex items-start gap-3">
              <SparklesIcon className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" />
              <div className="space-y-2">
                <span className="text-sm font-semibold text-purple-300">🎯 Active Features:</span>
                <div className="text-xs text-gray-400 space-y-1">
                  {settings.humanizer_enabled && (
                    <div className="flex items-start gap-2">
                      <span>✅</span>
                      <span><strong className="text-purple-300">Humanizer:</strong> Makes content sound natural, varies sentence structure, removes AI patterns</span>
                    </div>
                  )}
                  {settings.review_mode && (
                    <div className="flex items-start gap-2">
                      <span>✅</span>
                      <span><strong className="text-purple-300">Review Mode:</strong> Shows popup to check/edit before using (great for important work)</span>
                    </div>
                  )}
                  {settings.learning_mode && (
                    <div className="flex items-start gap-2">
                      <span>✅</span>
                      <span><strong className="text-purple-300">Learning Mode:</strong> Saves content as lessons for future reference</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Section */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <label className="block text-sm font-medium mb-2">Your Input</label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter your topic, idea, or text to enhance..."
          className="w-full h-32 bg-gray-800 rounded-lg p-4 border border-gray-600 focus:border-purple-500 focus:outline-none resize-none"
        />
        
        <div className="flex gap-3 mt-4">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleGenerate}
            disabled={isGenerating || !input.trim()}
            className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 py-3 rounded-lg font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Zap className="w-5 h-5" />
                Generate Content
              </>
            )}
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleEnhance}
            disabled={isGenerating || !output}
            className="px-6 bg-gray-800 border border-gray-600 py-3 rounded-lg font-medium flex items-center gap-2 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Wand2 className="w-5 h-5" />
            Enhance
          </motion.button>
        </div>
      </div>

      {/* Output Section */}
      <AnimatePresence>
        {output && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50"
          >
            <div className="flex justify-between items-center mb-4">
              <label className="text-sm font-medium">AI Generated Output</label>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={copyToClipboard}
                className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </motion.button>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 max-h-64 overflow-y-auto">
              <p className="whitespace-pre-wrap">{output}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* History */}
      {history.length > 0 && (
        <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Generations</h3>
          <div className="space-y-3 max-h-48 overflow-y-auto">
            {history.map((item, index) => (
              <div key={index} className="bg-gray-800 bg-gray-900/30 rounded-lg p-3">
                <div className="text-xs text-gray-400 mb-1">{item.timestamp}</div>
                <div className="text-sm text-gray-300">{item.input}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}