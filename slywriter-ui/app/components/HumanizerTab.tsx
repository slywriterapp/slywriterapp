'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { 
  SparklesIcon, BrainIcon, EyeIcon, BookOpenIcon,
  SlidersIcon, FileTextIcon, ClipboardIcon, PlayIcon,
  CheckCircleIcon, XCircleIcon, AlertCircleIcon, ZapIcon,
  GraduationCapIcon, PenToolIcon, MessageSquareIcon,
  RefreshCwIcon, SaveIcon, CopyIcon, EditIcon
} from 'lucide-react'

const API_URL = 'http://localhost:8000'

interface HumanizerSettings {
  // AI Generation Settings
  response_type: 'short_response' | 'essay'
  response_length: number // 1-5 for short, pages for essay
  academic_format: string
  required_pages: number
  
  // Traditional Humanizer Settings
  grade_level: number
  tone: string
  depth: number
  rewrite_style: string
  use_of_evidence: string
  
  // Mode Settings
  humanizer_enabled: boolean
  review_mode: boolean
  learning_mode: boolean
}

export default function HumanizerTab() {
  const { user, canType, wordsRemaining } = useAuth()
  
  // Core state
  const [inputText, setInputText] = useState('')
  const [outputText, setOutputText] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [clipboardMonitoring, setClipboardMonitoring] = useState(false)
  const [lastClipboard, setLastClipboard] = useState('')
  
  // Settings state
  const [settings, setSettings] = useState<HumanizerSettings>({
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
  
  // Load saved settings
  useEffect(() => {
    const saved = localStorage.getItem('slywriter-humanizer-settings')
    if (saved) {
      setSettings(JSON.parse(saved))
    }
  }, [])
  
  // Save settings on change
  useEffect(() => {
    localStorage.setItem('slywriter-humanizer-settings', JSON.stringify(settings))
  }, [settings])
  
  // Clipboard monitoring
  useEffect(() => {
    if (!clipboardMonitoring) return
    
    const interval = setInterval(async () => {
      try {
        const text = await navigator.clipboard.readText()
        if (text && text !== lastClipboard && text.length > 20) {
          setLastClipboard(text)
          setInputText(text)
          toast.success('📋 Captured highlighted text!')
          
          // Auto-process if modes are enabled
          if (settings.humanizer_enabled || settings.learning_mode) {
            processText(text)
          }
        }
      } catch (err) {
        // Silent fail - clipboard access denied
      }
    }, 500)
    
    return () => clearInterval(interval)
  }, [clipboardMonitoring, lastClipboard, settings])
  
  const processText = async (text?: string) => {
    const processText = text || inputText
    if (!processText.trim()) {
      toast.error('Please enter text to process')
      return
    }
    
    // Check word limit
    const wordCount = processText.split(/\s+/).length * 2 // Estimate output
    if (!canType(wordCount)) {
      toast.error(`Word limit exceeded! ${wordsRemaining} words remaining`)
      return
    }
    
    setIsProcessing(true)
    
    try {
      // Build AI prompt based on settings
      const prompt = buildAIPrompt(processText)
      
      // Call AI generation endpoint
      const response = await axios.post(`${API_URL}/api/ai/generate`, {
        prompt,
        settings
      })
      
      let generatedText = response.data.text
      
      // Apply humanizer if enabled
      if (settings.humanizer_enabled) {
        const humanizeResponse = await axios.post(`${API_URL}/api/ai/humanize`, {
          text: generatedText,
          grade_level: settings.grade_level,
          tone: settings.tone,
          style: settings.rewrite_style
        })
        generatedText = humanizeResponse.data.text
      }
      
      setOutputText(generatedText)
      
      // Show preview if review mode
      if (settings.review_mode) {
        setShowPreview(true)
      } else {
        // Auto-type if not in review mode
        await startTyping(generatedText)
      }
      
      // Create lesson if learning mode
      if (settings.learning_mode) {
        await createLesson(processText, generatedText)
      }
      
      toast.success('✨ Text processed successfully!')
    } catch (error) {
      console.error('Processing failed:', error)
      toast.error('Failed to process text')
    } finally {
      setIsProcessing(false)
    }
  }
  
  const buildAIPrompt = (text: string): string => {
    const { response_type, response_length, academic_format, required_pages,
            grade_level, tone, depth, use_of_evidence } = settings
    
    let prompt = `Process this text: "${text}"\n\n`
    
    if (response_type === 'short_response') {
      const lengths = {
        1: 'very brief (1-2 sentences)',
        2: 'short (2-4 sentences)', 
        3: 'medium (4-8 sentences)',
        4: 'long (8-15 sentences)',
        5: 'very detailed (15+ sentences)'
      }
      prompt += `Create a ${lengths[response_length as keyof typeof lengths]} response.\n`
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
    prompt += `- Depth: ${['shallow', 'basic', 'moderate', 'deep', 'comprehensive'][depth - 1]}\n`
    prompt += `- Style: ${settings.rewrite_style.toLowerCase()}\n`
    
    if (use_of_evidence !== 'None') {
      prompt += `- Evidence/examples are ${use_of_evidence.toLowerCase()}\n`
    }
    
    return prompt
  }
  
  const startTyping = async (text: string) => {
    try {
      await axios.post(`${API_URL}/api/typing/start`, {
        text,
        profile: 'Medium',
        preview_mode: false
      })
      toast.success('🤖 Automation started!')
    } catch (error) {
      toast.error('Failed to start typing')
    }
  }
  
  const createLesson = async (input: string, output: string) => {
    try {
      await axios.post(`${API_URL}/api/learning/create-lesson`, {
        topic: input.substring(0, 100),
        content: output,
        method: 'ai_generated'
      })
      toast.success('📚 Lesson created!')
    } catch (error) {
      console.error('Failed to create lesson:', error)
    }
  }
  
  const getWordEstimate = (): string => {
    if (settings.response_type === 'short_response') {
      const estimates = {
        1: '~15-30 words',
        2: '~30-80 words',
        3: '~80-160 words',
        4: '~160-300 words',
        5: '~300+ words'
      }
      return estimates[settings.response_length as keyof typeof estimates] || ''
    } else {
      const wordsPerPage = settings.academic_format === 'MLA' ? 275 : 
                          settings.academic_format === 'APA' ? 260 :
                          settings.academic_format === 'Chicago' ? 250 : 250
      const totalWords = settings.required_pages * wordsPerPage
      return `~${totalWords} words (${settings.required_pages} ${settings.required_pages === 1 ? 'page' : 'pages'})`
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 rounded-2xl p-6 backdrop-blur-sm border border-purple-500/20">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <BrainIcon className="w-8 h-8 text-purple-400" />
              <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                AI Humanizer Engine
              </h2>
            </div>
            <p className="text-gray-400">Transform any text into human-like, natural content</p>
            <div className="mt-3 p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
              <p className="text-xs text-yellow-300">
                <strong>Important:</strong> This tool is designed for legitimate content creation, 
                accessibility, and productivity purposes. We do not condone academic dishonesty or plagiarism. 
                Always cite your sources and follow your institution's guidelines.
              </p>
            </div>
          </div>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setClipboardMonitoring(!clipboardMonitoring)}
            className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${
              clipboardMonitoring 
                ? 'bg-green-500/20 text-green-400 border border-green-500/50' 
                : 'bg-gray-800 text-gray-400 border border-gray-700'
            }`}
          >
            <ClipboardIcon className="w-4 h-4" />
            {clipboardMonitoring ? 'Monitoring Active' : 'Start Monitoring'}
          </motion.button>
        </div>
      </div>
      
      {/* Workflow Explanation */}
      <AnimatePresence>
        {!localStorage.getItem('slywriter-humanizer-workflow-seen') && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-xl p-4 border border-blue-500/30"
          >
            <div className="flex justify-between items-start mb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <ZapIcon className="w-4 h-4 text-yellow-400" />
                The Magic Workflow - How It Works
              </h3>
              <button
                onClick={() => {
                  localStorage.setItem('slywriter-humanizer-workflow-seen', 'true')
                  window.location.reload()
                }}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <XCircleIcon className="w-4 h-4" />
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              {[
                { step: 1, title: "Highlight Question", desc: "Select any text or question anywhere", icon: "🔍" },
                { step: 2, title: "AI Generates", desc: "ChatGPT creates perfect answer", icon: "🤖" },
                { step: 3, title: "Humanize", desc: "Make it undetectable (optional)", icon: "✨" },
                { step: 4, title: "Auto-Type", desc: "Types with human speed & patterns", icon: "⌨️" }
              ].map((item) => (
                <div key={item.step} className="flex items-start gap-2">
                  <div className="w-8 h-8 bg-purple-500/20 bg-purple-500/10 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-sm">{item.icon}</span>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-white">Step {item.step}</div>
                    <div className="text-xs text-purple-300 text-purple-400">{item.title}</div>
                    <div className="text-xs text-gray-400 mt-1">{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-3 flex items-center gap-2 text-xs">
              <kbd className="px-2 py-0.5 bg-gray-700 bg-gray-800 rounded">Ctrl+Alt+G</kbd>
              <span className="text-gray-400">triggers this workflow instantly on any highlighted text</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Original Workflow Section */}
      <div className="bg-blue-900/20 rounded-xl p-4 border border-blue-500/20">
        <div className="flex items-start gap-3">
          <AlertCircleIcon className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-300">
            <strong>SlyWriter Workflow:</strong> Highlight text anywhere → Press Ctrl+Alt+G (or enable monitoring) → 
            AI enhances content → Humanizer makes it undetectable → Review (optional) → Auto-types for you!
          </div>
        </div>
      </div>
      
      {/* Mode Toggles */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-sm font-semibold uppercase tracking-wider mb-4">Enhancement Modes</h3>
        
        <div className="grid grid-cols-3 gap-4">
          {/* AI Humanizer */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setSettings({...settings, humanizer_enabled: !settings.humanizer_enabled})}
            className={`p-4 rounded-lg border transition-all ${
              settings.humanizer_enabled 
                ? 'bg-purple-500/20 bg-purple-500/10 border-purple-500 text-purple-300 text-purple-400' 
                : 'bg-gray-800/50 bg-gray-900/50 border-gray-700 text-gray-400'
            }`}
          >
            <SparklesIcon className="w-6 h-6 mx-auto mb-2" />
            <div className="text-sm font-medium">AI Humanizer</div>
            <div className="text-xs mt-1 opacity-70">Makes AI undetectable</div>
          </motion.button>
          
          {/* Review Mode */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setSettings({...settings, review_mode: !settings.review_mode})}
            className={`p-4 rounded-lg border transition-all ${
              settings.review_mode 
                ? 'bg-blue-500/20 border-blue-500 text-blue-300' 
                : 'bg-gray-800/50 bg-gray-900/50 border-gray-700 text-gray-400'
            }`}
          >
            <EyeIcon className="w-6 h-6 mx-auto mb-2" />
            <div className="text-sm font-medium">Review Mode</div>
            <div className="text-xs mt-1 opacity-70">Preview before typing</div>
          </motion.button>
          
          {/* Learning Mode */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setSettings({...settings, learning_mode: !settings.learning_mode})}
            className={`relative p-4 rounded-lg border transition-all ${
              settings.learning_mode 
                ? 'bg-green-500/20 border-green-500 text-green-300' 
                : 'bg-gray-800/50 bg-gray-900/50 border-gray-700 text-gray-400'
            }`}
          >
            {settings.learning_mode && (
              <span className="absolute -top-2 -right-2 text-xs bg-yellow-500 text-white text-black px-2 py-0.5 rounded-full font-bold">
                RECOMMENDED
              </span>
            )}
            <BookOpenIcon className="w-6 h-6 mx-auto mb-2" />
            <div className="text-sm font-medium">Learning Mode</div>
            <div className="text-xs mt-1 opacity-70">Auto-create lessons</div>
          </motion.button>
        </div>
        
        <div className="mt-3 text-xs text-yellow-400">
          ⚠️ Words deducted even if review declined (API costs apply)
        </div>
      </div>
      
      {/* AI Generation Settings */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
          <SlidersIcon className="w-4 h-4 text-purple-400" />
          AI Generation Settings
        </h3>
        
        {/* Response Type Toggle */}
        <div className="mb-6">
          <label className="text-xs text-gray-400 mb-2 block">Response Type</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setSettings({...settings, response_type: 'short_response'})}
              className={`p-3 rounded-lg border transition-all ${
                settings.response_type === 'short_response'
                  ? 'bg-purple-500/20 bg-purple-500/10 border-purple-500 text-purple-300 text-purple-400'
                  : 'bg-gray-800/50 bg-gray-900/50 border-gray-700 text-gray-400'
              }`}
            >
              <MessageSquareIcon className="w-4 h-4 mx-auto mb-1" />
              <div className="text-sm">Short Response</div>
            </button>
            <button
              onClick={() => setSettings({...settings, response_type: 'essay'})}
              className={`p-3 rounded-lg border transition-all ${
                settings.response_type === 'essay'
                  ? 'bg-purple-500/20 bg-purple-500/10 border-purple-500 text-purple-300 text-purple-400'
                  : 'bg-gray-800/50 bg-gray-900/50 border-gray-700 text-gray-400'
              }`}
            >
              <FileTextIcon className="w-4 h-4 mx-auto mb-1" />
              <div className="text-sm">Essay/Document</div>
            </button>
          </div>
        </div>
        
        {/* Current Settings Preview */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <div className="text-sm text-gray-300">
            <span className="text-purple-400">📊 Output:</span> {getWordEstimate()}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {settings.response_type === 'short_response' 
              ? 'Perfect for quick responses and answers'
              : `Perfect for essays, reports, and documents${settings.academic_format !== 'None' ? ` (${settings.academic_format} format)` : ''}`}
          </div>
        </div>
        
        {/* Response Length (for short) / Pages (for essay) */}
        <div className="grid grid-cols-2 gap-4">
          {settings.response_type === 'short_response' ? (
            <div>
              <label className="text-xs text-gray-400 mb-2 block">Response Length</label>
              <input
                type="range"
                min="1"
                max="5"
                value={settings.response_length}
                onChange={(e) => setSettings({...settings, response_length: Number(e.target.value)})}
                className="w-full accent-purple-500"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>Very Short</span>
                <span className="text-purple-400 font-medium">
                  {['Very Short', 'Short', 'Medium', 'Long', 'Very Long'][settings.response_length - 1]}
                </span>
                <span>Very Long</span>
              </div>
            </div>
          ) : (
            <>
              <div>
                <label className="text-xs text-gray-400 mb-2 block">Required Pages</label>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={settings.required_pages}
                  onChange={(e) => setSettings({...settings, required_pages: Number(e.target.value)})}
                  className="w-full accent-purple-500"
                />
                <div className="text-center text-xs text-purple-400 mt-1">
                  {settings.required_pages} {settings.required_pages === 1 ? 'page' : 'pages'}
                </div>
              </div>
              
              <div>
                <label className="text-xs text-gray-400 mb-2 block">Academic Format</label>
                <select
                  value={settings.academic_format}
                  onChange={(e) => setSettings({...settings, academic_format: e.target.value})}
                  className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white border border-gray-700 focus:border-purple-500 focus:outline-none"
                >
                  <option value="None">No Format</option>
                  <option value="MLA">MLA</option>
                  <option value="APA">APA</option>
                  <option value="Chicago">Chicago</option>
                  <option value="IEEE">IEEE</option>
                </select>
              </div>
            </>
          )}
        </div>
      </div>
      
      {/* Traditional Humanizer Settings */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
          <PenToolIcon className="w-4 h-4 text-blue-400" />
          Humanizer Settings
        </h3>
        
        <div className="grid grid-cols-2 gap-4">
          {/* Grade Level */}
          <div>
            <label className="text-xs text-gray-400 mb-2 block">Grade Level</label>
            <input
              type="range"
              min="3"
              max="16"
              value={settings.grade_level}
              onChange={(e) => setSettings({...settings, grade_level: Number(e.target.value)})}
              className="w-full accent-blue-500"
            />
            <div className="text-center text-xs text-blue-400 mt-1">
              {settings.grade_level <= 12 ? `${settings.grade_level}th Grade` : 
               settings.grade_level === 13 ? 'Freshman' :
               settings.grade_level === 14 ? 'Sophomore' :
               settings.grade_level === 15 ? 'Junior' : 'Senior/Graduate'}
            </div>
          </div>
          
          {/* Depth */}
          <div>
            <label className="text-xs text-gray-400 mb-2 block">Depth of Answer</label>
            <input
              type="range"
              min="1"
              max="5"
              value={settings.depth}
              onChange={(e) => setSettings({...settings, depth: Number(e.target.value)})}
              className="w-full accent-blue-500"
            />
            <div className="text-center text-xs text-blue-400 mt-1">
              {['Shallow', 'Basic', 'Moderate', 'Deep', 'Comprehensive'][settings.depth - 1]}
            </div>
          </div>
          
          {/* Tone */}
          <div>
            <label className="text-xs text-gray-400 mb-2 block">Tone</label>
            <select
              value={settings.tone}
              onChange={(e) => setSettings({...settings, tone: e.target.value})}
              className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white border border-gray-700 focus:border-blue-500 focus:outline-none"
            >
              <option value="Neutral">Neutral</option>
              <option value="Formal">Formal</option>
              <option value="Casual">Casual</option>
              <option value="Witty">Witty</option>
            </select>
          </div>
          
          {/* Rewrite Style */}
          <div>
            <label className="text-xs text-gray-400 mb-2 block">Rewrite Style</label>
            <select
              value={settings.rewrite_style}
              onChange={(e) => setSettings({...settings, rewrite_style: e.target.value})}
              className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white border border-gray-700 focus:border-blue-500 focus:outline-none"
            >
              <option value="Clear">Clear</option>
              <option value="Concise">Concise</option>
              <option value="Creative">Creative</option>
            </select>
          </div>
          
          {/* Use of Evidence */}
          <div className="col-span-2">
            <label className="text-xs text-gray-400 mb-2 block">Use of Evidence</label>
            <select
              value={settings.use_of_evidence}
              onChange={(e) => setSettings({...settings, use_of_evidence: e.target.value})}
              className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white border border-gray-700 focus:border-blue-500 focus:outline-none"
            >
              <option value="None">None</option>
              <option value="Optional">Optional</option>
              <option value="Required">Required</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Input/Output */}
      <div className="grid grid-cols-2 gap-6">
        {/* Input */}
        <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
          <h3 className="text-sm font-semibold uppercase tracking-wider mb-4">Input Text</h3>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste text here or highlight anywhere while monitoring..."
            className="w-full h-64 bg-gray-800 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm"
          />
          <div className="mt-3 text-xs text-gray-400">
            {inputText.length} characters • {inputText.split(/\s+/).filter(Boolean).length} words
          </div>
        </div>
        
        {/* Output */}
        <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
          <h3 className="text-sm font-semibold uppercase tracking-wider mb-4">Processed Output</h3>
          <textarea
            value={outputText}
            readOnly
            placeholder="Processed text will appear here..."
            className="w-full h-64 bg-gray-800 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none text-sm"
          />
          <div className="mt-3 flex justify-between items-center">
            <div className="text-xs text-gray-400">
              {outputText.length} characters • {outputText.split(/\s+/).filter(Boolean).length} words
            </div>
            {outputText && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  navigator.clipboard.writeText(outputText)
                  toast.success('Copied to clipboard!')
                }}
                className="text-xs text-purple-400 hover:text-purple-300"
              >
                <CopyIcon className="w-4 h-4" />
              </motion.button>
            )}
          </div>
        </div>
      </div>
      
      {/* Action Buttons */}
      <div className="flex justify-center gap-4">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => processText()}
          disabled={isProcessing || !inputText.trim()}
          className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isProcessing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
              Processing...
            </>
          ) : (
            <>
              <SparklesIcon className="w-4 h-4" />
              Process & Humanize
            </>
          )}
        </motion.button>
        
        {outputText && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => startTyping(outputText)}
            className="px-6 py-3 bg-green-500 hover:bg-green-600 rounded-lg font-medium transition-all flex items-center gap-2"
          >
            <PlayIcon className="w-4 h-4" />
            Start Typing
          </motion.button>
        )}
      </div>
      
      {/* Preview Modal */}
      <AnimatePresence>
        {showPreview && outputText && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-8"
            onClick={() => setShowPreview(false)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-gray-900 rounded-xl p-6 max-w-4xl w-full max-h-[80vh] overflow-auto border border-purple-500/50"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-xl font-bold text-white mb-4">Review Generated Content</h3>
              
              <div className="bg-gray-800 rounded-lg p-4 mb-6">
                <pre className="whitespace-pre-wrap text-sm text-gray-300">{outputText}</pre>
              </div>
              
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowPreview(false)}
                  className="px-4 py-2 bg-gray-700 bg-gray-800 hover:bg-gray-600 rounded-lg text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    setShowPreview(false)
                    startTyping(outputText)
                  }}
                  className="px-4 py-2 bg-purple-500 bg-purple-500 hover:bg-purple-600 hover:bg-purple-500-dark rounded-lg text-white transition-colors flex items-center gap-2"
                >
                  <CheckCircleIcon className="w-4 h-4" />
                  Approve & Type
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}