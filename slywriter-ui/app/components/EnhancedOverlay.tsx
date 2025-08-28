'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, useDragControls, AnimatePresence } from 'framer-motion'
import { X, Move, Minimize, Maximize, Pin, Settings } from 'lucide-react'

interface OverlayProps {
  onClose: () => void
  initialPosition?: { x: number; y: number }
  initialSize?: { width: number; height: number }
}

export default function EnhancedOverlay({ onClose, initialPosition, initialSize }: OverlayProps) {
  const [position, setPosition] = useState(initialPosition || { x: 100, y: 100 })
  const [size, setSize] = useState(initialSize || { width: 300, height: 200 })
  const [isPinned, setIsPinned] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  
  const dragControls = useDragControls()
  const overlayRef = useRef<HTMLDivElement>(null)
  const dragTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  // GPU-accelerated dragging with throttling
  const handleDragStart = useCallback(() => {
    setIsDragging(true)
    
    // Add GPU acceleration class
    if (overlayRef.current) {
      overlayRef.current.style.willChange = 'transform'
    }
  }, [])
  
  const handleDragEnd = useCallback((event: any, info: any) => {
    setIsDragging(false)
    
    // Update position with throttling
    if (dragTimeoutRef.current) {
      clearTimeout(dragTimeoutRef.current)
    }
    
    dragTimeoutRef.current = setTimeout(() => {
      setPosition({
        x: position.x + info.offset.x,
        y: position.y + info.offset.y
      })
      
      // Remove GPU acceleration after drag
      if (overlayRef.current) {
        overlayRef.current.style.willChange = 'auto'
      }
    }, 16) // 60fps throttling
  }, [position])
  
  // Attempt to keep overlay on top (browser limitations apply)
  useEffect(() => {
    if (isPinned && overlayRef.current) {
      overlayRef.current.style.zIndex = '999999'
      
      // Try to use browser-specific features if available
      if ('alwaysOnTop' in window) {
        (window as any).alwaysOnTop = true
      }
    }
  }, [isPinned])
  
  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (dragTimeoutRef.current) {
        clearTimeout(dragTimeoutRef.current)
      }
    }
  }, [])
  
  return (
    <AnimatePresence>
      <motion.div
        ref={overlayRef}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ 
          opacity: 1, 
          scale: isMinimized ? 0.3 : 1,
          width: isMinimized ? 150 : size.width,
          height: isMinimized ? 40 : size.height
        }}
        exit={{ opacity: 0, scale: 0.9 }}
        drag={!isPinned}
        dragControls={dragControls}
        dragMomentum={false}
        dragElastic={0}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        style={{
          position: 'fixed',
          x: position.x,
          y: position.y,
          transform: 'translate3d(0, 0, 0)', // Force GPU acceleration
          backfaceVisibility: 'hidden', // Optimize rendering
          perspective: 1000, // Enable 3D acceleration
        }}
        className={`
          bg-gray-900/95 backdrop-blur-xl rounded-lg shadow-2xl border border-purple-500/30
          ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}
          ${isPinned ? 'ring-2 ring-purple-500' : ''}
          transition-none // Disable transitions during drag
        `}
      >
        {/* Header */}
        <div 
          className="bg-gray-800 rounded-t-lg p-2 flex items-center justify-between"
          onPointerDown={(e) => !isPinned && dragControls.start(e)}
        >
          <div className="flex items-center gap-2">
            <Move size={14} className="text-gray-500" />
            <span className="text-xs font-semibold text-white">SlyWriter Overlay</span>
          </div>
          
          <div className="flex items-center gap-1">
            {/* Pin button */}
            <button
              onClick={() => setIsPinned(!isPinned)}
              className={`p-1 rounded hover:bg-gray-700 transition-colors ${
                isPinned ? 'text-purple-400' : 'text-gray-400'
              }`}
              title={isPinned ? 'Unpin' : 'Pin on top'}
            >
              <Pin size={14} />
            </button>
            
            {/* Minimize button */}
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1 rounded hover:bg-gray-700 transition-colors text-gray-400"
              title={isMinimized ? 'Maximize' : 'Minimize'}
            >
              {isMinimized ? <Maximize size={14} /> : <Minimize size={14} />}
            </button>
            
            {/* Close button */}
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-red-600 transition-colors text-gray-400 hover:text-white"
              title="Close"
            >
              <X size={14} />
            </button>
          </div>
        </div>
        
        {/* Content */}
        {!isMinimized && (
          <div className="p-4">
            <div className="space-y-3">
              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-gray-800 rounded p-2">
                  <p className="text-xs text-gray-400">Status</p>
                  <p className="text-sm font-semibold text-green-400">Ready</p>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <p className="text-xs text-gray-400">WPM</p>
                  <p className="text-sm font-semibold text-white">0</p>
                </div>
              </div>
              
              {/* Quick Controls */}
              <div className="flex gap-2">
                <button className="flex-1 px-2 py-1 bg-purple-600 hover:bg-purple-700 rounded text-xs font-semibold text-white transition-colors">
                  Start
                </button>
                <button className="flex-1 px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs font-semibold text-white transition-colors">
                  Stop
                </button>
              </div>
              
              {/* Performance indicator */}
              {isDragging && (
                <div className="absolute top-0 right-0 m-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                </div>
              )}
            </div>
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  )
}