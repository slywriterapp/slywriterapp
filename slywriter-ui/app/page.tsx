'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Page() {
  const router = useRouter()
  
  useEffect(() => {
    // Redirect directly to the app instead of showing landing page
    router.replace('/app')
  }, [router])
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-purple-400 mx-auto mb-4" />
        <p className="text-gray-400">Loading SlyWriter...</p>
      </div>
    </div>
  )
}