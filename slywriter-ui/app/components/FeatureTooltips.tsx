'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { InfoIcon, XIcon } from 'lucide-react'

interface TooltipProps {
  title: string
  content: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}

export function FeatureTooltip({ title, content, position = 'top' }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  
  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2'
  }
  
  return (
    <div className="relative inline-block">
      <button
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="text-gray-400 hover:text-purple-400 transition-colors"
      >
        <InfoIcon className="w-3.5 h-3.5" />
      </button>
      
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.15 }}
            className={`absolute z-50 ${positionClasses[position]} pointer-events-none`}
          >
            <div className="bg-gray-800 rounded-lg shadow-xl border border-purple-500/30 p-3 w-64">
              <h4 className="text-sm font-semibold text-white mb-1">{title}</h4>
              <p className="text-xs text-gray-300 leading-relaxed">{content}</p>
              
              {/* Arrow */}
              <div className={`absolute w-2 h-2 bg-gray-800 border border-purple-500/30 transform rotate-45 ${
                position === 'top' ? 'bottom-[-5px] left-1/2 -translate-x-1/2 border-t-0 border-l-0' :
                position === 'bottom' ? 'top-[-5px] left-1/2 -translate-x-1/2 border-b-0 border-r-0' :
                position === 'left' ? 'right-[-5px] top-1/2 -translate-y-1/2 border-l-0 border-b-0' :
                'left-[-5px] top-1/2 -translate-y-1/2 border-r-0 border-t-0'
              }`} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export function FirstTimeHelper({ feature }: { feature: string }) {
  const [isDismissed, setIsDismissed] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(`slywriter-helper-${feature}`) === 'dismissed'
    }
    return false
  })
  
  if (isDismissed) return null
  
  const helpers = {
    typing: {
      title: "SlyWriter Types FOR You",
      content: "Paste any text here and watch SlyWriter type it automatically with human-like patterns. No more manual typing!",
      tips: [
        "Choose a typing profile to match your speed",
        "AI Filler adds realistic thinking pauses",
        "Typos are ON by default to avoid detection"
      ]
    },
    humanizer: {
      title: "Make AI Undetectable",
      content: "Transform AI-generated text to bypass detection systems while maintaining quality.",
      tips: [
        "Highlight any text and press Ctrl+Alt+G",
        "AI generates, humanizes, then auto-types",
        "Perfect for assignments and content"
      ]
    },
    'ai-hub': {
      title: "AI Content Generator",
      content: "Generate essays, articles, and any content instantly with AI.",
      tips: [
        "Select content type and length",
        "One-click to humanize output",
        "Seamlessly flows to auto-typing"
      ]
    }
  }
  
  const helper = helpers[feature as keyof typeof helpers]
  if (!helper) return null
  
  const dismiss = () => {
    localStorage.setItem(`slywriter-helper-${feature}`, 'dismissed')
    setIsDismissed(true)
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-6 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg border border-purple-500/30 p-4"
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          {helper.title}
        </h3>
        <button
          onClick={dismiss}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <XIcon className="w-4 h-4" />
        </button>
      </div>
      
      <p className="text-sm text-gray-300 mb-3">{helper.content}</p>
      
      <div className="space-y-1">
        {helper.tips.map((tip, i) => (
          <div key={i} className="flex items-start gap-2 text-xs">
            <span className="text-purple-400 mt-0.5">•</span>
            <span className="text-gray-400">{tip}</span>
          </div>
        ))}
      </div>
      
      <button
        onClick={dismiss}
        className="mt-3 text-xs text-purple-400 hover:text-purple-300 transition-colors"
      >
        Got it, don't show again
      </button>
    </motion.div>
  )
}

export function QuickTip({ text }: { text: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="inline-flex items-center gap-2 px-3 py-1.5 bg-purple-500/10 rounded-full border border-purple-500/30"
    >
      <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-pulse" />
      <span className="text-xs text-purple-300">{text}</span>
    </motion.div>
  )
}