'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { Timer, RotateCcw, Trophy, Target, Zap, TrendingUp } from 'lucide-react'
import toast from 'react-hot-toast'

const API_URL = 'http://localhost:8000'

const TEST_TEXTS = [
  "The quick brown fox jumps over the lazy dog. This pangram contains all letters of the alphabet.",
  "Technology has revolutionized the way we communicate, work, and live our daily lives.",
  "In the digital age, typing speed and accuracy have become increasingly important skills.",
  "Practice makes perfect. The more you type, the faster and more accurate you will become.",
  "Artificial intelligence is transforming industries and creating new opportunities worldwide."
]

export default function WPMTest() {
  const [testActive, setTestActive] = useState(false)
  const [testText, setTestText] = useState('')
  const [userInput, setUserInput] = useState('')
  const [startTime, setStartTime] = useState<number | null>(null)
  const [endTime, setEndTime] = useState<number | null>(null)
  const [wpm, setWpm] = useState(0)
  const [accuracy, setAccuracy] = useState(100)
  const [countdown, setCountdown] = useState<number | null>(null)
  const [results, setResults] = useState<any>(null)
  const [bestWpm, setBestWpm] = useState(0)
  
  const inputRef = useRef<HTMLTextAreaElement>(null)
  
  useEffect(() => {
    const saved = localStorage.getItem('bestWpm')
    if (saved) setBestWpm(Number(saved))
  }, [])
  
  const startTest = () => {
    // Select random text
    const text = TEST_TEXTS[Math.floor(Math.random() * TEST_TEXTS.length)]
    setTestText(text)
    setUserInput('')
    setResults(null)
    setCountdown(3)
    
    // Countdown
    let count = 3
    const countdownInterval = setInterval(() => {
      count--
      setCountdown(count)
      if (count === 0) {
        clearInterval(countdownInterval)
        setCountdown(null)
        setTestActive(true)
        setStartTime(Date.now())
        inputRef.current?.focus()
      }
    }, 1000)
  }
  
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const input = e.target.value
    setUserInput(input)
    
    // Calculate live WPM
    if (startTime) {
      const timeElapsed = (Date.now() - startTime) / 1000 / 60 // in minutes
      const words = input.trim().split(/\s+/).length
      const currentWpm = Math.round(words / timeElapsed)
      setWpm(currentWpm)
    }
    
    // Check if test complete
    if (input.length >= testText.length) {
      endTest()
    }
  }
  
  const endTest = async () => {
    if (!startTime) return
    
    const endTime = Date.now()
    setEndTime(endTime)
    setTestActive(false)
    
    const timeElapsed = (endTime - startTime) / 1000
    
    try {
      const response = await axios.post(`${API_URL}/api/wpm-test/calculate`, {
        test_text: testText,
        user_input: userInput,
        time_taken: timeElapsed
      })
      
      setResults(response.data)
      setWpm(response.data.wpm)
      setAccuracy(response.data.accuracy)
      
      // Update best WPM
      if (response.data.wpm > bestWpm) {
        setBestWpm(response.data.wpm)
        localStorage.setItem('bestWpm', response.data.wpm.toString())
        toast.success('New personal record!')
      }
    } catch (error) {
      console.error('Failed to calculate results:', error)
    }
  }
  
  const resetTest = () => {
    setTestActive(false)
    setTestText('')
    setUserInput('')
    setStartTime(null)
    setEndTime(null)
    setWpm(0)
    setAccuracy(100)
    setResults(null)
    setCountdown(null)
  }
  
  const getAccuracyColor = (acc: number) => {
    if (acc >= 95) return 'text-green-400'
    if (acc >= 90) return 'text-yellow-400'
    if (acc >= 80) return 'text-orange-400'
    return 'text-red-400'
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 rounded-2xl p-6 backdrop-blur-sm border border-blue-500/20">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <Zap className="w-8 h-8 text-blue-400" />
              <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                WPM Speed Test
              </h2>
            </div>
            <p className="text-gray-400">Test your typing speed and accuracy</p>
          </div>
          
          <div className="text-center">
            <div className="text-xs text-gray-400 mb-1">Personal Best</div>
            <div className="text-3xl font-bold text-yellow-400 flex items-center gap-2">
              <Trophy className="w-6 h-6" />
              {bestWpm} WPM
            </div>
          </div>
        </div>
      </div>
      
      {/* Countdown */}
      <AnimatePresence>
        {countdown !== null && countdown > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none"
          >
            <div className="bg-black/80 backdrop-blur-xl rounded-full w-32 h-32 flex items-center justify-center">
              <motion.div
                key={countdown}
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 1.5, opacity: 0 }}
                transition={{ duration: 0.5 }}
                className="text-6xl font-bold text-blue-400"
              >
                {countdown}
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Test Area */}
      {!results ? (
        <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
          {testText && (
            <>
              {/* Test Text Display */}
              <div className="mb-4 p-4 bg-gray-800/50 rounded-lg">
                <h3 className="text-sm font-semibold mb-2 text-gray-400">Type this text:</h3>
                <div className="text-lg leading-relaxed font-mono">
                  {testText.split('').map((char, index) => {
                    const userChar = userInput[index]
                    let className = 'text-gray-400'
                    if (userChar !== undefined) {
                      className = userChar === char ? 'text-green-400' : 'text-red-400 bg-red-500/20'
                    }
                    return (
                      <span key={index} className={className}>
                        {char}
                      </span>
                    )
                  })}
                </div>
              </div>
              
              {/* Input Area */}
              <textarea
                ref={inputRef}
                value={userInput}
                onChange={handleInputChange}
                disabled={!testActive}
                placeholder={testActive ? "Start typing..." : "Click 'Start Test' to begin"}
                className="w-full h-32 bg-gray-800/50 rounded-lg p-4 text-white placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all font-mono"
                spellCheck={false}
              />
              
              {/* Live Stats */}
              {testActive && (
                <div className="mt-4 flex justify-between items-center">
                  <div className="flex gap-6">
                    <div>
                      <span className="text-xs text-gray-400">Live WPM</span>
                      <span className="ml-2 text-lg font-bold text-blue-400">{wpm}</span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">Progress</span>
                      <span className="ml-2 text-lg font-bold text-purple-400">
                        {Math.round((userInput.length / testText.length) * 100)}%
                      </span>
                    </div>
                  </div>
                  
                  <button
                    onClick={endTest}
                    className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                  >
                    End Test
                  </button>
                </div>
              )}
            </>
          )}
          
          {/* Start Button */}
          {!testText && (
            <div className="text-center py-12">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={startTest}
                className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl font-semibold text-lg flex items-center gap-3 mx-auto shadow-lg hover:shadow-blue-500/25 transition-all"
              >
                <Timer className="w-6 h-6" />
                Start Speed Test
              </motion.button>
              <p className="text-sm text-gray-400 mt-4">
                Test your typing speed with a random text passage
              </p>
            </div>
          )}
        </div>
      ) : (
        /* Results */
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50"
        >
          <h3 className="text-xl font-semibold mb-6 text-center">Test Results</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800/50 rounded-lg p-4 text-center">
              <Zap className="w-8 h-8 mx-auto mb-2 text-blue-400" />
              <div className="text-2xl font-bold text-blue-400">{results.wpm}</div>
              <div className="text-xs text-gray-400">WPM</div>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-4 text-center">
              <Target className="w-8 h-8 mx-auto mb-2 text-green-400" />
              <div className={`text-2xl font-bold text-white ${getAccuracyColor(results.accuracy)}`}>
                {results.accuracy.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-400">Accuracy</div>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-4 text-center">
              <Timer className="w-8 h-8 mx-auto mb-2 text-purple-400" />
              <div className="text-2xl font-bold text-purple-400">
                {Math.round(results.time_taken)}s
              </div>
              <div className="text-xs text-gray-400">Time</div>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-4 text-center">
              <TrendingUp className="w-8 h-8 mx-auto mb-2 text-yellow-400" />
              <div className="text-2xl font-bold text-yellow-400">
                {results.words_typed}
              </div>
              <div className="text-xs text-gray-400">Words</div>
            </div>
          </div>
          
          {/* Performance Analysis */}
          <div className="bg-gray-800/30 rounded-lg p-4 mb-6">
            <h4 className="text-sm font-semibold mb-2 text-gray-400">Performance Analysis</h4>
            <div className="space-y-2 text-sm">
              {results.wpm >= 60 && (
                <p className="text-green-400">✓ Excellent typing speed!</p>
              )}
              {results.wpm >= 40 && results.wpm < 60 && (
                <p className="text-yellow-400">✓ Good typing speed, keep practicing!</p>
              )}
              {results.wpm < 40 && (
                <p className="text-orange-400">→ Practice regularly to improve speed</p>
              )}
              {results.accuracy >= 95 && (
                <p className="text-green-400">✓ Outstanding accuracy!</p>
              )}
              {results.accuracy < 95 && results.accuracy >= 90 && (
                <p className="text-yellow-400">✓ Good accuracy, minor improvements needed</p>
              )}
              {results.accuracy < 90 && (
                <p className="text-orange-400">→ Focus on accuracy over speed</p>
              )}
            </div>
          </div>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={resetTest}
            className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg font-medium flex items-center justify-center gap-2"
          >
            <RotateCcw className="w-5 h-5" />
            Try Again
          </motion.button>
        </motion.div>
      )}
    </div>
  )
}