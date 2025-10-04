'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { HotkeySettings } from './GlobalHotkeys'
import { OverlaySettings } from './OverlayWindowEnhanced'
import toast from 'react-hot-toast'
import { 
  SettingsIcon, MoonIcon, SunIcon, VolumeIcon, AlertCircleIcon, 
  KeyboardIcon, MonitorIcon, BellIcon, CreditCardIcon,
  PaletteIcon, ShieldIcon, SaveIcon, RefreshCwIcon,
  ClockIcon, GiftIcon, UserIcon, MailIcon, LogOutIcon,
  CrownIcon, CheckIcon, XIcon, ChevronRightIcon
} from 'lucide-react'

interface SettingsSection {
  id: string
  title: string
  icon: any
  description: string
}

export default function SettingsTabComplete() {
  const { user, logout } = useAuth()
  const [activeSection, setActiveSection] = useState('general')
  
  // Settings state
  const [settings, setSettings] = useState({
    // General
    theme: 'dark',
    language: 'en',
    autoSave: true,
    soundEffects: true,
    notifications: true,
    
    // Typing
    defaultProfile: 'Medium',
    autoStart: false,
    confirmStop: true,
    preserveFormatting: true,
    
    // Privacy & Security
    dataCollection: false,
    crashReports: true,
    encryptLocal: false,
    clearOnExit: false,
    
    // Schedule
    scheduleEnabled: false,
    scheduleTime: '09:00',
    scheduleDays: ['mon', 'tue', 'wed', 'thu', 'fri'],
    
    // Advanced
    cacheSize: 100,
    logLevel: 'info',
    experimentalFeatures: false,
    developerMode: false
  })
  
  const sections: SettingsSection[] = [
    { id: 'general', title: 'General', icon: SettingsIcon, description: 'App preferences' },
    { id: 'hotkeys', title: 'Hotkeys', icon: KeyboardIcon, description: 'Keyboard shortcuts' },
    { id: 'overlay', title: 'Overlay', icon: MonitorIcon, description: 'Floating window' },
    { id: 'typing', title: 'Typing', icon: KeyboardIcon, description: 'Automation settings' },
    { id: 'notifications', title: 'Notifications', icon: BellIcon, description: 'Alerts & sounds' },
    { id: 'schedule', title: 'Schedule', icon: ClockIcon, description: 'Automation timing' },
    { id: 'account', title: 'Account', icon: UserIcon, description: 'Profile & plan' },
    { id: 'referrals', title: 'Referrals', icon: GiftIcon, description: 'Invite friends' },
    { id: 'privacy', title: 'Privacy', icon: ShieldIcon, description: 'Security settings' },
    { id: 'advanced', title: 'Advanced', icon: SettingsIcon, description: 'Expert options' }
  ]
  
  // Load settings
  useEffect(() => {
    const saved = localStorage.getItem('slywriter-settings')
    if (saved) {
      setSettings({...settings, ...JSON.parse(saved)})
    }
  }, [])
  
  // Save settings
  const saveSettings = () => {
    localStorage.setItem('slywriter-settings', JSON.stringify(settings))
    toast.success('Settings saved!')
    
    // Apply theme
    if (settings.theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }
  
  const renderSection = () => {
    switch (activeSection) {
      case 'general':
        return <GeneralSettings settings={settings} setSettings={setSettings} />
      case 'hotkeys':
        return <HotkeySettings />
      case 'overlay':
        return <OverlaySettings />
      case 'typing':
        return <TypingSettings settings={settings} setSettings={setSettings} />
      case 'notifications':
        return <NotificationSettings settings={settings} setSettings={setSettings} />
      case 'schedule':
        return <ScheduleSettings settings={settings} setSettings={setSettings} />
      case 'account':
        return <AccountSettings user={user} logout={logout} />
      case 'referrals':
        return <ReferralSettings user={user} />
      case 'privacy':
        return <PrivacySettings settings={settings} setSettings={setSettings} />
      case 'advanced':
        return <AdvancedSettings settings={settings} setSettings={setSettings} />
      default:
        return null
    }
  }
  
  return (
    <div className="flex gap-6 h-full">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900/50 rounded-xl p-4 backdrop-blur-sm border border-gray-700/50">
        <h2 className="text-lg font-semibold text-white mb-4">Settings</h2>
        
        <div className="space-y-1">
          {sections.map((section) => {
            const Icon = section.icon
            return (
              <motion.button
                key={section.id}
                whileHover={{ x: 2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${
                  activeSection === section.id
                    ? 'bg-purple-500/20 bg-purple-500/10 text-purple-300 text-purple-400 border border-purple-500/50'
                    : 'hover:bg-gray-800/50 hover:bg-gray-800 text-gray-400'
                }`}
              >
                <Icon className="w-4 h-4" />
                <div className="text-left flex-1">
                  <div className="text-sm font-medium">{section.title}</div>
                  <div className="text-xs opacity-70">{section.description}</div>
                </div>
                {activeSection === section.id && (
                  <ChevronRightIcon className="w-4 h-4" />
                )}
              </motion.button>
            )
          })}
        </div>
        
        {/* Save Button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={saveSettings}
          className="w-full mt-6 px-4 py-2 bg-purple-500 bg-purple-500 hover:bg-purple-600 hover:bg-purple-500-dark rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
          <SaveIcon className="w-4 h-4" />
          Save All Settings
        </motion.button>
      </div>
      
      {/* Content */}
      <div className="flex-1 bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeSection}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {renderSection()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}

// General Settings Component
function GeneralSettings({ settings, setSettings }: any) {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-white mb-4">General Settings</h3>
      
      {/* Theme */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Theme</div>
          <div className="text-xs text-gray-400">Choose your interface theme</div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setSettings({...settings, theme: 'light'})}
            className={`p-2 rounded-lg transition-all ${
              settings.theme === 'light' 
                ? 'bg-yellow-500/20 text-yellow-400' 
                : 'bg-gray-700 bg-gray-800 text-gray-400'
            }`}
          >
            <SunIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => setSettings({...settings, theme: 'dark'})}
            className={`p-2 rounded-lg transition-all ${
              settings.theme === 'dark' 
                ? 'bg-purple-500/20 bg-purple-500/10 text-purple-400' 
                : 'bg-gray-700 bg-gray-800 text-gray-400'
            }`}
          >
            <MoonIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Auto Save */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Auto Save</div>
          <div className="text-xs text-gray-400">Automatically save your work</div>
        </div>
        <input
          type="checkbox"
          checked={settings.autoSave}
          onChange={(e) => setSettings({...settings, autoSave: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      {/* Sound Effects */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Sound Effects</div>
          <div className="text-xs text-gray-400">Play sounds for actions</div>
        </div>
        <input
          type="checkbox"
          checked={settings.soundEffects}
          onChange={(e) => setSettings({...settings, soundEffects: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      {/* Language */}
      <div className="p-4 bg-gray-800 rounded-lg">
        <label className="text-sm font-medium text-white block mb-2">Language</label>
        <select
          value={settings.language}
          onChange={(e) => {
            setSettings({...settings, language: e.target.value})
            const languages: Record<string, string> = {
              en: 'English',
              es: 'Spanish',
              fr: 'French',
              de: 'German',
              ja: 'Japanese'
            }
            toast.success(`Language changed to ${languages[e.target.value]}`)
          }}
          className="w-full bg-gray-700 bg-gray-800 rounded-lg px-3 py-2 text-sm text-white border border-gray-600 border-gray-700 focus:border-purple-500 focus:border-purple-500 focus:outline-none"
        >
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="ja">Japanese</option>
        </select>
      </div>

      {/* Check for Updates (Electron only) */}
      {typeof window !== 'undefined' && (window as any).electron && (
        <div className="p-4 bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-500/30 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-white">App Updates</div>
              <div className="text-xs text-gray-400">Check for the latest version</div>
            </div>
            <button
              onClick={async () => {
                toast.loading('Checking for updates...', { id: 'manual-update-check' })
                try {
                  const result = await (window as any).electron.ipcRenderer.invoke('check-for-updates')
                  console.log('Manual update check result:', result)

                  // Get current version
                  const version = await (window as any).electron.ipcRenderer.invoke('get-app-version')

                  // The actual update status will come via IPC events
                  setTimeout(() => {
                    toast.dismiss('manual-update-check')
                  }, 3000)
                } catch (error) {
                  console.error('Update check failed:', error)
                  toast.error('Failed to check for updates', { id: 'manual-update-check' })
                }
              }}
              className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg text-sm font-medium transition-all flex items-center gap-2"
            >
              <RefreshCwIcon className="w-4 h-4" />
              Check for Updates
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// Typing Settings Component
function TypingSettings({ settings, setSettings }: any) {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-white mb-4">Typing Settings</h3>
      
      {/* Default Profile */}
      <div className="p-4 bg-gray-800 rounded-lg">
        <label className="text-sm font-medium text-white block mb-2">Default Profile</label>
        <select
          value={settings.defaultProfile}
          onChange={(e) => setSettings({...settings, defaultProfile: e.target.value})}
          className="w-full bg-gray-700 bg-gray-800 rounded-lg px-3 py-2 text-sm text-white border border-gray-600 border-gray-700 focus:border-purple-500 focus:border-purple-500 focus:outline-none"
        >
          <option value="Slow">Slow (~60 WPM)</option>
          <option value="Medium">Medium (~100 WPM)</option>
          <option value="Fast">Fast (~180 WPM)</option>
          <option value="Essay">Essay (AI Enhanced)</option>
          <option value="Custom">Custom</option>
        </select>
      </div>
      
      {/* Auto Start */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Auto Start</div>
          <div className="text-xs text-gray-400">Start typing immediately after generation</div>
        </div>
        <input
          type="checkbox"
          checked={settings.autoStart}
          onChange={(e) => setSettings({...settings, autoStart: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      {/* Confirm Stop */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Confirm Stop</div>
          <div className="text-xs text-gray-400">Ask before stopping typing session</div>
        </div>
        <input
          type="checkbox"
          checked={settings.confirmStop}
          onChange={(e) => setSettings({...settings, confirmStop: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      {/* Preserve Formatting */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Preserve Formatting</div>
          <div className="text-xs text-gray-400">Keep original text formatting</div>
        </div>
        <input
          type="checkbox"
          checked={settings.preserveFormatting}
          onChange={(e) => setSettings({...settings, preserveFormatting: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
    </div>
  )
}

// Notification Settings Component
function NotificationSettings({ settings, setSettings }: any) {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-white mb-4">Notification Settings</h3>
      
      {/* Enable Notifications */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Enable Notifications</div>
          <div className="text-xs text-gray-400">Show system notifications</div>
        </div>
        <input
          type="checkbox"
          checked={settings.notifications}
          onChange={(e) => setSettings({...settings, notifications: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      <div className="space-y-3">
        <label className="text-sm font-medium text-white">Notify me about:</label>
        
        {['Typing complete', 'Errors', 'Daily limit warnings', 'New features'].map((item) => (
          <div key={item} className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg">
            <input type="checkbox" defaultChecked className="accent-purple-500" />
            <span className="text-sm text-gray-300">{item}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Schedule Settings Component
function ScheduleSettings({ settings, setSettings }: any) {
  const days = [
    { id: 'mon', label: 'Mon' },
    { id: 'tue', label: 'Tue' },
    { id: 'wed', label: 'Wed' },
    { id: 'thu', label: 'Thu' },
    { id: 'fri', label: 'Fri' },
    { id: 'sat', label: 'Sat' },
    { id: 'sun', label: 'Sun' }
  ]
  
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-white mb-4">Schedule Settings</h3>
      
      {/* Enable Schedule */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Enable Schedule</div>
          <div className="text-xs text-gray-400">Automate typing at specific times</div>
        </div>
        <input
          type="checkbox"
          checked={settings.scheduleEnabled}
          onChange={(e) => setSettings({...settings, scheduleEnabled: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      {settings.scheduleEnabled && (
        <>
          {/* Time */}
          <div className="p-4 bg-gray-800 rounded-lg">
            <label className="text-sm font-medium text-white block mb-2">Daily Time</label>
            <input
              type="time"
              value={settings.scheduleTime}
              onChange={(e) => setSettings({...settings, scheduleTime: e.target.value})}
              className="bg-gray-700 bg-gray-800 rounded-lg px-3 py-2 text-sm text-white border border-gray-600 border-gray-700 focus:border-purple-500 focus:border-purple-500 focus:outline-none"
            />
          </div>
          
          {/* Days */}
          <div className="p-4 bg-gray-800 rounded-lg">
            <label className="text-sm font-medium text-white block mb-3">Active Days</label>
            <div className="flex gap-2">
              {days.map((day) => (
                <button
                  key={day.id}
                  onClick={() => {
                    const newDays = settings.scheduleDays.includes(day.id)
                      ? settings.scheduleDays.filter((d: string) => d !== day.id)
                      : [...settings.scheduleDays, day.id]
                    setSettings({...settings, scheduleDays: newDays})
                  }}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                    settings.scheduleDays.includes(day.id)
                      ? 'bg-purple-500 bg-purple-500 text-white text-white'
                      : 'bg-gray-700 bg-gray-800 text-gray-400'
                  }`}
                >
                  {day.label}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// Account Settings Component
function AccountSettings({ user, logout }: any) {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-white mb-4">Account Settings</h3>
      
      {user ? (
        <>
          {/* User Info */}
          <div className="p-4 bg-gray-800 rounded-lg">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                <UserIcon className="w-8 h-8 text-white" />
              </div>
              <div>
                <div className="text-lg font-medium text-white">{user.name || user.email}</div>
                <div className="text-sm text-gray-400">{user.email}</div>
                <div className="flex items-center gap-2 mt-1">
                  {user.plan === 'premium' && <CrownIcon className="w-4 h-4 text-yellow-400" />}
                  <span className="text-xs bg-purple-500/20 bg-purple-500/10 px-2 py-0.5 rounded-full text-purple-300 text-purple-400">
                    {user.plan.toUpperCase()} PLAN
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Usage Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-800 rounded-lg">
              <div className="text-2xl font-bold text-purple-400">{user.words_used_today || 0}</div>
              <div className="text-xs text-gray-400">Words Used Today</div>
            </div>
            <div className="p-4 bg-gray-800 rounded-lg">
              <div className="text-2xl font-bold text-blue-400">{user.daily_limit || 4000}</div>
              <div className="text-xs text-gray-400">Daily Limit</div>
            </div>
          </div>
          
          {/* Actions */}
          <div className="space-y-3">
            <button className="w-full p-3 bg-purple-500 bg-purple-500 hover:bg-purple-600 hover:bg-purple-500-dark rounded-lg font-medium transition-colors">
              Upgrade to Premium
            </button>
            <button 
              onClick={logout}
              className="w-full p-3 bg-gray-700 bg-gray-800 hover:bg-gray-600 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              <LogOutIcon className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </>
      ) : (
        <div className="text-center py-8">
          <UserIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-400">Not signed in</p>
          <button className="mt-4 px-6 py-2 bg-purple-500 bg-purple-500 hover:bg-purple-600 hover:bg-purple-500-dark rounded-lg font-medium transition-colors">
            Sign In with Google
          </button>
        </div>
      )}
    </div>
  )
}

// Referral Settings Component
function ReferralSettings({ user }: any) {
  const referralCode = user?.referral_code || 'SLYWRITER123'
  const referralLink = `https://slywriter.com/ref/${referralCode}`
  
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-white mb-4">Referral Program</h3>
      
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="p-4 bg-gray-800 rounded-lg text-center">
          <div className="text-2xl font-bold text-purple-400">{user?.referral_count || 0}</div>
          <div className="text-xs text-gray-400">Referrals</div>
        </div>
        <div className="p-4 bg-gray-800 rounded-lg text-center">
          <div className="text-2xl font-bold text-green-400">{user?.referral_bonus || 0}</div>
          <div className="text-xs text-gray-400">Bonus Words</div>
        </div>
        <div className="p-4 bg-gray-800 rounded-lg text-center">
          <div className="text-2xl font-bold text-yellow-400">1000</div>
          <div className="text-xs text-gray-400">Words per Referral</div>
        </div>
      </div>
      
      {/* Referral Link */}
      <div className="p-4 bg-gray-800 rounded-lg">
        <label className="text-sm font-medium text-white block mb-2">Your Referral Link</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={referralLink}
            readOnly
            className="flex-1 bg-gray-700 bg-gray-800 rounded-lg px-3 py-2 text-sm text-white border border-gray-600 border-gray-700"
          />
          <button
            onClick={() => {
              navigator.clipboard.writeText(referralLink)
              toast.success('Link copied!')
            }}
            className="px-4 py-2 bg-purple-500 bg-purple-500 hover:bg-purple-600 hover:bg-purple-500-dark rounded-lg text-white transition-colors"
          >
            Copy
          </button>
        </div>
      </div>
      
      {/* How it Works */}
      <div className="p-4 bg-purple-500/10 rounded-lg border border-purple-500/30">
        <h4 className="text-sm font-medium text-purple-300 text-purple-400 mb-2">How It Works</h4>
        <ol className="space-y-2 text-xs text-purple-200">
          <li>1. Share your referral link with friends</li>
          <li>2. They sign up using your link</li>
          <li>3. You get 1000 bonus words for every 2 referrals</li>
          <li>4. They get 500 bonus words as a welcome gift</li>
        </ol>
      </div>
    </div>
  )
}

// Privacy Settings Component
function PrivacySettings({ settings, setSettings }: any) {
  const [betaTelemetryEnabled, setBetaTelemetryEnabled] = useState(true)
  const [betaUserId, setBetaUserId] = useState('')
  
  useEffect(() => {
    // Load beta telemetry settings
    const enabled = localStorage.getItem('betaTelemetryEnabled') !== 'false'
    setBetaTelemetryEnabled(enabled)
    setBetaUserId(localStorage.getItem('betaUserId') || 'Not generated')
  }, [])
  
  const toggleBetaTelemetry = (enabled: boolean) => {
    setBetaTelemetryEnabled(enabled)
    localStorage.setItem('betaTelemetryEnabled', enabled.toString())
    toast.success(enabled ? 'Beta telemetry enabled' : 'Beta telemetry disabled')
  }
  
  const exportMyData = () => {
    const data = JSON.parse(localStorage.getItem('betaTelemetryData') || '[]')
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `my_telemetry_data_${new Date().toISOString()}.json`
    a.click()
    toast.success('Your data exported successfully')
  }
  
  const clearMyData = () => {
    if (confirm('This will clear all your locally stored telemetry data. Continue?')) {
      localStorage.removeItem('betaTelemetryData')
      toast.success('Your telemetry data has been cleared')
    }
  }
  
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-white mb-4">Privacy & Security</h3>
      
      {/* Beta Testing Notice */}
      <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4 mb-4">
        <div className="flex items-start gap-3">
          <AlertCircleIcon className="w-5 h-5 text-orange-400 mt-0.5" />
          <div>
            <div className="text-sm font-semibold text-orange-300 mb-1">Beta Testing Mode Active</div>
            <div className="text-xs text-gray-300">
              You're using a beta version that collects anonymous usage data to improve the app.
              No personal information or typed content is ever collected.
            </div>
          </div>
        </div>
      </div>
      
      {/* Beta Telemetry Control */}
      <div className="bg-gray-800 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-white flex items-center gap-2">
              Beta Telemetry
              <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 text-xs rounded">BETA</span>
            </div>
            <div className="text-xs text-gray-400">Anonymous app usage and error tracking</div>
          </div>
          <button
            onClick={() => toggleBetaTelemetry(!betaTelemetryEnabled)}
            className={`relative w-14 h-7 rounded-full transition-colors ${
              betaTelemetryEnabled ? 'bg-green-500' : 'bg-gray-600'
            }`}
          >
            <div
              className={`absolute top-1 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                betaTelemetryEnabled ? 'translate-x-7' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        
        {/* Beta User ID */}
        <div className="pt-2 border-t border-gray-700">
          <div className="text-xs text-gray-400 mb-1">Your Anonymous Beta ID:</div>
          <code className="text-xs text-purple-300 font-mono bg-gray-900 px-2 py-1 rounded">
            {betaUserId}
          </code>
        </div>
        
        {/* Data Actions */}
        <div className="flex gap-2 pt-2">
          <button
            onClick={exportMyData}
            className="flex-1 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-xs text-white rounded transition-colors"
          >
            Export My Data
          </button>
          <button
            onClick={clearMyData}
            className="flex-1 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-xs text-white rounded transition-colors"
          >
            Clear My Data
          </button>
        </div>
      </div>
      
      {/* Original Data Collection */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Usage Statistics</div>
          <div className="text-xs text-gray-400">Local statistics about your typing sessions</div>
        </div>
        <input
          type="checkbox"
          checked={settings.dataCollection}
          onChange={(e) => setSettings({...settings, dataCollection: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      {/* Crash Reports */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Crash Reports</div>
          <div className="text-xs text-gray-400">Send crash reports to help fix bugs</div>
        </div>
        <input
          type="checkbox"
          checked={settings.crashReports}
          onChange={(e) => setSettings({...settings, crashReports: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      {/* Encrypt Local Data */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Encrypt Local Data</div>
          <div className="text-xs text-gray-400">Encrypt data stored on your device</div>
        </div>
        <input
          type="checkbox"
          checked={settings.encryptLocal}
          onChange={(e) => setSettings({...settings, encryptLocal: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      {/* Clear on Exit */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Clear Data on Exit</div>
          <div className="text-xs text-gray-400">Remove temporary data when closing app</div>
        </div>
        <input
          type="checkbox"
          checked={settings.clearOnExit}
          onChange={(e) => setSettings({...settings, clearOnExit: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      {/* Data Management */}
      <div className="space-y-3">
        <button 
          onClick={() => {
            if (confirm('Are you sure you want to clear all local data? This cannot be undone.')) {
              localStorage.clear()
              toast.success('All local data cleared')
              setTimeout(() => window.location.reload(), 1000)
            }
          }}
          className="w-full p-3 bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 rounded-lg text-red-300 font-medium transition-colors"
        >
          Clear All Local Data
        </button>
        <button 
          onClick={() => {
            const data = {
              settings: localStorage.getItem('slywriter-settings'),
              learning: localStorage.getItem('slywriter-learning'),
              profiles: localStorage.getItem('slywriter-profiles'),
              history: localStorage.getItem('aiHistory'),
              exportDate: new Date().toISOString()
            }
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `slywriter-data-${Date.now()}.json`
            a.click()
            toast.success('Data exported successfully')
          }}
          className="w-full p-3 bg-gray-700 bg-gray-800 hover:bg-gray-600 rounded-lg font-medium transition-colors"
        >
          Export My Data
        </button>
      </div>
    </div>
  )
}

// Advanced Settings Component
function AdvancedSettings({ settings, setSettings }: any) {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-white mb-4">Advanced Settings</h3>
      
      {/* Cache Size */}
      <div className="p-4 bg-gray-800 rounded-lg">
        <label className="text-sm font-medium text-white block mb-2">
          Cache Size (MB): {settings.cacheSize}
        </label>
        <input
          type="range"
          min="10"
          max="500"
          value={settings.cacheSize}
          onChange={(e) => setSettings({...settings, cacheSize: Number(e.target.value)})}
          className="w-full accent-purple-500"
        />
      </div>
      
      {/* Log Level */}
      <div className="p-4 bg-gray-800 rounded-lg">
        <label className="text-sm font-medium text-white block mb-2">Log Level</label>
        <select
          value={settings.logLevel}
          onChange={(e) => setSettings({...settings, logLevel: e.target.value})}
          className="w-full bg-gray-700 bg-gray-800 rounded-lg px-3 py-2 text-sm text-white border border-gray-600 border-gray-700 focus:border-purple-500 focus:border-purple-500 focus:outline-none"
        >
          <option value="error">Error</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
          <option value="debug">Debug</option>
        </select>
      </div>
      
      {/* Experimental Features */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Experimental Features</div>
          <div className="text-xs text-gray-400">Enable beta features (may be unstable)</div>
        </div>
        <input
          type="checkbox"
          checked={settings.experimentalFeatures}
          onChange={(e) => setSettings({...settings, experimentalFeatures: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      {/* Developer Mode */}
      <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
        <div>
          <div className="text-sm font-medium text-white">Developer Mode</div>
          <div className="text-xs text-gray-400">Show debug information and tools</div>
        </div>
        <input
          type="checkbox"
          checked={settings.developerMode}
          onChange={(e) => setSettings({...settings, developerMode: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      {/* Reset */}
      <div className="p-4 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
        <h4 className="text-sm font-medium text-yellow-300 mb-2">Danger Zone</h4>
        <button 
          onClick={() => {
            if (confirm('This will reset ALL settings to their default values. Continue?')) {
              localStorage.removeItem('slywriter-settings')
              setSettings({
                theme: 'dark',
                language: 'en',
                autoSave: true,
                soundEffects: false,
                notifications: true,
                defaultTypingSpeed: 100,
                autoCorrect: true,
                smartPunctuation: true,
                predictiveText: false,
                overlayPosition: 'top-right',
                overlayOpacity: 90,
                overlaySize: 'medium',
                dataCollection: false,
                crashReports: true,
                encryptLocal: false,
                clearOnExit: false,
                cacheSize: 50,
                logLevel: 'error',
                developerMode: false,
                experimentalFeatures: false,
                performanceMode: false
              })
              toast.success('All settings reset to defaults')
              setTimeout(() => window.location.reload(), 1500)
            }
          }}
          className="w-full p-2 bg-red-500 hover:bg-red-600 rounded-lg text-white font-medium transition-colors"
        >
          Reset All Settings to Default
        </button>
      </div>
    </div>
  )
}