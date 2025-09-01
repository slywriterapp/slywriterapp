'use client'

import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'

interface HotkeyConfig {
  start: string
  stop: string
  pause: string
  overlay: string
  ai_generation: string
}

// This component only handles hotkey settings UI
// All actual hotkey functionality is in GlobalHotkeyListener which uses Electron globalShortcut
export default function GlobalHotkeys() {
  // Empty component - all functionality moved to GlobalHotkeyListener
  return null
}

export function HotkeySettings() {
  const [hotkeys, setHotkeys] = useState<HotkeyConfig>(() => {
    // Load saved hotkeys on mount
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('slywriter-hotkeys')
      if (saved) {
        try {
          return JSON.parse(saved)
        } catch {
          // If parse fails, return defaults
        }
      }
    }
    return {
      start: 'ctrl+alt+s',
      stop: 'ctrl+alt+q',
      pause: 'ctrl+alt+p',
      overlay: 'ctrl+alt+o',
      ai_generation: 'ctrl+alt+g'
    }
  })
  
  const [editing, setEditing] = useState<string | null>(null)
  
  const saveHotkeys = () => {
    localStorage.setItem('slywriter-hotkeys', JSON.stringify(hotkeys))
    
    // Send updated hotkeys to Electron main process
    if (typeof window !== 'undefined' && window.electron?.ipcRenderer) {
      window.electron.ipcRenderer.send('update-hotkeys', hotkeys)
    }
    
    toast.success('Hotkeys saved!')
    
    // Reload the page to apply new hotkeys
    setTimeout(() => window.location.reload(), 1000)
  }
  
  const recordHotkey = (key: string) => {
    setEditing(key)
    toast('Press your desired key combination...', { icon: '⌨️' })
    
    const handler = (e: KeyboardEvent) => {
      e.preventDefault()
      
      const parts = []
      if (e.ctrlKey) parts.push('ctrl')
      if (e.altKey) parts.push('alt')
      if (e.shiftKey) parts.push('shift')
      if (e.metaKey) parts.push('cmd')
      
      // Get the actual key
      if (e.key && e.key !== 'Control' && e.key !== 'Alt' && e.key !== 'Shift' && e.key !== 'Meta') {
        parts.push(e.key.toLowerCase())
      }
      
      if (parts.length > 1) {
        const combo = parts.join('+')
        const newHotkeys = {...hotkeys, [key]: combo}
        setHotkeys(newHotkeys)
        setEditing(null)
        document.removeEventListener('keydown', handler)
        
        // Auto-save the new hotkey immediately
        localStorage.setItem('slywriter-hotkeys', JSON.stringify(newHotkeys))
        
        // Send to Electron immediately
        if (typeof window !== 'undefined' && window.electron?.ipcRenderer) {
          window.electron.ipcRenderer.send('update-hotkeys', newHotkeys)
        }
        
        toast.success(`Hotkey set to ${combo} and saved!`)
      }
    }
    
    document.addEventListener('keydown', handler)
    
    // Remove listener after 5 seconds
    setTimeout(() => {
      document.removeEventListener('keydown', handler)
      if (editing === key) {
        setEditing(null)
        toast.error('Hotkey recording timeout')
      }
    }, 5000)
  }
  
  const hotkeyDescriptions: Record<string, string> = {
    start: 'Start typing from Type Here box or clipboard',
    stop: 'Emergency stop (Panic button)', 
    pause: 'Pause/Resume typing',
    overlay: 'Toggle overlay window',
    ai_generation: 'AI generate from highlighted text'
  }
  
  return (
    <div className="bg-gray-900/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700/50 border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-6">Global Hotkeys</h3>
      
      <div className="space-y-4">
        {Object.entries(hotkeys).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
            <div>
              <div className="text-sm font-medium text-white capitalize">
                {key.replace('_', ' ')}
              </div>
              <div className="text-xs text-gray-400">
                {hotkeyDescriptions[key]}
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <kbd className="px-3 py-1 bg-gray-800 rounded text-sm text-white font-mono">
                {editing === key ? 'Recording...' : value}
              </kbd>
              <button
                onClick={() => recordHotkey(key)}
                disabled={editing !== null}
                className="px-3 py-1 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-600 rounded text-sm text-white transition-colors"
              >
                {editing === key ? 'Press keys...' : 'Change'}
              </button>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-6 flex justify-end gap-3">
        <button
          onClick={() => {
            const defaultHotkeys = {
              start: 'ctrl+alt+s',
              stop: 'ctrl+alt+q',
              pause: 'ctrl+alt+p',
              overlay: 'ctrl+alt+o',
              ai_generation: 'ctrl+alt+g'
            }
            setHotkeys(defaultHotkeys)
            localStorage.setItem('slywriter-hotkeys', JSON.stringify(defaultHotkeys))
            
            // Send to Electron
            if (typeof window !== 'undefined' && window.electron?.ipcRenderer) {
              window.electron.ipcRenderer.send('update-hotkeys', defaultHotkeys)
            }
            
            toast.success('Reset to default hotkeys!')
          }}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition-colors"
        >
          Reset to Defaults
        </button>
        <button
          onClick={saveHotkeys}
          className="px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg text-white transition-colors"
        >
          Save Hotkeys
        </button>
      </div>
      
      <div className="mt-4 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
        <p className="text-xs text-yellow-300">
          <strong>Important:</strong> These hotkeys work globally across your entire computer when SlyWriter is running.
          The AI Generation hotkey (Ctrl+Alt+G) is the most powerful - highlight any text anywhere and press it!
        </p>
      </div>
    </div>
  )
}