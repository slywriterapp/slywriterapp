'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, Clock, Keyboard, Target, Award, Calendar, Activity, Zap, BarChart3, PieChart } from 'lucide-react'
import { RENDER_API_URL } from '../config/api'

interface DailyStats {
  date: string
  words: number
  characters: number
  sessions: number
  avgSpeed: number
}

interface Achievement {
  id: string
  name: string
  description: string
  icon: any
  unlocked: boolean
  progress: number
  target: number
}

export default function StatisticsTab() {
  const [totalWords, setTotalWords] = useState(0)
  const [totalCharacters, setTotalCharacters] = useState(0)
  const [totalSessions, setTotalSessions] = useState(0)
  const [avgSpeed, setAvgSpeed] = useState(0)
  const [dailyGoal, setDailyGoal] = useState(1000)
  const [dailyProgress, setDailyProgress] = useState(0)
  const [weeklyStats, setWeeklyStats] = useState<DailyStats[]>([])
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [todayWords, setTodayWords] = useState(0)
  const [todaySessions, setTodaySessions] = useState(0)
  const [bestWpm, setBestWpm] = useState(0)
  const [timeSaved, setTimeSaved] = useState(0)
  const [trends, setTrends] = useState({
    words: 0,
    characters: 0,
    sessions: 0,
    wpm: 0
  })

  // Load and update stats from PostgreSQL
  const loadStats = async () => {
    try {
      // Get auth token from localStorage
      const token = localStorage.getItem('auth_token')
      if (!token) {
        console.log('No auth token found')
        return
      }

      // Fetch stats from PostgreSQL backend
      const response = await fetch(`${RENDER_API_URL}/api/stats/user`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success && data.stats) {
          const stats = data.stats
          setTotalWords(stats.totalWords || 0)
          setTotalCharacters(stats.totalCharacters || 0)
          setTotalSessions(stats.totalSessions || 0)
          setAvgSpeed(stats.avgSpeed || 0)
          setTodayWords(stats.todayWords || 0)
          setTodaySessions(stats.todaySessions || 0)
          setBestWpm(stats.bestWpm || 0)

          // Set daily progress
          setDailyProgress(stats.todayWords || 0)

          // Calculate trends (simplified for now - backend can be enhanced later)
          setTrends({
            words: 0,
            characters: 0,
            sessions: 0,
            wpm: 0
          })
        }
      }
    } catch (error) {
      console.error('Failed to load stats from PostgreSQL:', error)
    }
  }
  
  useEffect(() => {
    loadStats()
    
    // Refresh stats every 2 seconds for live updates
    const interval = setInterval(loadStats, 2000)
    
    // Listen for typing completion events
    const handleTypingComplete = (event: CustomEvent) => {
      const { words, characters, wpm } = event.detail
      const currentStats = JSON.parse(localStorage.getItem('slywriter-stats') || '{}')
      
      // Update stats
      const newStats = {
        ...currentStats,
        totalWords: (currentStats.totalWords || 0) + words,
        totalCharacters: (currentStats.totalCharacters || 0) + characters,
        totalSessions: (currentStats.totalSessions || 0) + 1,
        todayWords: (currentStats.todayWords || 0) + words,
        todaySessions: (currentStats.todaySessions || 0) + 1,
        bestWpm: Math.max(currentStats.bestWpm || 0, wpm),
        avgSpeed: Math.round(((currentStats.avgSpeed || 0) * (currentStats.totalSessions || 0) + wpm) / ((currentStats.totalSessions || 0) + 1)),
        timeSaved: (currentStats.timeSaved || 0) + Math.round(words / 40) // Assuming manual typing is 40 WPM
      }
      
      localStorage.setItem('slywriter-stats', JSON.stringify(newStats))
      
      // Also update daily stats for weekly chart
      const today = new Date().toISOString().split('T')[0]
      const dailyStats = JSON.parse(localStorage.getItem('slywriter-daily-stats') || '{}')
      
      if (!dailyStats[today]) {
        dailyStats[today] = { words: 0, characters: 0, sessions: 0, totalWpm: 0 }
      }
      
      dailyStats[today].words = (dailyStats[today].words || 0) + words
      dailyStats[today].characters = (dailyStats[today].characters || 0) + characters
      dailyStats[today].sessions = (dailyStats[today].sessions || 0) + 1
      dailyStats[today].totalWpm = (dailyStats[today].totalWpm || 0) + wpm
      dailyStats[today].avgSpeed = Math.round(dailyStats[today].totalWpm / dailyStats[today].sessions)
      
      localStorage.setItem('slywriter-daily-stats', JSON.stringify(dailyStats))
      
      loadStats()
      loadWeeklyStats()
    }
    
    window.addEventListener('typing-complete', handleTypingComplete as EventListener)
    
    // Load real weekly stats from localStorage
    const loadWeeklyStats = () => {
      const today = new Date()
      const weekStats: DailyStats[] = []
      const dailyData = JSON.parse(localStorage.getItem('slywriter-daily-stats') || '{}')
      
      for (let i = 6; i >= 0; i--) {
        const date = new Date(today)
        date.setDate(date.getDate() - i)
        const dateKey = date.toISOString().split('T')[0]
        
        const dayData = dailyData[dateKey] || { words: 0, characters: 0, sessions: 0, avgSpeed: 0 }
        
        weekStats.push({
          date: date.toLocaleDateString('en', { weekday: 'short' }),
          words: dayData.words || 0,
          characters: dayData.characters || 0,
          sessions: dayData.sessions || 0,
          avgSpeed: dayData.avgSpeed || 0,
        })
      }
      setWeeklyStats(weekStats)
    }
    
    loadWeeklyStats()
    
    return () => {
      clearInterval(interval)
      window.removeEventListener('typing-complete', handleTypingComplete as EventListener)
    }

  }, [dailyGoal])

  // Update achievements based on real data
  useEffect(() => {
    setAchievements([
      { id: 'first', name: 'First Automation', description: 'Complete your first typing session', icon: Award, unlocked: totalSessions > 0, progress: totalSessions, target: 1 },
      { id: 'marathon', name: 'Word Master', description: 'Automate 10,000 words', icon: TrendingUp, unlocked: totalWords >= 10000, progress: totalWords, target: 10000 },
      { id: 'daily', name: 'Daily Goal', description: `Type ${dailyGoal} words today`, icon: Target, unlocked: todayWords >= dailyGoal, progress: todayWords, target: dailyGoal },
    ])
  }, [totalWords, totalSessions, todayWords, dailyGoal])

  const StatCard = ({ icon: Icon, label, value, color, trend }: any) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50"
    >
      <div className="flex items-center justify-between mb-4">
        <Icon className={`w-6 h-6 ${color}`} />
        {trend && (
          <span className={`text-xs ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value.toLocaleString()}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </motion.div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 rounded-2xl p-6 backdrop-blur-sm border border-blue-500/20">
        <div className="flex items-center gap-3 mb-3">
          <BarChart3 className="w-8 h-8 text-blue-400" />
          <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Performance Analytics
          </h2>
        </div>
        <p className="text-gray-400">Track your typing progress and achievements</p>
        
        {/* Test Buttons for Development */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-2 flex gap-2">
            <button
              onClick={() => {
                const testEvent = new CustomEvent('typing-complete', {
                  detail: {
                    words: Math.floor(Math.random() * 500) + 100,
                    characters: Math.floor(Math.random() * 2500) + 500,
                    wpm: Math.floor(Math.random() * 50) + 80
                  }
                })
                window.dispatchEvent(testEvent)
              }}
              className="px-3 py-1 bg-purple-500 hover:bg-purple-600 rounded text-sm text-white"
            >
              Simulate Typing
            </button>
            <button
              onClick={() => {
                const stats = JSON.parse(localStorage.getItem('slywriter-stats') || '{}')
                stats.todayWords = 0
                stats.todaySessions = 0
                localStorage.setItem('slywriter-stats', JSON.stringify(stats))
                
                // Also reset today's daily stats
                const dailyStats = JSON.parse(localStorage.getItem('slywriter-daily-stats') || '{}')
                const today = new Date().toISOString().split('T')[0]
                delete dailyStats[today]
                localStorage.setItem('slywriter-daily-stats', JSON.stringify(dailyStats))
                
                loadStats()
              }}
              className="px-3 py-1 bg-red-500 hover:bg-red-600 rounded text-sm text-white"
            >
              Reset Today
            </button>
          </div>
        )}
      </div>

      {/* Daily Goal */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Target className="w-5 h-5 text-yellow-400" />
              Daily Goal
            </h3>
            <p className="text-sm text-gray-400 mt-1">Keep your streak going!</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-purple-400">
              {todayWords} / {dailyGoal}
            </div>
            <div className="text-sm text-gray-400">words today</div>
          </div>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-3">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min((todayWords / dailyGoal) * 100, 100)}%` }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="bg-gradient-to-r from-purple-600 to-pink-600 h-3 rounded-full relative"
          >
            <div className="absolute right-0 top-0 h-3 w-3 bg-gray-900 rounded-full animate-pulse" />
          </motion.div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={Keyboard} label="Total Words" value={totalWords} color="text-blue-400" trend={trends.words} />
        <StatCard icon={Activity} label="Characters" value={totalCharacters} color="text-green-400" trend={trends.characters} />
        <StatCard icon={Clock} label="Sessions" value={totalSessions} color="text-yellow-400" trend={trends.sessions} />
        <StatCard icon={Zap} label="Avg WPM" value={avgSpeed} color="text-purple-400" trend={trends.wpm} />
      </div>

      {/* Weekly Chart */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <PieChart className="w-5 h-5 text-blue-400" />
          Weekly Activity
        </h3>
        <div className="h-48 flex items-end justify-between gap-2">
          {weeklyStats.map((day, index) => {
            const maxWords = Math.max(...weeklyStats.map(d => d.words), 100);
            const heightPercent = (day.words / maxWords) * 100;
            
            return (
              <div key={index} className="flex-1 flex flex-col items-center justify-end h-full">
                <div className="w-full flex flex-col items-center justify-end h-full">
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${heightPercent}%` }}
                    transition={{ delay: index * 0.1, duration: 0.5, ease: "easeOut" }}
                    className="w-full bg-gradient-to-t from-purple-600 to-pink-600 rounded-t-lg relative group min-h-[2px]"
                    style={{ maxWidth: '40px' }}
                  >
                    <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-800 px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                      <div className="text-purple-400 font-semibold">{day.words}</div>
                      <div className="text-gray-400 text-[10px]">words</div>
                    </div>
                  </motion.div>
                </div>
                <div className="mt-2 text-center">
                  <div className="text-xs text-gray-400">{day.date}</div>
                  {day.sessions > 0 && (
                    <div className="text-[10px] text-gray-500">{day.sessions} sessions</div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
        {/* Chart Legend */}
        <div className="mt-4 flex justify-center gap-6 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded"></div>
            <span className="text-gray-400">Words typed</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-purple-400 font-semibold">{weeklyStats.reduce((sum, day) => sum + day.words, 0).toLocaleString()}</span>
            <span className="text-gray-400">Total this week</span>
          </div>
        </div>
      </div>

      {/* Achievements */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Award className="w-5 h-5 text-yellow-400" />
          Achievements
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {achievements.map((achievement) => {
            const Icon = achievement.icon
            return (
              <motion.div
                key={achievement.id}
                whileHover={{ scale: 1.02 }}
                className={`p-4 rounded-lg border ${
                  achievement.unlocked
                    ? 'bg-gradient-to-r from-yellow-900/20 to-orange-900/20 border-yellow-500/50'
                    : 'bg-gray-800/30 border-gray-700'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${
                    achievement.unlocked ? 'bg-yellow-500/20' : 'bg-gray-700/50'
                  }`}>
                    <Icon className={`w-6 h-6 ${
                      achievement.unlocked ? 'text-yellow-400' : 'text-gray-400'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium mb-1">{achievement.name}</div>
                    <div className="text-xs text-gray-400 mb-2">{achievement.description}</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-800 rounded-full h-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.min((achievement.progress / achievement.target) * 100, 100)}%` }}
                          className={`h-2 rounded-full ${
                            achievement.unlocked
                              ? 'bg-gradient-to-r from-yellow-400 to-orange-400'
                              : 'bg-gray-600 bg-gray-800'
                          }`}
                        />
                      </div>
                      <span className="text-xs text-gray-400">
                        {achievement.progress}/{achievement.target}
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Export Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="w-full bg-gradient-to-r from-blue-600 to-purple-600 py-3 rounded-lg font-medium flex items-center justify-center gap-2"
      >
        <TrendingUp className="w-5 h-5" />
        Export Full Report
      </motion.button>
    </div>
  )
}