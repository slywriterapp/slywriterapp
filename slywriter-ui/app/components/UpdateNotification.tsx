'use client'

import { useState, useEffect } from 'react'
import { X, Download, ExternalLink } from 'lucide-react'

interface UpdateBannerProps {
  onDismiss?: () => void
}

export default function UpdateNotification({ onDismiss }: UpdateBannerProps = {}) {
  const [showBanner, setShowBanner] = useState(false)
  const [latestVersion, setLatestVersion] = useState('')
  const [currentVersion, setCurrentVersion] = useState('')
  const [isChecking, setIsChecking] = useState(false)

  useEffect(() => {
    checkForUpdate()

    // Check every 24 hours
    const interval = setInterval(checkForUpdate, 24 * 60 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const checkForUpdate = async () => {
    try {
      setIsChecking(true)

      // Get current version from Electron
      let current = '3.1.6' // Fallback
      if (typeof window !== 'undefined' && (window as any).electron) {
        try {
          current = await (window as any).electron.ipcRenderer.invoke('get-app-version')
        } catch (e) {
          console.log('Could not get version from Electron, using fallback')
        }
      }
      setCurrentVersion(current)

      // Fetch latest version from GitHub API
      const response = await fetch('https://api.github.com/repos/slywriterapp/slywriter-releases/releases/latest')
      if (!response.ok) throw new Error('Failed to fetch latest version')

      const data = await response.json()
      const latest = data.tag_name.replace('v', '')
      setLatestVersion(latest)

      // Check if dismissed
      const dismissedVersion = localStorage.getItem('dismissed_update_version')
      if (dismissedVersion === latest) {
        setShowBanner(false)
        return
      }

      // Compare versions
      if (isNewerVersion(latest, current)) {
        setShowBanner(true)
      }
    } catch (error) {
      console.error('Failed to check for updates:', error)
    } finally {
      setIsChecking(false)
    }
  }

  const isNewerVersion = (latest: string, current: string): boolean => {
    const latestParts = latest.split('.').map(Number)
    const currentParts = current.split('.').map(Number)

    for (let i = 0; i < 3; i++) {
      if (latestParts[i] > currentParts[i]) return true
      if (latestParts[i] < currentParts[i]) return false
    }
    return false
  }

  const handleDownload = () => {
    window.open('https://slywriter.ai/download', '_blank')
  }

  const handleDismiss = () => {
    setShowBanner(false)
    onDismiss?.()
  }

  const handleDismissForVersion = () => {
    localStorage.setItem('dismissed_update_version', latestVersion)
    setShowBanner(false)
    onDismiss?.()
  }

  if (!showBanner) return null

  return (
    <div className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-3 shadow-lg">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1">
          <Download className="w-5 h-5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium">
              New version v{latestVersion} available!
              <span className="text-white/80 ml-1">(Current: v{currentVersion})</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleDownload}
            className="px-4 py-1.5 bg-white text-purple-600 hover:bg-purple-50 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5"
          >
            Download Update
            <ExternalLink className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleDismissForVersion}
            className="px-3 py-1.5 hover:bg-white/10 rounded-md text-sm transition-colors"
          >
            Not now
          </button>

          <button
            onClick={handleDismiss}
            className="p-1.5 hover:bg-white/10 rounded-md transition-colors"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
