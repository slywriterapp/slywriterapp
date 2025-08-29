'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Wand2, RefreshCw, Copy, Check, Brain, Zap, BookOpen, Briefcase, Heart, Gamepad2, Code, Palette, AlertCircleIcon, XCircleIcon } from 'lucide-react'
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

export default function AIHubTab() {
  const [input, setInput] = useState('')
  const [output, setOutput] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState('creative')
  const [isGenerating, setIsGenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [wordCount, setWordCount] = useState(300)
  const [tone, setTone] = useState('neutral')
  const [history, setHistory] = useState<Array<{input: string, output: string, timestamp: string}>>([])

  useEffect(() => {
    const savedHistory = localStorage.getItem('aiHistory')
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory))
    }
  }, [])

  const handleGenerate = async () => {
    if (!input.trim()) return
    
    setIsGenerating(true)
    
    try {
      const template = templates.find(t => t.id === selectedTemplate)
      const systemPrompt = `You are a ${template?.name} writer. Generate content with a ${tone} tone.`
      const prompt = `${template?.prompt}: ${input}. Target approximately ${wordCount} words.`
      
      const response = await axios.post(`${API_URL}/api/ai/generate`, {
        prompt,
        max_tokens: Math.round(wordCount * 1.3),
        temperature: tone === 'creative' || tone === 'humorous' ? 0.9 : 0.7,
        system_prompt: systemPrompt
      })
      
      if (response.data.success) {
        const generatedText = response.data.text
        setOutput(generatedText)
        
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
      const response = await axios.post(`${API_URL}/api/ai/humanize`, {
        text: output,
        style: tone === 'formal' ? 'professional' : tone === 'casual' ? 'conversational' : 'natural',
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

      {/* Controls */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900/50 rounded-xl p-4 backdrop-blur-sm border border-gray-700/50">
          <label className="block text-sm font-medium mb-2">Word Count Target</label>
          <input
            type="range"
            min="100"
            max="1000"
            step="50"
            value={wordCount}
            onChange={(e) => setWordCount(Number(e.target.value))}
            className="w-full"
          />
          <div className="text-center text-purple-400 mt-2">{wordCount} words</div>
        </div>
        
        <div className="bg-gray-900/50 rounded-xl p-4 backdrop-blur-sm border border-gray-700/50">
          <label className="block text-sm font-medium mb-2">Tone</label>
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            className="w-full bg-gray-800 rounded-lg px-3 py-2 border border-gray-600 focus:border-purple-500 focus:outline-none"
          >
            <option value="neutral">Neutral</option>
            <option value="formal">Formal</option>
            <option value="casual">Casual</option>
            <option value="enthusiastic">Enthusiastic</option>
            <option value="professional">Professional</option>
            <option value="humorous">Humorous</option>
          </select>
        </div>
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