'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import toast from 'react-hot-toast'
import { 
  SparklesIcon, CopyIcon, RefreshCwIcon, TrashIcon,
  Lightbulb, Shield, Zap, AlertCircle, CheckCircle2
} from 'lucide-react'

const API_URL = 'https://slywriterapp.onrender.com'

export default function HumanizerTab() {
  const [inputText, setInputText] = useState('')
  const [outputText, setOutputText] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [autoHumanize, setAutoHumanize] = useState(false)
  const [userPlan, setUserPlan] = useState<string>('free')
  const [hasAccess, setHasAccess] = useState(false)
  
  // Check user's plan and access
  useEffect(() => {
    const checkAccess = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        if (!token) {
          setHasAccess(false)
          return
        }

        const response = await axios.get(`${API_URL}/api/user-dashboard`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })

        if (response.data.success) {
          const plan = response.data.dashboard.plan.name
          setUserPlan(plan)
          setHasAccess(plan !== 'free')
        }
      } catch (error) {
        console.error('Failed to check access:', error)
        setHasAccess(false)
      }
    }
    
    checkAccess()
  }, [])
  
  // Load and sync auto-humanize state with AI Writer tab
  useEffect(() => {
    const saved = localStorage.getItem('slywriter-auto-humanize')
    if (saved !== null) {
      setAutoHumanize(saved === 'true')
    }
  }, [])
  
  // Save auto-humanize state
  useEffect(() => {
    localStorage.setItem('slywriter-auto-humanize', autoHumanize.toString())
  }, [autoHumanize])
  
  // Listen for changes from other tabs (like AI Writer)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'slywriter-auto-humanize' && e.newValue !== null) {
        setAutoHumanize(e.newValue === 'true')
      }
    }
    
    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])
  
  const processText = async () => {
    if (!inputText.trim()) {
      toast.error('Please enter some text')
      return
    }
    
    setIsProcessing(true)
    try {
      const response = await axios.post(`${API_URL}/api/ai/humanize`, {
        text: inputText,
        settings: {
          grade_level: 11,
          tone: 'Neutral',
          style: 'Clear'
        }
      })
      
      setOutputText(response.data.text)
      toast.success('✨ Text humanized!')
    } catch (error) {
      console.error('Processing failed:', error)
      toast.error('Failed to humanize text')
    } finally {
      setIsProcessing(false)
    }
  }
  
  const copyToClipboard = () => {
    if (outputText) {
      navigator.clipboard.writeText(outputText)
      toast.success('Copied to clipboard!')
    }
  }
  
  const clearAll = () => {
    setInputText('')
    setOutputText('')
  }
  
  // Show upgrade message for free users
  if (!hasAccess) {
    return (
      <div className="space-y-6">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-2xl p-8 backdrop-blur-sm border border-purple-500/20"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-purple-500/20 rounded-xl">
              <Shield className="w-8 h-8 text-purple-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Premium Feature: AI Text Humanizer
              </h2>
              <p className="text-gray-400 mt-1">Upgrade to unlock advanced humanization technology</p>
            </div>
          </div>
          
          <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700 mb-6">
            <div className="flex items-start gap-3 mb-4">
              <AlertCircle className="w-5 h-5 text-yellow-400 mt-0.5" />
              <div>
                <h3 className="text-white font-semibold mb-2">This feature requires a paid plan</h3>
                <p className="text-gray-400 text-sm">
                  The Humanizer uses advanced AI technology to transform text into natural, human-like writing. 
                  Due to high API costs, this feature is available exclusively for our paid plans.
                </p>
              </div>
            </div>
            
            <div className="space-y-3 mt-6">
              <h4 className="text-white font-medium">What you get with the Humanizer:</h4>
              <ul className="space-y-2">
                <li className="flex items-center gap-2 text-gray-300 text-sm">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  Transform AI-generated content to bypass detection
                </li>
                <li className="flex items-center gap-2 text-gray-300 text-sm">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  Maintain original meaning while improving naturalness
                </li>
                <li className="flex items-center gap-2 text-gray-300 text-sm">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  Advanced linguistic patterns and variations
                </li>
                <li className="flex items-center gap-2 text-gray-300 text-sm">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  Perfect for academic and professional writing
                </li>
              </ul>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <motion.div 
              whileHover={{ scale: 1.02 }}
              className="bg-gradient-to-br from-green-900/30 to-emerald-900/30 rounded-xl p-4 border border-green-500/30"
            >
              <h4 className="text-green-400 font-semibold mb-2">Basic Plan</h4>
              <p className="text-2xl font-bold text-white mb-1">$9.99<span className="text-sm text-gray-400">/mo</span></p>
              <p className="text-gray-400 text-xs">10,000 words + Humanizer</p>
            </motion.div>
            
            <motion.div 
              whileHover={{ scale: 1.02 }}
              className="bg-gradient-to-br from-blue-900/30 to-cyan-900/30 rounded-xl p-4 border border-blue-500/30"
            >
              <h4 className="text-blue-400 font-semibold mb-2">Pro Plan</h4>
              <p className="text-2xl font-bold text-white mb-1">$19.99<span className="text-sm text-gray-400">/mo</span></p>
              <p className="text-gray-400 text-xs">20,000 words + All features</p>
            </motion.div>
            
            <motion.div 
              whileHover={{ scale: 1.02 }}
              className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 rounded-xl p-4 border border-purple-500/30"
            >
              <h4 className="text-purple-400 font-semibold mb-2">Premium Plan</h4>
              <p className="text-2xl font-bold text-white mb-1">$39.99<span className="text-sm text-gray-400">/mo</span></p>
              <p className="text-gray-400 text-xs">50,000 words + Priority</p>
            </motion.div>
          </div>
          
          <div className="mt-6 flex justify-center">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-8 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all"
            >
              Upgrade Now to Unlock Humanizer
            </motion.button>
          </div>
        </motion.div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-2xl p-8 backdrop-blur-sm border border-purple-500/20"
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="p-3 bg-purple-500/20 rounded-xl">
            <SparklesIcon className="w-8 h-8 text-purple-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI Text Humanizer
            </h2>
            <p className="text-gray-400 mt-1">Transform AI content into natural, human-like writing</p>
          </div>
        </div>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mt-6">
          <div className="bg-gray-800/50 rounded-lg p-3 text-center">
            <Zap className="w-5 h-5 text-yellow-400 mx-auto mb-1" />
            <p className="text-xs text-gray-400">Instant</p>
            <p className="text-sm font-semibold text-white">Processing</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3 text-center">
            <Shield className="w-5 h-5 text-green-400 mx-auto mb-1" />
            <p className="text-xs text-gray-400">Undetectable</p>
            <p className="text-sm font-semibold text-white">Output</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3 text-center">
            <CheckCircle2 className="w-5 h-5 text-blue-400 mx-auto mb-1" />
            <p className="text-xs text-gray-400">Preserves</p>
            <p className="text-sm font-semibold text-white">Meaning</p>
          </div>
        </div>
      </motion.div>

      {/* Auto-Humanize Toggle */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-xl p-6 backdrop-blur-sm border border-purple-500/30"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <SparklesIcon className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">
                Auto-Humanize Mode
              </h3>
              <p className="text-sm text-gray-400 mt-0.5">
                Automatically humanize all AI Writer content
              </p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={autoHumanize}
              onChange={(e) => setAutoHumanize(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-14 h-7 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-purple-500 peer-checked:to-pink-500"></div>
          </label>
        </div>
        
        {autoHumanize && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-4 p-3 bg-purple-500/10 rounded-lg border border-purple-500/20"
          >
            <p className="text-xs text-purple-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Active: All AI Writer outputs will be automatically humanized
            </p>
          </motion.div>
        )}
      </motion.div>
      
      {/* Manual Humanizer */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Manual Humanizer</h3>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <RefreshCwIcon className="w-3 h-3" />
            Instant conversion
          </div>
        </div>
        
        {/* Input */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-400">AI Text Input</label>
            <span className="text-xs text-gray-500">{inputText.length} characters</span>
          </div>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste your AI-generated text here..."
            className="w-full h-40 bg-gray-800/70 rounded-lg p-4 text-white placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
          />
        </div>
        
        {/* Action Buttons */}
        <div className="flex gap-2 mb-4">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={processText}
            disabled={isProcessing || !inputText.trim()}
            className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-all flex items-center justify-center gap-2 shadow-lg"
          >
            {isProcessing ? (
              <>
                <RefreshCwIcon className="w-4 h-4 animate-spin" />
                Humanizing...
              </>
            ) : (
              <>
                <SparklesIcon className="w-4 h-4" />
                Humanize Text
              </>
            )}
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={clearAll}
            className="px-4 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition-all"
            title="Clear all text"
          >
            <TrashIcon className="w-4 h-4" />
          </motion.button>
        </div>
        
        {/* Output */}
        <AnimatePresence>
          {outputText && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-gray-400">Humanized Output</label>
                <button
                  onClick={copyToClipboard}
                  className="px-3 py-1 bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 rounded-lg text-xs text-green-400 flex items-center gap-1 transition-all"
                >
                  <CopyIcon className="w-3 h-3" />
                  Copy Result
                </button>
              </div>
              <div className="bg-gradient-to-r from-green-900/20 to-blue-900/20 border border-green-500/20 rounded-lg p-4">
                <pre className="whitespace-pre-wrap text-sm text-white/90">{outputText}</pre>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
      
      {/* Tips Section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 rounded-xl p-6 border border-blue-500/20"
      >
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb className="w-5 h-5 text-yellow-400" />
          <h3 className="text-lg font-semibold text-white">Pro Tips</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-300">
              <span className="font-semibold">Best Results:</span> Input text should be at least 50 words for optimal humanization
            </p>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-300">
              <span className="font-semibold">Auto Mode:</span> Enable auto-humanize to process all AI Writer content automatically
            </p>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-300">
              <span className="font-semibold">Preservation:</span> Original meaning and key information is always maintained
            </p>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-300">
              <span className="font-semibold">Detection:</span> Output bypasses all major AI detection tools
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}