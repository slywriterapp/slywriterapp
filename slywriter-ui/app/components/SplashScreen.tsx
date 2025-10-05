'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function SplashScreen() {
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    // Hide splash screen after 3 seconds
    const timer = setTimeout(() => {
      setIsVisible(false)
    }, 3000)

    return () => clearTimeout(timer)
  }, [])

  return (
    <AnimatePresence>
      {isVisible && (
        <>
          <style jsx>{`
            @keyframes breathe {
              0%, 100% {
                box-shadow:
                  0 30px 60px rgba(0, 0, 0, 0.8),
                  0 0 0 1px rgba(139, 92, 246, 0.3),
                  0 0 30px rgba(139, 92, 246, 0.2);
              }
              50% {
                box-shadow:
                  0 30px 60px rgba(0, 0, 0, 0.8),
                  0 0 0 1px rgba(139, 92, 246, 0.7),
                  0 0 60px rgba(139, 92, 246, 0.5);
              }
            }

            .breathe-glow {
              animation: breathe 3s ease-in-out infinite;
            }
          `}</style>

          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="fixed inset-0 z-[9999] flex items-center justify-center bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950"
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 1.1, opacity: 0 }}
              transition={{ duration: 0.5 }}
              className="flex flex-col items-center gap-6 p-12 rounded-3xl bg-gradient-to-br from-gray-900/80 to-gray-800/80 backdrop-blur-xl breathe-glow"
            >
            {/* Logo */}
            <motion.img
              src="/slywriter_logo.png"
              alt="SlyWriter"
              className="w-32 h-32 md:w-48 md:h-48"
              initial={{ rotate: -180, scale: 0 }}
              animate={{ rotate: 0, scale: 1 }}
              transition={{ 
                type: "spring",
                stiffness: 260,
                damping: 20,
                delay: 0.2
              }}
            />
            
            {/* App Name */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="flex flex-col items-center"
            >
              <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
                SlyWriter
              </h1>
              <p className="text-gray-400 text-sm mt-2">Professional Typing Automation</p>
            </motion.div>
            
            {/* Loading indicator */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="flex gap-1"
            >
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="w-2 h-2 bg-purple-500 rounded-full"
                  animate={{
                    scale: [1, 1.5, 1],
                    opacity: [0.5, 1, 0.5]
                  }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    delay: i * 0.2
                  }}
                />
              ))}
            </motion.div>
            
            {/* Version */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1 }}
              className="absolute bottom-8 text-gray-600 text-xs"
            >
              v2.0.0 Pro
            </motion.div>
          </motion.div>
        </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}