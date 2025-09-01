'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'
import { 
  UserIcon, ActivityIcon, AlertTriangleIcon, TrendingUpIcon,
  DatabaseIcon, DownloadIcon, RefreshCwIcon, SearchIcon,
  BarChart3Icon, PieChartIcon, CalendarIcon, ClockIcon,
  UsersIcon, MousePointerClickIcon, ZapIcon, BugIcon
} from 'lucide-react'

interface TelemetryStats {
  total_users: number
  total_sessions: number
  total_actions: number
  total_errors: number
  most_used_features: Record<string, number>
  common_errors: Record<string, number>
  data_points: number
}

interface TelemetryEntry {
  userId: string
  sessionId: string
  systemInfo: any
  actions: any[]
  errors: any[]
  featureUsage: any[]
  performanceMetrics: any[]
  sessionDuration: number
  timestamp: string
  received_at: string
}

export default function AdminDashboard() {
  const [isAuthorized, setIsAuthorized] = useState(false)
  const [password, setPassword] = useState('')
  const [stats, setStats] = useState<TelemetryStats | null>(null)
  const [recentEntries, setRecentEntries] = useState<TelemetryEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedUser, setSelectedUser] = useState<string | null>(null)
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null)

  // Check if already authorized
  useEffect(() => {
    const auth = sessionStorage.getItem('adminAuth')
    if (auth === 'true') {
      setIsAuthorized(true)
      loadData()
    }
  }, [])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (isAuthorized) {
      const interval = setInterval(() => {
        loadData()
      }, 30000)
      setRefreshInterval(interval)
      
      return () => {
        if (interval) clearInterval(interval)
      }
    }
  }, [isAuthorized])

  const handleAuth = () => {
    // Check password against what you set in Render
    if (password === 'slywriter-admin-brice') {
      setIsAuthorized(true)
      sessionStorage.setItem('adminAuth', 'true')
      sessionStorage.setItem('adminPassword', password)
      loadData()
    } else {
      alert('Invalid password')
    }
  }

  const loadData = async () => {
    setLoading(true)
    try {
      // Load stats from cloud
      const statsRes = await axios.get('https://slywriterapp.onrender.com/api/admin/telemetry/stats', {
        headers: {
          'X-Admin-Password': sessionStorage.getItem('adminPassword') || password
        }
      })
      setStats(statsRes.data)
      
      // Load recent entries from cloud
      const entriesRes = await axios.get('https://slywriterapp.onrender.com/api/admin/telemetry?limit=50', {
        headers: {
          'X-Admin-Password': sessionStorage.getItem('adminPassword') || password
        }
      })
      setRecentEntries(entriesRes.data.recent_entries || [])
    } catch (error: any) {
      console.error('Failed to load telemetry data:', error)
      if (error?.response?.status === 401) {
        setIsAuthorized(false)
        sessionStorage.removeItem('adminAuth')
      }
    }
    setLoading(false)
  }

  const exportData = async () => {
    try {
      const res = await axios.get('https://slywriterapp.onrender.com/api/admin/telemetry/export', {
        headers: {
          'X-Admin-Password': sessionStorage.getItem('adminPassword') || password
        }
      })
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `telemetry_export_${new Date().toISOString()}.json`
      a.click()
    } catch (error) {
      console.error('Failed to export data:', error)
    }
  }

  if (!isAuthorized) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
        <div className="bg-gray-800 rounded-xl p-8 max-w-md w-full">
          <h2 className="text-2xl font-bold text-white mb-4">Admin Access Required</h2>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAuth()}
            placeholder="Enter admin password"
            className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg mb-4"
          />
          <button
            onClick={handleAuth}
            className="w-full py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold"
          >
            Access Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Beta Telemetry Dashboard</h1>
          <p className="text-gray-400 mt-1">Real-time usage data from beta testers</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg flex items-center gap-2"
          >
            <RefreshCwIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={exportData}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg flex items-center gap-2"
          >
            <DownloadIcon className="w-4 h-4" />
            Export All
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-800 rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <UsersIcon className="w-8 h-8 text-blue-400" />
              <span className="text-3xl font-bold text-white">{stats.total_users}</span>
            </div>
            <h3 className="text-gray-400 text-sm">Total Users</h3>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gray-800 rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <ActivityIcon className="w-8 h-8 text-green-400" />
              <span className="text-3xl font-bold text-white">{stats.total_sessions}</span>
            </div>
            <h3 className="text-gray-400 text-sm">Total Sessions</h3>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gray-800 rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <MousePointerClickIcon className="w-8 h-8 text-purple-400" />
              <span className="text-3xl font-bold text-white">{stats.total_actions}</span>
            </div>
            <h3 className="text-gray-400 text-sm">User Actions</h3>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gray-800 rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <BugIcon className="w-8 h-8 text-red-400" />
              <span className="text-3xl font-bold text-white">{stats.total_errors}</span>
            </div>
            <h3 className="text-gray-400 text-sm">Errors Tracked</h3>
          </motion.div>
        </div>
      )}

      {/* Feature Usage & Errors */}
      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Most Used Features */}
          <div className="bg-gray-800 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <TrendingUpIcon className="w-5 h-5 text-green-400" />
              Most Used Features
            </h3>
            <div className="space-y-3">
              {Object.entries(stats.most_used_features).slice(0, 5).map(([feature, count]) => (
                <div key={feature} className="flex items-center justify-between">
                  <span className="text-gray-300">{feature}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${(count / Object.values(stats.most_used_features)[0]) * 100}%` }}
                      />
                    </div>
                    <span className="text-gray-400 text-sm w-12 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Common Errors */}
          <div className="bg-gray-800 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <AlertTriangleIcon className="w-5 h-5 text-red-400" />
              Common Errors
            </h3>
            <div className="space-y-3">
              {Object.entries(stats.common_errors).slice(0, 5).map(([error, count]) => (
                <div key={error} className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm truncate flex-1">{error}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-red-500 h-2 rounded-full"
                        style={{ width: `${(count / Object.values(stats.common_errors)[0]) * 100}%` }}
                      />
                    </div>
                    <span className="text-gray-400 text-sm w-12 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="bg-gray-800 rounded-xl p-6">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <ClockIcon className="w-5 h-5 text-blue-400" />
          Recent Activity
        </h3>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {recentEntries.map((entry, index) => (
            <div 
              key={`${entry.userId}-${entry.sessionId}-${index}`}
              className="bg-gray-700/50 rounded-lg p-3 hover:bg-gray-700 transition-colors cursor-pointer"
              onClick={() => setSelectedUser(selectedUser === entry.userId ? null : entry.userId)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <UserIcon className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-300 font-mono">{entry.userId.substring(0, 20)}...</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>{entry.actions?.length || 0} actions</span>
                  <span>{entry.errors?.length || 0} errors</span>
                  <span>{Math.round((entry.sessionDuration || 0) / 1000 / 60)}m</span>
                  <span>{new Date(entry.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
              
              {selectedUser === entry.userId && (
                <div className="mt-3 pt-3 border-t border-gray-600 text-xs text-gray-400">
                  <div>Platform: {entry.systemInfo?.platform}</div>
                  <div>Screen: {entry.systemInfo?.screenResolution}</div>
                  <div>Last Action: {entry.actions?.[entry.actions.length - 1]?.action}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Data Points Counter */}
      <div className="mt-6 text-center text-gray-500 text-sm">
        <DatabaseIcon className="w-4 h-4 inline mr-2" />
        {stats?.data_points || 0} data points collected • Auto-refreshing every 30s
      </div>
    </div>
  )
}