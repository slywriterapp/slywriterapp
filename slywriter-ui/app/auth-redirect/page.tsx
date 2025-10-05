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
    <>
      {/* Breathing animation styles */}
      <style jsx>{`
        @keyframes breathe {
          0%, 100% {
            box-shadow:
              0 20px 40px rgba(0, 0, 0, 0.6),
              0 0 0 1px rgba(139, 92, 246, 0.3),
              0 0 20px rgba(139, 92, 246, 0.15);
          }
          50% {
            box-shadow:
              0 20px 40px rgba(0, 0, 0, 0.6),
              0 0 0 1px rgba(139, 92, 246, 0.6),
              0 0 40px rgba(139, 92, 246, 0.4);
          }
        }

        .breathe-border {
          animation: breathe 3s ease-in-out infinite;
        }

        @keyframes shimmer {
          0% { background-position: -1000px 0; }
          100% { background-position: 1000px 0; }
        }

        .shimmer {
          background: linear-gradient(
            90deg,
            rgba(139, 92, 246, 0) 0%,
            rgba(139, 92, 246, 0.3) 50%,
            rgba(139, 92, 246, 0) 100%
          );
          background-size: 1000px 100%;
          animation: shimmer 2s infinite;
        }
      `}</style>

      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
        <div className="relative">
          <div className="bg-gradient-to-br from-gray-900/95 to-gray-800/95 backdrop-blur-xl p-12 rounded-2xl border border-purple-500/30 breathe-border">
            <div className="text-center">
              <div className="relative mb-6">
                <div className="absolute inset-0 shimmer rounded-full" />
                <Loader2 className="w-16 h-16 text-purple-400 animate-spin mx-auto relative z-10" />
              </div>
              <p className="text-white text-xl font-medium mb-2">Completing sign in</p>
              <p className="text-gray-400 text-sm">Please wait...</p>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}