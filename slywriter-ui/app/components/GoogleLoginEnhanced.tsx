'use client'

import { useState } from 'react'
import { useGoogleLogin } from '@react-oauth/google'
import { useAuth } from '../context/AuthContext'
import { motion, AnimatePresence } from 'framer-motion'
import { RENDER_API_URL } from '../config/api'
import { 
  LogInIcon, LogOutIcon, UserIcon, GiftIcon, 
  CheckCircleIcon, XCircleIcon, CrownIcon, KeyIcon
} from 'lucide-react'
import toast from 'react-hot-toast'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || RENDER_API_URL

export default function GoogleLoginEnhanced() {
  const { user, login, logout, isLoading } = useAuth()
  const [showPromoCode, setShowPromoCode] = useState(false)
  const [promoCode, setPromoCode] = useState('')
  const [applyingCode, setApplyingCode] = useState(false)
  
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
  
  // Apply promo code
  const applyPromoCode = async () => {
    if (!promoCode.trim()) {
      toast.error('Please enter a promo code')
      return
    }
    
    setApplyingCode(true)
    
    try {
      // For testing, accept these codes
      const validCodes = {
        'TESTER2025': { plan: 'premium', duration: 30, message: '30 days of Premium activated!' },
        'BETA2025': { plan: 'premium', duration: 14, message: '14 days of Premium activated!' },
        'SLYWRITER': { plan: 'premium', duration: 7, message: '7 days of Premium activated!' },
        'PREMIUM30': { plan: 'premium', duration: 30, message: '30 days of Premium activated!' },
      }
      
      const codeData = validCodes[promoCode.toUpperCase() as keyof typeof validCodes]
      
      if (codeData) {
        // Update user plan in localStorage for testing
        const currentUser = user || { email: 'guest@slywriter.app', name: 'Guest User', plan: 'free' }
        const updatedUser = { ...currentUser, plan: 'premium' }
        
        localStorage.setItem('slywriter-user', JSON.stringify(updatedUser))
        
        toast.success(codeData.message)
        setPromoCode('')
        setShowPromoCode(false)
        
        // Reload to apply changes
        setTimeout(() => window.location.reload(), 1000)
      } else {
        toast.error('Invalid promo code')
      }
    } catch (error) {
      toast.error('Failed to apply promo code')
    } finally {
      setApplyingCode(false)
    }
  }

  if (isLoading) {
    return (
      <div className="animate-pulse bg-gray-800 h-10 w-32 rounded-lg" />
    )
  }

  if (user) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <div className="text-sm font-medium text-white">{user.name || user.email}</div>
            <div className="flex items-center gap-2">
              <span className={`text-xs ${user.plan === 'premium' ? 'text-purple-400' : 'text-gray-400'}`}>
                {user.plan === 'premium' ? (
                  <>
                    <CrownIcon className="w-3 h-3 inline mr-1" />
                    Premium
                  </>
                ) : (
                  'Free plan'
                )}
              </span>
              {user.plan === 'free' && (
                <button
                  onClick={() => setShowPromoCode(!showPromoCode)}
                  className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
                >
                  <KeyIcon className="w-3 h-3 inline mr-1" />
                  Promo Code
                </button>
              )}
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={logout}
            className="p-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
          >
            <LogOutIcon className="w-5 h-5" />
          </motion.button>
        </div>
        
        {/* Promo Code Input */}
        <AnimatePresence>
          {showPromoCode && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-gray-800 rounded-lg p-3"
            >
              <div className="flex gap-2">
                <input
                  type="text"
                  value={promoCode}
                  onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                  placeholder="Enter promo code"
                  className="flex-1 px-3 py-1 bg-gray-700 text-white text-sm rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                  onKeyDown={(e) => e.key === 'Enter' && applyPromoCode()}
                />
                <button
                  onClick={applyPromoCode}
                  disabled={applyingCode}
                  className="px-3 py-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white text-sm rounded transition-colors"
                >
                  {applyingCode ? '...' : 'Apply'}
                </button>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                Test codes: TESTER2025, BETA2025, SLYWRITER
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }
  
  // Guest user with promo code option
  return (
    <div className="space-y-3">
      {hasGoogleAuth ? (
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => googleLogin()}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Sign in with Google
        </motion.button>
      ) : (
        <div className="text-sm text-gray-400 text-center">
          <UserIcon className="w-8 h-8 mx-auto mb-2 text-gray-600" />
          <p>Guest Mode</p>
        </div>
      )}
      
      {/* Promo Code for non-logged in users */}
      <button
        onClick={() => setShowPromoCode(!showPromoCode)}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-purple-400 rounded-lg text-sm font-medium transition-colors"
      >
        <GiftIcon className="w-4 h-4" />
        Have a promo code?
      </button>
      
      <AnimatePresence>
        {showPromoCode && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gray-800 rounded-lg p-3"
          >
            <div className="flex gap-2">
              <input
                type="text"
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                placeholder="Enter promo code"
                className="flex-1 px-3 py-1 bg-gray-700 text-white text-sm rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                onKeyDown={(e) => e.key === 'Enter' && applyPromoCode()}
              />
              <button
                onClick={applyPromoCode}
                disabled={applyingCode}
                className="px-3 py-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white text-sm rounded transition-colors"
              >
                {applyingCode ? '...' : 'Apply'}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              For testers: Use code TESTER2025
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}