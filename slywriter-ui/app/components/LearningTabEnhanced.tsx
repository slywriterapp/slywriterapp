'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RENDER_API_URL } from '../config/api'
import axios from 'axios'
import toast from 'react-hot-toast'
import { 
  BrainIcon, BookOpenIcon, GraduationCapIcon, SparklesIcon,
  TrendingUpIcon, ClipboardIcon, PlayIcon, ChevronRightIcon,
  StarIcon, AwardIcon, RefreshCwIcon, Lightbulb, GamepadIcon,
  HeadphonesIcon, EyeIcon, PenToolIcon, HandIcon, 
  MessageSquareIcon, QuoteIcon, MapIcon, ZapIcon,
  RocketIcon, TargetIcon, CheckCircleIcon, XCircleIcon, ClockIcon
} from 'lucide-react'

const API_URL = ${RENDER_API_URL}'

// Learning style quiz questions
const QUIZ_QUESTIONS = [
  {
    id: 1,
    question: "When learning something new, I prefer to:",
    options: [
      { text: "Watch videos or diagrams", style: "visual", icon: EyeIcon },
      { text: "Listen to explanations or podcasts", style: "auditory", icon: HeadphonesIcon },
      { text: "Try it myself hands-on", style: "kinesthetic", icon: HandIcon },
      { text: "Read detailed instructions", style: "reading", icon: BookOpenIcon }
    ]
  },
  {
    id: 2,
    question: "I remember things best when I:",
    options: [
      { text: "See pictures or visualizations", style: "visual", icon: EyeIcon },
      { text: "Hear them explained out loud", style: "auditory", icon: HeadphonesIcon },
      { text: "Practice or experience them", style: "kinesthetic", icon: HandIcon },
      { text: "Write notes or read about them", style: "reading", icon: BookOpenIcon }
    ]
  },
  {
    id: 3,
    question: "In my free time, I enjoy:",
    options: [
      { text: "Watching movies or looking at art", style: "visual", icon: EyeIcon },
      { text: "Listening to music or audiobooks", style: "auditory", icon: HeadphonesIcon },
      { text: "Playing sports or building things", style: "kinesthetic", icon: HandIcon },
      { text: "Reading books or articles", style: "reading", icon: BookOpenIcon }
    ]
  },
  {
    id: 4,
    question: "When giving directions, I would:",
    options: [
      { text: "Draw a map or use landmarks", style: "visual", icon: MapIcon },
      { text: "Explain verbally step by step", style: "auditory", icon: MessageSquareIcon },
      { text: "Walk them through it physically", style: "kinesthetic", icon: HandIcon },
      { text: "Write down detailed instructions", style: "reading", icon: PenToolIcon }
    ]
  }
]

// Teaching methods for content
const TEACHING_METHODS = {
  storytelling: {
    name: "Storytelling",
    icon: BookOpenIcon,
    description: "Learn through narratives and examples",
    prompt: "Explain this concept through an engaging story with characters and a plot that illustrates the key ideas."
  },
  gamification: {
    name: "Gamification",
    icon: GamepadIcon,
    description: "Learn through challenges and rewards",
    prompt: "Turn this into a game-like learning experience with levels, challenges, and rewards. Include points to earn."
  },
  analogy: {
    name: "Analogies",
    icon: Lightbulb,
    description: "Learn through comparisons to familiar things",
    prompt: "Explain this using creative analogies and metaphors that relate to everyday experiences."
  },
  socratic: {
    name: "Socratic Method",
    icon: MessageSquareIcon,
    description: "Learn through guided questions",
    prompt: "Teach this through a series of thought-provoking questions that lead to understanding."
  },
  visual: {
    name: "Visual Learning",
    icon: EyeIcon,
    description: "Learn through descriptions of diagrams and charts",
    prompt: "Describe detailed visual representations, diagrams, and mind maps that would illustrate this concept."
  },
  practical: {
    name: "Practical Examples",
    icon: HandIcon,
    description: "Learn through real-world applications",
    prompt: "Provide concrete, real-world examples and practical applications of this concept."
  }
}

interface Lesson {
  id: string
  topic: string
  content: string
  method: string
  createdAt: Date
  reviewCount: number
  lastReviewed?: Date
  nextReview?: Date
  confidence: number
  notes: string[]
  quiz?: QuizQuestion[]
}

interface QuizQuestion {
  question: string
  options: string[]
  correct: number
  explanation: string
}

