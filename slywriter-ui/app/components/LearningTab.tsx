'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { 
  BookOpen, Brain, Target, TrendingUp, Award, Clock, 
  CheckCircle, Circle, Lock, Unlock, BarChart, Sparkles,
  ChevronRight, RefreshCw, PlayCircle
} from 'lucide-react'

const API_URL = 'http://localhost:8000'

interface LearningTopic {
  id: string
  name: string
  description: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  progress: number
  unlocked: boolean
  exercises: number
  completedExercises: number
}

const TOPICS: LearningTopic[] = [
  {
    id: 'basics',
    name: 'Typing Basics',
    description: 'Master the fundamentals of touch typing',
    difficulty: 'beginner',
    progress: 0,
    unlocked: true,
    exercises: 10,
    completedExercises: 0
  },
  {
    id: 'speed',
    name: 'Speed Building',
    description: 'Increase your typing speed systematically',
    difficulty: 'intermediate',
    progress: 0,
    unlocked: true,
    exercises: 15,
    completedExercises: 0
  },
  {
    id: 'accuracy',
    name: 'Accuracy Training',
    description: 'Improve precision and reduce errors',
    difficulty: 'intermediate',
    progress: 0,
    unlocked: true,
    exercises: 12,
    completedExercises: 0
  },
  {
    id: 'advanced',
    name: 'Advanced Techniques',
    description: 'Master complex typing patterns',
    difficulty: 'advanced',
    progress: 0,
    unlocked: false,
    exercises: 20,
    completedExercises: 0
  },
  {
    id: 'programming',
    name: 'Code Typing',
    description: 'Special characters and programming syntax',
    difficulty: 'advanced',
    progress: 0,
    unlocked: false,
    exercises: 18,
    completedExercises: 0
  }
]

