'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, Brain, TrendingUp, Clock, Star, ChevronRight, Sparkles, Target, Zap, Check } from 'lucide-react'
import { RENDER_API_URL } from '../config/api'
import toast from 'react-hot-toast'
import axios from 'axios'

const API_URL = RENDER_API_URL

interface LearningTopic {
  id: string
  question: string
  answer: string
  timestamp: string
  reviewed: boolean
  mastery: number // 0-100
  category?: string
}

interface PotentialTopic {
  id: string
  text: string
  frequency: number
  lastSeen: string
  suggested: boolean
}

export default function LearningHub() {
  const [topics, setTopics] = useState<LearningTopic[]>([])
  const [potentialTopics, setPotentialTopics] = useState<PotentialTopic[]>([])
  const [selectedTopic, setSelectedTopic] = useState<LearningTopic | null>(null)
  const [filter, setFilter] = useState<'all' | 'unreviewed' | 'mastered'>('all')
  const [isGeneratingLesson, setIsGeneratingLesson] = useState(false)

  useEffect(() => {
    loadTopics()
    loadPotentialTopics()
  }, [])

  const loadTopics = () => {
    const saved = localStorage.getItem('slywriter-learning-topics')
    if (saved) {
      setTopics(JSON.parse(saved))
    }
  }

  const loadPotentialTopics = () => {
    const saved = localStorage.getItem('slywriter-potential-topics')
    if (saved) {
      setPotentialTopics(JSON.parse(saved))
    }
  }

  const saveTopics = (newTopics: LearningTopic[]) => {
    setTopics(newTopics)
    localStorage.setItem('slywriter-learning-topics', JSON.stringify(newTopics))
  }

  const addTopic = (question: string, answer: string, category?: string) => {
    const newTopic: LearningTopic = {
      id: Date.now().toString(),
      question,
      answer,
      timestamp: new Date().toISOString(),
      reviewed: false,
      mastery: 0,
      category
    }
    
    const updatedTopics = [newTopic, ...topics]
    saveTopics(updatedTopics)
    
    // Also track as potential topic
    trackPotentialTopic(question)
    
    toast.success('📚 Added to learning topics!')
  }

  const trackPotentialTopic = (text: string) => {
    const existing = potentialTopics.find(t => t.text.toLowerCase() === text.toLowerCase())
    
    if (existing) {
      // Increase frequency
      const updated = potentialTopics.map(t => 
        t.id === existing.id 
          ? { ...t, frequency: t.frequency + 1, lastSeen: new Date().toISOString() }
          : t
      )
      setPotentialTopics(updated)
      localStorage.setItem('slywriter-potential-topics', JSON.stringify(updated))
    } else {
      // Add new potential topic
      const newPotential: PotentialTopic = {
        id: Date.now().toString(),
        text: text.substring(0, 100),
        frequency: 1,
        lastSeen: new Date().toISOString(),
        suggested: false
      }
      const updated = [newPotential, ...potentialTopics].slice(0, 20) // Keep only 20 most recent
      setPotentialTopics(updated)
      localStorage.setItem('slywriter-potential-topics', JSON.stringify(updated))
    }
  }

  const markAsReviewed = (id: string) => {
    const updated = topics.map(t => 
      t.id === id ? { ...t, reviewed: true, mastery: Math.min(100, t.mastery + 20) } : t
    )
    saveTopics(updated)
    toast.success('✅ Marked as reviewed!')
  }

  const generateDeepLesson = async (topic: PotentialTopic) => {
    setIsGeneratingLesson(true)
    
    try {
      const response = await axios.post(`${API_URL}/api/ai/generate`, {
        prompt: `Create a comprehensive learning lesson about: "${topic.text}"
        
        Include:
        1. Core concepts and definitions
        2. Key points to remember
        3. Real-world applications
        4. Common misconceptions
        5. Practice questions
        
        Format as a clear, educational lesson.`,
        max_tokens: 500
      })
      
      if (response.data.success) {
        addTopic(topic.text, response.data.text, 'AI Generated Lesson')
        
        // Mark as suggested
        const updated = potentialTopics.map(t => 
          t.id === topic.id ? { ...t, suggested: true } : t
        )
        setPotentialTopics(updated)
        localStorage.setItem('slywriter-potential-topics', JSON.stringify(updated))
        
        toast.success('🎓 Deep lesson created!')
      }
    } catch (error) {
      toast.error('Failed to generate lesson')
    } finally {
      setIsGeneratingLesson(false)
    }
  }

  const filteredTopics = topics.filter(topic => {
    if (filter === 'unreviewed') return !topic.reviewed
    if (filter === 'mastered') return topic.mastery >= 80
    return true
  })

  const suggestedTopics = potentialTopics
    .filter(t => !t.suggested && t.frequency > 1)
    .sort((a, b) => b.frequency - a.frequency)
    .slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-900/20 to-blue-900/20 rounded-2xl p-6 backdrop-blur-sm border border-green-500/20">
        <div className="flex items-center gap-3 mb-3">
          <BookOpen className="w-8 h-8 text-green-400" />
          <h2 className="text-2xl font-bold bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent">
            Smart Learning Hub
          </h2>
        </div>
        <p className="text-gray-400">AI-powered learning from your questions. Every query becomes a lesson!</p>
        
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mt-6">
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-white">{topics.length}</div>
            <div className="text-xs text-gray-400">Total Topics</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-green-400">
              {topics.filter(t => t.reviewed).length}
            </div>
            <div className="text-xs text-gray-400">Reviewed</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-purple-400">
              {Math.round(topics.reduce((acc, t) => acc + t.mastery, 0) / (topics.length || 1))}%
            </div>
            <div className="text-xs text-gray-400">Avg Mastery</div>
          </div>
        </div>
      </div>

      {/* Suggested Topics - The Magic! */}
      {suggestedTopics.length > 0 && (
        <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 rounded-xl p-6 border border-purple-500/20">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <h3 className="text-lg font-semibold text-white">🎯 Topics You're Using AI For</h3>
            <span className="text-xs bg-purple-500/20 px-2 py-1 rounded-full text-purple-300">
              Auto-detected
            </span>
          </div>
          
          <p className="text-sm text-gray-400 mb-4">
            We noticed you're asking about these topics frequently. Want to master them?
          </p>
          
          <div className="space-y-2">
            {suggestedTopics.map(topic => (
              <motion.div
                key={topic.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg hover:bg-gray-700/50 transition-all group"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">{topic.text}</span>
                    <span className="text-xs bg-purple-500/20 px-2 py-0.5 rounded text-purple-300">
                      Used {topic.frequency}x
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Last used: {new Date(topic.lastSeen).toLocaleDateString()}
                  </div>
                </div>
                
                <button
                  onClick={() => generateDeepLesson(topic)}
                  disabled={isGeneratingLesson}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg text-sm font-medium opacity-0 group-hover:opacity-100 transition-all flex items-center gap-2 hover:scale-105"
                >
                  <Zap className="w-4 h-4" />
                  Create Lesson
                </button>
              </motion.div>
            ))}
          </div>
          
          <div className="mt-4 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
            <p className="text-xs text-yellow-300">
              💡 <strong>Pro tip:</strong> Creating lessons from frequently used topics helps you understand 
              the material instead of just using AI. Perfect for exams!
            </p>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {(['all', 'unreviewed', 'mastered'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg capitalize transition-all ${
              filter === f 
                ? 'bg-green-500/20 text-green-300 border border-green-500'
                : 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:bg-gray-700/50'
            }`}
          >
            {f === 'all' && `All (${topics.length})`}
            {f === 'unreviewed' && `Unreviewed (${topics.filter(t => !t.reviewed).length})`}
            {f === 'mastered' && `Mastered (${topics.filter(t => t.mastery >= 80).length})`}
          </button>
        ))}
      </div>

      {/* Topics List */}
      <div className="space-y-3">
        <AnimatePresence>
          {filteredTopics.map((topic, index) => (
            <motion.div
              key={topic.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: index * 0.05 }}
              className="bg-gray-900/50 rounded-xl p-4 border border-gray-700/50 hover:border-green-500/30 transition-all cursor-pointer"
              onClick={() => setSelectedTopic(topic)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {topic.reviewed && <Check className="w-4 h-4 text-green-400" />}
                    <h4 className="font-medium text-white">{topic.question}</h4>
                    {topic.category && (
                      <span className="text-xs bg-blue-500/20 px-2 py-0.5 rounded text-blue-300">
                        {topic.category}
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-400 line-clamp-2">{topic.answer}</p>
                  
                  <div className="flex items-center gap-4 mt-3">
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      {new Date(topic.timestamp).toLocaleDateString()}
                    </div>
                    
                    {/* Mastery Bar */}
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">Mastery:</span>
                      <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-green-500 to-blue-500 transition-all"
                          style={{ width: `${topic.mastery}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">{topic.mastery}%</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  {!topic.reviewed && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        markAsReviewed(topic.id)
                      }}
                      className="p-2 bg-green-500/20 hover:bg-green-500/30 rounded-lg transition-colors"
                    >
                      <Target className="w-4 h-4 text-green-400" />
                    </button>
                  )}
                  <ChevronRight className="w-5 h-5 text-gray-600" />
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {filteredTopics.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No topics yet. Start using AI and they'll appear here!</p>
          </div>
        )}
      </div>

      {/* Topic Detail Modal */}
      <AnimatePresence>
        {selectedTopic && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedTopic(null)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              className="bg-gray-900 rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-xl font-bold text-white mb-4">{selectedTopic.question}</h3>
              <div className="prose prose-invert max-w-none">
                <p className="whitespace-pre-wrap">{selectedTopic.answer}</p>
              </div>
              
              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => setSelectedTopic(null)}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                  Close
                </button>
                {!selectedTopic.reviewed && (
                  <button
                    onClick={() => {
                      markAsReviewed(selectedTopic.id)
                      setSelectedTopic(null)
                    }}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                  >
                    Mark as Reviewed
                  </button>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Export function for external components to add topics
export function addLearningTopic(question: string, answer: string) {
  const saved = localStorage.getItem('slywriter-learning-topics')
  const topics = saved ? JSON.parse(saved) : []
  
  const newTopic: LearningTopic = {
    id: Date.now().toString(),
    question,
    answer,
    timestamp: new Date().toISOString(),
    reviewed: false,
    mastery: 0
  }
  
  const updated = [newTopic, ...topics]
  localStorage.setItem('slywriter-learning-topics', JSON.stringify(updated))
  
  // Track potential topic
  const potentialSaved = localStorage.getItem('slywriter-potential-topics')
  const potentialTopics = potentialSaved ? JSON.parse(potentialSaved) : []
  
  const existing = potentialTopics.find((t: PotentialTopic) => 
    t.text.toLowerCase() === question.toLowerCase()
  )
  
  if (existing) {
    const updated = potentialTopics.map((t: PotentialTopic) => 
      t.id === existing.id 
        ? { ...t, frequency: t.frequency + 1, lastSeen: new Date().toISOString() }
        : t
    )
    localStorage.setItem('slywriter-potential-topics', JSON.stringify(updated))
  } else {
    const newPotential: PotentialTopic = {
      id: Date.now().toString(),
      text: question.substring(0, 100),
      frequency: 1,
      lastSeen: new Date().toISOString(),
      suggested: false
    }
    const updated = [newPotential, ...potentialTopics].slice(0, 20)
    localStorage.setItem('slywriter-potential-topics', JSON.stringify(updated))
  }
}