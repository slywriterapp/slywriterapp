'use client'

import { useGoogleLogin } from '@react-oauth/google'
import { useAuth } from '../context/AuthContext'
import { motion } from 'framer-motion'
import { LogInIcon, LogOutIcon, UserIcon } from 'lucide-react'

export default function GoogleLogin({ onShowDashboard }: { onShowDashboard?: () => void }) {
  const { user, login, logout, isLoading } = useAuth()
  
  // Skip Google login if no client ID
  const hasGoogleAuth = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID && process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID !== ''
  
  const googleLogin = hasGoogleAuth ? useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        // Get user info from Google
        const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` }
        })
        const userInfo = await userInfoResponse.json()
        
        // Send to our backend
        await login(tokenResponse.access_token)
      } catch (error) {
        console.error('Login failed:', error)
      }
    },
    onError: () => {
      console.error('Google Login Failed')
    }
  }) : () => {}

  if (isLoading) {
    return (
      <div className="animate-pulse bg-gray-800 h-10 w-32 rounded-lg" />
    )
  }

  if (user) {
    return (
      <div className="flex items-center gap-3">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onShowDashboard}
          className="flex-1 text-left hover:bg-white/5 rounded-lg p-2 transition-colors"
        >
          <div className="text-sm font-medium text-white">{user.name || user.email}</div>
          <div className="text-xs text-gray-400">{user.plan} plan • Click for dashboard</div>
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={logout}
          className="p-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
        >
          <LogOutIcon className="w-5 h-5" />
        </motion.button>
      </div>
    )
  }

  if (!hasGoogleAuth) {
    return (
      <div className="text-sm text-gray-400 text-center">
        <p>Sign in disabled</p>
        <p className="text-xs">(No Google Client ID)</p>
      </div>
    )
  }
  
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={() => googleLogin()}
      className="flex items-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors"
    >
      <svg className="w-5 h-5" viewBox="0 0 24 24">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
      Sign in with Google
    </motion.button>
  )
}