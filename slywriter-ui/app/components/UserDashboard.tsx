'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  User, Mail, Calendar, Shield, Zap, TrendingUp, 
  Award, Users, Copy, Check, AlertCircle, Sparkles,
  CreditCard, ChevronRight, BarChart3, Clock, Gift,
  Star, Crown, Rocket, Target, Share2, RefreshCw
} from 'lucide-react'
import { toast } from 'react-hot-toast'

interface DashboardData {
  user: {
    name: string
    email: string
    user_id: string
    joined: string
    verified: boolean
  }
  plan: {
    name: string
    words_limit: number
    words_used: number
    words_remaining: number
    usage_percentage: number
    reset_date: string
    features: {
      ai_generation: boolean
      humanizer: boolean
      premium_typing: boolean
      learning_hub: boolean
      missions: boolean
      unlimited_profiles: boolean
      priority_support: boolean
      advanced_analytics: boolean
    }
  }
  referrals: {
    code: string
    successful: number
    pending: number
    bonus_words: number
    share_link: string
  }
  stats: {
    total_generations: number
    total_typing_sessions: number
    favorite_profile: string
    avg_wpm: number
  }
}

export default function UserDashboard({ onClose }: { onClose: () => void }) {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'plan' | 'referrals' | 'stats'>('overview')

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://slywriterapp.onrender.com'

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        toast.error('Please login to view dashboard')
        onClose()
        return
      }

      const response = await fetch(`${API_URL}/api/user-dashboard`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      const data = await response.json()
      if (data.success) {
        setDashboardData(data.dashboard)
      } else {
        toast.error('Failed to load dashboard')
      }
    } catch (error) {
      console.error('Dashboard error:', error)
      toast.error('Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  const copyReferralCode = () => {
    if (dashboardData?.referrals.code) {
      navigator.clipboard.writeText(dashboardData.referrals.share_link)
      setCopied(true)
      toast.success('Referral link copied!')
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const getPlanColor = (plan: string) => {
    switch(plan) {
      case 'premium': return 'from-purple-500 to-pink-500'
      case 'pro': return 'from-blue-500 to-cyan-500'
      case 'basic': return 'from-green-500 to-emerald-500'
      default: return 'from-gray-500 to-gray-600'
    }
  }

  const getPlanIcon = (plan: string) => {
    switch(plan) {
      case 'premium': return <Crown className="w-6 h-6" />
      case 'pro': return <Rocket className="w-6 h-6" />
      case 'basic': return <Star className="w-6 h-6" />
      default: return <Zap className="w-6 h-6" />
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-gray-900 rounded-2xl p-8 text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (!dashboardData) return null

  const isLowOnWords = dashboardData.plan.usage_percentage > 80
  const isOutOfWords = dashboardData.plan.words_remaining <= 0

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden border border-purple-500/20"
        >
          {/* Header */}
          <div className={`bg-gradient-to-r ${getPlanColor(dashboardData.plan.name)} p-6`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
                  {getPlanIcon(dashboardData.plan.name)}
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">
                    {dashboardData.user.name || 'User'} Dashboard
                  </h2>
                  <p className="text-white/80 text-sm">
                    {dashboardData.plan.name.charAt(0).toUpperCase() + dashboardData.plan.name.slice(1)} Plan
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-white/80 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-800">
            {['overview', 'plan', 'referrals', 'stats'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'text-purple-400 border-b-2 border-purple-400'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[60vh]">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Word Usage Card */}
                <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">Word Usage</h3>
                    {isOutOfWords && (
                      <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm flex items-center gap-1">
                        <AlertCircle className="w-4 h-4" />
                        Out of words
                      </span>
                    )}
                    {isLowOnWords && !isOutOfWords && (
                      <span className="px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-full text-sm flex items-center gap-1">
                        <AlertCircle className="w-4 h-4" />
                        Running low
                      </span>
                    )}
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Words Used</span>
                      <span className="text-white font-medium">
                        {dashboardData.plan.words_used.toLocaleString()} / {dashboardData.plan.words_limit.toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(100, dashboardData.plan.usage_percentage)}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className={`h-full rounded-full ${
                          isOutOfWords ? 'bg-red-500' :
                          isLowOnWords ? 'bg-yellow-500' :
                          'bg-gradient-to-r from-purple-500 to-pink-500'
                        }`}
                      />
                    </div>
                    
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Words Remaining</span>
                      <span className={`font-medium ${
                        isOutOfWords ? 'text-red-400' :
                        isLowOnWords ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        {dashboardData.plan.words_remaining.toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-2 text-sm text-gray-400">
                      <Clock className="w-4 h-4" />
                      <span>Resets on {formatDate(dashboardData.plan.reset_date)}</span>
                    </div>
                  </div>

                  {isOutOfWords && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-4 p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg"
                    >
                      <p className="text-purple-300 text-sm mb-3">
                        💡 Get more words by referring friends! Each successful referral gives you <strong>500 bonus words</strong>.
                      </p>
                      <button
                        onClick={() => setActiveTab('referrals')}
                        className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600 transition-colors"
                      >
                        Share & Earn Words
                      </button>
                    </motion.div>
                  )}
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-500/20 rounded-lg">
                        <Sparkles className="w-5 h-5 text-blue-400" />
                      </div>
                      <div>
                        <p className="text-gray-400 text-xs">AI Generations</p>
                        <p className="text-white font-semibold">
                          {dashboardData.stats.total_generations}
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-green-500/20 rounded-lg">
                        <Target className="w-5 h-5 text-green-400" />
                      </div>
                      <div>
                        <p className="text-gray-400 text-xs">Typing Sessions</p>
                        <p className="text-white font-semibold">
                          {dashboardData.stats.total_typing_sessions}
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-purple-500/20 rounded-lg">
                        <Users className="w-5 h-5 text-purple-400" />
                      </div>
                      <div>
                        <p className="text-gray-400 text-xs">Referrals</p>
                        <p className="text-white font-semibold">
                          {dashboardData.referrals.successful}
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-yellow-500/20 rounded-lg">
                        <Gift className="w-5 h-5 text-yellow-400" />
                      </div>
                      <div>
                        <p className="text-gray-400 text-xs">Bonus Words</p>
                        <p className="text-white font-semibold">
                          {dashboardData.referrals.bonus_words}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'plan' && (
              <div className="space-y-6">
                {/* Plan Details */}
                <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Plan Features</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(dashboardData.plan.features).map(([feature, enabled]) => (
                      <div key={feature} className="flex items-center gap-3">
                        <div className={`p-1 rounded-full ${enabled ? 'bg-green-500/20' : 'bg-gray-700'}`}>
                          {enabled ? (
                            <Check className="w-4 h-4 text-green-400" />
                          ) : (
                            <span className="w-4 h-4 block text-gray-500 text-center">✕</span>
                          )}
                        </div>
                        <span className={`text-sm ${enabled ? 'text-white' : 'text-gray-500'}`}>
                          {feature.split('_').map(word => 
                            word.charAt(0).toUpperCase() + word.slice(1)
                          ).join(' ')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {dashboardData.plan.name === 'free' && (
                  <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-xl p-6 border border-purple-500/30">
                    <h3 className="text-lg font-semibold text-white mb-2">Upgrade Your Plan</h3>
                    <p className="text-gray-300 text-sm mb-4">
                      Unlock premium features like the Humanizer, unlimited profiles, and more words!
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                        <h4 className="text-green-400 font-semibold mb-2">Basic</h4>
                        <p className="text-2xl font-bold text-white mb-1">$9.99<span className="text-sm text-gray-400">/mo</span></p>
                        <p className="text-gray-400 text-xs">10,000 words/month</p>
                      </div>
                      <div className="bg-gray-900/50 rounded-lg p-4 border border-blue-500/50">
                        <h4 className="text-blue-400 font-semibold mb-2">Pro</h4>
                        <p className="text-2xl font-bold text-white mb-1">$19.99<span className="text-sm text-gray-400">/mo</span></p>
                        <p className="text-gray-400 text-xs">20,000 words/month</p>
                      </div>
                      <div className="bg-gray-900/50 rounded-lg p-4 border border-purple-500/50">
                        <h4 className="text-purple-400 font-semibold mb-2">Premium</h4>
                        <p className="text-2xl font-bold text-white mb-1">$39.99<span className="text-sm text-gray-400">/mo</span></p>
                        <p className="text-gray-400 text-xs">50,000 words/month</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'referrals' && (
              <div className="space-y-6">
                <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Your Referral Program</h3>
                  
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4 mb-6">
                    <p className="text-purple-300 text-sm mb-3">
                      Share your referral link and earn <strong>500 bonus words</strong> for each friend who signs up!
                    </p>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={dashboardData.referrals.share_link}
                        readOnly
                        className="flex-1 px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white text-sm"
                      />
                      <button
                        onClick={copyReferralCode}
                        className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors flex items-center gap-2"
                      >
                        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                        {copied ? 'Copied!' : 'Copy'}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="text-center">
                      <p className="text-3xl font-bold text-white">{dashboardData.referrals.successful}</p>
                      <p className="text-gray-400 text-sm">Successful</p>
                    </div>
                    <div className="text-center">
                      <p className="text-3xl font-bold text-yellow-400">{dashboardData.referrals.pending}</p>
                      <p className="text-gray-400 text-sm">Pending</p>
                    </div>
                    <div className="text-center">
                      <p className="text-3xl font-bold text-green-400">{dashboardData.referrals.bonus_words}</p>
                      <p className="text-gray-400 text-sm">Words Earned</p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="text-white font-medium">Share on Social Media</h4>
                    <div className="flex gap-3">
                      <button className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm">
                        Twitter
                      </button>
                      <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm">
                        Facebook
                      </button>
                      <button className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm">
                        WhatsApp
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'stats' && (
              <div className="space-y-6">
                <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Your Statistics</h3>
                  
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <p className="text-gray-400 text-sm mb-2">Average WPM</p>
                      <p className="text-3xl font-bold text-white">{dashboardData.stats.avg_wpm}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm mb-2">Favorite Profile</p>
                      <p className="text-3xl font-bold text-white">{dashboardData.stats.favorite_profile}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm mb-2">Total Generations</p>
                      <p className="text-3xl font-bold text-purple-400">{dashboardData.stats.total_generations}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm mb-2">Typing Sessions</p>
                      <p className="text-3xl font-bold text-green-400">{dashboardData.stats.total_typing_sessions}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Account Information</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Email</span>
                      <span className="text-white">{dashboardData.user.email}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">User ID</span>
                      <span className="text-white font-mono text-sm">{dashboardData.user.user_id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Member Since</span>
                      <span className="text-white">{formatDate(dashboardData.user.joined)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Email Verified</span>
                      <span className={dashboardData.user.verified ? 'text-green-400' : 'text-yellow-400'}>
                        {dashboardData.user.verified ? 'Verified' : 'Pending'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}