export default function LearningTabEnhanced() {
  // Core state
  const [learningStyle, setLearningStyle] = useState<string | null>(null)
  const [showQuiz, setShowQuiz] = useState(!learningStyle)
  const [quizStep, setQuizStep] = useState(0)
  const [quizAnswers, setQuizAnswers] = useState<string[]>([])
  
  // Lesson state
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [currentLesson, setCurrentLesson] = useState<Lesson | null>(null)
  const [selectedMethod, setSelectedMethod] = useState('storytelling')
  const [isGenerating, setIsGenerating] = useState(false)
  const [inputTopic, setInputTopic] = useState('')
  
  // Learning progress
  const [streak, setStreak] = useState(0)
  const [totalLessons, setTotalLessons] = useState(0)
  const [totalReviews, setTotalReviews] = useState(0)
  const [achievements, setAchievements] = useState<string[]>([])
  
  // Clipboard monitoring
  const [clipboardContent, setClipboardContent] = useState('')
  const [isMonitoring, setIsMonitoring] = useState(false)
  
  // Quiz state
  const [lessonQuiz, setLessonQuiz] = useState<QuizQuestion[]>([])
  const [quizIndex, setQuizIndex] = useState(0)
  const [quizScore, setQuizScore] = useState(0)
  const [showQuizResults, setShowQuizResults] = useState(false)
  
  // Load saved data
  useEffect(() => {
    loadLearningData()
    if (isMonitoring) {
      const interval = setInterval(checkClipboard, 1000)
      return () => clearInterval(interval)
    }
  }, [isMonitoring])
  
  const loadLearningData = () => {
    const saved = localStorage.getItem('slywriter-learning')
    if (saved) {
      const data = JSON.parse(saved)
      setLearningStyle(data.style)
      setLessons(data.lessons || [])
      setStreak(data.streak || 0)
      setTotalLessons(data.totalLessons || 0)
      setTotalReviews(data.totalReviews || 0)
      setAchievements(data.achievements || [])
    }
  }
  
  const saveLearningData = () => {
    const data = {
      style: learningStyle,
      lessons,
      streak,
      totalLessons,
      totalReviews,
      achievements
    }
    localStorage.setItem('slywriter-learning', JSON.stringify(data))
  }
  
  const checkClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText()
      if (text && text !== clipboardContent && text.length > 50) {
        setClipboardContent(text)
        // Auto-detect topic from clipboard
        const topic = text.substring(0, 50) + '...'
        toast.success(`Detected new content: ${topic}`)
        
        // Offer to create lesson
        if (confirm('Create a lesson from this highlighted content?')) {
          generateLesson(text)
        }
      }
    } catch (err) {
      // Silent fail - clipboard access denied
    }
  }
  
  const handleQuizAnswer = (styleAnswer: string) => {
    const newAnswers = [...quizAnswers, styleAnswer]
    setQuizAnswers(newAnswers)
    
    if (quizStep < QUIZ_QUESTIONS.length - 1) {
      setQuizStep(quizStep + 1)
    } else {
      // Calculate predominant learning style
      const styleCounts: Record<string, number> = {}
      newAnswers.forEach(style => {
        styleCounts[style] = (styleCounts[style] || 0) + 1
      })
      
      const dominantStyle = Object.entries(styleCounts)
        .sort(([,a], [,b]) => b - a)[0][0]
      
      setLearningStyle(dominantStyle)
      setShowQuiz(false)
      saveLearningData()
      
      toast.success(`Learning style identified: ${dominantStyle.charAt(0).toUpperCase() + dominantStyle.slice(1)}!`)
    }
  }
  
  const generateLesson = async (topic: string) => {
    setIsGenerating(true)
    
    try {
      // Get the teaching method prompt
      const method = TEACHING_METHODS[selectedMethod as keyof typeof TEACHING_METHODS]
      
      // Generate lesson content using AI
      const prompt = `
        Create a comprehensive lesson about: ${topic}
        
        Teaching Method: ${method.prompt}
        Learning Style: ${learningStyle || 'general'}
        
        Structure the lesson with:
        1. Overview (what will be learned)
        2. Core Concepts (main ideas explained using the teaching method)
        3. Examples (practical illustrations)
        4. Key Takeaways (summary points)
        5. Practice Questions (3 multiple choice questions with explanations)
        
        Make it engaging, memorable, and appropriate for the ${learningStyle} learning style.
      `
      
      // Simulate AI generation (replace with actual API call)
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const newLesson: Lesson = {
        id: Date.now().toString(),
        topic: topic.substring(0, 100),
        content: `# Learning: ${topic}\n\n## Overview\n\nThis lesson will teach you about ${topic} using ${method.name.toLowerCase()}.\n\n## Core Concepts\n\n[AI-generated content would go here]\n\n## Examples\n\n[Practical examples]\n\n## Key Takeaways\n\n- Important point 1\n- Important point 2\n- Important point 3`,
        method: selectedMethod,
        createdAt: new Date(),
        reviewCount: 0,
        confidence: 0,
        notes: [],
        quiz: [
          {
            question: "Sample question about the topic?",
            options: ["Option A", "Option B", "Option C", "Option D"],
            correct: 0,
            explanation: "Option A is correct because..."
          }
        ]
      }
      
      setLessons([newLesson, ...lessons])
      setCurrentLesson(newLesson)
      setTotalLessons(totalLessons + 1)
      saveLearningData()
      
      toast.success('Lesson created successfully!')
      
      // Check for achievements
      checkAchievements()
    } catch (error) {
      toast.error('Failed to generate lesson')
    } finally {
      setIsGenerating(false)
    }
  }
  
  const startLessonQuiz = () => {
    if (!currentLesson?.quiz) return
    
    setLessonQuiz(currentLesson.quiz)
    setQuizIndex(0)
    setQuizScore(0)
    setShowQuizResults(false)
  }
  
  const handleLessonQuizAnswer = (answerIndex: number) => {
    const question = lessonQuiz[quizIndex]
    
    if (answerIndex === question.correct) {
      setQuizScore(quizScore + 1)
      toast.success('Correct!')
    } else {
      toast.error(`Incorrect. ${question.explanation}`)
    }
    
    if (quizIndex < lessonQuiz.length - 1) {
      setQuizIndex(quizIndex + 1)
    } else {
      setShowQuizResults(true)
      updateLessonConfidence()
    }
  }
  
  const updateLessonConfidence = () => {
    if (!currentLesson) return
    
    const confidence = (quizScore / lessonQuiz.length) * 100
    const updatedLesson = {
      ...currentLesson,
      confidence,
      reviewCount: currentLesson.reviewCount + 1,
      lastReviewed: new Date(),
      nextReview: calculateNextReview(confidence)
    }
    
    const updatedLessons = lessons.map(l => 
      l.id === currentLesson.id ? updatedLesson : l
    )
    
    setLessons(updatedLessons)
    setCurrentLesson(updatedLesson)
    setTotalReviews(totalReviews + 1)
    saveLearningData()
  }
  
  const calculateNextReview = (confidence: number): Date => {
    // Spaced repetition algorithm
    const days = confidence > 80 ? 7 : confidence > 60 ? 3 : 1
    const next = new Date()
    next.setDate(next.getDate() + days)
    return next
  }
  
  const checkAchievements = () => {
    const newAchievements = []
    
    if (totalLessons === 1 && !achievements.includes('first-lesson')) {
      newAchievements.push('first-lesson')
      toast.success('🏆 Achievement: First Lesson Created!')
    }
    
    if (totalLessons === 10 && !achievements.includes('knowledge-seeker')) {
      newAchievements.push('knowledge-seeker')
      toast.success('🏆 Achievement: Knowledge Seeker - 10 Lessons!')
    }
    
    if (totalReviews === 20 && !achievements.includes('dedicated-learner')) {
      newAchievements.push('dedicated-learner')
      toast.success('🏆 Achievement: Dedicated Learner - 20 Reviews!')
    }
    
    if (newAchievements.length > 0) {
      setAchievements([...achievements, ...newAchievements])
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-900/20 to-blue-900/20 rounded-2xl p-6 backdrop-blur-sm border border-green-500/20">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <BrainIcon className="w-8 h-8 text-green-400" />
              <h2 className="text-2xl font-bold bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent">
                AI-Powered Content Learning
              </h2>
              <span className="text-xs bg-green-500/20 px-2 py-1 rounded-full text-green-300">
                Learn ANYTHING
              </span>
            </div>
            <p className="text-gray-400">Transform any content into personalized lessons with AI</p>
          </div>
          
          <div className="text-right">
            <div className="flex items-center gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">{streak}</div>
                <div className="text-xs text-gray-400">Day Streak</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">{totalLessons}</div>
                <div className="text-xs text-gray-400">Lessons</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">{totalReviews}</div>
                <div className="text-xs text-gray-400">Reviews</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Learning Style Quiz */}
      <AnimatePresence>
        {showQuiz && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-xl p-6 backdrop-blur-sm border border-purple-500/20"
          >
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <SparklesIcon className="w-6 h-6 text-purple-400" />
              Personalize Your Learning Experience
            </h3>
            
            <div className="mb-4">
              <div className="flex justify-between mb-2">
                <span className="text-sm text-gray-400">Question {quizStep + 1} of {QUIZ_QUESTIONS.length}</span>
                <span className="text-sm text-gray-400">{Math.round(((quizStep) / QUIZ_QUESTIONS.length) * 100)}% Complete</span>
              </div>
              <div className="w-full bg-gray-700 bg-gray-800 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all"
                  style={{ width: `${((quizStep) / QUIZ_QUESTIONS.length) * 100}%` }}
                />
              </div>
            </div>
            
            <h4 className="text-lg text-white mb-4">{QUIZ_QUESTIONS[quizStep].question}</h4>
            
            <div className="grid grid-cols-2 gap-3">
              {QUIZ_QUESTIONS[quizStep].options.map((option) => {
                const Icon = option.icon
                return (
                  <motion.button
                    key={option.style}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleQuizAnswer(option.style)}
                    className="p-4 bg-gray-800 hover:bg-purple-500/20 bg-purple-500/10 rounded-lg border border-gray-700 hover:border-purple-500 transition-all flex items-center gap-3"
                  >
                    <Icon className="w-6 h-6 text-purple-400" />
                    <span className="text-sm text-white">{option.text}</span>
                  </motion.button>
                )
              })}
            </div>
            
            <button
              onClick={() => setShowQuiz(false)}
              className="mt-4 text-xs text-gray-400 hover:text-gray-400"
            >
              Skip for now
            </button>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Learning Style Badge */}
      {learningStyle && !showQuiz && (
        <div className="bg-gray-900/50 rounded-xl p-4 backdrop-blur-sm border border-gray-700/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                {learningStyle === 'visual' && <EyeIcon className="w-6 h-6 text-white" />}
                {learningStyle === 'auditory' && <HeadphonesIcon className="w-6 h-6 text-white" />}
                {learningStyle === 'kinesthetic' && <HandIcon className="w-6 h-6 text-white" />}
                {learningStyle === 'reading' && <BookOpenIcon className="w-6 h-6 text-white" />}
              </div>
              <div>
                <div className="text-sm font-medium text-white">
                  {learningStyle.charAt(0).toUpperCase() + learningStyle.slice(1)} Learner
                </div>
                <div className="text-xs text-gray-400">
                  Your lessons are optimized for {learningStyle} learning
                </div>
              </div>
            </div>
            
            <button
              onClick={() => setShowQuiz(true)}
              className="text-sm text-purple-400 hover:text-purple-300"
            >
              Retake Quiz
            </button>
          </div>
        </div>
      )}
      
      {/* Recommended Topics */}
      <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-xl p-6 backdrop-blur-sm border border-blue-500/20">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <RocketIcon className="w-4 h-4 text-blue-400" />
            Recommended Learning Topics
          </h3>
          <RefreshCwIcon className="w-4 h-4 text-gray-400 cursor-pointer hover:text-white transition-colors" />
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            { topic: "Essay Writing Techniques", icon: PenToolIcon, color: "from-purple-500 to-pink-500" },
            { topic: "Research Paper Structure", icon: BookOpenIcon, color: "from-blue-500 to-cyan-500" },
            { topic: "Critical Thinking Skills", icon: BrainIcon, color: "from-green-500 to-emerald-500" },
            { topic: "Time Management", icon: ClockIcon, color: "from-orange-500 to-red-500" },
            { topic: "Academic Citations", icon: QuoteIcon, color: "from-indigo-500 to-purple-500" },
            { topic: "Public Speaking", icon: MessageSquareIcon, color: "from-pink-500 to-rose-500" }
          ].map((item, i) => (
            <motion.button
              key={i}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                setInputTopic(item.topic)
                toast.success(`Selected: ${item.topic}`)
              }}
              className="relative bg-gray-800/50 hover:bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-blue-500/50 transition-all group"
            >
              <div className={`absolute inset-0 bg-gradient-to-r ${item.color} opacity-0 group-hover:opacity-10 rounded-lg transition-opacity`} />
              <item.icon className="w-5 h-5 text-blue-400 mb-2" />
              <div className="text-sm font-medium text-white">{item.topic}</div>
              <div className="text-xs text-gray-400 mt-1">Click to learn</div>
            </motion.button>
          ))}
        </div>
        
        <div className="mt-4 flex items-center gap-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span className="text-xs text-gray-400">Popular topics among students</span>
        </div>
      </div>
      
      {/* Content Capture */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <ClipboardIcon className="w-4 h-4 text-green-400" />
            Create Lesson From Content
          </h3>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsMonitoring(!isMonitoring)}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              isMonitoring 
                ? 'bg-green-500/20 text-green-400 border border-green-500/50' 
                : 'bg-gray-800 text-gray-400 border border-gray-700'
            }`}
          >
            {isMonitoring ? '🟢 Monitoring Clipboard' : '⚪ Start Monitoring'}
          </motion.button>
        </div>
        
        <div className="space-y-4">
          <textarea
            value={inputTopic}
            onChange={(e) => setInputTopic(e.target.value)}
            placeholder="Paste content here or highlight text anywhere while monitoring is on..."
            className="w-full h-32 bg-gray-800 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all"
          />
          
          {/* Teaching Method Selection */}
          <div>
            <label className="text-xs text-gray-400 mb-2 block">Select Teaching Method</label>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(TEACHING_METHODS).map(([key, method]) => {
                const Icon = method.icon
                return (
                  <button
                    key={key}
                    onClick={() => setSelectedMethod(key)}
                    className={`p-3 rounded-lg border transition-all ${
                      selectedMethod === key
                        ? 'bg-green-500/20 border-green-500 text-green-400'
                        : 'bg-gray-800/50 bg-gray-900/50 border-gray-700 text-gray-400 hover:border-green-500/50'
                    }`}
                  >
                    <Icon className="w-4 h-4 mx-auto mb-1" />
                    <div className="text-xs font-medium">{method.name}</div>
                  </button>
                )
              })}
            </div>
            <div className="mt-2 text-xs text-gray-400">
              {TEACHING_METHODS[selectedMethod as keyof typeof TEACHING_METHODS].description}
            </div>
          </div>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => generateLesson(inputTopic)}
            disabled={!inputTopic.trim() || isGenerating}
            className="w-full py-3 bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isGenerating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                Generating Lesson...
              </>
            ) : (
              <>
                <SparklesIcon className="w-4 h-4" />
                Generate AI Lesson
              </>
            )}
          </motion.button>
        </div>
      </div>
      
      {/* Current Lesson Display */}
      {currentLesson && (
        <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-white">
              {currentLesson.topic}
            </h3>
            
            <div className="flex items-center gap-2">
              <span className="text-xs bg-blue-500/20 px-2 py-1 rounded-full text-blue-300">
                {TEACHING_METHODS[currentLesson.method as keyof typeof TEACHING_METHODS].name}
              </span>
              <span className="text-xs bg-purple-500/20 bg-purple-500/10 px-2 py-1 rounded-full text-purple-300 text-purple-400">
                {currentLesson.confidence}% Mastered
              </span>
            </div>
          </div>
          
          <div className="prose prose-invert max-w-none">
            <div className="whitespace-pre-wrap text-gray-300 text-sm">
              {currentLesson.content}
            </div>
          </div>
          
          {/* Lesson Actions */}
          <div className="mt-6 flex gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={startLessonQuiz}
              className="px-4 py-2 bg-purple-500/20 bg-purple-500/10 hover:bg-purple-500/30 rounded-lg text-purple-300 text-purple-400 font-medium flex items-center gap-2"
            >
              <QuoteIcon className="w-4 h-4" />
              Take Quiz
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                const note = prompt('Add a note:')
                if (note) {
                  const updated = { ...currentLesson, notes: [...currentLesson.notes, note] }
                  setCurrentLesson(updated)
                  setLessons(lessons.map(l => l.id === updated.id ? updated : l))
                  saveLearningData()
                }
              }}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-300 font-medium flex items-center gap-2"
            >
              <PenToolIcon className="w-4 h-4" />
              Add Note
            </motion.button>
          </div>
        </div>
      )}
      
      {/* Lesson Quiz */}
      {lessonQuiz.length > 0 && !showQuizResults && (
        <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-purple-500/20">
          <h4 className="text-lg font-semibold text-white mb-4">
            Question {quizIndex + 1} of {lessonQuiz.length}
          </h4>
          
          <p className="text-gray-300 mb-4">{lessonQuiz[quizIndex].question}</p>
          
          <div className="space-y-2">
            {lessonQuiz[quizIndex].options.map((option, idx) => (
              <motion.button
                key={idx}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={() => handleLessonQuizAnswer(idx)}
                className="w-full p-3 bg-gray-800 hover:bg-purple-500/20 bg-purple-500/10 rounded-lg text-left text-white border border-gray-700 hover:border-purple-500 transition-all"
              >
                {option}
              </motion.button>
            ))}
          </div>
        </div>
      )}
      
      {/* Quiz Results */}
      {showQuizResults && (
        <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-xl p-6 backdrop-blur-sm border border-purple-500/20 text-center">
          <h3 className="text-xl font-bold text-white mb-4">Quiz Complete!</h3>
          
          <div className="text-4xl font-bold text-purple-400 mb-2">
            {quizScore}/{lessonQuiz.length}
          </div>
          
          <div className="text-gray-400 mb-4">
            {quizScore === lessonQuiz.length && '🎉 Perfect Score!'}
            {quizScore >= lessonQuiz.length * 0.8 && quizScore < lessonQuiz.length && '👏 Great Job!'}
            {quizScore >= lessonQuiz.length * 0.6 && quizScore < lessonQuiz.length * 0.8 && '💪 Good Effort!'}
            {quizScore < lessonQuiz.length * 0.6 && '📚 Keep Practicing!'}
          </div>
          
          <button
            onClick={() => {
              setLessonQuiz([])
              setShowQuizResults(false)
            }}
            className="px-6 py-2 bg-purple-500 bg-purple-500 hover:bg-purple-600 hover:bg-purple-500-dark rounded-lg font-medium transition-colors"
          >
            Continue Learning
          </button>
        </div>
      )}
      
      {/* Lessons Library */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
          <BookOpenIcon className="w-4 h-4 text-blue-400" />
          Your Lessons Library
        </h3>
        
        {lessons.length === 0 ? (
          <div className="text-center py-8">
            <BookOpenIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-400">No lessons yet. Create your first one above!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {lessons.map((lesson) => (
              <motion.div
                key={lesson.id}
                whileHover={{ scale: 1.01 }}
                className="p-4 bg-gray-800 rounded-lg border border-gray-700 hover:border-blue-500/50 transition-all cursor-pointer"
                onClick={() => setCurrentLesson(lesson)}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-white font-medium mb-1">{lesson.topic}</h4>
                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      <span>{TEACHING_METHODS[lesson.method as keyof typeof TEACHING_METHODS].name}</span>
                      <span>•</span>
                      <span>{lesson.reviewCount} reviews</span>
                      <span>•</span>
                      <span>{lesson.confidence}% confidence</span>
                    </div>
                  </div>
                  
                  {lesson.nextReview && new Date(lesson.nextReview) <= new Date() && (
                    <span className="text-xs bg-yellow-500/20 px-2 py-1 rounded-full text-yellow-300">
                      Review Due
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
      
      {/* Achievements */}
      {achievements.length > 0 && (
        <div className="bg-gradient-to-r from-yellow-900/20 to-orange-900/20 from-yellow-50 to-orange-50 rounded-xl p-6 backdrop-blur-sm border border-yellow-500/20 border-yellow-400">
          <h3 className="text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            <AwardIcon className="w-4 h-4 text-yellow-400" />
            Achievements Unlocked
          </h3>
          
          <div className="flex flex-wrap gap-2">
            {achievements.includes('first-lesson') && (
              <div className="bg-yellow-500/20 bg-yellow-100 px-3 py-1 rounded-full text-yellow-300 text-yellow-700 text-sm">
                🎯 First Lesson
              </div>
            )}
            {achievements.includes('knowledge-seeker') && (
              <div className="bg-purple-500/20 bg-purple-500/10 px-3 py-1 rounded-full text-purple-300 text-purple-400 text-sm">
                📚 Knowledge Seeker
              </div>
            )}
            {achievements.includes('dedicated-learner') && (
              <div className="bg-blue-500/20 bg-blue-100 px-3 py-1 rounded-full text-blue-300 text-blue-700 text-sm">
                🏆 Dedicated Learner
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}