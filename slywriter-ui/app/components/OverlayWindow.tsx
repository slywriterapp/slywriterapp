'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, useDragControls } from 'framer-motion'
import { X, Move, Minimize2, Maximize2, Activity } from 'lucide-react'

interface OverlayWindowProps {
  isTyping: boolean
  status: string
  wpm: number
  progress: number
  onClose: () => void
}

export default function OverlayWindow({ isTyping, status, wpm, progress, onClose }: OverlayWindowProps) {
  const [isMinimized, setIsMinimized] = useState(false)
  const [opacity, setOpacity] = useState(0.9)
  const [position, setPosition] = useState({ x: window.innerWidth - 320, y: 20 })
  const dragControls = useDragControls()
  const constraintsRef = useRef(null)

  useEffect(() => {
    // Load saved position
    const saved = localStorage.getItem('overlayPosition')
    if (saved) {
      setPosition(JSON.parse(saved))
    }
  }, [])

  const handleDragEnd = (event: any, info: any) => {
    const newPosition = { x: info.x, y: info.y }
    setPosition(newPosition)
    localStorage.setItem('overlayPosition', JSON.stringify(newPosition))
  }

  return (
    <>
      {/* Constraints container */}
      <div ref={constraintsRef} className="fixed inset-0 pointer-events-none" />
      
      <motion.div
        drag
        dragControls={dragControls}
        dragConstraints={constraintsRef}
        dragElastic={0.1}
        dragMomentum={false}
        onDragEnd={handleDragEnd}
        initial={{ x: position.x, y: position.y }}
        animate={{ 
          width: isMinimized ? 200 : 300,
          height: isMinimized ? 40 : 120,
          opacity
        }}
        className="fixed z-50 bg-gray-900/95 backdrop-blur-xl rounded-xl border border-purple-500/30 shadow-2xl overflow-hidden pointer-events-auto"
        style={{ touchAction: 'none' }}
      >
        {/* Header */}
        <div 
          className="flex items-center justify-between px-3 py-2 bg-gradient-to-r from-purple-900/50 to-blue-900/50 cursor-move"
          onPointerDown={(e) => dragControls.start(e)}
        >
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-semibold">SlyWriter Overlay</span>
          </div>
          
          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1 hover:bg-gray-900/10 rounded transition-colors"
            >
              {isMinimized ? <Maximize2 className="w-3 h-3" /> : <Minimize2 className="w-3 h-3" />}
            </button>
            <button
              onClick={onClose}
              className="p-1 hover:bg-red-500/20 rounded transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        </div>
        
        {/* Content */}
        {!isMinimized && (
          <div className="p-3">
            <div className="flex justify-between items-center mb-2">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  isTyping ? 'bg-green-400 animate-pulse' : 'bg-gray-400'
                }`} />
                <span className="text-xs">{status}</span>
              </div>
              <span className="text-xs text-gray-400">{Math.round(progress)}%</span>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-800/50 rounded-lg p-2 text-center">
                <div className="text-xs text-gray-400">WPM</div>
                <div className="text-lg font-bold text-purple-400">{wpm}</div>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-2 text-center">
                <div className="text-xs text-gray-400">Progress</div>
                <div className="text-lg font-bold text-blue-400">{Math.round(progress)}%</div>
              </div>
            </div>
            
            {/* Mini progress bar */}
            <div className="mt-2 h-1 bg-gray-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
              />
            </div>
          </div>
        )}
      </motion.div>
      
      {/* Opacity control */}
      <div className="fixed bottom-4 right-4 z-50 bg-gray-900/95 backdrop-blur-xl rounded-lg p-2">
        <label className="text-xs text-gray-400">Opacity</label>
        <input
          type="range"
          min="0.3"
          max="1"
          step="0.1"
          value={opacity}
          onChange={(e) => setOpacity(Number(e.target.value))}
          className="w-24 mt-1"
        />
      </div>
    </>
  )
}