'use client'

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import Draggable from 'react-draggable'
import { XIcon, MoveIcon, ActivityIcon, PauseIcon, PlayIcon } from 'lucide-react'

interface OverlayProps {
  isVisible: boolean
  onClose: () => void
}

export default function OverlayWindowEnhanced({ isVisible, onClose }: OverlayProps) {
  const [status, setStatus] = useState('Ready')
  const [wpm, setWpm] = useState(0)
  const [progress, setProgress] = useState(0)
  const [opacity, setOpacity] = useState(0.9)
  const [size, setSize] = useState({ width: 250, height: 80 })
  const [position, setPosition] = useState({ x: 20, y: 20 })
  const nodeRef = useRef(null)
  
  // Load saved settings
  useEffect(() => {
    const saved = localStorage.getItem('slywriter-overlay')
    if (saved) {
      const settings = JSON.parse(saved)
      setOpacity(settings.opacity || 0.9)
      setSize(settings.size || { width: 250, height: 80 })
      setPosition(settings.position || { x: 20, y: 20 })
    }
  }, [])
  
  // Save settings on change
  useEffect(() => {
    const settings = { opacity, size, position }
    localStorage.setItem('slywriter-overlay', JSON.stringify(settings))
  }, [opacity, size, position])
  
  // Listen for typing updates via custom events
  useEffect(() => {
    // Listen for typing status updates
    const handleTypingUpdate = (event: CustomEvent) => {
      console.log('Overlay received typing-update:', event.detail)
      const { status: newStatus, wpm: newWpm, progress: newProgress } = event.detail
      if (newStatus) setStatus(newStatus)
      if (newWpm !== undefined) setWpm(newWpm)
      if (newProgress !== undefined) setProgress(newProgress)
    }
    
    // Listen for typing start
    const handleTypingStart = () => {
      console.log('Overlay received typing-start')
      setStatus('Starting...')
      setProgress(0)
      setWpm(0)
    }
    
    // Listen for typing stop
    const handleTypingStop = () => {
      console.log('Overlay received typing-stop')
      setStatus('Stopped')
    }
    
    // Listen for typing complete
    const handleTypingComplete = (event: CustomEvent) => {
      console.log('Overlay received typing-complete:', event.detail)
      setStatus('Complete!')
      setProgress(100)
      // Safely access wpm from event.detail, default to current wpm if not provided
      if (event.detail && event.detail.wpm !== undefined) {
        setWpm(event.detail.wpm)
      }
      
      // Reset after 5 seconds
      setTimeout(() => {
        setStatus('Ready')
        setProgress(0)
      }, 5000)
    }
    
    window.addEventListener('typing-update', handleTypingUpdate as EventListener)
    window.addEventListener('typing-start', handleTypingStart as EventListener)
    window.addEventListener('typing-stop', handleTypingStop as EventListener)
    window.addEventListener('typing-complete', handleTypingComplete as EventListener)
    
    // Log that listeners are attached
    console.log('Overlay event listeners attached, visible:', isVisible)
    
    return () => {
      window.removeEventListener('typing-update', handleTypingUpdate as EventListener)
      window.removeEventListener('typing-start', handleTypingStart as EventListener)
      window.removeEventListener('typing-stop', handleTypingStop as EventListener)
      window.removeEventListener('typing-complete', handleTypingComplete as EventListener)
    }
  }, [])
  
  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!isVisible) return
    
    let ws: WebSocket | null = null
    
    try {
      // Connect to the same WebSocket endpoint as the main typing tab
      const userId = localStorage.getItem('user-email') || 'anonymous'
      ws = new WebSocket(`ws://localhost:8000/ws/${userId}`)
      
      ws.onopen = () => {
        console.log('Overlay WebSocket connected')
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          switch (data.type) {
            case 'countdown':
              setStatus(`Starting in ${data.data.count}...`)
              break
            case 'progress':
              setProgress(data.data.progress)
              setWpm(data.data.wpm)
              setStatus(data.data.status)
              break
            case 'pause':
              setStatus('Paused')
              break
            case 'complete':
              setStatus('Complete!')
              setProgress(100)
              break
          }
        } catch (err) {
          console.warn('Overlay WebSocket parse error:', err)
        }
      }
      
      ws.onerror = () => {
        console.warn('Overlay WebSocket error - this is normal if not typing')
      }
      
      ws.onclose = () => {
        console.log('Overlay WebSocket disconnected')
      }
    } catch (error) {
      console.warn('Could not connect overlay WebSocket')
    }
    
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [isVisible])
  
  if (!isVisible) return null
  
  const getStatusColor = () => {
    switch (status.toLowerCase()) {
      case 'typing...':
      case 'typing':
        return 'text-green-400'
      case 'paused':
        return 'text-yellow-400'
      case 'stopped':
      case 'error':
        return 'text-red-400'
      case 'ai processing...':
      case 'ai filler...':
        return 'text-purple-400'
      case 'thinking...':
        return 'text-blue-400'
      default:
        return 'text-gray-400'
    }
  }
  
  const getStatusIcon = () => {
    switch (status.toLowerCase()) {
      case 'typing...':
      case 'typing':
        return <PlayIcon className="w-4 h-4" />
      case 'paused':
        return <PauseIcon className="w-4 h-4" />
      default:
        return <ActivityIcon className="w-4 h-4" />
    }
  }
  
  return (
    <Draggable
      nodeRef={nodeRef}
      handle=".drag-handle"
      defaultPosition={position}
      onStop={(_, data) => setPosition({ x: data.x, y: data.y })}
    >
      <motion.div
        ref={nodeRef}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        style={{
          width: size.width,
          height: size.height,
          opacity,
          position: 'fixed',
          zIndex: 99999,
          top: position.y,
          left: position.x,
        }}
        className="bg-gray-900 rounded-lg shadow-2xl border border-purple-500/50 overflow-hidden"
      >
        {/* Header/Drag Handle */}
        <div className="drag-handle bg-gradient-to-r from-purple-600 to-purple-700 px-3 py-2 cursor-move flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MoveIcon className="w-3 h-3 text-white/70" />
            <span className="text-xs font-medium text-white">SlyWriter</span>
          </div>
          <button
            onClick={onClose}
            className="text-white/70 hover:text-white transition-colors"
            title="Toggle Overlay (or press hotkey)"
          >
            <XIcon className="w-3 h-3" />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-3">
          {/* Status */}
          <div className="flex items-center justify-between mb-2">
            <div className={`flex items-center gap-2 text-sm font-medium ${getStatusColor()}`}>
              {getStatusIcon()}
              <span>{status}</span>
            </div>
            <div className="text-sm text-white font-bold">
              {wpm > 0 && `${wpm} WPM`}
            </div>
          </div>
          
          {/* Progress Bar */}
          {progress > 0 && (
            <div className="mt-2">
              <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-700 bg-gray-800 rounded-full h-1.5">
                <motion.div
                  className="bg-gradient-to-r from-purple-500 to-purple-400 h-1.5 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </div>
          )}
        </div>
        
        {/* Resize Handle */}
        <div
          className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize"
          onMouseDown={(e) => {
            e.preventDefault()
            const startX = e.clientX
            const startY = e.clientY
            const startWidth = size.width
            const startHeight = size.height
            
            const handleMouseMove = (e: MouseEvent) => {
              const newWidth = Math.max(200, Math.min(600, startWidth + e.clientX - startX))
              const newHeight = Math.max(60, Math.min(200, startHeight + e.clientY - startY))
              setSize({ width: newWidth, height: newHeight })
            }
            
            const handleMouseUp = () => {
              document.removeEventListener('mousemove', handleMouseMove)
              document.removeEventListener('mouseup', handleMouseUp)
            }
            
            document.addEventListener('mousemove', handleMouseMove)
            document.addEventListener('mouseup', handleMouseUp)
          }}
        >
          <div className="absolute bottom-0.5 right-0.5 w-2 h-2 border-b border-r border-gray-600" />
        </div>
        
        {/* Opacity Control */}
        <div className="absolute bottom-2 left-2">
          <input
            type="range"
            min="30"
            max="100"
            value={opacity * 100}
            onChange={(e) => setOpacity(Number(e.target.value) / 100)}
            className="w-16 h-1 opacity-50 hover:opacity-100 transition-opacity accent-purple-500"
            title="Opacity"
          />
        </div>
      </motion.div>
    </Draggable>
  )
}

