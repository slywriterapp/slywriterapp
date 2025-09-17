'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'

export default function AuthRedirectPage() {
  const router = useRouter()

  useEffect(() => {
    // This page is used as an intermediate step after successful authentication
    // to ensure localStorage is properly set before checking auth
    const checkAndRedirect = async () => {
      // Wait a moment for localStorage to be fully written
      await new Promise(resolve => setTimeout(resolve, 500))
      
      const token = localStorage.getItem('auth_token')
      if (token) {
        // We have a token, go to main app
        window.location.href = '/'
      } else {
        // No token, something went wrong, go back to login
        window.location.href = '/login'
      }
    }
    
    checkAndRedirect()
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900">
      <div className="text-center">
        <Loader2 className="w-12 h-12 text-white animate-spin mx-auto mb-4" />
        <p className="text-white text-lg">Completing sign in...</p>
      </div>
    </div>
  )
}