export default function LearningTab() {
  const { user, isPremium } = useAuth()
  const [topics, setTopics] = useState<LearningTopic[]>(TOPICS)
  const [selectedTopic, setSelectedTopic] = useState<LearningTopic | null>(null)
  const [currentSession, setCurrentSession] = useState<any>(null)
  const [sessionActive, setSessionActive] = useState(false)
  const [currentExercise, setCurrentExercise] = useState<any>(null)
  const [userInput, setUserInput] = useState('')
  const [exerciseComplete, setExerciseComplete] = useState(false)
  const [stats, setStats] = useState({
    totalTime: 0,
    exercisesCompleted: 0,
    averageAccuracy: 0,
    streak: 0
  })

  useEffect(() => {
    loadProgress()
  }, [])

  const loadProgress = () => {
    const saved = localStorage.getItem('learningProgress')
    if (saved) {
      const progress = JSON.parse(saved)
      setTopics(prev => prev.map(topic => ({
        ...topic,
        progress: progress[topic.id]?.progress || 0,
        completedExercises: progress[topic.id]?.completed || 0,
        unlocked: topic.difficulty === 'beginner' || 
                  topic.difficulty === 'intermediate' || 
                  (isPremium && topic.difficulty === 'advanced')
      })))
      setStats(progress.stats || stats)
    }
  }

  const saveProgress = () => {
    const progress: any = {}
    topics.forEach(topic => {
      progress[topic.id] = {
        progress: topic.progress,
        completed: topic.completedExercises
      }
    })
    progress.stats = stats
    localStorage.setItem('learningProgress', JSON.stringify(progress))
  }

  const startLearningSession = async (topic: LearningTopic) => {
    if (!topic.unlocked) {
      toast.error('This topic is locked. Complete previous topics or upgrade to premium.')
      return
    }

    try {
      // Generate study content using AI
      const explanationResponse = await axios.post(`${API_URL}/api/ai/explain`, {
        topic: topic.name,
        learning_style: 'analytical',
        complexity: topic.difficulty
      })
      
      // Generate study questions
      const questionsResponse = await axios.post(`${API_URL}/api/ai/study-questions`, {
        topic: topic.name,
        num_questions: 5,
        difficulty: topic.difficulty
      })
      
      // Create session with AI-generated content
      const exercises = []
      
      // Add explanation as first exercise
      if (explanationResponse.data.success) {
        exercises.push({
          id: 'explain-1',
          type: 'Learn: Topic Overview',
          content: explanationResponse.data.text || 'Study this topic and understand its key concepts.'
        })
      }
      
      // Add practice typing exercises
      const practiceTexts = [
        'Practice typing this sentence to improve your muscle memory and accuracy.',
        'The quick brown fox jumps over the lazy dog - a classic typing practice phrase.',
        'Consistent practice is the key to developing fast and accurate typing skills.',
        'Focus on accuracy first, then gradually increase your typing speed over time.',
        'Proper hand positioning and posture are essential for efficient typing.'
      ]
      
      practiceTexts.slice(0, 3).forEach((text, index) => {
        exercises.push({
          id: `practice-${index + 1}`,
          type: 'Practice: Type this text',
          content: text
        })
      })
      
      // Add study questions if available
      if (questionsResponse.data.success && questionsResponse.data.text) {
        exercises.push({
          id: 'questions-1',
          type: 'Review: Study Questions',
          content: questionsResponse.data.text
        })
      }
      
      const sessionData = {
        id: Date.now().toString(),
        topic: topic.name,
        exercises,
        startTime: new Date().toISOString()
      }

      setCurrentSession(sessionData)
      setSelectedTopic(topic)
      setSessionActive(true)
      
      // Load first exercise
      if (exercises.length > 0) {
        setCurrentExercise(exercises[0])
      }
      
      // Show warning if using mock data
      if (explanationResponse.data.mock || questionsResponse.data.mock) {
        toast('Using simulated content. Add OpenAI API key for personalized learning.', {
          icon: '⚠️',
          duration: 4000
        })
      }
    } catch (error) {
      console.error('Failed to start learning session:', error)
      
      // Fallback to basic exercises
      const fallbackExercises = [
        {
          id: 'fallback-1',
          type: 'Practice: Basic Typing',
          content: 'Type this text to practice your typing skills. Focus on accuracy over speed.'
        },
        {
          id: 'fallback-2',
          type: 'Practice: Common Words',
          content: 'The quick brown fox jumps over the lazy dog. Practice typing common English words.'
        }
      ]
      
      setCurrentSession({
        id: Date.now().toString(),
        topic: topic.name,
        exercises: fallbackExercises,
        startTime: new Date().toISOString()
      })
      setSelectedTopic(topic)
      setSessionActive(true)
      setCurrentExercise(fallbackExercises[0])
      
      toast.error('Using offline mode. Some features may be limited.')
    }
  }

  const completeExercise = () => {
    if (!currentSession || !selectedTopic) return

    // Calculate accuracy
    const accuracy = calculateAccuracy(currentExercise.content, userInput)
    
    // Update topic progress
    const updatedTopics = topics.map(t => {
      if (t.id === selectedTopic.id) {
        const newCompleted = t.completedExercises + 1
        const newProgress = (newCompleted / t.exercises) * 100
        return { ...t, completedExercises: newCompleted, progress: newProgress }
      }
      return t
    })
    setTopics(updatedTopics)
    
    // Update stats
    setStats(prev => ({
      ...prev,
      exercisesCompleted: prev.exercisesCompleted + 1,
      averageAccuracy: (prev.averageAccuracy * prev.exercisesCompleted + accuracy) / (prev.exercisesCompleted + 1),
      streak: accuracy >= 90 ? prev.streak + 1 : 0
    }))
    
    setExerciseComplete(true)
    saveProgress()
    
    toast.success(`Exercise complete! Accuracy: ${accuracy.toFixed(1)}%`)
    
    // Load next exercise or complete session
    const currentIndex = currentSession.exercises.findIndex((e: any) => e.id === currentExercise.id)
    if (currentIndex < currentSession.exercises.length - 1) {
      setTimeout(() => {
        setCurrentExercise(currentSession.exercises[currentIndex + 1])
        setUserInput('')
        setExerciseComplete(false)
      }, 2000)
    } else {
      setTimeout(() => {
        completeSession()
      }, 2000)
    }
  }

  const completeSession = () => {
    setSessionActive(false)
    setCurrentSession(null)
    setSelectedTopic(null)
    setCurrentExercise(null)
    setUserInput('')
    toast.success('Learning session complete! Great job!')
  }

  const calculateAccuracy = (original: string, typed: string) => {
    if (!original || !typed) return 0
    let correct = 0
    for (let i = 0; i < Math.min(original.length, typed.length); i++) {
      if (original[i] === typed[i]) correct++
    }
    return (correct / original.length) * 100
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'text-green-400 bg-green-500/10'
      case 'intermediate': return 'text-yellow-400 bg-yellow-500/10'
      case 'advanced': return 'text-red-400 bg-red-500/10'
      default: return 'text-gray-400 bg-gray-900/500/10'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-900/20 to-blue-900/20 rounded-2xl p-6 backdrop-blur-sm border border-green-500/20">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <Brain className="w-8 h-8 text-green-400" />
              <h2 className="text-2xl font-bold bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent">
                Adaptive Learning System
              </h2>
            </div>
            <p className="text-gray-400">Personalized typing lessons with spaced repetition</p>
          </div>
          
          <div className="text-right">
            <div className="flex items-center gap-4">
              <div>
                <div className="text-xs text-gray-400">Streak</div>
                <div className="text-2xl font-bold text-yellow-400">{stats.streak} 🔥</div>
              </div>
              <div>
                <div className="text-xs text-gray-400">Completed</div>
                <div className="text-2xl font-bold text-green-400">{stats.exercisesCompleted}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400">Accuracy</div>
                <div className="text-2xl font-bold text-blue-400">{stats.averageAccuracy.toFixed(1)}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {!sessionActive ? (
        <>
          {/* Topics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {topics.map((topic) => (
              <motion.div
                key={topic.id}
                whileHover={{ scale: topic.unlocked ? 1.02 : 1 }}
                className={`bg-gray-900/50 rounded-xl p-5 backdrop-blur-sm border ${
                  topic.unlocked ? 'border-gray-700/50 cursor-pointer' : 'border-gray-800 opacity-50'
                } transition-all`}
                onClick={() => topic.unlocked && startLearningSession(topic)}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-gray-400" />
                    <h3 className="font-semibold">{topic.name}</h3>
                  </div>
                  {topic.unlocked ? (
                    <Unlock className="w-4 h-4 text-green-400" />
                  ) : (
                    <Lock className="w-4 h-4 text-gray-400" />
                  )}
                </div>
                
                <p className="text-sm text-gray-400 mb-3">{topic.description}</p>
                
                <div className="flex items-center gap-2 mb-3">
                  <span className={`text-xs px-2 py-1 rounded-full ${getDifficultyColor(topic.difficulty)}`}>
                    {topic.difficulty}
                  </span>
                  <span className="text-xs text-gray-400">
                    {topic.completedExercises}/{topic.exercises} exercises
                  </span>
                </div>
                
                {/* Progress Bar */}
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${topic.progress}%` }}
                    className="h-full bg-gradient-to-r from-green-500 to-blue-500 rounded-full"
                  />
                </div>
                
                {topic.progress === 100 && (
                  <div className="mt-2 text-xs text-green-400 flex items-center gap-1">
                    <CheckCircle className="w-4 h-4" />
                    Completed
                  </div>
                )}
              </motion.div>
            ))}
          </div>

          {/* Learning Path */}
          <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-400" />
              Your Learning Path
            </h3>
            
            <div className="relative">
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-700" />
              
              {topics.map((topic, index) => (
                <div key={topic.id} className="relative flex items-center gap-4 mb-6 last:mb-0">
                  <div className={`w-8 h-8 rounded-full border-2 ${
                    topic.progress === 100 
                      ? 'bg-green-500 border-green-500' 
                      : topic.progress > 0 
                        ? 'bg-blue-500 border-blue-500'
                        : 'bg-gray-700 border-gray-600'
                  } flex items-center justify-center z-10`}>
                    {topic.progress === 100 ? (
                      <CheckCircle className="w-4 h-4 text-white" />
                    ) : topic.progress > 0 ? (
                      <Circle className="w-4 h-4 text-white" />
                    ) : (
                      <Circle className="w-4 h-4 text-gray-400" />
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <span className={`font-medium ${
                        topic.unlocked ? 'text-white' : 'text-gray-400'
                      }`}>
                        {topic.name}
                      </span>
                      <span className="text-sm text-gray-400">{topic.progress.toFixed(0)}%</span>
                    </div>
                    {topic.progress > 0 && topic.progress < 100 && (
                      <p className="text-xs text-gray-400 mt-1">In progress</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        /* Active Learning Session */
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50"
        >
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-xl font-semibold">{selectedTopic?.name}</h3>
              <p className="text-sm text-gray-400 mt-1">
                Exercise {currentSession?.exercises.findIndex((e: any) => e.id === currentExercise?.id) + 1} of {currentSession?.exercises.length}
              </p>
            </div>
            
            <button
              onClick={completeSession}
              className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
            >
              End Session
            </button>
          </div>
          
          {currentExercise && (
            <>
              <div className="mb-4 p-4 bg-gray-800/50 rounded-lg">
                <h4 className="text-sm font-semibold mb-2 text-gray-400">{currentExercise.type}</h4>
                <p className="text-lg">{currentExercise.content}</p>
              </div>
              
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="Type the text above..."
                disabled={exerciseComplete}
                className="w-full h-32 bg-gray-800/50 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all"
              />
              
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={completeExercise}
                disabled={!userInput || exerciseComplete}
                className="mt-4 w-full py-3 bg-gradient-to-r from-green-600 to-blue-600 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {exerciseComplete ? 'Loading next...' : 'Complete Exercise'}
              </motion.button>
            </>
          )}
        </motion.div>
      )}
    </div>
  )
}