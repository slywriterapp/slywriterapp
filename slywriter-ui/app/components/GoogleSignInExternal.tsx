'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { ExternalLink, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function GoogleSignInExternal({ isSignup }: { isSignup: boolean }) {
  const [isLoading, setIsLoading] = useState(false)
  
  const handleExternalGoogleSignIn = () => {
    setIsLoading(true)
    
    // Open Google OAuth in external browser
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
      `client_id=675434683795-shrls6suu68dj0cuvqct28gf3o6u3jav.apps.googleusercontent.com` +
      `&redirect_uri=${encodeURIComponent('http://localhost:3000/auth/google/callback')}` +
      `&response_type=code` +
      `&scope=openid%20email%20profile` +
      `&access_type=offline` +
      `&prompt=consent`
    
    // In Electron, open in external browser
    if (typeof window !== 'undefined' && (window as any).electron) {
      (window as any).electron.ipcRenderer.invoke('open-external', authUrl)
      
      toast.success('Opening Google Sign-In in your browser...', {
        duration: 5000,
        icon: '🌐'
      })
      
      // Show instructions
      toast('After signing in, copy the code and paste it here', {
        duration: 10000,
        position: 'top-center'
      })
      
      setIsLoading(false)
    } else {
      // In browser, just redirect
      window.location.href = authUrl
    }
  }
  
  return (
    <div className="space-y-4">
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        type="button"
        onClick={handleExternalGoogleSignIn}
        disabled={isLoading}
        className="w-full py-3 bg-white text-gray-900 font-medium rounded-lg flex items-center justify-center gap-3 hover:bg-gray-100 transition-colors disabled:opacity-50"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Opening Browser...
          </>
        ) : (
          <>
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            {isSignup ? 'Sign up with Google' : 'Sign in with Google'}
            <ExternalLink className="w-4 h-4 ml-1" />
          </>
        )}
      </motion.button>
      
      {typeof window !== 'undefined' && (window as any).electron && (
        <p className="text-xs text-gray-400 text-center">
          Opens in your default browser for secure authentication
        </p>
      )}
    </div>
  )
}