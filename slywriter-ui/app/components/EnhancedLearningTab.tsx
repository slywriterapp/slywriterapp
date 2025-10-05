'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RENDER_API_URL } from '../config/api'
import toast from 'react-hot-toast'
import axios from 'axios'

// Use Render server for AI generation (has OpenAI API key configured server-side)
const API_URL = ${RENDER_API_URL}'
import {
  BookOpenIcon,
  BrainIcon,
  TrophyIcon,
  TargetIcon,
  SparklesIcon,
  FlaskConicalIcon,
  GraduationCapIcon,
  LightbulbIcon,
  PlayCircleIcon,
  PauseCircleIcon,
  ChevronRightIcon,
  ChevronLeftIcon,
  SettingsIcon,
  TimerIcon,
  AwardIcon,
  TrendingUpIcon,
  LayersIcon,
  MessageSquareIcon,
  ZapIcon,
  RefreshCwIcon,
  CheckCircleIcon,
  XCircleIcon,
  StarIcon,
  FlameIcon,
  RocketIcon,
  MapIcon,
  CompassIcon,
  ActivityIcon
} from 'lucide-react'

// API key is handled server-side on Render

interface LessonContent {
  topic: string
  coreConcepts: string[]
  explanation: string
  examples: string[]
  commonMisconceptions: string[]
  practiceProblems: Array<{
    question: string
    options: string[]
    correct: number
    explanation: string
    hint: string
  }>
  relatedTopics: string[]
  realWorldApplications: string[]
  visualAids: string[]
  keyTakeaways: string[]
  quiz: Array<{
    question: string
    options: string[]
    correct: number
    explanation: string
  }>
}

interface LearningSettings {
  depth: 'surface' | 'intermediate' | 'advanced'
  duration: number // minutes
  style: 'visual' | 'textual' | 'interactive' | 'mixed'
  focus: 'theory' | 'practice' | 'applications' | 'balanced'
  notifications: boolean
  spacedRepetition: boolean
  gamification: boolean
  aiTutor: boolean
}

interface LearningProgress {
  topicsLearned: number
  totalTime: number
  currentStreak: number
  bestStreak: number
  points: number
  level: number
  achievements: string[]
  masteredTopics: string[]
}

