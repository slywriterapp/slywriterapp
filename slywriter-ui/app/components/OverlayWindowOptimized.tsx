'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, useDragControls } from 'framer-motion'
import { 
  XIcon, MoveIcon, PlayIcon, PauseIcon, StopCircleIcon,
  ActivityIcon, ZapIcon, CheckCircleIcon, AlertCircleIcon
} from 'lucide-react'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

interface OverlayWindowOptimizedProps {
  isVisible: boolean
  onClose: () => void
}

export default function OverlayWindowOptimized({ isVisible, onClose }: OverlayWindowOptimizedProps) {
  const [position, setPosition] = useState({ x: 0, y: 100 })
  const [isTyping, setIsTyping] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentWPM, setCurrentWPM] = useState(0)
  const [charsTyped, setCharsTyped] = useState(0)
  const [totalChars, setTotalChars] = useState(0)
  const [status, setStatus] = useState<'idle' | 'typing' | 'paused' | 'completed'>('idle')
  
  const dragControls = useDragControls()
  const constraintsRef = useRef(null)
  const wsRef = useRef<WebSocket | null>(null)
  const dragTimeoutRef = useRef<NodeJS.Timeout>()
  
  // Set initial position on client side
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setPosition({ x: window.innerWidth - 320, y: 100 })
    }
  }, [])
  
  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!isVisible) return
    
    const connectWebSocket = () => {
      const ws = new WebSocket(`ws://localhost:8000/ws/typing`)
      
      ws.onopen = () => {
        console.log('Overlay WebSocket connected')
        wsRef.current = ws
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'typing_update') {
            // Update all stats at once to reduce re-renders
            setProgress(data.progress || 0)
            setCharsTyped(data.chars_typed || 0)
            setTotalChars(data.total_chars || 0)
            setCurrentWPM(data.wpm || 0)
            
            // Update status
            if (data.status === 'typing') {
              setStatus('typing')
              setIsTyping(true)
              setIsPaused(false)
            } else if (data.status === 'paused') {
              setStatus('paused')
              setIsTyping(true)
              setIsPaused(true)
            } else if (data.status === 'completed') {
              setStatus('completed')
              setIsTyping(false)
              setIsPaused(false)
            } else {
              setStatus('idle')
              setIsTyping(false)
              setIsPaused(false)
            }
          }
        } catch (error) {
          console.error('Overlay WebSocket message parsing error')
        }
      }
      
      ws.onerror = (error) => {
        console.error('Overlay WebSocket error:', error)
      }
      
      ws.onclose = () => {
        console.log('Overlay WebSocket disconnected')
        wsRef.current = null
        // Reconnect after 2 seconds
        setTimeout(connectWebSocket, 2000)
      }
      
      return ws
    }
    
    const ws = connectWebSocket()
    
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [isVisible])
  
  // Throttled drag handler for better performance
  const handleDrag = useCallback((event: any, info: any) => {
    // Clear existing timeout
    if (dragTimeoutRef.current) {
      clearTimeout(dragTimeoutRef.current)
    }
    
    // Throttle position updates to every 50ms
    dragTimeoutRef.current = setTimeout(() => {
      setPosition({ x: info.x, y: info.y })
    }, 50)
  }, [])
  
  // Control functions
  const handlePauseResume = async () => {
    try {
      const endpoint = isPaused ? 'resume' : 'pause'
      await axios.post(`${API_URL}/api/typing/${endpoint}`)
    } catch (error) {
      console.error('Failed to pause/resume:', error)
    }
  }
  
  const handleStop = async () => {
    try {
      await axios.post(`${API_URL}/api/typing/stop`)
      setIsTyping(false)
      setIsPaused(false)
      setProgress(0)
      setStatus('idle')
    } catch (error) {
      console.error('Failed to stop:', error)
    }
  }
  
  if (!isVisible) return null
  
  // Get status color
  const getStatusColor = () => {
    switch (status) {
      case 'typing': return 'text-green-400'
      case 'paused': return 'text-yellow-400'
      case 'completed': return 'text-blue-400'
      default: return 'text-gray-400'
    }
  }
  
  const getStatusIcon = () => {
    switch (status) {
      case 'typing': return <ActivityIcon className="w-4 h-4 animate-pulse" />
      case 'paused': return <PauseIcon className="w-4 h-4" />
      case 'completed': return <CheckCircleIcon className="w-4 h-4" />
      default: return <AlertCircleIcon className="w-4 h-4" />
    }
  }
  
  return (
    <>
      {/* Invisible constraints ref for drag boundaries */}
      <div 
        ref={constraintsRef}
        className="fixed inset-0 pointer-events-none"
        style={{ zIndex: 9998 }}
      />
      
      <motion.div
        drag
        dragControls={dragControls}
        dragConstraints={constraintsRef}
        dragElastic={0}
        dragMomentum={false}
        dragTransition={{ bounceStiffness: 600, bounceDamping: 20 }}
        onDrag={handleDrag}
        initial={{ x: position.x, y: position.y, opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        style={{
          position: 'fixed',
          x: position.x,
          y: position.y,
          zIndex: 9999,
        }}
        className="w-80"
      >
        <div className="bg-gray-900/95 backdrop-blur-xl rounded-xl shadow-2xl border border-purple-500/30 overflow-hidden">
          {/* Header with drag handle */}
          <div 
            className="bg-gradient-to-r from-purple-600 to-blue-600 p-3 cursor-move flex items-center justify-between"
            onPointerDown={(e) => dragControls.start(e)}
          >
            <div className="flex items-center gap-2">
              <MoveIcon className="w-4 h-4 text-white/70" />
              <span className="text-sm font-bold text-white">SlyWriter Overlay</span>
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-white/20 rounded transition-colors"
            >
              <XIcon className="w-4 h-4 text-white" />
            </button>
          </div>
          
          {/* Status Bar */}
          <div className="bg-gray-800/50 px-4 py-2 border-b border-gray-700">
            <div className="flex items-center justify-between">
              <div className={`flex items-center gap-2 ${getStatusColor()}`}>
                {getStatusIcon()}
                <span className="text-xs font-medium capitalize">{status}</span>
              </div>
              {currentWPM > 0 && (
                <div className="flex items-center gap-2">
                  <ZapIcon className="w-3 h-3 text-purple-400" />
                  <span className="text-xs font-bold text-white">{currentWPM} WPM</span>
                </div>
              )}
            </div>
          </div>
          
          {/* Main Content */}
          <div className="p-4 space-y-3">
            {/* Progress Section */}
            {isTyping && (
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Progress</span>
                  <span className="text-purple-400 font-medium">{Math.round(progress)}%</span>
                </div>
                <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>{charsTyped} chars</span>
                  <span>{totalChars} total</span>
                </div>
              </div>
            )}
            
            {/* Controls */}
            <div className="flex gap-2">
              {isTyping ? (
                <>
                  <button
                    onClick={handlePauseResume}
                    className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg font-medium text-sm transition-all ${
                      isPaused 
                        ? 'bg-green-600 hover:bg-green-700 text-white' 
                        : 'bg-yellow-600 hover:bg-yellow-700 text-white'
                    }`}
                  >
                    <PauseIcon className="w-4 h-4" />
                    {isPaused ? 'Resume' : 'Pause'}
                  </button>
                  <button
                    onClick={handleStop}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium text-sm transition-all"
                  >
                    <StopCircleIcon className="w-4 h-4" />
                    Stop
                  </button>
                </>
              ) : (
                <div className="flex-1 text-center py-2 text-gray-500 text-sm">
                  {status === 'completed' ? 'Typing completed!' : 'No active typing session'}
                </div>
              )}
            </div>
            
            {/* Quick Stats */}
            {isTyping && (
              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-gray-700">
                <div className="text-center">
                  <div className="text-xs text-gray-400">Speed</div>
                  <div className="text-sm font-bold text-white">{currentWPM}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-400">Typed</div>
                  <div className="text-sm font-bold text-white">{charsTyped}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-400">Left</div>
                  <div className="text-sm font-bold text-white">{totalChars - charsTyped}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </>
  )
}