'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Check, Edit3, Copy, BookOpen, Sparkles, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

interface ReviewPopupProps {
  isOpen: boolean
  onClose: () => void
  text: string
  question: string
  onConfirm: (text: string) => void
  onSaveToLearning?: (question: string, answer: string) => void
}

export default function ReviewPopup({ isOpen, onClose, text, question, onConfirm, onSaveToLearning }: ReviewPopupProps) {
  const [editedText, setEditedText] = useState(text)
  const [isEditing, setIsEditing] = useState(false)
  const [autoLearn, setAutoLearn] = useState(true)

  useEffect(() => {
    setEditedText(text)
    setIsEditing(false)
    
    // Load auto-learn preference
    const saved = localStorage.getItem('slywriter-auto-learn')
    setAutoLearn(saved !== 'false')
  }, [text])

  const handleConfirm = () => {
    // Save to learning if enabled
    if (autoLearn && onSaveToLearning) {
      onSaveToLearning(question, editedText)
    }
    
    onConfirm(editedText)
    onClose()
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(editedText)
    toast.success('Copied to clipboard!')
  }

  const toggleAutoLearn = () => {
    const newValue = !autoLearn
    setAutoLearn(newValue)
    localStorage.setItem('slywriter-auto-learn', String(newValue))
    toast.success(newValue ? 'Auto-learn enabled!' : 'Auto-learn disabled')
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden shadow-2xl border border-purple-500/20"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 p-6 border-b border-gray-700/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Sparkles className="w-6 h-6 text-purple-400" />
                <h2 className="text-xl font-bold text-white">Review AI Answer</h2>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* Question Display */}
            {question && (
              <div className="mt-4 p-3 bg-gray-800/50 rounded-lg">
                <p className="text-sm text-gray-400">Question:</p>
                <p className="text-white font-medium">{question}</p>
              </div>
            )}
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            {/* Text Area */}
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-300">AI Generated Answer:</label>
                <div className="flex gap-2">
                  {!isEditing ? (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm flex items-center gap-2 transition-colors"
                    >
                      <Edit3 className="w-3 h-3" />
                      Edit
                    </button>
                  ) : (
                    <button
                      onClick={() => setIsEditing(false)}
                      className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded-lg text-sm flex items-center gap-2 transition-colors"
                    >
                      <Check className="w-3 h-3" />
                      Done
                    </button>
                  )}
                  <button
                    onClick={handleCopy}
                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm flex items-center gap-2 transition-colors"
                  >
                    <Copy className="w-3 h-3" />
                    Copy
                  </button>
                </div>
              </div>
              
              <textarea
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                readOnly={!isEditing}
                className={`w-full h-64 p-4 rounded-lg border transition-all ${
                  isEditing 
                    ? 'bg-gray-800 border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50' 
                    : 'bg-gray-900/50 border-gray-700 cursor-default'
                } text-white resize-none`}
              />
              
              {/* Character count */}
              <div className="mt-2 text-xs text-gray-500 text-right">
                {editedText.length} characters | {editedText.split(/\s+/).filter(w => w).length} words
              </div>
            </div>

            {/* Learning Integration */}
            <div className="bg-gradient-to-r from-green-900/20 to-blue-900/20 rounded-xl p-4 border border-green-500/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <BookOpen className="w-5 h-5 text-green-400" />
                  <div>
                    <p className="text-sm font-medium text-white">Smart Learning</p>
                    <p className="text-xs text-gray-400">Auto-save Q&A for future study</p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoLearn}
                    onChange={toggleAutoLearn}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                </label>
              </div>
              
              {autoLearn && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-3 text-xs text-gray-400"
                >
                  📚 This Q&A will be saved to your learning topics for review later
                </motion.div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-gray-700/50 flex justify-between items-center">
            <div className="text-xs text-gray-500">
              Tip: Enable auto-learn to build your knowledge base!
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-lg font-medium flex items-center gap-2 transition-all transform hover:scale-105"
              >
                <Check className="w-4 h-4" />
                Use This Answer
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}