export default function EnhancedLearningTab() {
  const [topics, setTopics] = useState<Array<{ topic: string, answer: string, timestamp: string }>>([])
  const [selectedTopic, setSelectedTopic] = useState<any>(null)
  const [currentLesson, setCurrentLesson] = useState<LessonContent | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [learningMode, setLearningMode] = useState<'overview' | 'lesson' | 'practice' | 'quiz'>('overview')
  const [settings, setSettings] = useState<LearningSettings>({
    depth: 'intermediate',
    duration: 10,
    style: 'mixed',
    focus: 'balanced',
    notifications: true,
    spacedRepetition: true,
    gamification: true,
    aiTutor: true
  })
  const [progress, setProgress] = useState<LearningProgress>({
    topicsLearned: 0,
    totalTime: 0,
    currentStreak: 0,
    bestStreak: 0,
    points: 0,
    level: 1,
    achievements: [],
    masteredTopics: []
  })
  const [showSettings, setShowSettings] = useState(false)
  const [quizScore, setQuizScore] = useState(0)
  const [quizAnswers, setQuizAnswers] = useState<Record<number, number>>({})
  const [showQuizResults, setShowQuizResults] = useState(false)
  const [currentProblemIndex, setCurrentProblemIndex] = useState(0)
  const [showHint, setShowHint] = useState(false)
  const [userAnswer, setUserAnswer] = useState('')
  const [sessionTime, setSessionTime] = useState(0)
  const sessionTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [savedLessons, setSavedLessons] = useState<Array<any>>([])
  const [loadingLessons, setLoadingLessons] = useState(false)

  // Function to load saved lessons from server
  const loadSavedLessons = async () => {
    setLoadingLessons(true)
    try {
      const response = await axios.get(`${API_URL}/api/learning/get-lessons`, {
        timeout: 5000,
        validateStatus: (status) => status < 500 // Accept any status < 500
      })
      
      if (response.status === 404) {
        // Endpoint not deployed yet
        console.log('[Learning] Lessons endpoint not available yet - server needs update')
        setSavedLessons([])
      } else if (response.data?.success) {
        setSavedLessons(response.data.lessons || [])
        console.log('Loaded saved lessons:', response.data.lessons)
      }
    } catch (error: any) {
      console.error('Failed to load saved lessons:', error.message)
      // Don't show error toast - this is expected until server is updated
      setSavedLessons([])
    } finally {
      setLoadingLessons(false)
    }
  }

  // Load topics from localStorage and saved lessons from server
  useEffect(() => {
    const storedTopics = localStorage.getItem('slywriter-learning-topics')
    if (storedTopics) {
      setTopics(JSON.parse(storedTopics))
    }
    
    // Load saved lessons from server
    loadSavedLessons()

    const storedProgress = localStorage.getItem('slywriter-learning-progress')
    if (storedProgress) {
      setProgress(JSON.parse(storedProgress))
    }

    const storedSettings = localStorage.getItem('slywriter-learning-settings')
    if (storedSettings) {
      setSettings(JSON.parse(storedSettings))
    }
    
    // Load the current lesson if it exists
    const storedCurrentLesson = localStorage.getItem('slywriter-current-lesson')
    if (storedCurrentLesson) {
      try {
        const lesson = JSON.parse(storedCurrentLesson)
        setCurrentLesson(lesson)
        // Restore the learning mode if there was an active lesson
        const storedLearningMode = localStorage.getItem('slywriter-learning-mode')
        if (storedLearningMode && storedLearningMode !== 'overview') {
          setLearningMode(storedLearningMode as any)
        }
      } catch (e) {
        console.error('Failed to restore lesson:', e)
      }
    }

    // Listen for new topics from AI generation
    const handleNewTopic = (event: CustomEvent) => {
      const { topic, answer } = event.detail
      const newTopic = {
        topic,
        answer,
        timestamp: new Date().toLocaleString()
      }
      
      setTopics(prev => {
        const updated = [newTopic, ...prev].slice(0, 50) // Keep last 50 topics
        localStorage.setItem('slywriter-learning-topics', JSON.stringify(updated))
        return updated
      })

      // Show notification if enabled
      if (settings.notifications) {
        toast('📚 New topic available for learning!', {
          duration: 3000,
          icon: '🎓'
        })
      }
    }

    window.addEventListener('newLearningTopic', handleNewTopic as EventListener)
    return () => {
      window.removeEventListener('newLearningTopic', handleNewTopic as EventListener)
    }
  }, [settings.notifications])

  // Session timer
  useEffect(() => {
    if (learningMode !== 'overview') {
      sessionTimerRef.current = setInterval(() => {
        setSessionTime(prev => prev + 1)
      }, 1000)
    } else {
      if (sessionTimerRef.current) {
        clearInterval(sessionTimerRef.current as any)
      }
    }

    return () => {
      if (sessionTimerRef.current) {
        clearInterval(sessionTimerRef.current as any)
      }
    }
  }, [learningMode])

  const generateComprehensiveLesson = async (topic: string, answer: string) => {
    setIsGenerating(true)
    
    // Try AI generation first, fall back to enhanced content if it fails
    const useAI = true
    
    try {
      if (useAI) {
        const prompt = `
        Create a comprehensive, state-of-the-art educational lesson for the following topic and answer.
        The lesson should be ${settings.depth} level, focus on ${settings.focus}, and be suitable for ${settings.duration} minutes of learning.
        
        Topic: ${topic}
        Answer/Context: ${answer}
        
        IMPORTANT: Generate ACTUAL CONTENT, not placeholders. Every field must have real, educational content.
        
        Provide a detailed JSON response with the following structure:
        {
          "topic": "Clear topic title",
          "coreConcepts": ["List 4-6 actual core concepts related to the topic"],
          "explanation": "A comprehensive 3-4 paragraph explanation that teaches the underlying principles, mechanisms, and context. This should go BEYOND the simple answer and provide deep understanding.",
          "examples": ["3-4 specific, detailed real-world examples that illustrate the concept"],
          "commonMisconceptions": ["2-3 actual misconceptions people have about this topic with corrections"],
          "practiceProblems": [
            {
              "question": "A specific multiple choice question testing understanding",
              "options": ["Option A (specific content)", "Option B (specific content)", "Option C (specific content)", "Option D (specific content)"],
              "correct": 0,
              "explanation": "Why this answer is correct and why others are wrong",
              "hint": "A helpful hint that guides toward the answer without giving it away"
            },
            {
              "question": "Another specific multiple choice question",
              "options": ["Option A", "Option B", "Option C", "Option D"],
              "correct": 2,
              "explanation": "Detailed explanation of the correct answer",
              "hint": "A guiding hint for this problem"
            },
            {
              "question": "A third multiple choice question testing application",
              "options": ["Option A", "Option B", "Option C", "Option D"],
              "correct": 1,
              "explanation": "Why this is the right answer",
              "hint": "Think about how this applies in practice"
            }
          ],
          "relatedTopics": ["3-4 specific related topics for further learning"],
          "realWorldApplications": ["2-3 specific real-world applications with details"],
          "visualAids": ["2-3 detailed descriptions of diagrams or visualizations that would help understand this topic"],
          "keyTakeaways": ["3-4 specific, actionable key points to remember"],
          "quiz": [
            {"question": "Specific quiz question 1", "options": ["Option A", "Option B", "Option C", "Option D"], "correct": 0, "explanation": "Why this is correct"},
            {"question": "Specific quiz question 2", "options": ["Option A", "Option B", "Option C", "Option D"], "correct": 1, "explanation": "Explanation"},
            {"question": "Specific quiz question 3", "options": ["Option A", "Option B", "Option C", "Option D"], "correct": 2, "explanation": "Explanation"},
            {"question": "Specific quiz question 4", "options": ["Option A", "Option B", "Option C", "Option D"], "correct": 3, "explanation": "Explanation"},
            {"question": "Specific quiz question 5", "options": ["Option A", "Option B", "Option C", "Option D"], "correct": 0, "explanation": "Explanation"}
          ]
        }
        
        Remember: NO PLACEHOLDERS. Generate actual educational content for every single field.
      `

      // Call the Render server which has the OpenAI API key configured
      console.log('Calling AI API at:', `${API_URL}/api/ai/generate`)
      const response = await axios.post(`${API_URL}/api/ai/generate`, {
        prompt: prompt + '\n\nIMPORTANT: Return ONLY valid JSON, no markdown formatting or extra text. Start with { and end with }',
        user_id: localStorage.getItem('userId') || 'anonymous',
        settings: {
          response_type: 'json',
          response_length: 5, // Detailed response
          grade_level: 12,
          tone: 'Educational'
        }
      }, {
        timeout: 60000 // 60 second timeout for AI generation
      })

      // The server returns text in response.data.text
      const generatedText = response.data.text || response.data.output || ''
      console.log('Generated text from server (first 500 chars):', generatedText.substring(0, 500))
      
      // Parse the JSON from the generated text
      let lessonData
      try {
        // Clean up the response text
        let cleanedText = generatedText
          .replace(/```json\s*/gi, '') // Remove markdown code blocks
          .replace(/```\s*/gi, '')
          .replace(/^\s*json\s*/i, '') // Remove "json" prefix
          .trim()
        
        // Try to extract JSON from the response
        // First try: parse as-is
        try {
          lessonData = JSON.parse(cleanedText)
        } catch (e) {
          // Second try: extract JSON object
          const startIndex = cleanedText.indexOf('{')
          const endIndex = cleanedText.lastIndexOf('}')
          
          if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
            let jsonString = cleanedText.substring(startIndex, endIndex + 1)
            
            // Fix common JSON issues
            jsonString = jsonString
              .replace(/,\s*}/g, '}') // Remove trailing commas
              .replace(/,\s*]/g, ']') // Remove trailing commas in arrays
              .replace(/([{,]\s*)(\w+):/g, '$1"$2":') // Quote unquoted keys
              .replace(/:\s*'([^']*)'/g, ': "$1"') // Convert single quotes to double
              .replace(/\n/g, ' ') // Remove newlines that might break strings
              .replace(/\t/g, ' ') // Remove tabs
            
            console.log('Attempting to parse cleaned JSON (first 500 chars):', jsonString.substring(0, 500))
            lessonData = JSON.parse(jsonString)
          } else {
            throw new Error('No JSON object found in response')
          }
        }
      } catch (parseError) {
        console.error('Failed to parse AI response as JSON:', parseError)
        console.log('Raw response was:', generatedText.substring(0, 1000))
        // Use fallback lesson
        throw new Error(`JSON parsing failed: ${(parseError as Error).message}`)
      }
      
      // Validate and fill in missing fields with defaults
      lessonData = {
        topic: lessonData.topic || topic,
        coreConcepts: lessonData.coreConcepts || [`Understanding ${topic}`, 'Key principles', 'Applications', 'Best practices'],
        explanation: lessonData.explanation || answer,
        examples: lessonData.examples || ['Example 1: Practical application', 'Example 2: Real-world scenario', 'Example 3: Common use case'],
        commonMisconceptions: lessonData.commonMisconceptions || ['Misconception 1', 'Misconception 2'],
        practiceProblems: lessonData.practiceProblems || [],
        relatedTopics: lessonData.relatedTopics || [`Advanced ${topic}`, `${topic} in practice`, `${topic} theory`],
        realWorldApplications: lessonData.realWorldApplications || ['Professional use', 'Educational application'],
        visualAids: lessonData.visualAids || ['Diagram showing the concept', 'Flowchart of the process'],
        keyTakeaways: lessonData.keyTakeaways || ['Key point 1', 'Key point 2', 'Key point 3'],
        quiz: lessonData.quiz || []
      }
      
      // Ensure practice problems have the correct structure
      if (lessonData.practiceProblems.length === 0) {
        // Generate default practice problems if none provided
        lessonData.practiceProblems = [
          {
            question: `What is the main concept of ${topic}?`,
            options: ['Understanding the basics', 'Advanced application', 'Theoretical framework', 'Practical implementation'],
            correct: 0,
            explanation: 'The basics are fundamental to understanding',
            hint: 'Start with the fundamentals'
          },
          {
            question: `How does ${topic} apply in practice?`,
            options: ['Direct application', 'Indirect influence', 'Theoretical only', 'Not applicable'],
            correct: 0,
            explanation: 'Direct application is most common',
            hint: 'Think about real-world use'
          },
          {
            question: `What's important about ${topic}?`,
            options: ['Its versatility', 'Limited scope', 'Single use', 'Complexity'],
            correct: 0,
            explanation: 'Versatility makes it valuable',
            hint: 'Consider multiple applications'
          }
        ]
      } else {
        lessonData.practiceProblems = lessonData.practiceProblems.map((problem: any) => ({
          question: problem.question || 'Practice question',
          options: problem.options || ['Option A', 'Option B', 'Option C', 'Option D'],
          correct: typeof problem.correct === 'number' ? problem.correct : 0,
          explanation: problem.explanation || 'Explanation not provided',
          hint: problem.hint || 'Think about the main concepts'
        }))
      }
      
      // Ensure quiz has questions
      if (!lessonData.quiz || lessonData.quiz.length === 0) {
        lessonData.quiz = lessonData.practiceProblems.slice(0, 5).map((p: any) => ({
          question: p.question,
          options: p.options,
          correct: p.correct,
          explanation: p.explanation
        }))
      }
      
      setCurrentLesson(lessonData)
      setLearningMode('lesson')
      
      // Save lesson to localStorage for persistence
      localStorage.setItem('slywriter-current-lesson', JSON.stringify(lessonData))
      localStorage.setItem('slywriter-learning-mode', 'lesson')
      
      // Add to recent topics with full content
      const lessonWithMetadata = {
        ...lessonData,
        generatedAt: new Date().toISOString(),
        originalTopic: topic,
        originalAnswer: answer,
        interactionCount: 1
      }
      
      // Save to topics list with lesson content
      setTopics(prev => {
        const updated = [
          {
            topic,
            answer,
            timestamp: new Date().toISOString(),
            lessonContent: lessonWithMetadata
          },
          ...prev.filter(t => t.topic !== topic).slice(0, 19) // Keep max 20 topics
        ]
        localStorage.setItem('slywriter-learning-topics', JSON.stringify(updated))
        return updated
      })
      
      // Update progress
      updateProgress('topicStarted')
      
      toast.success('🎓 Comprehensive lesson generated!', { duration: 3000 })
      } else {
        // Use fallback when AI is disabled
        console.log('AI generation disabled, using enhanced fallback')
        throw new Error('AI disabled - using fallback')
      }
    } catch (error: any) {
      console.error('AI generation failed, using enhanced fallback:', error.message || error)
      
      // Show user-friendly message based on error type
      if (error.response?.status === 500) {
        toast('⚡ Using enhanced content (AI service warming up)', { 
          icon: '📚',
          duration: 3000 
        })
      } else if (error.code === 'ECONNABORTED') {
        toast('⏱️ AI generation timed out, using enhanced content', { 
          icon: '📚',
          duration: 3000 
        })
      }
      
      // Generate content based on user settings
      const conceptCount = settings.depth === 'surface' ? 3 : settings.depth === 'intermediate' ? 5 : 7
      const problemCount = settings.duration <= 5 ? 2 : settings.duration <= 10 ? 3 : 5
      
      const fallbackLesson: LessonContent = {
        topic: `Understanding ${topic}`,
        coreConcepts: [
          `Fundamental principles of ${topic}`,
          `How ${topic} works in practice`,
          `Key theories and mechanisms`,
          settings.depth !== 'surface' ? `Unique characteristics and features` : null,
          settings.depth !== 'surface' ? `Practical applications and importance` : null,
          settings.depth === 'advanced' ? `Advanced concepts and edge cases` : null,
          settings.depth === 'advanced' ? `Research and future directions` : null
        ].filter(Boolean).slice(0, conceptCount) as string[],
        explanation: `${answer}\n\nTo truly understand ${topic}, we need to explore several key dimensions. First, let's examine the fundamental principles that govern this concept. ${topic} operates on the basis of specific mechanisms that we'll break down step by step.\n\nThe theoretical foundation of ${topic} rests on established principles that have been validated through research and practice. When we apply these principles, we see how ${topic} manifests in real-world scenarios.\n\nFurthermore, understanding ${topic} requires recognizing both its applications and limitations. By studying concrete examples and common pitfalls, we can develop a comprehensive understanding that goes beyond surface-level knowledge.`,
        examples: [
          `Professional application: ${topic} is used in workplace settings to improve efficiency and outcomes`,
          `Everyday relevance: ${topic} appears in daily life when making decisions and solving problems`,
          `Case study: Real-world implementation of ${topic} demonstrates its practical value`,
          `Historical context: The evolution of ${topic} shows how understanding has developed over time`
        ],
        commonMisconceptions: [
          `Oversimplifying ${topic} as just one aspect when it's actually multifaceted`,
          `Thinking ${topic} only applies to specific situations rather than broadly`,
          `Confusing ${topic} with related but distinct concepts`
        ],
        practiceProblems: [
          {
            question: `What is the primary function of ${topic}?`,
            options: [
              `Direct application to solve specific problems`,
              `Establishing a theoretical framework`,
              `Systematic analysis of factors`,
              `Synthesizing multiple elements`
            ],
            correct: 0,
            explanation: `The correct answer is direct application because ${topic} is fundamentally practical`,
            hint: `Think about how ${topic} is actually used`
          },
          {
            question: `What's most important when applying ${topic}?`,
            options: [
              `Complete theoretical understanding`,
              `Context and adaptation`,
              `Following exact procedures`,
              `Focus on outcomes only`
            ],
            correct: 1,
            explanation: `Context matters most because ${topic} must be adapted to each situation`,
            hint: `Consider flexibility in application`
          },
          {
            question: `Which best illustrates proper use of ${topic}?`,
            options: [
              `Textbook application only`,
              `Adaptive implementation`,
              `Intuitive approach`,
              `Controlled environment only`
            ],
            correct: 1,
            explanation: `Adaptive implementation works best because real situations vary`,
            hint: `Think about flexibility`
          }
        ],
        relatedTopics: [
          `Advanced applications of ${topic} in specialized fields`,
          `The relationship between ${topic} and emerging technologies`,
          `Historical development and evolution of ${topic}`,
          `Comparative analysis: ${topic} versus alternative approaches`
        ],
        realWorldApplications: [
          `Technology: Using ${topic} to optimize systems and improve performance`,
          `Education: Teaching ${topic} to help students develop critical thinking`,
          `Business: Applying ${topic} for strategic planning and decision-making`
        ],
        visualAids: [
          `A flowchart showing how ${topic} progresses from initial concept through ${answer.substring(0, 30)}... to final implementation`,
          `A comparison diagram illustrating the differences between ${topic} and related concepts`,
          `An infographic displaying the key components of ${topic} and their interconnections`
        ],
        keyTakeaways: [
          `${topic} involves multiple interconnected principles and applications`,
          `Success with ${topic} requires both theoretical knowledge and practical experience`,
          `Avoid oversimplifying ${topic} - embrace its complexity`,
          `Practice applying ${topic} in different contexts for true mastery`
        ],
        quiz: [
          {
            question: `What is the core principle of ${topic}?`,
            options: [
              `Practical problem-solving approach`,
              `Random unstructured application`,
              `Pure theoretical knowledge`,
              `Memorization without understanding`
            ],
            correct: 0,
            explanation: `The core principle is practical problem-solving, forming the foundation`
          },
          {
            question: `How does ${topic} differ from similar concepts?`,
            options: [
              `It doesn't differ significantly from related ideas`,
              `It specifically focuses on ${answer.substring(0, 40)}... unlike alternatives`,
              `It's completely unrelated to other concepts`,
              `It's just another name for the same thing`
            ],
            correct: 1,
            explanation: `${topic} is unique because it specifically addresses ${answer.substring(0, 60)}...`
          },
          {
            question: `What's the biggest challenge in implementing ${topic}?`,
            options: [
              `Lack of resources`,
              `Understanding how to adapt it to specific contexts while maintaining core principles`,
              `Finding the right textbook`,
              `Getting approval from authorities`
            ],
            correct: 1,
            explanation: `The main challenge is balancing adaptation with maintaining essential elements of ${topic}.`
          },
          {
            question: `Which skill is most important for mastering ${topic}?`,
            options: [
              `Memorization of all details`,
              `Speed of implementation`,
              `Critical thinking and application ability`,
              `Following instructions exactly`
            ],
            correct: 2,
            explanation: `Critical thinking is essential because ${topic} requires thoughtful application based on ${answer.substring(0, 50)}...`
          },
          {
            question: `What indicates successful understanding of ${topic}?`,
            options: [
              `Ability to apply it flexibly in various situations`,
              `Perfect recall of definitions`,
              `Speed of problem-solving`,
              `Agreement with all expert opinions`
            ],
            correct: 0,
            explanation: `True understanding shows through flexible application because ${topic} manifests differently in various contexts.`
          }
        ]
      }
      
      setCurrentLesson(fallbackLesson)
      setLearningMode('lesson')
      
      // Save lesson to localStorage for persistence
      localStorage.setItem('slywriter-current-lesson', JSON.stringify(fallbackLesson))
      localStorage.setItem('slywriter-learning-mode', 'lesson')
      
      // Add to recent topics with full content
      const lessonWithMetadata = {
        ...fallbackLesson,
        generatedAt: new Date().toISOString(),
        originalTopic: topic,
        originalAnswer: answer,
        interactionCount: 1
      }
      
      // Save to topics list with lesson content
      setTopics(prev => {
        const updated = [
          {
            topic,
            answer,
            timestamp: new Date().toISOString(),
            lessonContent: lessonWithMetadata
          },
          ...prev.filter(t => t.topic !== topic).slice(0, 19) // Keep max 20 topics
        ]
        localStorage.setItem('slywriter-learning-topics', JSON.stringify(updated))
        return updated
      })
      
      // Update progress
      updateProgress('topicStarted')
      
      toast.success('🎓 Comprehensive lesson created!', { 
        icon: '📚',
        duration: 3000 
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const updateProgress = (action: string, quizScore: number = 0) => {
    // Only update if gamification is enabled
    if (!settings.gamification) return
    
    setProgress(prev => {
      const updated = { ...prev }
      
      // Track session time
      const sessionMinutes = Math.floor(sessionTime / 60)
      if (sessionMinutes > 0 && !updated.totalTime) {
        updated.totalTime = sessionMinutes
      } else if (sessionMinutes > 0) {
        updated.totalTime += sessionMinutes
      }
      
      switch (action) {
        case 'topicStarted':
          updated.topicsLearned++
          updated.points += 10
          
          // Check if this is a new day for streak tracking
          const lastActivity = localStorage.getItem('slywriter-last-learning-activity')
          const today = new Date().toDateString()
          const yesterday = new Date(Date.now() - 86400000).toDateString()
          
          if (lastActivity === yesterday || !lastActivity) {
            updated.currentStreak++
          } else if (lastActivity !== today) {
            // Streak broken
            updated.currentStreak = 1
          }
          
          localStorage.setItem('slywriter-last-learning-activity', today)
          
          if (updated.currentStreak > updated.bestStreak) {
            updated.bestStreak = updated.currentStreak
          }
          break
        case 'quizCompleted':
          updated.points += quizScore * 10
          // Add topic to mastered if quiz score is high
          if (quizScore >= 80 && currentLesson) {
            const topic = (currentLesson as any).originalTopic || currentLesson.topic
            if (!updated.masteredTopics.includes(topic)) {
              updated.masteredTopics.push(topic)
              toast('🌟 Topic Mastered!', { duration: 3000 })
            }
          }
          break
        case 'problemSolved':
          updated.points += 15
          break
      }
      
      // Level calculation
      updated.level = Math.floor(updated.points / 100) + 1
      
      // Check for achievements
      if (updated.topicsLearned === 1 && !updated.achievements.includes('firstTopic')) {
        updated.achievements.push('firstTopic')
        toast('🎉 Achievement: First Topic Learned!', { duration: 5000 })
      }
      
      if (updated.topicsLearned === 5 && !updated.achievements.includes('fiveTopics')) {
        updated.achievements.push('fiveTopics')
        toast('📚 Achievement: 5 Topics Learned!', { duration: 5000 })
      }
      
      if (updated.topicsLearned === 10 && !updated.achievements.includes('firstTen')) {
        updated.achievements.push('firstTen')
        toast('🏆 Achievement: Learned 10 topics!', { duration: 5000 })
      }
      
      if (updated.topicsLearned === 25 && !updated.achievements.includes('quarterCentury')) {
        updated.achievements.push('quarterCentury')
        toast('💎 Achievement: 25 Topics Mastered!', { duration: 5000 })
      }
      
      if (updated.currentStreak === 3 && !updated.achievements.includes('threeStreak')) {
        updated.achievements.push('threeStreak')
        toast('🔥 Achievement: 3-day learning streak!', { duration: 5000 })
      }
      
      if (updated.currentStreak === 7 && !updated.achievements.includes('weekStreak')) {
        updated.achievements.push('weekStreak')
        toast('🔥 Achievement: 7-day learning streak!', { duration: 5000 })
      }
      
      if (updated.points >= 500 && !updated.achievements.includes('scholar')) {
        updated.achievements.push('scholar')
        toast('🎓 Achievement: Scholar Status (500 points)!', { duration: 5000 })
      }
      
      if (updated.points >= 1000 && !updated.achievements.includes('expert')) {
        updated.achievements.push('expert')
        toast('👨‍🎓 Achievement: Expert Learner (1000 points)!', { duration: 5000 })
      }
      
      localStorage.setItem('slywriter-learning-progress', JSON.stringify(updated))
      return updated
    })
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const submitQuiz = () => {
    if (!currentLesson) return
    
    let score = 0
    currentLesson.quiz.forEach((q, index) => {
      if (quizAnswers[index] === q.correct) {
        score++
      }
    })
    
    setQuizScore(score)
    setShowQuizResults(true)
    
    const percentage = (score / currentLesson.quiz.length) * 100
    updateProgress('quizCompleted', percentage)
    if (percentage === 100) {
      toast('🎉 Perfect score! You mastered this topic!', { duration: 5000 })
    } else if (percentage >= 80) {
      toast('🌟 Great job! You understand this well!', { duration: 4000 })
    } else if (percentage >= 60) {
      toast('👍 Good effort! Review the explanations to improve.', { duration: 4000 })
    } else {
      toast('📚 Keep learning! Review the lesson and try again.', { duration: 4000 })
    }
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900">
      {/* Header */}
      <div className="p-6 border-b border-white/10">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl">
              <GraduationCapIcon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Smart Learning System</h2>
              <p className="text-gray-400">Transform answers into knowledge</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Progress Stats - Only show if gamification is enabled */}
            {settings.gamification && (
              <div className="flex items-center gap-6 px-4 py-2 bg-black/20 rounded-xl">
                <div className="flex items-center gap-2">
                  <FlameIcon className="w-5 h-5 text-orange-400" />
                  <span className="text-white font-medium">{progress.currentStreak} day streak</span>
                </div>
                <div className="flex items-center gap-2">
                  <TrophyIcon className="w-5 h-5 text-yellow-400" />
                  <span className="text-white font-medium">Level {progress.level}</span>
                </div>
                <div className="flex items-center gap-2">
                  <StarIcon className="w-5 h-5 text-purple-400" />
                  <span className="text-white font-medium">{progress.points} pts</span>
                </div>
              </div>
            )}
            
            {/* Settings Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowSettings(!showSettings)}
              className="p-3 bg-gray-800 rounded-xl hover:bg-gray-700 transition-colors"
            >
              <SettingsIcon className="w-5 h-5 text-gray-400" />
            </motion.button>
          </div>
        </div>
        
        {/* Session Timer */}
        {learningMode !== 'overview' && (
          <div className="mt-4 flex items-center gap-2 text-sm text-gray-400">
            <TimerIcon className="w-4 h-4" />
            <span>Session time: {formatTime(sessionTime)}</span>
          </div>
        )}
      </div>

      {/* Settings Panel */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-b border-white/10 overflow-hidden"
          >
            <div className="p-6 bg-black/20">
              <h3 className="text-lg font-semibold text-white mb-4">Learning Preferences</h3>
              
              <div className="grid grid-cols-4 gap-6">
                {/* Depth Setting */}
                <div>
                  <label className="text-sm text-gray-400 mb-2 block">Learning Depth</label>
                  <select
                    value={settings.depth}
                    onChange={(e) => setSettings(prev => ({ ...prev, depth: e.target.value as any }))}
                    className="w-full px-3 py-2 bg-gray-800 text-white rounded-lg"
                  >
                    <option value="surface">Surface (Quick)</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced (Deep)</option>
                  </select>
                </div>
                
                {/* Duration Setting */}
                <div>
                  <label className="text-sm text-gray-400 mb-2 block">Session Duration</label>
                  <select
                    value={settings.duration}
                    onChange={(e) => setSettings(prev => ({ ...prev, duration: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 bg-gray-800 text-white rounded-lg"
                  >
                    <option value="5">5 minutes</option>
                    <option value="10">10 minutes</option>
                    <option value="15">15 minutes</option>
                    <option value="20">20 minutes</option>
                  </select>
                </div>
                
                {/* Style Setting */}
                <div>
                  <label className="text-sm text-gray-400 mb-2 block">Learning Style</label>
                  <select
                    value={settings.style}
                    onChange={(e) => setSettings(prev => ({ ...prev, style: e.target.value as any }))}
                    className="w-full px-3 py-2 bg-gray-800 text-white rounded-lg"
                  >
                    <option value="visual">Visual</option>
                    <option value="textual">Textual</option>
                    <option value="interactive">Interactive</option>
                    <option value="mixed">Mixed</option>
                  </select>
                </div>
                
                {/* Focus Setting */}
                <div>
                  <label className="text-sm text-gray-400 mb-2 block">Focus Area</label>
                  <select
                    value={settings.focus}
                    onChange={(e) => setSettings(prev => ({ ...prev, focus: e.target.value as any }))}
                    className="w-full px-3 py-2 bg-gray-800 text-white rounded-lg"
                  >
                    <option value="theory">Theory</option>
                    <option value="practice">Practice</option>
                    <option value="applications">Applications</option>
                    <option value="balanced">Balanced</option>
                  </select>
                </div>
              </div>
              
              {/* Toggle Settings */}
              <div className="mt-4 flex gap-6">
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <input
                    type="checkbox"
                    checked={settings.notifications}
                    onChange={(e) => setSettings(prev => ({ ...prev, notifications: e.target.checked }))}
                    className="rounded"
                  />
                  Notifications
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <input
                    type="checkbox"
                    checked={settings.spacedRepetition}
                    onChange={(e) => setSettings(prev => ({ ...prev, spacedRepetition: e.target.checked }))}
                    className="rounded"
                  />
                  Spaced Repetition
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <input
                    type="checkbox"
                    checked={settings.gamification}
                    onChange={(e) => setSettings(prev => ({ ...prev, gamification: e.target.checked }))}
                    className="rounded"
                  />
                  Gamification
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <input
                    type="checkbox"
                    checked={settings.aiTutor}
                    onChange={(e) => setSettings(prev => ({ ...prev, aiTutor: e.target.checked }))}
                    className="rounded"
                  />
                  AI Tutor
                </label>
              </div>
              
              <button
                onClick={() => {
                  localStorage.setItem('slywriter-learning-settings', JSON.stringify(settings))
                  toast.success('Settings saved!', { duration: 2000 })
                }}
                className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Save Settings
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Topics Sidebar */}
        {learningMode === 'overview' && (
          <div className="w-1/3 border-r border-white/10 overflow-y-auto p-6">
            {/* Tab selector for Topics vs Saved Lessons */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setSelectedTopic(null)}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  !savedLessons ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                Recent Topics
              </button>
              <button
                onClick={() => {
                  loadSavedLessons()
                  setSelectedTopic('saved-lessons')
                }}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedTopic === 'saved-lessons' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                AI Lessons ({savedLessons.length})
              </button>
            </div>
            
            {selectedTopic === 'saved-lessons' ? (
              // Show saved AI lessons
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Saved AI Lessons</h3>
                {loadingLessons ? (
                  <div className="text-center py-8">
                    <RefreshCwIcon className="w-8 h-8 text-purple-400 animate-spin mx-auto mb-2" />
                    <p className="text-gray-400">Loading lessons...</p>
                  </div>
                ) : savedLessons.length === 0 ? (
                  <div className="text-center py-8">
                    <BookOpenIcon className="w-12 h-12 text-gray-600 mx-auto mb-2" />
                    <p className="text-gray-400">No saved lessons yet</p>
                    <p className="text-sm text-gray-500 mt-2">Enable Auto-Learn in AI Writer to save lessons</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {savedLessons.map((lesson, index) => (
                      <motion.div
                        key={lesson.id || index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        onClick={() => {
                          setSelectedTopic({ 
                            topic: lesson.topic, 
                            answer: lesson.content,
                            timestamp: new Date(lesson.created_at).toLocaleString()
                          })
                        }}
                        className="p-4 rounded-xl cursor-pointer transition-all bg-gray-800/50 hover:bg-gray-800"
                      >
                        <h4 className="font-medium text-white mb-1 line-clamp-1">{lesson.topic}</h4>
                        <p className="text-sm text-gray-400 line-clamp-2">{lesson.content}</p>
                        <div className="flex items-center justify-between mt-2">
                          <p className="text-xs text-gray-500">{new Date(lesson.created_at).toLocaleDateString()}</p>
                          <span className="text-xs text-purple-400">{lesson.word_count} words</span>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              // Show recent topics (original content)
              <>
                <h3 className="text-lg font-semibold text-white mb-4">Recent Topics</h3>
                {topics.length === 0 ? (
              <div className="text-center py-8">
                <BookOpenIcon className="w-12 h-12 text-gray-600 mx-auto mb-2" />
                <p className="text-gray-400">No topics yet</p>
                <p className="text-sm text-gray-500 mt-2">Generate content with AI to start learning</p>
              </div>
            ) : (
              <div className="space-y-3">
                {topics.map((topic, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    onClick={() => setSelectedTopic(topic)}
                    className={`p-4 rounded-xl cursor-pointer transition-all ${
                      selectedTopic === topic
                        ? 'bg-purple-600/20 border border-purple-500/50'
                        : 'bg-gray-800/50 hover:bg-gray-800'
                    }`}
                  >
                    <h4 className="font-medium text-white mb-1">{topic.topic}</h4>
                    <p className="text-sm text-gray-400 line-clamp-2">{topic.answer}</p>
                    <p className="text-xs text-gray-500 mt-2">{topic.timestamp}</p>
                    {progress.masteredTopics.includes(topic.topic) && (
                      <span className="inline-block mt-2 px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded">
                        Mastered ✓
                      </span>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
              </>
            )}
          </div>
        )}

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {learningMode === 'overview' ? (
            // Overview Mode
            <div>
              {selectedTopic ? (
                <div className="bg-gray-800/50 rounded-2xl p-6">
                  <h3 className="text-2xl font-bold text-white mb-4">{selectedTopic.topic}</h3>
                  <div className="bg-black/30 rounded-xl p-4 mb-6">
                    <p className="text-gray-300">{selectedTopic.answer}</p>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-4">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => {
                        // Check if this topic already has a saved lesson
                        if (selectedTopic.lessonContent) {
                          // Restore the saved lesson
                          setCurrentLesson(selectedTopic.lessonContent)
                          setLearningMode('lesson')
                          localStorage.setItem('slywriter-current-lesson', JSON.stringify(selectedTopic.lessonContent))
                          localStorage.setItem('slywriter-learning-mode', 'lesson')
                          
                          // Update interaction count
                          const updatedLesson = {
                            ...selectedTopic.lessonContent,
                            interactionCount: (selectedTopic.lessonContent.interactionCount || 0) + 1
                          }
                          
                          // Update in topics list
                          setTopics(prev => prev.map(t => 
                            t.topic === selectedTopic.topic 
                              ? { ...t, lessonContent: updatedLesson }
                              : t
                          ))
                          
                          toast.success('📚 Lesson restored from your saved content!', { duration: 2000 })
                        } else {
                          // Generate new lesson
                          generateComprehensiveLesson(selectedTopic.topic, selectedTopic.answer)
                        }
                      }}
                      disabled={isGenerating}
                      className="p-4 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl text-white font-medium disabled:opacity-50"
                    >
                      {isGenerating ? (
                        <div className="flex items-center justify-center gap-2">
                          <RefreshCwIcon className="w-5 h-5 animate-spin" />
                          <span>Generating...</span>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center gap-2">
                          <BrainIcon className="w-6 h-6" />
                          <span>{selectedTopic.lessonContent ? 'Resume' : 'Deep Learn'}</span>
                        </div>
                      )}
                    </motion.button>
                    
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={async () => {
                        // First generate or restore lesson if needed
                        if (!selectedTopic.lessonContent) {
                          await generateComprehensiveLesson(selectedTopic.topic, selectedTopic.answer)
                        } else {
                          setCurrentLesson(selectedTopic.lessonContent)
                          localStorage.setItem('slywriter-current-lesson', JSON.stringify(selectedTopic.lessonContent))
                        }
                        // Then switch to practice mode
                        setTimeout(() => {
                          setLearningMode('practice')
                          localStorage.setItem('slywriter-learning-mode', 'practice')
                          toast.success('🎯 Practice mode activated!', { duration: 2000 })
                        }, 100)
                      }}
                      disabled={isGenerating}
                      className="p-4 bg-blue-600 rounded-xl text-white font-medium disabled:opacity-50"
                    >
                      <div className="flex flex-col items-center gap-2">
                        <FlaskConicalIcon className="w-6 h-6" />
                        <span>Practice</span>
                      </div>
                    </motion.button>
                    
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={async () => {
                        // First generate or restore lesson if needed
                        if (!selectedTopic.lessonContent) {
                          await generateComprehensiveLesson(selectedTopic.topic, selectedTopic.answer)
                        } else {
                          setCurrentLesson(selectedTopic.lessonContent)
                          localStorage.setItem('slywriter-current-lesson', JSON.stringify(selectedTopic.lessonContent))
                        }
                        // Then switch to quiz mode
                        setTimeout(() => {
                          setLearningMode('quiz')
                          localStorage.setItem('slywriter-learning-mode', 'quiz')
                          toast.success('🎮 Quiz mode activated!', { duration: 2000 })
                        }, 100)
                      }}
                      disabled={isGenerating}
                      className="p-4 bg-green-600 rounded-xl text-white font-medium disabled:opacity-50"
                    >
                      <div className="flex flex-col items-center gap-2">
                        <TargetIcon className="w-6 h-6" />
                        <span>Quiz Me</span>
                      </div>
                    </motion.button>
                    
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={async () => {
                        // First generate or restore lesson if needed
                        if (!selectedTopic.lessonContent) {
                          await generateComprehensiveLesson(selectedTopic.topic, selectedTopic.answer)
                        } else {
                          setCurrentLesson(selectedTopic.lessonContent)
                          localStorage.setItem('slywriter-current-lesson', JSON.stringify(selectedTopic.lessonContent))
                        }
                        // Show lesson with exploration focus
                        setTimeout(() => {
                          setLearningMode('lesson')
                          localStorage.setItem('slywriter-learning-mode', 'lesson')
                          // Scroll to related topics section
                          setTimeout(() => {
                            const relatedSection = document.getElementById('related-topics-section')
                            if (relatedSection) {
                              relatedSection.scrollIntoView({ behavior: 'smooth', block: 'center' })
                            }
                          }, 500)
                          toast.success('🔍 Explore related topics and applications!', { duration: 2000 })
                        }, 100)
                      }}
                      disabled={isGenerating}
                      className="p-4 bg-orange-600 rounded-xl text-white font-medium disabled:opacity-50"
                    >
                      <div className="flex flex-col items-center gap-2">
                        <MapIcon className="w-6 h-6" />
                        <span>Explore</span>
                      </div>
                    </motion.button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-16">
                  <RocketIcon className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                  <h3 className="text-2xl font-bold text-white mb-2">Ready to Learn?</h3>
                  <p className="text-gray-400 mb-6">Select a topic from the left to begin your learning journey</p>
                  
                  {/* Quick Stats */}
                  <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto mt-8">
                    <div className="bg-gray-800/50 rounded-xl p-4">
                      <BookOpenIcon className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                      <p className="text-2xl font-bold text-white">{progress.topicsLearned}</p>
                      <p className="text-sm text-gray-400">Topics Learned</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-xl p-4">
                      <FlameIcon className="w-8 h-8 text-orange-400 mx-auto mb-2" />
                      <p className="text-2xl font-bold text-white">{progress.currentStreak}</p>
                      <p className="text-sm text-gray-400">Day Streak</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-xl p-4">
                      <TrophyIcon className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
                      <p className="text-2xl font-bold text-white">{progress.achievements.length}</p>
                      <p className="text-sm text-gray-400">Achievements</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : learningMode === 'lesson' && currentLesson ? (
            // Lesson Mode
            <div className="max-w-4xl mx-auto">
              <div className="mb-6 flex justify-between items-center">
                <button
                  onClick={() => {
                    setLearningMode('overview')
                    localStorage.setItem('slywriter-learning-mode', 'overview')
                  }}
                  className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                >
                  <ChevronLeftIcon className="w-5 h-5" />
                  Back to Topics
                </button>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setLearningMode('practice')
                      localStorage.setItem('slywriter-learning-mode', 'practice')
                      // Track interaction
                      if (currentLesson) {
                        const updatedLesson = {
                          ...currentLesson,
                          interactionCount: ((currentLesson as any).interactionCount || 0) + 1,
                          lastInteraction: 'practice'
                        }
                        setCurrentLesson(updatedLesson)
                        localStorage.setItem('slywriter-current-lesson', JSON.stringify(updatedLesson))
                      }
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Practice Problems
                  </button>
                  <button
                    onClick={() => {
                      setLearningMode('quiz')
                      localStorage.setItem('slywriter-learning-mode', 'quiz')
                      // Track interaction
                      if (currentLesson) {
                        const updatedLesson = {
                          ...currentLesson,
                          interactionCount: ((currentLesson as any).interactionCount || 0) + 1,
                          lastInteraction: 'quiz'
                        }
                        setCurrentLesson(updatedLesson)
                        localStorage.setItem('slywriter-current-lesson', JSON.stringify(updatedLesson))
                      }
                    }}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Take Quiz
                  </button>
                </div>
              </div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gray-800/50 rounded-2xl p-8"
              >
                <h2 className="text-3xl font-bold text-white mb-6">{currentLesson.topic}</h2>
                
                {/* Core Concepts */}
                <div className="mb-8">
                  <h3 className="text-xl font-semibold text-purple-400 mb-4 flex items-center gap-2">
                    <LightbulbIcon className="w-5 h-5" />
                    Core Concepts
                  </h3>
                  <div className="grid grid-cols-3 gap-3">
                    {currentLesson.coreConcepts.map((concept, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.1 }}
                        className="p-3 bg-purple-600/20 rounded-lg text-purple-300 text-center"
                      >
                        {concept}
                      </motion.div>
                    ))}
                  </div>
                </div>
                
                {/* Detailed Explanation */}
                <div className="mb-8">
                  <h3 className="text-xl font-semibold text-blue-400 mb-4 flex items-center gap-2">
                    <BookOpenIcon className="w-5 h-5" />
                    Understanding the Topic
                  </h3>
                  <div className="bg-black/30 rounded-xl p-6">
                    <p className="text-gray-300 leading-relaxed">{currentLesson.explanation}</p>
                  </div>
                </div>
                
                {/* Examples */}
                <div className="mb-8">
                  <h3 className="text-xl font-semibold text-green-400 mb-4 flex items-center gap-2">
                    <LayersIcon className="w-5 h-5" />
                    Examples
                  </h3>
                  <div className="space-y-3">
                    {currentLesson.examples.map((example, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="p-4 bg-green-600/10 border-l-4 border-green-500 rounded"
                      >
                        <p className="text-gray-300">{example}</p>
                      </motion.div>
                    ))}
                  </div>
                </div>
                
                {/* Common Misconceptions */}
                <div className="mb-8">
                  <h3 className="text-xl font-semibold text-orange-400 mb-4 flex items-center gap-2">
                    <XCircleIcon className="w-5 h-5" />
                    Common Misconceptions
                  </h3>
                  <div className="space-y-3">
                    {currentLesson.commonMisconceptions.map((misconception, index) => (
                      <div key={index} className="p-4 bg-orange-600/10 border-l-4 border-orange-500 rounded">
                        <p className="text-gray-300">{misconception}</p>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Real World Applications */}
                <div className="mb-8">
                  <h3 className="text-xl font-semibold text-cyan-400 mb-4 flex items-center gap-2">
                    <CompassIcon className="w-5 h-5" />
                    Real World Applications
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    {currentLesson.realWorldApplications.map((app, index) => (
                      <div key={index} className="p-4 bg-cyan-600/10 rounded-lg">
                        <p className="text-gray-300">{app}</p>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Key Takeaways */}
                <div className="mb-8">
                  <h3 className="text-xl font-semibold text-pink-400 mb-4 flex items-center gap-2">
                    <StarIcon className="w-5 h-5" />
                    Key Takeaways
                  </h3>
                  <div className="bg-gradient-to-r from-pink-600/20 to-purple-600/20 rounded-xl p-6">
                    <ul className="space-y-2">
                      {currentLesson.keyTakeaways.map((takeaway, index) => (
                        <li key={index} className="flex items-start gap-2 text-gray-300">
                          <CheckCircleIcon className="w-5 h-5 text-pink-400 mt-0.5" />
                          <span>{takeaway}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
                
                {/* Related Topics - for Explore button */}
                <div id="related-topics-section" className="mb-8">
                  <h3 className="text-xl font-semibold text-indigo-400 mb-4 flex items-center gap-2">
                    <CompassIcon className="w-5 h-5" />
                    Related Topics to Explore
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    {currentLesson.relatedTopics.map((topic, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.1 }}
                        className="p-4 bg-indigo-600/10 rounded-lg border border-indigo-500/30 hover:bg-indigo-600/20 transition-colors cursor-pointer"
                        onClick={() => {
                          // Create a new topic for exploration
                          const newTopic = {
                            topic: topic,
                            answer: `Explore this related concept to deepen your understanding of ${currentLesson.topic}`,
                            timestamp: new Date().toISOString()
                          }
                          setTopics(prev => [newTopic, ...prev])
                          setSelectedTopic(newTopic)
                          setLearningMode('overview')
                          localStorage.setItem('slywriter-learning-mode', 'overview')
                          toast.success(`Ready to explore: ${topic}`, { duration: 2000 })
                        }}
                      >
                        <p className="text-indigo-300 font-medium">{topic}</p>
                      </motion.div>
                    ))}
                  </div>
                </div>
                
                {/* Visual Aids Descriptions */}
                <div className="mb-8">
                  <h3 className="text-xl font-semibold text-yellow-400 mb-4 flex items-center gap-2">
                    <LightbulbIcon className="w-5 h-5" />
                    Visual Learning Aids
                  </h3>
                  <div className="space-y-3">
                    {currentLesson.visualAids.map((aid, index) => (
                      <div key={index} className="p-4 bg-yellow-600/10 rounded-lg">
                        <p className="text-gray-300">📊 {aid}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            </div>
          ) : learningMode === 'practice' && currentLesson ? (
            // Practice Mode
            <div className="max-w-3xl mx-auto">
              <div className="mb-6 flex justify-between items-center">
                <button
                  onClick={() => {
                    setLearningMode('lesson')
                    localStorage.setItem('slywriter-learning-mode', 'lesson')
                  }}
                  className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                >
                  <ChevronLeftIcon className="w-5 h-5" />
                  Back to Lesson
                </button>
                
                <div className="text-sm text-gray-400">
                  Problem {currentProblemIndex + 1} of {currentLesson.practiceProblems.length}
                </div>
              </div>
              
              <motion.div
                key={currentProblemIndex}
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-gray-800/50 rounded-2xl p-8"
              >
                <h3 className="text-2xl font-bold text-white mb-6">
                  Practice Problem {currentProblemIndex + 1} of {currentLesson.practiceProblems.length}
                </h3>
                
                <div className="bg-black/30 rounded-xl p-6 mb-6">
                  <p className="text-lg text-gray-300">
                    {currentLesson.practiceProblems[currentProblemIndex].question}
                  </p>
                </div>
                
                {showHint && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mb-6 p-4 bg-yellow-600/20 border-l-4 border-yellow-500 rounded"
                  >
                    <p className="text-yellow-300">
                      💡 Hint: {currentLesson.practiceProblems[currentProblemIndex].hint}
                    </p>
                  </motion.div>
                )}
                
                {/* Multiple Choice Options */}
                <div className="space-y-3 mb-6">
                  {currentLesson.practiceProblems[currentProblemIndex].options.map((option, index) => (
                    <label
                      key={index}
                      className={`flex items-center gap-3 p-4 rounded-lg cursor-pointer transition-all ${
                        parseInt(userAnswer) === index
                          ? 'bg-purple-600/30 border border-purple-500'
                          : 'bg-gray-800 hover:bg-gray-700'
                      }`}
                    >
                      <input
                        type="radio"
                        name="practice-answer"
                        value={index}
                        checked={parseInt(userAnswer) === index}
                        onChange={(e) => setUserAnswer(e.target.value)}
                        className="text-purple-600"
                      />
                      <span className="text-gray-300">{option}</span>
                    </label>
                  ))}
                </div>
                
                {/* Show result if answer was checked */}
                {userAnswer !== '' && parseInt(userAnswer) === currentLesson.practiceProblems[currentProblemIndex].correct && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mb-6 p-4 bg-green-600/20 border-l-4 border-green-500 rounded"
                  >
                    <p className="text-green-300">
                      ✅ Correct! {currentLesson.practiceProblems[currentProblemIndex].explanation}
                    </p>
                  </motion.div>
                )}
                
                {userAnswer !== '' && parseInt(userAnswer) !== currentLesson.practiceProblems[currentProblemIndex].correct && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mb-6 p-4 bg-red-600/20 border-l-4 border-red-500 rounded"
                  >
                    <p className="text-red-300">
                      ❌ Not quite. {currentLesson.practiceProblems[currentProblemIndex].explanation}
                    </p>
                  </motion.div>
                )}
                
                <div className="flex gap-3">
                  {!showHint && userAnswer === '' && (
                    <button
                      onClick={() => setShowHint(true)}
                      className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
                    >
                      Show Hint
                    </button>
                  )}
                  
                  {userAnswer !== '' ? (
                    currentProblemIndex < currentLesson.practiceProblems.length - 1 ? (
                      <button
                        onClick={() => {
                          setCurrentProblemIndex(currentProblemIndex + 1)
                          setShowHint(false)
                          setUserAnswer('')
                        }}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Next Problem
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          setLearningMode('quiz')
                          setCurrentProblemIndex(0)
                          setUserAnswer('')
                          setShowHint(false)
                        }}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        Move to Quiz
                      </button>
                    )
                  ) : (
                    <button
                      onClick={() => {
                        if (userAnswer === '') {
                          toast.error('Please select an answer first!', { duration: 3000 })
                        } else {
                          updateProgress('problemSolved')
                        }
                      }}
                      disabled={userAnswer === ''}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Check Answer
                    </button>
                  )}
                </div>
              </motion.div>
            </div>
          ) : learningMode === 'quiz' && currentLesson ? (
            // Quiz Mode
            <div className="max-w-3xl mx-auto">
              <div className="mb-6 flex justify-between items-center">
                <button
                  onClick={() => {
                    setLearningMode('lesson')
                    setShowQuizResults(false)
                    setQuizAnswers({})
                  }}
                  className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
                >
                  <ChevronLeftIcon className="w-5 h-5" />
                  Back to Lesson
                </button>
                
                {!showQuizResults && (
                  <div className="text-sm text-gray-400">
                    {Object.keys(quizAnswers).length} of {currentLesson.quiz.length} answered
                  </div>
                )}
              </div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gray-800/50 rounded-2xl p-8"
              >
                <h3 className="text-2xl font-bold text-white mb-6">Knowledge Check Quiz</h3>
                
                {!showQuizResults ? (
                  <div className="space-y-6">
                    {currentLesson.quiz.map((question, qIndex) => (
                      <div key={qIndex} className="p-6 bg-black/30 rounded-xl">
                        <p className="text-lg text-white mb-4">
                          {qIndex + 1}. {question.question}
                        </p>
                        <div className="space-y-2">
                          {question.options.map((option, oIndex) => (
                            <label
                              key={oIndex}
                              className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                                quizAnswers[qIndex] === oIndex
                                  ? 'bg-purple-600/30 border border-purple-500'
                                  : 'bg-gray-800 hover:bg-gray-700'
                              }`}
                            >
                              <input
                                type="radio"
                                name={`question-${qIndex}`}
                                checked={quizAnswers[qIndex] === oIndex}
                                onChange={() => setQuizAnswers({ ...quizAnswers, [qIndex]: oIndex })}
                                className="text-purple-600"
                              />
                              <span className="text-gray-300">{option}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    ))}
                    
                    <button
                      onClick={submitQuiz}
                      disabled={Object.keys(quizAnswers).length < currentLesson.quiz.length}
                      className="w-full py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Submit Quiz
                    </button>
                  </div>
                ) : (
                  <div>
                    <div className="text-center mb-8">
                      <div className="text-5xl font-bold text-white mb-2">
                        {quizScore} / {currentLesson.quiz.length}
                      </div>
                      <div className="text-xl text-gray-400">
                        {((quizScore / currentLesson.quiz.length) * 100).toFixed(0)}% Correct
                      </div>
                    </div>
                    
                    <div className="space-y-4">
                      {currentLesson.quiz.map((question, qIndex) => {
                        const isCorrect = quizAnswers[qIndex] === question.correct
                        return (
                          <div
                            key={qIndex}
                            className={`p-4 rounded-lg ${
                              isCorrect ? 'bg-green-600/20' : 'bg-red-600/20'
                            }`}
                          >
                            <div className="flex items-start gap-2 mb-2">
                              {isCorrect ? (
                                <CheckCircleIcon className="w-5 h-5 text-green-400 mt-0.5" />
                              ) : (
                                <XCircleIcon className="w-5 h-5 text-red-400 mt-0.5" />
                              )}
                              <p className="text-white">{question.question}</p>
                            </div>
                            {!isCorrect && (
                              <p className="text-sm text-gray-400 ml-7">
                                Correct answer: {question.options[question.correct]}
                              </p>
                            )}
                            <p className="text-sm text-gray-300 ml-7 mt-2">
                              {question.explanation}
                            </p>
                          </div>
                        )
                      })}
                    </div>
                    
                    <button
                      onClick={() => {
                        setShowQuizResults(false)
                        setQuizAnswers({})
                        setQuizScore(0)
                      }}
                      className="mt-6 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      Retake Quiz
                    </button>
                  </div>
                )}
              </motion.div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}