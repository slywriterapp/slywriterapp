'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Settings, User, Palette, Keyboard, Bell, Shield, Database, Save, Upload, Download, Trash2, Moon, Sun, Monitor, Activity, Users, ChartBar } from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { RENDER_API_URL } from '../config/api'

interface Profile {
  id: string
  name: string
  speed: number
  typosEnabled: boolean
  aiFiller: boolean
  pauseFrequency: number
  theme: string
  hotkeys: {
    start: string
    pause: string
    stop: string
  }
}

// Helper function to convert speed slider (1-10) to approximate WPM
function speedToWPM(speed: number): number {
  // Map 1-10 scale to WPM (roughly 20-250 WPM range)
  const wpmMap: Record<number, number> = {
    1: 20,
    2: 30,
    3: 40,
    4: 55,
    5: 70,
    6: 85,
    7: 100,
    8: 130,
    9: 180,
    10: 250
  }
  return wpmMap[speed] || 70
}

export default function SettingsTab() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [activeProfile, setActiveProfile] = useState<string>('medium')
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null)
  const [theme, setTheme] = useState('dark')
  const [notifications, setNotifications] = useState(true)
  const [autoSave, setAutoSave] = useState(true)
  const [dataUsage, setDataUsage] = useState(0)
  const [dataCollection, setDataCollection] = useState(false)
  const [analyticsEnabled, setAnalyticsEnabled] = useState(false)
  const [betaTester, setBetaTester] = useState(false)

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
          id: 'slow',
          name: 'Slow',
          speed: 3, // ~40 WPM on scale of 1-10
          typosEnabled: false,
          aiFiller: false,
          pauseFrequency: 5,
          theme: 'dark',
          hotkeys: { start: 'Ctrl+Enter', pause: 'Space', stop: 'Escape' }
        },
        {
          id: 'medium',
          name: 'Medium',
          speed: 5, // ~70 WPM on scale of 1-10
          typosEnabled: false,
          aiFiller: false,
          pauseFrequency: 5,
          theme: 'dark',
          hotkeys: { start: 'Ctrl+Enter', pause: 'Space', stop: 'Escape' }
        },
        {
          id: 'fast',
          name: 'Fast',
          speed: 7, // ~100 WPM on scale of 1-10
          typosEnabled: false,
          aiFiller: false,
          pauseFrequency: 5,
          theme: 'dark',
          hotkeys: { start: 'Ctrl+Enter', pause: 'Space', stop: 'Escape' }
        },
        {
          id: 'lightning',
          name: 'Lightning',
          speed: 10, // ~250 WPM on scale of 1-10
          typosEnabled: false,
          aiFiller: false,
          pauseFrequency: 5,
          theme: 'dark',
          hotkeys: { start: 'Ctrl+Enter', pause: 'Space', stop: 'Escape' }
        },
        {
          id: 'custom',
          name: 'Custom',
          speed: 6, // Default ~85 WPM on scale of 1-10
          typosEnabled: false,
          aiFiller: false,
          pauseFrequency: 5,
          theme: 'dark',
          hotkeys: { start: 'Ctrl+Enter', pause: 'Space', stop: 'Escape' }
        }
      ]
      setProfiles(defaultProfiles)
      setCurrentProfile(defaultProfiles[1]) // Default to Medium profile
      localStorage.setItem('profiles', JSON.stringify(defaultProfiles))
    }

    // Calculate data usage
    const storageUsed = Object.keys(localStorage).reduce((acc, key) => {
      return acc + (localStorage.getItem(key)?.length || 0)
    }, 0)
    setDataUsage(storageUsed / 1024) // Convert to KB
    
    // Load data collection settings
    const dataCollectionSetting = localStorage.getItem('dataCollection')
    if (dataCollectionSetting !== null) {
      setDataCollection(dataCollectionSetting === 'true')
    }
    const analyticsSetting = localStorage.getItem('analyticsEnabled')
    if (analyticsSetting !== null) {
      setAnalyticsEnabled(analyticsSetting === 'true')
    }
    const betaTesterSetting = localStorage.getItem('betaTester')
    if (betaTesterSetting !== null) {
      setBetaTester(betaTesterSetting === 'true')
    }
    
    // Apply theme
    const savedTheme = localStorage.getItem('theme') || 'dark'
    setTheme(savedTheme)
    applyTheme(savedTheme)
    
  }, [activeProfile])

  const applyTheme = (themeName: string) => {
    if (themeName === 'light') {
      document.documentElement.classList.remove('dark')
      document.documentElement.classList.add('light')
    } else if (themeName === 'dark') {
      document.documentElement.classList.remove('light')
      document.documentElement.classList.add('dark')
    } else {
      // Auto - follow system preference
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      if (isDark) {
        document.documentElement.classList.add('dark')
        document.documentElement.classList.remove('light')
      } else {
        document.documentElement.classList.add('light')
        document.documentElement.classList.remove('dark')
      }
    }
  }

  const sendTelemetry = async (event: string, data: any) => {
    if (!dataCollection) return
    
    try {
      await axios.post(`${RENDER_API_URL}/api/telemetry`, {
        event,
        data,
        userId: localStorage.getItem('userId') || 'anonymous',
        timestamp: new Date().toISOString(),
        betaTester
      })
    } catch (error) {
      console.error('Failed to send telemetry:', error)
    }
  }

  const saveProfile = () => {
    if (!currentProfile) return
    
    const updatedProfiles = profiles.map(p => 
      p.id === currentProfile.id ? currentProfile : p
    )
    setProfiles(updatedProfiles)
    localStorage.setItem('profiles', JSON.stringify(updatedProfiles))
    localStorage.setItem('activeProfile', activeProfile)
    
    // Apply profile settings globally
    localStorage.setItem('typingSpeed', currentProfile.speed.toString())
    localStorage.setItem('typosEnabled', currentProfile.typosEnabled.toString())
    localStorage.setItem('aiFiller', currentProfile.aiFiller.toString())
    localStorage.setItem('pauseFrequency', currentProfile.pauseFrequency.toString())
    
    // Save the selected profile name for the typing tab
    localStorage.setItem('slywriter-selected-profile', currentProfile.name)
    
    // Send telemetry if enabled
    if (dataCollection) {
      sendTelemetry('profile_saved', { profileId: currentProfile.id, settings: currentProfile })
    }
    
    toast.success('Profile saved successfully!')
  }

  const createNewProfile = () => {
    const newProfile: Profile = {
      id: `custom-${Date.now()}`,
      name: 'Custom Profile',
      speed: 5,
      typosEnabled: false,
      aiFiller: false,
      pauseFrequency: 5,
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
        setNotifications(settings.notifications !== false)
        setAutoSave(settings.autoSave !== false)
        
        localStorage.setItem('profiles', JSON.stringify(settings.profiles || []))
        toast.success('Settings imported successfully!')
      } catch (error) {
        console.error('Failed to import settings:', error)
        toast.error('Failed to import settings')
      }
    }
    reader.readAsText(file)
  }

  const exportBetaTestData = async () => {
    try {
      // Collect all usage data
      const usageData = {
        profiles,
        activeProfile,
        theme,
          notifications,
        autoSave,
        dataCollection,
        analyticsEnabled,
        betaTester,
        localStorage: Object.keys(localStorage).reduce((acc, key) => {
          if (!key.includes('secret') && !key.includes('token')) {
            acc[key] = localStorage.getItem(key)
          }
          return acc
        }, {} as any),
        sessionHistory: JSON.parse(localStorage.getItem('sessionHistory') || '[]'),
        typingStats: JSON.parse(localStorage.getItem('typingStats') || '{}'),
        exportDate: new Date().toISOString(),
        userId: localStorage.getItem('userId') || 'anonymous'
      }
      
      // Send to server
      if (dataCollection) {
        await axios.post(`${RENDER_API_URL}/api/beta-data/export`, usageData)
        toast.success('Beta test data exported successfully!')
      }
      
      // Download locally
      const blob = new Blob([JSON.stringify(usageData, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `beta-test-data-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export beta test data:', error)
      toast.error('Failed to export data')
    }
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
                <div className="text-center text-purple-400 text-sm mt-1">~{speedToWPM(currentProfile.speed)} WPM</div>
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
            onClick={() => {
              setTheme('dark')
              localStorage.setItem('theme', 'dark')
              applyTheme('dark')
              if (dataCollection) sendTelemetry('theme_changed', { theme: 'dark' })
            }}
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
            onClick={() => {
              setTheme('light')
              localStorage.setItem('theme', 'light')
              applyTheme('light')
              if (dataCollection) sendTelemetry('theme_changed', { theme: 'light' })
            }}
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
            onClick={() => {
              setTheme('auto')
              localStorage.setItem('theme', 'auto')
              applyTheme('auto')
              if (dataCollection) sendTelemetry('theme_changed', { theme: 'auto' })
            }}
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
              <Bell className="w-5 h-5 text-gray-400" />
              <span>Notifications</span>
            </div>
            <input
              type="checkbox"
              checked={notifications}
              onChange={async (e) => {
                setNotifications(e.target.checked)
                localStorage.setItem('notifications', e.target.checked.toString())
                if (e.target.checked) {
                  // Request permission if needed
                  if ('Notification' in window && Notification.permission === 'default') {
                    const permission = await Notification.requestPermission()
                    if (permission === 'granted') {
                      toast.success('Notifications enabled')
                      new Notification('SlyWriter', { body: 'Notifications are now enabled' })
                    } else {
                      toast.error('Notification permission denied')
                      setNotifications(false)
                      localStorage.setItem('notifications', 'false')
                    }
                  } else if (Notification.permission === 'granted') {
                    toast.success('Notifications enabled')
                    new Notification('SlyWriter', { body: 'Notifications are now enabled' })
                  }
                }
                
                if (dataCollection) sendTelemetry('setting_changed', { setting: 'notifications', value: e.target.checked })
              }}
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
              onChange={(e) => {
                setAutoSave(e.target.checked)
                localStorage.setItem('autoSave', e.target.checked.toString())
                if (dataCollection) sendTelemetry('setting_changed', { setting: 'autoSave', value: e.target.checked })
              }}
              className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
            />
          </label>
        </div>
      </div>

      {/* Privacy & Data Collection */}
      <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-orange-400" />
          Privacy & Analytics
        </h3>
        
        <div className="space-y-3 mb-4">
          <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg bg-gray-800/50 hover:bg-gray-800/70">
            <div className="flex items-center gap-3">
              <ChartBar className="w-5 h-5 text-gray-400" />
              <div>
                <span>Usage Analytics</span>
                <p className="text-xs text-gray-500 mt-1">Help improve SlyWriter by sharing anonymous usage data</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={dataCollection}
              onChange={(e) => {
                setDataCollection(e.target.checked)
                localStorage.setItem('dataCollection', e.target.checked.toString())
                if (e.target.checked) {
                  // Generate user ID if not exists
                  if (!localStorage.getItem('userId')) {
                    localStorage.setItem('userId', `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
                  }
                  sendTelemetry('analytics_enabled', {})
                }
                toast.success(e.target.checked ? 'Analytics enabled' : 'Analytics disabled')
              }}
              className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
            />
          </label>
          
          <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg bg-gray-800/50 hover:bg-gray-800/70">
            <div className="flex items-center gap-3">
              <Users className="w-5 h-5 text-gray-400" />
              <div>
                <span>Beta Testing Program</span>
                <p className="text-xs text-gray-500 mt-1">Join our beta program to test new features early</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={betaTester}
              onChange={(e) => {
                setBetaTester(e.target.checked)
                localStorage.setItem('betaTester', e.target.checked.toString())
                if (dataCollection) sendTelemetry('beta_status_changed', { enrolled: e.target.checked })
                toast.success(e.target.checked ? 'Welcome to the beta program!' : 'Left beta program')
              }}
              className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
            />
          </label>
          
          <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg bg-gray-800/50 hover:bg-gray-800/70">
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-gray-400" />
              <div>
                <span>Performance Metrics</span>
                <p className="text-xs text-gray-500 mt-1">Track typing speed and accuracy over time</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={analyticsEnabled}
              onChange={(e) => {
                setAnalyticsEnabled(e.target.checked)
                localStorage.setItem('analyticsEnabled', e.target.checked.toString())
                if (dataCollection) sendTelemetry('performance_tracking', { enabled: e.target.checked })
              }}
              className="w-5 h-5 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
            />
          </label>
        </div>
        
        {betaTester && dataCollection && (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={exportBetaTestData}
            className="w-full mb-4 bg-gradient-to-r from-orange-600 to-red-600 py-2 rounded-lg font-medium flex items-center justify-center gap-2"
          >
            <Upload className="w-4 h-4" />
            Export Beta Test Data
          </motion.button>
        )}
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