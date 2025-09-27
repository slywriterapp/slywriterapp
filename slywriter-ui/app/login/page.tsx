'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Mail, Lock, User, Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { toast } from '@/lib/toast'
import Script from 'next/script'
import { LocalStorageMonitor } from '../utils/localStorage-monitor'

declare global {
  interface Window {
    google?: any
    handleGoogleResponse?: (response: any) => void
  }
}

export default function LoginPage() {
  const router = useRouter()
  const [isSignup, setIsSignup] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [googleLoaded, setGoogleLoaded] = useState(false)
  const [isElectron, setIsElectron] = useState(false)
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  })

  // Use local server in development, Render in production
  // Check if we're in the browser and force Render server if URL has ?server=render
  const [forceRender, setForceRender] = useState(false)
  const [apiUrl, setApiUrl] = useState('http://localhost:5000')
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Start localStorage monitoring
      LocalStorageMonitor.start()
      LocalStorageMonitor.logCurrentState()
      
      const params = new URLSearchParams(window.location.search)
      const shouldForceRender = params.get('server') === 'render'
      setForceRender(shouldForceRender)
      
      // Always use production backend when loaded from Render or Electron
      // Fixed: Check if we're in Electron or production environment
      const isElectronEnv = !!(window as any).electron
      const isProduction = window.location.hostname !== 'localhost' || isElectronEnv
      const isDevelopment = window.location.hostname === 'localhost' && window.location.port === '3000' && !isElectronEnv

      console.log('Environment detection:', {
        hostname: window.location.hostname,
        port: window.location.port,
        isElectron: isElectronEnv,
        isDevelopment,
        isProduction
      })

      const url = shouldForceRender
        ? 'https://slywriterapp.onrender.com'
        : (isDevelopment ? 'http://localhost:5000' : 'https://slywriterapp.onrender.com')
      setApiUrl(url)
      
      // Detect Electron environment
      setIsElectron(!!(window as any).electron)
    }
  }, [])
  
  const API_URL = apiUrl
  const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '675434683795-shrls6suu68dj0cuvqct28gf3o6u3jav.apps.googleusercontent.com'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const endpoint = isSignup ? '/auth/register' : '/auth/login'
      const body = isSignup 
        ? { email: formData.email, password: formData.password, name: formData.name }
        : { email: formData.email, password: formData.password }

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (data.success) {
        // Save token to localStorage and Electron if available
        localStorage.setItem('auth_token', data.token)
        localStorage.setItem('user_data', JSON.stringify({
          email: data.email,
          name: data.name,
          plan: data.plan,
          user_id: data.user_id
        }))

        toast.success(isSignup ? 'Account created successfully!' : 'Logged in successfully!')
        
        // Check if we're in Electron
        const isElectron = typeof window !== 'undefined' && (window as any).electron
        console.log('Regular login - Is Electron environment:', isElectron)
        
        if (isElectron) {
          try {
            await (window as any).electron.ipcRenderer.invoke('save-auth', {
              token: data.token,
              email: data.email,
              name: data.name,
              plan: data.plan,
              user_id: data.user_id
            })
            // Navigate to auth-redirect page
            console.log('Regular login - Navigating to auth redirect...')
            window.location.href = window.location.origin + '/auth-redirect'
          } catch (navError) {
            console.error('Regular login - Electron navigation error:', navError)
            window.location.replace(window.location.origin + '/')
          }
        } else {
          // In browser, navigate to auth redirect page
          window.location.href = window.location.origin + '/auth-redirect'
        }
        
        if (isSignup && !data.verified) {
          toast.success('Please check your email to verify your account', {
            duration: 5000
          })
        }
      } else {
        // Handle duplicate email error
        if (data.error && data.error.toLowerCase().includes('already exists')) {
          toast.error('This email is already registered. Please login instead.')
          setTimeout(() => {
            setIsSignup(false)
            toast('Switched to login mode. Enter your password to continue.', {
              icon: '👉',
              duration: 3000
            })
          }, 2000)
        } else {
          toast.error(data.error || 'Authentication failed')
        }
      }
    } catch (error: any) {
      console.error('Auth error:', error)
      toast.error(error.message || 'Something went wrong')
    } finally {
      setIsLoading(false)
    }
  }

  // Google Sign-In handler
  const handleGoogleLogin = async (response: any) => {
    console.log('=== GOOGLE SIGN-IN DEBUG START ===')
    console.log('[1] Google Sign-In response received:', response)
    console.log('[2] Current localStorage before auth:')
    console.log('  - auth_token:', localStorage.getItem('auth_token') ? 'EXISTS' : 'MISSING')
    console.log('  - user_data:', localStorage.getItem('user_data') ? 'EXISTS' : 'MISSING')
    console.log('[3] Sending to backend:', API_URL)
    console.log('[4] Server mode:', forceRender ? 'FORCED RENDER' : 'AUTO-DETECTED')
    setIsLoading(true)
    
    try {
      const result = await fetch(`${API_URL}/auth/google/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          credential: response.credential
        })
      })

      const data = await result.json()

      if (data.success) {
        console.log('[5] Backend returned success!')
        console.log('[6] Token from backend:', data.token ? `${data.token.substring(0, 20)}...` : 'MISSING')
        
        // Clear any existing auth data first
        console.log('[7] Clearing old auth data...')
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_data')
        
        // Save token to localStorage and Electron if available
        console.log('[8] Saving new auth data to localStorage...')
        localStorage.setItem('auth_token', data.token)
        localStorage.setItem('user_data', JSON.stringify({
          email: data.email,
          name: data.name,
          plan: data.plan,
          user_id: data.user_id,
          picture: data.picture
        }))
        
        // Verify it was saved
        console.log('[9] Verification - localStorage after save:')
        const savedToken = localStorage.getItem('auth_token')
        const savedUserData = localStorage.getItem('user_data')
        console.log('  - auth_token:', savedToken ? `${savedToken.substring(0, 20)}...` : 'MISSING')
        console.log('  - user_data:', savedUserData ? 'SAVED' : 'MISSING')

        // Show success message first
        toast.success(data.is_new_user ? 'Welcome to SlyWriter!' : 'Welcome back!')
        
        // Check if we're in Electron
        const isElectron = typeof window !== 'undefined' && (window as any).electron
        console.log('[10] Is Electron environment:', isElectron)
        console.log('[11] Window location before redirect:', window.location.href)
        
        if (isElectron) {
          try {
            console.log('Saving auth data to Electron...')
            await (window as any).electron.ipcRenderer.invoke('save-auth', {
              token: data.token,
              email: data.email,
              name: data.name,
              plan: data.plan,
              user_id: data.user_id,
              picture: data.picture
            })
            console.log('Auth data saved, navigating to app...')
            
            // Navigate to auth-redirect page which will handle the final redirect
            console.log('[12] Electron: Navigating to auth redirect page...')
            console.log('[13] Using window.location.href = ' + window.location.origin + '/auth-redirect')
            window.location.href = window.location.origin + '/auth-redirect'
            console.log('[14] Navigation command sent!')
          } catch (navError) {
            console.error('Electron navigation error:', navError)
            // Fallback: force browser navigation
            window.location.replace(window.location.origin + '/')
          }
        } else {
          // In browser, navigate to auth redirect page
          console.log('[12] Browser: Navigating to auth redirect page...')
          console.log('[13] Using window.location.href = ' + window.location.origin + '/auth-redirect')
          window.location.href = window.location.origin + '/auth-redirect'
          console.log('[14] Navigation command sent!')
        }
        console.log('=== GOOGLE SIGN-IN DEBUG END ===')
      } else {
        toast.error(data.error || 'Google login failed')
      }
    } catch (error: any) {
      console.error('Google auth error:', error)
      toast.error('Failed to login with Google')
    } finally {
      setIsLoading(false)
    }
  }

  // Initialize Google Sign-In
  useEffect(() => {
    // Set up the callback function on window
    window.handleGoogleResponse = handleGoogleLogin

    // Initialize Google Sign-In when script loads
    const initializeGoogle = () => {
      if (window.google) {
        try {
          window.google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: handleGoogleLogin,
            auto_select: false,
            cancel_on_tap_outside: true,
            ux_mode: 'popup',
            hosted_domain: undefined,
            login_uri: undefined,
          })
          
          // Render the Google Sign-In button
          const googleButtonDiv = document.getElementById('googleSignInButton')
          if (googleButtonDiv) {
            window.google.accounts.id.renderButton(
              googleButtonDiv,
              { 
                theme: 'filled_black',
                size: 'large',
                type: 'standard',
                shape: 'rectangular',
                text: isSignup ? 'signup_with' : 'signin_with',
                width: 360
              }
            )
          }
          setGoogleLoaded(true)
        } catch (error) {
          console.error('Google Sign-In initialization failed:', error)
          // Google Sign-In not available in Electron without proper origin setup
          // This is expected in Electron apps without custom protocol handlers
          setGoogleLoaded(false)
        }
      }
    }

    // Check if Google script is already loaded
    if (window.google) {
      initializeGoogle()
    } else {
      // Wait for script to load
      const checkGoogle = setInterval(() => {
        if (window.google) {
          clearInterval(checkGoogle)
          initializeGoogle()
        }
      }, 100)

      // Cleanup
      return () => clearInterval(checkGoogle)
    }
  }, [isSignup])

  return (
    <>
      {/* Google Sign-In Script */}
      <Script 
        src="https://accounts.google.com/gsi/client" 
        strategy="afterInteractive"
        onLoad={() => {
          // Script loaded, initialization will happen in useEffect
        }}
      />
      
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-black/40 backdrop-blur-xl p-8 rounded-2xl shadow-2xl w-full max-w-md border border-purple-500/20"
      >
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">SlyWriter</h1>
          <p className="text-gray-300">AI-Powered Writing Assistant</p>
        </div>

        <div className="flex mb-6">
          <button
            onClick={() => setIsSignup(false)}
            className={`flex-1 py-2 px-4 rounded-l-lg transition-colors ${
              !isSignup 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => setIsSignup(true)}
            className={`flex-1 py-2 px-4 rounded-r-lg transition-colors ${
              isSignup 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {isSignup && (
            <div className="relative">
              <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Full Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full pl-10 pr-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 transition-colors"
                required={isSignup}
              />
            </div>
          )}

          <div className="relative">
            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="email"
              placeholder="Email Address"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full pl-10 pr-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 transition-colors"
              required
            />
          </div>

          <div className="relative">
            <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full pl-10 pr-12 py-3 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 transition-colors"
              required
              minLength={8}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>

          {isSignup && (
            <p className="text-xs text-gray-400">
              Password must be at least 8 characters with uppercase, lowercase, and numbers
            </p>
          )}

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-gradient-to-r from-purple-600 to-violet-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-violet-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                {isSignup ? 'Creating Account...' : 'Signing In...'}
              </>
            ) : (
              isSignup ? 'Create Account' : 'Sign In'
            )}
          </motion.button>
        </form>

        {/* Divider */}
        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-700"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-black/40 text-gray-400">Or continue with</span>
          </div>
        </div>

        {/* Google Sign-In Button */}
        <div className="mb-6">
          {/* Show regular Google Sign-In button if it loads */}
          <div id="googleSignInButton" className="w-full flex justify-center"></div>
          
          {/* Show fallback button if Google Sign-In doesn't load */}
          {!googleLoaded && isElectron && (
            <div className="space-y-2">
              <button
                type="button"
                onClick={async () => {
                  console.log('Google Sign-In button clicked in Electron')
                  // Open Google Sign-In in the default browser
                  if ((window as any).electron) {
                    console.log('Opening external browser...')
                    try {
                      await (window as any).electron.ipcRenderer.invoke('open-external', 'http://localhost:3000/login')
                      toast.info('Opening in your browser for Google Sign-In...', {
                        duration: 5000,
                        icon: '🌐'
                      })
                    } catch (error) {
                      console.error('Failed to open browser:', error)
                      toast.error('Failed to open browser. Please open http://localhost:3000/login manually.')
                    }
                  }
                }}
                className="w-full py-3 bg-white text-gray-900 font-medium rounded-lg flex items-center justify-center gap-3 hover:bg-gray-100 transition-colors"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Sign in with Google (Opens in Browser)
              </button>
              <p className="text-xs text-gray-400 text-center">
                Click to open Google Sign-In in your default browser
              </p>
            </div>
          )}
          
          {/* Show loading state in regular browser */}
          {!googleLoaded && !isElectron && (
            <button
              type="button"
              disabled
              className="w-full py-3 bg-gray-800 text-gray-400 font-medium rounded-lg flex items-center justify-center gap-3"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Loading Google Sign-In...
            </button>
          )}
        </div>

        <div className="text-center">
          <p className="text-gray-400 text-sm">
            {isSignup ? 'Already have an account?' : "Don't have an account?"}
            {' '}
            <button
              onClick={() => setIsSignup(!isSignup)}
              className="text-purple-400 hover:text-purple-300 transition-colors"
            >
              {isSignup ? 'Sign In' : 'Sign Up'}
            </button>
          </p>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-800">
          <p className="text-xs text-gray-500 text-center">
            By continuing, you agree to SlyWriter's Terms of Service and Privacy Policy
          </p>
          
          {/* Skip button for development/testing */}
          <button
            onClick={() => {
              console.log('Skip button clicked - bypassing authentication')
              // Set a minimal guest auth token
              localStorage.setItem('auth_token', 'guest-mode-token')
              localStorage.setItem('user_data', JSON.stringify({
                email: 'guest@slywriter.com',
                name: 'Guest User',
                plan: 'free',
                user_id: 'guest-user-id',
                is_guest: true
              }))
              
              // Force navigation with replace to prevent back button issues
              console.log('Navigating to main app...')
              // Use the current origin to maintain the same port
              window.location.replace(window.location.origin + '/')
            }}
            className="mt-4 w-full py-2 text-gray-400 hover:text-white text-sm transition-colors underline"
          >
            Skip Login (Continue as Guest)
          </button>
        </div>
      </motion.div>
      </div>
    </>
  )
}