'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { RENDER_API_URL } from '../config/api'
import axios from 'axios'
import toast from 'react-hot-toast'
import { 
  SparklesIcon, RefreshCwIcon, CopyIcon, TrashIcon,
  ClipboardIcon, ArrowRightIcon
} from 'lucide-react'

const API_URL = ${RENDER_API_URL}'

export default function HumanizerTabSimple() {
  const [inputText, setInputText] = useState('')
  const [outputText, setOutputText] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [autoHumanize, setAutoHumanize] = useState(false)
  
  // Load and sync auto-humanize state
  useEffect(() => {
    const saved = localStorage.getItem('slywriter-auto-humanize')
    if (saved !== null) {
      setAutoHumanize(saved === 'true')
    }
  }, [])
  
  // Listen for changes from other tabs
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'slywriter-auto-humanize' && e.newValue !== null) {
        setAutoHumanize(e.newValue === 'true')
      }
    }
    
    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])
  
  const toggleAutoHumanize = () => {
    const newValue = !autoHumanize
    setAutoHumanize(newValue)
    localStorage.setItem('slywriter-auto-humanize', newValue.toString())
    toast.success(newValue ? '✨ Auto-humanize enabled!' : 'Auto-humanize disabled')
  }
  
  const humanizeText = async () => {
    if (!inputText.trim()) {
      toast.error('Please enter some text to humanize')
      return
    }
    
    setIsProcessing(true)
    
    try {
      const response = await axios.post(`${API_URL}/api/ai/humanize`, {
        text: inputText,
        preserve_meaning: true
      })
      
      if (response.data.success) {
        setOutputText(response.data.text)
        toast.success('✨ Text humanized successfully!')
      } else {
        toast.error(response.data.error || 'Humanization failed')
      }
    } catch (error) {
      console.error('Humanization error:', error)
      toast.error('Failed to humanize text')
    } finally {
      setIsProcessing(false)
    }
  }
  
  const pasteFromClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText()
      if (text) {
        setInputText(text)
        toast.success('📋 Pasted from clipboard!')
      }
    } catch (err) {
      toast.error('Failed to read clipboard')
    }
  }
  
  const copyOutput = () => {
    if (outputText) {
      navigator.clipboard.writeText(outputText)
      toast.success('📋 Copied to clipboard!')
    }
  }
  
  const clearAll = () => {
    setInputText('')
    setOutputText('')
    toast.success('🗑️ Cleared all text')
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 rounded-2xl p-6 backdrop-blur-sm border border-purple-500/20">
        <div className="flex items-center gap-3 mb-3">
          <SparklesIcon className="w-8 h-8 text-purple-400" />
          <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            Text Humanizer
          </h2>
        </div>
        <p className="text-gray-400">
          Transform AI-generated text into natural, human-like writing
        </p>
        
        {/* Auto-Humanize Toggle */}
        <div className="mt-4 flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
          <div className="flex items-center gap-3">
            <div>
              <p className="text-sm font-medium text-white">Auto-Humanize AI Content</p>
              <p className="text-xs text-gray-400">Automatically humanize all AI-generated content</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={autoHumanize}
              onChange={toggleAutoHumanize}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
          </label>
        </div>
        {autoHumanize ? (
          <div className="mt-3 p-3 bg-purple-500/10 rounded-lg border border-purple-500/30">
            <p className="text-xs text-purple-300">
              ✅ <strong>Auto-Humanize Active:</strong> All AI content from the AI Writer tab will be automatically humanized!
            </p>
          </div>
        ) : (
          <div className="mt-3 p-3 bg-blue-500/10 rounded-lg border border-blue-500/30">
            <p className="text-xs text-blue-300">
              💡 <strong>Manual Mode:</strong> Paste any AI-generated text → Click Humanize → 
              Get natural, undetectable output. Simple as that!
            </p>
          </div>
        )}
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Input Text</h3>
            <div className="flex gap-2">
              <button
                onClick={pasteFromClipboard}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm flex items-center gap-2 transition-colors"
              >
                <ClipboardIcon className="w-4 h-4" />
                Paste
              </button>
              <button
                onClick={clearAll}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm flex items-center gap-2 transition-colors"
              >
                <TrashIcon className="w-4 h-4" />
                Clear
              </button>
            </div>
          </div>
          
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste AI-generated text here..."
            className="w-full h-80 bg-gray-800 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
          />
          
          <div className="mt-3 text-xs text-gray-500">
            {inputText.length} characters | {inputText.split(/\s+/).filter(w => w).length} words
          </div>
        </div>
        
        {/* Output Section */}
        <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Humanized Output</h3>
            {outputText && (
              <button
                onClick={copyOutput}
                className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded-lg text-sm flex items-center gap-2 transition-colors"
              >
                <CopyIcon className="w-4 h-4" />
                Copy
              </button>
            )}
          </div>
          
          {outputText ? (
            <>
              <textarea
                value={outputText}
                readOnly
                className="w-full h-80 bg-gray-800 rounded-lg p-4 text-white resize-none focus:outline-none"
              />
              <div className="mt-3 text-xs text-gray-500">
                {outputText.length} characters | {outputText.split(/\s+/).filter(w => w).length} words
              </div>
            </>
          ) : (
            <div className="h-80 bg-gray-800/50 rounded-lg flex items-center justify-center">
              <div className="text-center text-gray-500">
                <SparklesIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Humanized text will appear here</p>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Process Button */}
      <div className="flex justify-center">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={humanizeText}
          disabled={isProcessing || !inputText.trim()}
          className="px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg font-medium flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed hover:from-purple-700 hover:to-pink-700 transition-all"
        >
          {isProcessing ? (
            <>
              <RefreshCwIcon className="w-5 h-5 animate-spin" />
              Humanizing...
            </>
          ) : (
            <>
              <SparklesIcon className="w-5 h-5" />
              Humanize Text
              <ArrowRightIcon className="w-5 h-5" />
            </>
          )}
        </motion.button>
      </div>
      
      {/* Info Box */}
      <div className="bg-gradient-to-r from-green-900/20 to-blue-900/20 rounded-xl p-4 border border-green-500/20">
        <h4 className="text-sm font-semibold text-white mb-2">What Humanization Does:</h4>
        <ul className="text-xs text-gray-400 space-y-1">
          <li>• Varies sentence structure and length naturally</li>
          <li>• Removes AI detection patterns and markers</li>
          <li>• Adds natural flow and human-like transitions</li>
          <li>• Preserves meaning while changing style</li>
          <li>• Makes text undetectable by AI detectors</li>
        </ul>
      </div>
    </div>
  )
}