// Settings component for the overlay
export function OverlaySettings() {
  const [settings, setSettings] = useState({
    enabled: true,
    opacity: 90,
    width: 250,
    height: 80,
    position: 'top-right',
    alwaysOnTop: true
  })
  
  useEffect(() => {
    const saved = localStorage.getItem('slywriter-overlay-settings')
    if (saved) {
      setSettings(JSON.parse(saved))
    }
  }, [])
  
  const saveSettings = () => {
    localStorage.setItem('slywriter-overlay-settings', JSON.stringify(settings))
    
    // Send message to update overlay
    window.postMessage({
      type: 'update-overlay-settings',
      settings
    }, '*')
  }
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm text-white">Enable Overlay</label>
        <input
          type="checkbox"
          checked={settings.enabled}
          onChange={(e) => setSettings({...settings, enabled: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      <div>
        <label className="text-xs text-gray-400 block mb-2">Opacity</label>
        <input
          type="range"
          min="30"
          max="100"
          value={settings.opacity}
          onChange={(e) => setSettings({...settings, opacity: Number(e.target.value)})}
          className="w-full accent-purple-500"
        />
        <div className="text-center text-xs text-purple-400 mt-1">{settings.opacity}%</div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-gray-400 block mb-2">Width</label>
          <input
            type="range"
            min="200"
            max="600"
            step="10"
            value={settings.width}
            onChange={(e) => setSettings({...settings, width: Number(e.target.value)})}
            className="w-full accent-purple-500"
          />
          <div className="text-center text-xs text-purple-400 mt-1">{settings.width}px</div>
        </div>
        
        <div>
          <label className="text-xs text-gray-400 block mb-2">Height</label>
          <input
            type="range"
            min="60"
            max="200"
            step="10"
            value={settings.height}
            onChange={(e) => setSettings({...settings, height: Number(e.target.value)})}
            className="w-full accent-purple-500"
          />
          <div className="text-center text-xs text-purple-400 mt-1">{settings.height}px</div>
        </div>
      </div>
      
      <div>
        <label className="text-xs text-gray-400 block mb-2">Default Position</label>
        <select
          value={settings.position}
          onChange={(e) => setSettings({...settings, position: e.target.value})}
          className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm text-white border border-gray-700 focus:border-purple-500 focus:outline-none"
        >
          <option value="top-left">Top Left</option>
          <option value="top-right">Top Right</option>
          <option value="bottom-left">Bottom Left</option>
          <option value="bottom-right">Bottom Right</option>
          <option value="center">Center</option>
        </select>
      </div>
      
      <div className="flex items-center justify-between">
        <label className="text-sm text-white">Always On Top</label>
        <input
          type="checkbox"
          checked={settings.alwaysOnTop}
          onChange={(e) => setSettings({...settings, alwaysOnTop: e.target.checked})}
          className="accent-purple-500"
        />
      </div>
      
      <button
        onClick={saveSettings}
        className="w-full py-2 bg-purple-500 hover:bg-purple-600 rounded-lg text-white font-medium transition-colors"
      >
        Save Settings
      </button>
    </div>
  )
}