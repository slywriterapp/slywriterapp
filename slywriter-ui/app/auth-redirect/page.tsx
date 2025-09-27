'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'

export default function AuthRedirectPage() {
  const router = useRouter()
  const [debugInfo, setDebugInfo] = useState<string[]>([])

  useEffect(() => {
    // This page is used as an intermediate step after successful authentication
    // to ensure localStorage is properly set before checking auth
    const checkAndRedirect = async () => {
      const logs: string[] = []
      
      // Log initial state
      logs.push('Auth redirect page loaded')
      logs.push(`Current URL: ${window.location.href}`)
      logs.push(`Referrer: ${document.referrer}`)
      
      // Check localStorage immediately
      const immediateToken = localStorage.getItem('auth_token')
      const immediateUserData = localStorage.getItem('user_data')
      logs.push(`Immediate token check: ${immediateToken ? 'EXISTS' : 'MISSING'}`)
      logs.push(`Immediate user data: ${immediateUserData ? 'EXISTS' : 'MISSING'}`)
      
      // Wait a moment for localStorage to be fully written
      logs.push('Waiting 500ms for localStorage...')
      await new Promise(resolve => setTimeout(resolve, 500))

      // Check again after wait
      const token = localStorage.getItem('auth_token')
      const userData = localStorage.getItem('user_data')
      logs.push(`After wait - Token: ${token ? 'EXISTS' : 'MISSING'}`)
      logs.push(`After wait - User data: ${userData ? 'EXISTS' : 'MISSING'}`)

      // Extra check if still missing
      if (!token && immediateToken) {
        logs.push('Token disappeared! Restoring from immediate check...')
        localStorage.setItem('auth_token', immediateToken)
        localStorage.setItem('user_data', immediateUserData || '')
      }
      
      // Log to console
      console.log('=== Auth Redirect Debug ===')
      logs.forEach(log => console.log(log))
      console.log('===========================')
      
      // Update debug display
      setDebugInfo(logs)
      
      if (token) {
        // We have a token, go to main app
        logs.push('Token found! Redirecting to main app...')
        console.log('Redirecting to main app /')
        console.log('Full redirect URL:', window.location.origin + '/')

        // Small delay to ensure localStorage is fully written
        await new Promise(resolve => setTimeout(resolve, 100))

        // Use replace to prevent back button issues
        window.location.replace(window.location.origin + '/')
      } else {
        // No token, something went wrong, go back to login
        logs.push('No token found! Redirecting back to login...')
        console.log('No token, redirecting back to /login')
        console.log('localStorage keys:', Object.keys(localStorage))

        // Wait a bit before redirecting to login so user can see the debug info
        await new Promise(resolve => setTimeout(resolve, 2000))
        window.location.replace(window.location.origin + '/login')
      }
    }
    
    checkAndRedirect()
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900">
      <div className="text-center max-w-2xl p-8">
        <Loader2 className="w-12 h-12 text-white animate-spin mx-auto mb-4" />
        <p className="text-white text-lg mb-6">Completing sign in...</p>
        
        {/* Debug info */}
        {debugInfo.length > 0 && (
          <div className="bg-black/50 backdrop-blur p-4 rounded-lg text-left">
            <p className="text-yellow-400 font-mono text-xs mb-2">Debug Info:</p>
            {debugInfo.map((info, index) => (
              <p key={index} className="text-gray-300 font-mono text-xs">
                {info}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}