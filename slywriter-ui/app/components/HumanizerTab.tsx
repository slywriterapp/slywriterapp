'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RENDER_API_URL } from '../config/api'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import UpgradeModal from './UpgradeModal'
import UsageMeter from './UsageMeter'
import {
  SparklesIcon, CopyIcon, RefreshCwIcon, TrashIcon,
  Lightbulb, Shield, Zap, AlertCircle, CheckCircle2
} from 'lucide-react'

const API_URL = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:5000'
  : RENDER_API_URL

interface HumanizerTabProps {
  onNavigateToDashboard?: () => void
}

export default function HumanizerTab({ onNavigateToDashboard }: HumanizerTabProps = {}) {
  const { user, usageLimits, canUseHumanizer, trackHumanizerUsage } = useAuth()
  const [inputText, setInputText] = useState('')
  const [outputText, setOutputText] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [autoHumanize, setAutoHumanize] = useState(false)
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const isExternalUpdate = useRef(false)

  // Load and sync auto-humanize state with AI Writer tab
  useEffect(() => {
    const saved = localStorage.getItem('slywriter-auto-humanize')
    if (saved !== null) {
      setAutoHumanize(saved === 'true')
    }
  }, [])

  // Save auto-humanize state and notify other components
  useEffect(() => {
    localStorage.setItem('slywriter-auto-humanize', autoHumanize.toString())

    // Only dispatch event if this is a user-initiated change, not from external sync
    if (!isExternalUpdate.current) {
      window.dispatchEvent(new CustomEvent('autoHumanizeChange', {
        detail: { enabled: autoHumanize }
      }))
    }

    // Reset the flag
    isExternalUpdate.current = false
  }, [autoHumanize])

  // Listen for changes from other components (same page) and other tabs
  useEffect(() => {
    // Handle changes from other browser tabs/windows
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'slywriter-auto-humanize' && e.newValue !== null) {
        isExternalUpdate.current = true
        setAutoHumanize(e.newValue === 'true')
      }
    }

    // Handle changes from other components in same page (like AI Writer tab)
    const handleCustomEvent = (e: CustomEvent) => {
      if (e.detail?.enabled !== undefined) {
        isExternalUpdate.current = true
        setAutoHumanize(e.detail.enabled)
      }
    }

    window.addEventListener('storage', handleStorageChange)
    window.addEventListener('autoHumanizeChange', handleCustomEvent as EventListener)
    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('autoHumanizeChange', handleCustomEvent as EventListener)
    }
  }, [])

  const processText = async () => {
    if (!inputText.trim()) {
      toast.error('Please enter some text')
      return
    }

    // Check if user can use humanizer
    if (!canUseHumanizer) {
      const plan = user?.plan || 'Free'
      if (plan === 'Free') {
        setShowUpgradeModal(true)
        return
      } else {
        // Pro user out of uses
        toast.error(`You've used all ${usageLimits?.humanizer_limit} humanizer uses this week. Resets Monday!`)
        setShowUpgradeModal(true)
        return
      }
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

      // Track usage
      await trackHumanizerUsage()

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

  const plan = user?.plan || 'Free'
  const requiredPlan = plan === 'Free' ? 'Pro' : 'Premium'

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
          <div className="flex-1">
            <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI Text Humanizer
            </h2>
            <p className="text-gray-400 mt-1">Transform AI content into natural, human-like writing</p>
          </div>
        </div>

        {/* Usage Meter */}
        {usageLimits && (
          <UsageMeter
            label="Humanizer Uses"
            used={usageLimits.humanizer_uses}
            limit={usageLimits.humanizer_limit === -1 ? 'Unlimited' : usageLimits.humanizer_limit}
            icon={<SparklesIcon className="w-4 h-4 text-purple-400" />}
            showUpgrade={!canUseHumanizer}
            onUpgradeClick={() => setShowUpgradeModal(true)}
          />
        )}

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
              disabled={!canUseHumanizer}
            />
            <div className={`w-14 h-7 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-purple-500 peer-checked:to-pink-500 ${!canUseHumanizer ? 'opacity-50 cursor-not-allowed' : ''}`}></div>
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

        {!canUseHumanizer && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-4 p-3 bg-red-500/10 rounded-lg border border-red-500/20"
          >
            <p className="text-xs text-red-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {plan === 'Free' ? (
                <>
                  <button
                    onClick={() => onNavigateToDashboard?.()}
                    className="underline hover:text-red-200"
                  >
                    Upgrade to Pro
                  </button>
                  {' '}to use the humanizer
                </>
              ) : (
                'Out of humanizer uses this week'
              )}
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

      {/* Upgrade Modal */}
      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        feature="AI Humanizer"
        currentPlan={plan}
        requiredPlan={requiredPlan}
        usageInfo={usageLimits ? {
          used: usageLimits.humanizer_uses,
          limit: typeof usageLimits.humanizer_limit === 'number' ? usageLimits.humanizer_limit : 0,
          type: 'humanizer uses'
        } : undefined}
      />
    </div>
  )
}
