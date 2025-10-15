'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import axios from 'axios'
import Cookies from 'js-cookie'
import toast from 'react-hot-toast'

interface User {
  email: string
  name?: string
  picture?: string
  plan?: string
  referralCode?: string
}

interface UsageLimits {
  word_limit: number
  word_limit_display: string
  words_used: number
  words_remaining: number | string
  humanizer_limit: number
  humanizer_limit_display: string
  humanizer_uses: number
  humanizer_remaining: number | string
  ai_gen_limit: number
  ai_gen_limit_display: string
  ai_gen_uses: number
  ai_gen_remaining: number | string
  week_start_date: string
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isPremium: boolean
  canType: boolean
  wordsRemaining: number
  usageLimits: UsageLimits | null
  canUseHumanizer: boolean
  canUseAIGen: boolean
  login: (googleToken: string) => Promise<void>
  logout: () => Promise<void>
  updateUserPlan: (plan: string) => void
  checkAuth: () => Promise<void>
  refreshUsage: () => Promise<void>
  trackWordUsage: (words: number) => Promise<void>
  trackHumanizerUsage: () => Promise<void>
  trackAIGenUsage: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Use local server in development, Render in production
// Dynamically determine API URL based on environment
const getApiUrl = () => {
  if (typeof window === 'undefined') {
    // Server-side rendering
    return process.env.NEXT_PUBLIC_API_URL || 'https://slywriterapp.onrender.com'
  }
  // Client-side: use local for localhost development, Render for production
  return window.location.hostname === 'localhost' 
    ? 'http://localhost:5000' 
    : 'https://slywriterapp.onrender.com'
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isPremium, setIsPremium] = useState(false)
  const [wordsRemaining, setWordsRemaining] = useState(4000)
  const [usageLimits, setUsageLimits] = useState<UsageLimits | null>(null)

  useEffect(() => {
    checkAuth()
  }, [])

  // Check for weekly reset on mount and periodically
  useEffect(() => {
    if (user) {
      checkWeeklyReset()
      // Check for reset every hour
      const interval = setInterval(checkWeeklyReset, 60 * 60 * 1000)
      return () => clearInterval(interval)
    }
  }, [user])

  // Periodically check for plan changes
  useEffect(() => {
    if (user?.email) {
      // Check for plan updates every 2 minutes
      const interval = setInterval(async () => {
        await checkPlanUpdate()
      }, 2 * 60 * 1000)
      return () => clearInterval(interval)
    }
  }, [user?.email])

  const checkPlanUpdate = async () => {
    if (!user?.email) return

    try {
      const userId = user.email.replace('@', '_').replace(/\./g, '_')
      const response = await axios.get(`${getApiUrl()}/api/auth/user/${userId}`)

      if (response.data && response.data.plan) {
        const currentPlan = user.plan
        const newPlan = response.data.plan

        // Check if plan changed
        if (currentPlan !== newPlan) {
          console.log(`Plan changed from ${currentPlan} to ${newPlan}`)

          // Update user data in state
          const updatedUser = { ...user, plan: newPlan }
          setUser(updatedUser)

          // Update localStorage
          localStorage.setItem('user_data', JSON.stringify(updatedUser))

          // Update premium status
          const isPrem = newPlan === 'premium' || newPlan === 'Premium' ||
                         newPlan === 'pro' || newPlan === 'Pro'
          setIsPremium(isPrem)

          // Refresh usage limits
          await refreshUsage()

          // Show notification
          if (isPrem) {
            toast.success(`🎉 Your account has been upgraded to ${newPlan}!`, { duration: 5000 })
          } else {
            toast.info(`Your plan has been updated to ${newPlan}`, { duration: 4000 })
          }
        }
      }
    } catch (error) {
      console.error('Failed to check plan update:', error)
    }
  }

  const checkWeeklyReset = async () => {
    if (!user?.email) return

    try {
      const userId = user.email.replace('@', '_').replace(/\./g, '_')
      await axios.post(`${getApiUrl()}/api/usage/check-reset?user_id=${userId}`)
      // Refresh usage data after checking for reset
      await refreshUsage()
    } catch (error) {
      console.error('Failed to check weekly reset:', error)
    }
  }

  const checkAuth = async () => {
    try {
      const token = Cookies.get('auth_token') || localStorage.getItem('auth_token')
      const userDataStr = localStorage.getItem('user_data')

      if (!token || !userDataStr) {
        setIsLoading(false)
        return
      }

      // Load user data from localStorage
      const userData = JSON.parse(userDataStr)
      setUser(userData)

      const isPrem = userData.plan === 'premium' || userData.plan === 'Premium' ||
                     userData.plan === 'pro' || userData.plan === 'Pro'
      setIsPremium(isPrem)

      // Load usage limits from localStorage (they're part of userData now)
      setUsageLimits({
        word_limit: userData.word_limit || userData.base_word_limit || 500,
        word_limit_display: userData.word_limit_display || '',
        words_used: userData.words_used || userData.usage || 0,
        words_remaining: userData.words_remaining || 0,
        humanizer_limit: userData.humanizer_limit || 0,
        humanizer_limit_display: userData.humanizer_limit_display || '',
        humanizer_uses: userData.humanizer_uses || userData.humanizer_usage || 0,
        humanizer_remaining: userData.humanizer_remaining || 0,
        ai_gen_limit: userData.ai_gen_limit || 3,
        ai_gen_limit_display: userData.ai_gen_limit_display || '',
        ai_gen_uses: userData.ai_gen_uses || userData.ai_gen_usage || 0,
        ai_gen_remaining: userData.ai_gen_remaining !== undefined ? userData.ai_gen_remaining : 3,
        week_start_date: userData.week_start_date || ''
      })

      // Set words remaining
      const remaining = userData.words_remaining
      setWordsRemaining(typeof remaining === 'number' ? remaining : 999999)
    } catch (error) {
      console.error('Auth check failed:', error)
      Cookies.remove('auth_token')
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_data')
    } finally {
      setIsLoading(false)
    }
  }

