'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Settings, User, Palette, Keyboard, Bell, Shield, Database, Save, Upload, Download, Trash2, Moon, Sun, Monitor, Volume2, VolumeX } from 'lucide-react'

interface Profile {
  id: string
  name: string
  speed: number
  typosEnabled: boolean
  aiFiller: boolean
  pauseFrequency: number
  soundEnabled: boolean
  theme: string
  hotkeys: {
    start: string
    pause: string
    stop: string
  }
}

export default function SettingsTab() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [activeProfile, setActiveProfile] = useState<string>('default')
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null)
  const [theme, setTheme] = useState('dark')
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [notifications, setNotifications] = useState(true)
  const [autoSave, setAutoSave] = useState(true)
  const [dataUsage, setDataUsage] = useState(0)

  useEffect(() => {
    // Load settings from localStorage
    const savedProfiles = localStorage.getItem('profiles')
    if (savedProfiles) {
      const parsed = JSON.parse(savedProfiles)
      setProfiles(parsed)
      setCurrentProfile(parsed.find((p: Profile) => p.id === activeProfile) || parsed[0])
    } else {
      // Create default profiles
      const defaultProfiles: Profile[] = [
        {
          id: 'default',
          name: 'Default',
          speed: 5,
          typosEnabled: false,
          aiFiller: false,
          pauseFrequency: 5,
          soundEnabled: true,
          theme: 'dark',
          hotkeys: { start: 'Ctrl+Enter', pause: 'Space', stop: 'Escape' }
        },
        {
          id: 'fast',
          name: 'Speed Typist',
          speed: 9,
          typosEnabled: false,
          aiFiller: false,
          pauseFrequency: 10,
          soundEnabled: false,
          theme: 'dark',
          hotkeys: { start: 'Ctrl+Enter', pause: 'Space', stop: 'Escape' }
        },
        {
          id: 'natural',
          name: 'Natural',
          speed: 5,
          typosEnabled: true,
          aiFiller: true,
          pauseFrequency: 3,
          soundEnabled: true,
          theme: 'dark',
          hotkeys: { start: 'Ctrl+Enter', pause: 'Space', stop: 'Escape' }
        }
      ]
      setProfiles(defaultProfiles)
      setCurrentProfile(defaultProfiles[0])
      localStorage.setItem('profiles', JSON.stringify(defaultProfiles))
    }

    // Calculate data usage
    const storageUsed = Object.keys(localStorage).reduce((acc, key) => {
      return acc + (localStorage.getItem(key)?.length || 0)
    }, 0)
    setDataUsage(storageUsed / 1024) // Convert to KB
  }, [activeProfile])

  const saveProfile = () => {
    if (!currentProfile) return
    
    const updatedProfiles = profiles.map(p => 
      p.id === currentProfile.id ? currentProfile : p
    )
    setProfiles(updatedProfiles)
    localStorage.setItem('profiles', JSON.stringify(updatedProfiles))
    
    // Show save animation
    const saveBtn = document.getElementById('save-btn')
    if (saveBtn) {
      saveBtn.classList.add('animate-pulse')
      setTimeout(() => saveBtn.classList.remove('animate-pulse'), 1000)
    }
  }

  const createNewProfile = () => {
    const newProfile: Profile = {
      id: `custom-${Date.now()}`,
      name: 'Custom Profile',
      speed: 5,
      typosEnabled: false,
      aiFiller: false,
      pauseFrequency: 5,
      soundEnabled: true,
      theme: 'dark',
      hotkeys: { start: 'Ctrl+Enter', pause: 'Space', stop: 'Escape' }
    }
    const updatedProfiles = [...profiles, newProfile]
    setProfiles(updatedProfiles)
    setCurrentProfile(newProfile)
    setActiveProfile(newProfile.id)
    localStorage.setItem('profiles', JSON.stringify(updatedProfiles))
  }

  const deleteProfile = (profileId: string) => {
    if (profiles.length <= 1) return
    
    const updatedProfiles = profiles.filter(p => p.id !== profileId)
    setProfiles(updatedProfiles)
    localStorage.setItem('profiles', JSON.stringify(updatedProfiles))
    
    if (activeProfile === profileId) {
      setActiveProfile(updatedProfiles[0].id)
      setCurrentProfile(updatedProfiles[0])
    }
  }

  const exportSettings = () => {
    const settings = {
      profiles,
      activeProfile,
      theme,
      soundEnabled,
      notifications,
      autoSave,
      exportDate: new Date().toISOString()
    }
    
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `slywriter-settings-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const importSettings = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const settings = JSON.parse(e.target?.result as string)
        setProfiles(settings.profiles || [])
        setActiveProfile(settings.activeProfile || 'default')
        setTheme(settings.theme || 'dark')
        setSoundEnabled(settings.soundEnabled !== false)
        setNotifications(settings.notifications !== false)
        setAutoSave(settings.autoSave !== false)
        
        localStorage.setItem('profiles', JSON.stringify(settings.profiles || []))
      } catch (error) {
        console.error('Failed to import settings:', error)
      }
    }
    reader.readAsText(file)
  }

  const clearAllData = () => {
    if (confirm('Are you sure you want to clear all data? This cannot be undone.')) {
      localStorage.clear()
      window.location.reload()
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-900/20 to-purple-900/20 rounded-2xl p-6 backdrop-blur-sm border border-indigo-500/20">
        <div className="flex items-center gap-3 mb-3">
          <Settings className="w-8 h-8 text-indigo-400" />
          <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            Settings & Preferences
          </h2>
        </div>
        <p className="text-gray-400">Customize your typing experience and manage profiles</p>
      </div>

      {/* Profile Management */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <User className="w-5 h-5 text-blue-400" />
          Profile Management
        </h3>
        
        <div className="flex gap-3 mb-4 overflow-x-auto pb-2">
          {profiles.map((profile) => (
            <motion.button
              key={profile.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                setActiveProfile(profile.id)
                setCurrentProfile(profile)
              }}
              className={`px-4 py-2 rounded-lg whitespace-nowrap transition-all ${
                activeProfile === profile.id
                  ? 'bg-purple-500/20 border border-purple-500'
                  : 'bg-gray-800 border border-gray-700 hover:border-gray-600'
              }`}
            >
              {profile.name}
            </motion.button>
          ))}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={createNewProfile}
            className="px-4 py-2 rounded-lg bg-gray-800 border border-dashed border-gray-600 hover:border-purple-500"
          >
            + New Profile
          </motion.button>
        </div>

        {currentProfile && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Profile Name</label>
              <input
                type="text"
                value={currentProfile.name}
                onChange={(e) => setCurrentProfile({ ...currentProfile, name: e.target.value })}
                className="w-full bg-gray-800 rounded-lg px-3 py-2 border border-gray-600 focus:border-purple-500 focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Typing Speed</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={currentProfile.speed}
                  onChange={(e) => setCurrentProfile({ ...currentProfile, speed: Number(e.target.value) })}
                  className="w-full"
                />
                <div className="text-center text-purple-400 text-sm mt-1">Level {currentProfile.speed}</div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Pause Frequency</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={currentProfile.pauseFrequency}
                  onChange={(e) => setCurrentProfile({ ...currentProfile, pauseFrequency: Number(e.target.value) })}
                  className="w-full"
                />
                <div className="text-center text-purple-400 text-sm mt-1">Level {currentProfile.pauseFrequency}</div>
              </div>
            </div>

            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={currentProfile.typosEnabled}
                  onChange={(e) => setCurrentProfile({ ...currentProfile, typosEnabled: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Enable Typos</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={currentProfile.aiFiller}
                  onChange={(e) => setCurrentProfile({ ...currentProfile, aiFiller: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">AI Filler Text</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={currentProfile.soundEnabled}
                  onChange={(e) => setCurrentProfile({ ...currentProfile, soundEnabled: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Sound Effects</span>
              </label>
            </div>

            <div className="flex gap-3">
              <motion.button
                id="save-btn"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={saveProfile}
                className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 py-2 rounded-lg font-medium flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save Profile
              </motion.button>
              
              {currentProfile.id !== 'default' && (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => deleteProfile(currentProfile.id)}
                  className="px-4 bg-red-600/20 border border-red-600/50 py-2 rounded-lg font-medium flex items-center gap-2 hover:bg-red-600/30"
                >
                  <Trash2 className="w-4 h-4" />
                </motion.button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Hotkeys */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Keyboard className="w-5 h-5 text-yellow-400" />
          Keyboard Shortcuts
        </h3>
        
        {currentProfile && (
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Start Typing</label>
              <input
                type="text"
                value={currentProfile.hotkeys.start}
                readOnly
                className="w-full bg-gray-800 rounded-lg px-3 py-2 border border-gray-600 text-center"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Pause/Resume</label>
              <input
                type="text"
                value={currentProfile.hotkeys.pause}
                readOnly
                className="w-full bg-gray-800 rounded-lg px-3 py-2 border border-gray-600 text-center"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Stop</label>
              <input
                type="text"
                value={currentProfile.hotkeys.stop}
                readOnly
                className="w-full bg-gray-800 rounded-lg px-3 py-2 border border-gray-600 text-center"
              />
            </div>
          </div>
        )}
      </div>

      {/* Appearance */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Palette className="w-5 h-5 text-green-400" />
          Appearance
        </h3>
        
        <div className="flex gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setTheme('dark')}
            className={`flex-1 p-4 rounded-lg border transition-all ${
              theme === 'dark'
                ? 'bg-gray-800 border-purple-500'
                : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'
            }`}
          >
            <Moon className="w-6 h-6 mx-auto mb-2 text-purple-400" />
            <div className="text-sm">Dark</div>
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setTheme('light')}
            className={`flex-1 p-4 rounded-lg border transition-all ${
              theme === 'light'
                ? 'bg-gray-800 border-purple-500'
                : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'
            }`}
          >
            <Sun className="w-6 h-6 mx-auto mb-2 text-yellow-400" />
            <div className="text-sm">Light</div>
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setTheme('auto')}
            className={`flex-1 p-4 rounded-lg border transition-all ${
              theme === 'auto'
                ? 'bg-gray-800 border-purple-500'
                : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'
            }`}
          >
            <Monitor className="w-6 h-6 mx-auto mb-2 text-blue-400" />
            <div className="text-sm">System</div>
          </motion.button>
        </div>
      </div>

      {/* System Settings */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-red-400" />
          System Settings
        </h3>
        
        <div className="space-y-3">
          <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg bg-gray-800/50 hover:bg-gray-800/70">
            <div className="flex items-center gap-3">
              {soundEnabled ? <Volume2 className="w-5 h-5 text-gray-400" /> : <VolumeX className="w-5 h-5 text-gray-400" />}
              <span>Sound Effects</span>
            </div>
            <input
              type="checkbox"
              checked={soundEnabled}
              onChange={(e) => setSoundEnabled(e.target.checked)}
              className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
            />
          </label>
          
          <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg bg-gray-800/50 hover:bg-gray-800/70">
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-gray-400" />
              <span>Notifications</span>
            </div>
            <input
              type="checkbox"
              checked={notifications}
              onChange={(e) => setNotifications(e.target.checked)}
              className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
            />
          </label>
          
          <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg bg-gray-800/50 hover:bg-gray-800/70">
            <div className="flex items-center gap-3">
              <Database className="w-5 h-5 text-gray-400" />
              <span>Auto-save</span>
            </div>
            <input
              type="checkbox"
              checked={autoSave}
              onChange={(e) => setAutoSave(e.target.checked)}
              className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
            />
          </label>
        </div>
      </div>

      {/* Data Management */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Database className="w-5 h-5 text-cyan-400" />
          Data Management
        </h3>
        
        <div className="mb-4 p-3 bg-gray-800/50 rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm">Storage Used</span>
            <span className="text-sm text-purple-400">{dataUsage.toFixed(2)} KB</span>
          </div>
        </div>
        
        <div className="flex gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={exportSettings}
            className="flex-1 bg-gray-800 border border-gray-600 py-2 rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-gray-700"
          >
            <Download className="w-4 h-4" />
            Export
          </motion.button>
          
          <label className="flex-1">
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="bg-gray-800 border border-gray-600 py-2 rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-gray-700 cursor-pointer"
            >
              <Upload className="w-4 h-4" />
              Import
            </motion.div>
            <input
              type="file"
              accept=".json"
              onChange={importSettings}
              className="hidden"
            />
          </label>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={clearAllData}
            className="px-4 bg-red-600/20 border border-red-600/50 py-2 rounded-lg font-medium flex items-center gap-2 hover:bg-red-600/30"
          >
            <Trash2 className="w-4 h-4" />
          </motion.button>
        </div>
      </div>
    </div>
  )
}