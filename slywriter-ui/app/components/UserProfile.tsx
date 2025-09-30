'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { LogOutIcon, UserIcon } from 'lucide-react'

interface UserData {
  email?: string
  name?: string
  plan?: string
  user_id?: string
  picture?: string
}

export default function UserProfile({ onShowDashboard }: { onShowDashboard?: () => void }) {
  const [userData, setUserData] = useState<UserData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Load user data from localStorage
    const loadUserData = () => {
      try {
        const userDataString = localStorage.getItem('user_data')
        if (userDataString) {
          const parsed = JSON.parse(userDataString)
          setUserData(parsed)
        }
      } catch (error) {
        console.error('Failed to load user data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadUserData()

    // Listen for storage changes
    const handleStorageChange = () => {
      loadUserData()
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  const handleLogout = async () => {
    // Clear localStorage
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')

    // Clear Electron storage if available
    if (typeof window !== 'undefined' && (window as any).electron) {
      await (window as any).electron.ipcRenderer.invoke('logout')
    }

    // Redirect to login
    window.location.href = window.location.origin + '/login'
  }

  if (isLoading) {
    return (
      <div className="animate-pulse bg-gray-800 h-10 w-32 rounded-lg" />
    )
  }

  if (!userData) {
    return (
      <div className="text-sm text-gray-400 text-center">
        <p>Not signed in</p>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-3">
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onShowDashboard}
        className="flex-1 text-left hover:bg-white/5 rounded-lg p-2 transition-colors"
      >
        <div className="flex items-center gap-2">
          {userData.picture ? (
            <img
              src={userData.picture}
              alt={userData.name || userData.email}
              className="w-8 h-8 rounded-full"
            />
          ) : (
            <div className="w-8 h-8 bg-indigo-500/20 rounded-full flex items-center justify-center">
              <UserIcon className="w-4 h-4 text-indigo-400" />
            </div>
          )}
          <div>
            <div className="text-sm font-medium text-white">{userData.name || userData.email}</div>
            <div className="text-xs text-gray-400">{userData.plan || 'free'} plan • Dashboard</div>
          </div>
        </div>
      </motion.button>
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleLogout}
        className="p-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
        title="Sign Out"
      >
        <LogOutIcon className="w-5 h-5" />
      </motion.button>
    </div>
  )
}