  const refreshUsage = async () => {
    if (!user?.email) return

    try {
      const userId = user.email.replace('@', '_').replace(/\./g, '_')
      const response = await axios.get(`${getApiUrl()}/api/auth/user/${userId}`)

      if (response.data) {
        setUsageLimits(response.data)

        // Update words remaining for backwards compatibility
        const remaining = response.data.words_remaining
        setWordsRemaining(typeof remaining === 'number' ? remaining : 999999)

        // Also check if plan changed
        if (response.data.plan && user.plan !== response.data.plan) {
          const updatedUser = { ...user, plan: response.data.plan }
          setUser(updatedUser)
          localStorage.setItem('user_data', JSON.stringify(updatedUser))

          const isPrem = response.data.plan === 'premium' || response.data.plan === 'Premium' ||
                         response.data.plan === 'pro' || response.data.plan === 'Pro'
          setIsPremium(isPrem)
        }
      }
    } catch (error) {
      console.error('Failed to fetch usage limits:', error)
    }
  }

  const trackWordUsage = async (words: number) => {
    if (!user?.email) return

    try {
      const userId = user.email.replace('@', '_').replace(/\./g, '_')
      await axios.post(`${getApiUrl()}/api/usage/track?user_id=${userId}&words=${words}`)
      await refreshUsage()
    } catch (error) {
      console.error('Failed to track word usage:', error)
    }
  }

  const trackHumanizerUsage = async () => {
    if (!user?.email) return

    try {
      const userId = user.email.replace('@', '_').replace(/\./g, '_')
      await axios.post(`${getApiUrl()}/api/usage/track-humanizer?user_id=${userId}`)
      await refreshUsage()
    } catch (error) {
      console.error('Failed to track humanizer usage:', error)
    }
  }

  const trackAIGenUsage = async () => {
    if (!user?.email) return

    try {
      const userId = user.email.replace('@', '_').replace(/\./g, '_')
      await axios.post(`${getApiUrl()}/api/usage/track-ai-gen?user_id=${userId}`)
      await refreshUsage()
    } catch (error) {
      console.error('Failed to track AI gen usage:', error)
    }
  }

  const login = async (googleToken: string) => {
    try {
      const response = await axios.post(`${getApiUrl()}/api/auth/google`, {
        token: googleToken
      })

      if (response.data.access_token) {
        Cookies.set('auth_token', response.data.access_token, { expires: 7 })
        setUser(response.data.user)
        const isPrem = response.data.user.plan === 'premium' || response.data.user.plan === 'Premium' ||
                       response.data.user.plan === 'pro' || response.data.user.plan === 'Pro'
        setIsPremium(isPrem)
        await refreshUsage()
        toast.success('Successfully logged in!')
      }
    } catch (error) {
      console.error('Login failed:', error)
      toast.error('Failed to login')
      throw error
    }
  }

  const logout = async () => {
    try {
      // Call backend logout endpoint to invalidate server-side session
      const token = Cookies.get('auth_token') || localStorage.getItem('auth_token')
      if (token) {
        await axios.post(`${getApiUrl()}/api/auth/logout`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
      }
    } catch (error) {
      console.error('Logout endpoint error:', error)
      // Continue with client-side logout even if server logout fails
    } finally {
      // Clear client-side state
      Cookies.remove('auth_token')
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_data')
      setUser(null)
      setIsPremium(false)
      setWordsRemaining(4000)
      setUsageLimits(null)
      toast.success('Logged out successfully')
    }
  }

  const updateUserPlan = (plan: string) => {
    if (user) {
      setUser({ ...user, plan })
      const isPrem = plan === 'premium' || plan === 'Premium' || plan === 'pro' || plan === 'Pro'
      setIsPremium(isPrem)
      refreshUsage()
    }
  }

  // Compute can-use flags
  const canType = isPremium || wordsRemaining > 0

  const canUseHumanizer = usageLimits
    ? (usageLimits.humanizer_limit === -1 ||
       (typeof usageLimits.humanizer_remaining === 'number' && usageLimits.humanizer_remaining > 0))
    : false

  const canUseAIGen = usageLimits
    ? (usageLimits.ai_gen_limit === -1 ||
       (typeof usageLimits.ai_gen_remaining === 'number' && usageLimits.ai_gen_remaining > 0))
    : false

  return (
    <AuthContext.Provider value={{
      user,
      isLoading,
      isPremium,
      canType,
      wordsRemaining,
      usageLimits,
      canUseHumanizer,
      canUseAIGen,
      login,
      logout,
      updateUserPlan,
      checkAuth,
      refreshUsage,
      trackWordUsage,
      trackHumanizerUsage,
      trackAIGenUsage
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}