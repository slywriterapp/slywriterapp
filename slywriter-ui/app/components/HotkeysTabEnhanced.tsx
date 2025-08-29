'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import toast from 'react-hot-toast'
import { 
  KeyboardIcon, SaveIcon, RotateCcwIcon, AlertCircleIcon,
  PlayIcon, StopCircleIcon, PauseIcon, MicIcon, 
  CircleIcon, CheckIcon, XIcon, InfoIcon
} from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://slywriterapp.onrender.com'

interface Hotkey {
  action: string
  combination: string
  description: string
  icon: React.ElementType
}

export default function HotkeysTabEnhanced() {
  const [hotkeys, setHotkeys] = useState<Record<string, string>>({
    start: 'Ctrl+Shift+S',
    stop: 'Ctrl+Shift+X',
    pause: 'Ctrl+Shift+P',
    voice: 'Ctrl+Shift+V'
  })
  
  const [isRecording, setIsRecording] = useState(false)
  const [recordingAction, setRecordingAction] = useState<string | null>(null)
  const [pressedKeys, setPressedKeys] = useState<Set<string>>(new Set())
  const [showConflictWarning, setShowConflictWarning] = useState(false)
  const [conflicts, setConflicts] = useState<string[]>([])
  
  // Load hotkeys from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedHotkeys = localStorage.getItem('slywriter-hotkeys')
      if (savedHotkeys) {
        try {
          setHotkeys(JSON.parse(savedHotkeys))
        } catch (e) {
          console.error('Failed to load hotkeys:', e)
        }
      }
    }
    
    // Check recording status periodically
    const interval = setInterval(checkRecordingStatus, 1000)
    return () => clearInterval(interval)
  }, [])
  
  // Save hotkeys to localStorage
  const saveHotkeys = useCallback((newHotkeys: Record<string, string>) => {
    setHotkeys(newHotkeys)
    if (typeof window !== 'undefined') {
      localStorage.setItem('slywriter-hotkeys', JSON.stringify(newHotkeys))
    }
  }, [])
  
  // Check if hotkey recording is active on backend
  const checkRecordingStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/hotkeys/recording-status`)
      if (response.data.is_recording && !isRecording) {
        // Backend is recording but frontend doesn't know
        toast.warning('Hotkey recording active on another tab')
      }
    } catch (error) {
      // Ignore errors for status check
    }
  }
  
  // Start recording a hotkey
  const startRecording = async (action: string) => {
    try {
      // Notify backend to start recording
      await axios.post(`${API_URL}/api/hotkeys/record`, {
        action,
        recording: true
      })
      
      setIsRecording(true)
      setRecordingAction(action)
      setPressedKeys(new Set())
      
      toast.success(`Recording hotkey for ${action}. Press your key combination...`)
      
      // Listen for key presses
      document.addEventListener('keydown', handleKeyDown)
      document.addEventListener('keyup', handleKeyUp)
      
      // Auto-stop after 5 seconds
      setTimeout(() => {
        if (isRecording) {
          stopRecording(false)
          toast.error('Recording timeout. Please try again.')
        }
      }, 5000)
      
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start recording')
      setIsRecording(false)
      setRecordingAction(null)
    }
  }
  
  // Stop recording
  const stopRecording = async (save: boolean = true) => {
    try {
      // Notify backend to stop recording
      await axios.post(`${API_URL}/api/hotkeys/record`, {
        action: recordingAction,
        recording: false
      })
      
      // Remove event listeners
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('keyup', handleKeyUp)
      
      if (save && pressedKeys.size > 0 && recordingAction) {
        const combination = Array.from(pressedKeys).join('+')
        
        // Check for conflicts
        const conflictingActions = Object.entries(hotkeys)
          .filter(([action, combo]) => action !== recordingAction && combo === combination)
          .map(([action]) => action)
        
        if (conflictingActions.length > 0) {
          setConflicts(conflictingActions)
          setShowConflictWarning(true)
          toast.warning(`This combination is already used for: ${conflictingActions.join(', ')}`)
        }
        
        // Register the hotkey
        await axios.post(`${API_URL}/api/hotkeys/register`, {
          action: recordingAction,
          combination
        })
        
        // Save locally
        const newHotkeys = { ...hotkeys, [recordingAction]: combination }
        saveHotkeys(newHotkeys)
        
        toast.success(`Hotkey set: ${combination} for ${recordingAction}`)
      }
      
    } catch (error: any) {
      toast.error('Failed to save hotkey')
    } finally {
      setIsRecording(false)
      setRecordingAction(null)
      setPressedKeys(new Set())
    }
  }
  
  // Handle key press during recording
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    const key = getKeyName(e)
    setPressedKeys(prev => new Set([...prev, key]))
    
    // Stop recording on Escape
    if (e.key === 'Escape') {
      stopRecording(false)
      toast('Recording cancelled', { icon: 'ℹ️' })
    }
  }, [])
  
  const handleKeyUp = useCallback((e: KeyboardEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    // Auto-save when all keys are released
    if (pressedKeys.size > 0) {
      setTimeout(() => {
        if (isRecording) {
          stopRecording(true)
        }
      }, 100)
    }
  }, [pressedKeys, isRecording])
  
  // Convert KeyboardEvent to readable key name
  const getKeyName = (e: KeyboardEvent): string => {
    const keys: string[] = []
    
    if (e.ctrlKey || e.key === 'Control') keys.push('Ctrl')
    if (e.shiftKey || e.key === 'Shift') keys.push('Shift')
    if (e.altKey || e.key === 'Alt') keys.push('Alt')
    if (e.metaKey || e.key === 'Meta') keys.push('Cmd')
    
    // Add the actual key if it's not a modifier
    if (!['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) {
      keys.push(e.key.toUpperCase())
    }
    
    return keys.filter((v, i, a) => a.indexOf(v) === i).join('+')
  }
  
  // Reset hotkey to default
  const resetHotkey = (action: string) => {
    const defaults: Record<string, string> = {
      start: 'Ctrl+Shift+S',
      stop: 'Ctrl+Shift+X',
      pause: 'Ctrl+Shift+P',
      voice: 'Ctrl+Shift+V'
    }
    
    const newHotkeys = { ...hotkeys, [action]: defaults[action] }
    saveHotkeys(newHotkeys)
    toast.success(`Reset ${action} to default`)
  }
  
  // Test a hotkey
  const testHotkey = (action: string) => {
    toast.success(`Press ${hotkeys[action]} to trigger ${action}`)
    
    // Register temporary listener
    const handler = (e: KeyboardEvent) => {
      const pressed = getKeyName(e)
      if (pressed === hotkeys[action]) {
        e.preventDefault()
        toast.success(`✅ ${action} hotkey works!`)
        document.removeEventListener('keydown', handler)
      }
    }
    
    document.addEventListener('keydown', handler)
    
    // Remove listener after 5 seconds
    setTimeout(() => {
      document.removeEventListener('keydown', handler)
    }, 5000)
  }
  
  const hotkeyConfig: Hotkey[] = [
    {
      action: 'start',
      combination: hotkeys.start,
      description: 'Start typing the text',
      icon: PlayIcon
    },
    {
      action: 'stop',
      combination: hotkeys.stop,
      description: 'Stop typing immediately',
      icon: StopCircleIcon
    },
    {
      action: 'pause',
      combination: hotkeys.pause,
      description: 'Pause/Resume typing',
      icon: PauseIcon
    },
    {
      action: 'voice',
      combination: hotkeys.voice,
      description: 'Start voice input',
      icon: MicIcon
    }
  ]
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <KeyboardIcon className="text-purple-400" size={28} />
            <h2 className="text-2xl font-bold text-white">Hotkey Configuration</h2>
          </div>
          
          {isRecording && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-2 px-4 py-2 bg-red-500 rounded-lg"
            >
              <CircleIcon className="animate-pulse fill-current" size={20} />
              <span className="font-semibold">Recording {recordingAction}...</span>
            </motion.div>
          )}
        </div>
        
        {/* Info box */}
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4 mb-4">
          <div className="flex items-start gap-3">
            <InfoIcon className="text-blue-400 mt-0.5" size={20} />
            <div className="text-sm text-gray-300">
              <p className="mb-2">
                <strong>Dynamic Hotkeys:</strong> Your custom hotkeys are displayed throughout the app.
              </p>
              <p>
                <strong>Recording Protection:</strong> All typing operations are blocked while recording hotkeys to prevent conflicts.
              </p>
            </div>
          </div>
        </div>
        
        {/* Current hotkey display during recording */}
        {isRecording && pressedKeys.size > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-800 rounded-lg p-4 mb-4 text-center"
          >
            <p className="text-sm text-gray-400 mb-2">Current combination:</p>
            <p className="text-2xl font-bold text-purple-400">
              {Array.from(pressedKeys).join(' + ')}
            </p>
          </motion.div>
        )}
      </div>
      
      {/* Hotkey List */}
      <div className="grid gap-4">
        {hotkeyConfig.map((hotkey) => {
          const Icon = hotkey.icon
          const isCurrentlyRecording = isRecording && recordingAction === hotkey.action
          
          return (
            <motion.div
              key={hotkey.action}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className={`
                bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border
                ${isCurrentlyRecording 
                  ? 'border-red-500 shadow-lg shadow-red-500/20' 
                  : 'border-purple-500/20'
                }
                transition-all duration-300
              `}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`
                    p-3 rounded-lg
                    ${isCurrentlyRecording ? 'bg-red-500/20' : 'bg-purple-500/20'}
                  `}>
                    <Icon className={
                      isCurrentlyRecording ? 'text-red-400' : 'text-purple-400'
                    } size={24} />
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold text-white capitalize">
                      {hotkey.action}
                    </h3>
                    <p className="text-sm text-gray-400">{hotkey.description}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  {/* Current hotkey display */}
                  <div className="px-4 py-2 bg-gray-800 rounded-lg">
                    <code className="text-purple-400 font-mono font-semibold">
                      {hotkey.combination}
                    </code>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex gap-2">
                    {isCurrentlyRecording ? (
                      <>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => stopRecording(true)}
                          className="p-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                          title="Save"
                        >
                          <CheckIcon size={18} />
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => stopRecording(false)}
                          className="p-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                          title="Cancel"
                        >
                          <XIcon size={18} />
                        </motion.button>
                      </>
                    ) : (
                      <>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => startRecording(hotkey.action)}
                          disabled={isRecording}
                          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-semibold transition-colors"
                        >
                          Record
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => testHotkey(hotkey.action)}
                          disabled={isRecording}
                          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 rounded-lg font-semibold transition-colors"
                        >
                          Test
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => resetHotkey(hotkey.action)}
                          disabled={isRecording}
                          className="p-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 rounded-lg transition-colors"
                          title="Reset to default"
                        >
                          <RotateCcwIcon size={18} />
                        </motion.button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>
      
      {/* Conflict Warning */}
      <AnimatePresence>
        {showConflictWarning && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="bg-yellow-900/20 border border-yellow-500/30 rounded-xl p-4"
          >
            <div className="flex items-start gap-3">
              <AlertCircleIcon className="text-yellow-400 mt-0.5" size={20} />
              <div>
                <p className="text-yellow-400 font-semibold mb-1">Hotkey Conflict</p>
                <p className="text-sm text-gray-300">
                  This combination is already used for: {conflicts.join(', ')}
                </p>
                <button
                  onClick={() => setShowConflictWarning(false)}
                  className="mt-2 text-sm text-yellow-400 hover:text-yellow-300 underline"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Tips */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
        <h3 className="text-lg font-semibold text-white mb-3">Tips</h3>
        <ul className="space-y-2 text-sm text-gray-400">
          <li>• Press <code className="text-purple-400">ESC</code> to cancel recording</li>
          <li>• Hotkeys work globally when the app is focused</li>
          <li>• Your custom hotkeys are automatically saved and synced</li>
          <li>• Test your hotkeys to ensure they work correctly</li>
          <li>• All operations are blocked during hotkey recording to prevent conflicts</li>
        </ul>
      </div>
    </div>
  )
}