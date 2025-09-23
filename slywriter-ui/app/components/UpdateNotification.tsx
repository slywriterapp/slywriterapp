'use client'

import { useState, useEffect } from 'react'
import { Download, RefreshCw, Check, AlertCircle } from 'lucide-react'

export default function UpdateNotification() {
  const [updateStatus, setUpdateStatus] = useState<'checking' | 'available' | 'downloading' | 'ready' | 'none' | null>(null)
  const [progress, setProgress] = useState(0)
  const [version, setVersion] = useState('')
  const [currentVersion, setCurrentVersion] = useState('')

  useEffect(() => {
    // Only run in Electron environment
    if (typeof window !== 'undefined' && (window as any).electron) {
      const electron = (window as any).electron

      // Get current version
      electron.ipcRenderer.invoke('get-app-version').then((v: string) => {
        setCurrentVersion(v)
      })

      // Listen for update events
      electron.ipcRenderer.on('update-downloading', (_: any, info: any) => {
        setUpdateStatus('downloading')
        setVersion(info.version)
      })

      electron.ipcRenderer.on('update-progress', (_: any, progressObj: any) => {
        setProgress(Math.round(progressObj.percent))
      })

      // Check for updates on mount
      checkForUpdates()
    }
  }, [])

  const checkForUpdates = async () => {
    if (typeof window !== 'undefined' && (window as any).electron) {
      setUpdateStatus('checking')
      try {
        const result = await (window as any).electron.ipcRenderer.invoke('check-for-updates')
        // The dialog will be shown by the main process
        setTimeout(() => {
          if (updateStatus === 'checking') {
            setUpdateStatus('none')
          }
        }, 3000)
      } catch (error) {
        console.error('Failed to check for updates:', error)
        setUpdateStatus('none')
      }
    }
  }

  if (!updateStatus || updateStatus === 'none') {
    return (
      <button
        onClick={checkForUpdates}
        className="fixed bottom-4 right-4 p-2 bg-gray-800 hover:bg-gray-700 text-white rounded-full transition-all duration-300 shadow-lg"
        title={`Version ${currentVersion} - Check for updates`}
      >
        <RefreshCw className="w-5 h-5" />
      </button>
    )
  }

  return (
    <div className="fixed bottom-4 right-4 bg-gray-800 text-white rounded-lg shadow-xl p-4 min-w-[300px]">
      {updateStatus === 'checking' && (
        <div className="flex items-center gap-3">
          <RefreshCw className="w-5 h-5 animate-spin text-blue-400" />
          <span className="text-sm">Checking for updates...</span>
        </div>
      )}

      {updateStatus === 'available' && (
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-400" />
            <span className="text-sm font-medium">Update Available!</span>
          </div>
          <p className="text-xs text-gray-400">Version {version} is ready to download</p>
        </div>
      )}

      {updateStatus === 'downloading' && (
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <Download className="w-5 h-5 text-blue-400 animate-pulse" />
            <span className="text-sm">Downloading update...</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-400">{progress}% complete</p>
        </div>
      )}

      {updateStatus === 'ready' && (
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <Check className="w-5 h-5 text-green-400" />
            <span className="text-sm font-medium">Update Ready!</span>
          </div>
          <p className="text-xs text-gray-400">Restart to apply version {version}</p>
        </div>
      )}
    </div>
  )
}