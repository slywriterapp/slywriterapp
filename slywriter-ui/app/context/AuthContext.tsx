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

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isPremium: boolean
  login: (googleToken: string) => Promise<void>
  logout: () => void
  updateUserPlan: (plan: string) => void
  checkAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isPremium, setIsPremium] = useState(false)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = Cookies.get('auth_token')
      if (!token) {
        setIsLoading(false)
        return
      }

      const response = await axios.get(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (response.data.user) {
        setUser(response.data.user)
        setIsPremium(response.data.user.plan === 'premium' || response.data.user.plan === 'pro')
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      Cookies.remove('auth_token')
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (googleToken: string) => {
    try {
      const response = await axios.post(`${API_URL}/api/auth/google`, {
        token: googleToken
      })

      if (response.data.access_token) {
        Cookies.set('auth_token', response.data.access_token, { expires: 7 })
        setUser(response.data.user)
        setIsPremium(response.data.user.plan === 'premium' || response.data.user.plan === 'pro')
        toast.success('Successfully logged in!')
      }
    } catch (error) {
      console.error('Login failed:', error)
      toast.error('Failed to login')
      throw error
    }
  }

  const logout = () => {
    Cookies.remove('auth_token')
    setUser(null)
    setIsPremium(false)
    toast.success('Logged out successfully')
  }

  const updateUserPlan = (plan: string) => {
    if (user) {
      setUser({ ...user, plan })
      setIsPremium(plan === 'premium' || plan === 'pro')
    }
  }

  return (
    <AuthContext.Provider value={{
      user,
      isLoading,
      isPremium,
      login,
      logout,
      updateUserPlan,
      checkAuth
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