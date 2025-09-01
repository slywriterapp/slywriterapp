import { useState, useEffect } from 'react'

interface Hotkeys {
  start: string
  stop: string
  pause: string
  overlay: string
  ai_generation: string
}

const defaultHotkeys: Hotkeys = {
  start: 'Ctrl+Alt+S',
  stop: 'Ctrl+Alt+Q',
  pause: 'Ctrl+Alt+P',
  overlay: 'Ctrl+Alt+O',
  ai_generation: 'Ctrl+Alt+G'
}

export function useHotkeys() {
  const [hotkeys, setHotkeys] = useState<Hotkeys>(defaultHotkeys)

  useEffect(() => {
    // Load hotkeys from localStorage
    const loadHotkeys = () => {
      try {
        const saved = localStorage.getItem('slywriter-hotkeys')
        if (saved) {
          const parsed = JSON.parse(saved)
          // Convert from storage format to display format
          const displayHotkeys: Hotkeys = {
            start: formatHotkey(parsed.start || defaultHotkeys.start),
            stop: formatHotkey(parsed.stop || defaultHotkeys.stop),
            pause: formatHotkey(parsed.pause || defaultHotkeys.pause),
            overlay: formatHotkey(parsed.overlay || defaultHotkeys.overlay),
            ai_generation: formatHotkey(parsed.ai_generation || defaultHotkeys.ai_generation)
          }
          setHotkeys(displayHotkeys)
        }
      } catch (err) {
        console.error('Error loading hotkeys:', err)
      }
    }

    loadHotkeys()

    // Listen for hotkey updates
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'slywriter-hotkeys') {
        loadHotkeys()
      }
    }

    window.addEventListener('storage', handleStorageChange)
    
    // Also listen for custom event when hotkeys are updated
    const handleHotkeyUpdate = () => {
      loadHotkeys()
    }
    
    window.addEventListener('hotkeys-updated', handleHotkeyUpdate)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('hotkeys-updated', handleHotkeyUpdate)
    }
  }, [])

  return hotkeys
}

// Format hotkey for display
function formatHotkey(key: string): string {
  return key
    .replace('CommandOrControl', 'Ctrl')
    .replace('cmd', 'Cmd')
    .replace('ctrl', 'Ctrl')
    .replace('alt', 'Alt')
    .replace('shift', 'Shift')
    .replace(/\+/g, '+')
}