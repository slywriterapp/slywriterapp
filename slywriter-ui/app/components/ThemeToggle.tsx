'use client'

import { motion } from 'framer-motion'
import { SunIcon, MoonIcon } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()

  return (
    <motion.button
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      onClick={toggleTheme}
      className={`
        relative w-14 h-14 rounded-full flex items-center justify-center
        transition-all duration-300 shadow-lg
        ${theme === 'light' 
          ? 'bg-gray-900 border-2 border-purple-500 hover:shadow-brand-purple/20' 
          : 'bg-gray-900 border-2 border-purple-500 hover:shadow-purple-500/20'
        }
      `}
      aria-label="Toggle theme"
    >
      <motion.div
        initial={false}
        animate={{ rotate: theme === 'light' ? 0 : 180 }}
        transition={{ duration: 0.3 }}
        className="relative w-6 h-6"
      >
        {theme === 'light' ? (
          <SunIcon className="w-6 h-6 text-purple-400" />
        ) : (
          <MoonIcon className="w-6 h-6 text-purple-400" />
        )}
      </motion.div>
      
      {/* Pulse animation */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 0, 0.5]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          repeatType: "loop"
        }}
        className={`
          absolute inset-0 rounded-full pointer-events-none
          ${'bg-purple-500'}
        `}
      />
    </motion.button>
  )
}

// Compact version for header
export function ThemeToggleCompact() {
  const { theme, toggleTheme } = useTheme()

  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={toggleTheme}
      className={`
        relative p-2 rounded-lg transition-all duration-300
        ${theme === 'light' 
          ? 'bg-purple-500/10 hover:bg-purple-500/20' 
          : 'bg-purple-500/10 hover:bg-purple-500/20'
        }
      `}
      aria-label="Toggle theme"
    >
      <motion.div
        initial={false}
        animate={{ rotate: theme === 'light' ? 0 : 180 }}
        transition={{ duration: 0.3 }}
      >
        {theme === 'light' ? (
          <SunIcon className="w-5 h-5 text-purple-400" />
        ) : (
          <MoonIcon className="w-5 h-5 text-purple-400" />
        )}
      </motion.div>
    </motion.button>
  )
}