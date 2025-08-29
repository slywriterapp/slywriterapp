'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface ThemeContextType {
  theme: 'light' | 'dark'
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Load saved theme or default to dark
    const savedTheme = 'dark' // Force dark mode
    if (savedTheme) {
      setTheme(savedTheme as 'light' | 'dark')
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setTheme((prefersDark ? 'dark' : 'light') as 'light' | 'dark')
    }
  }, [])

  useEffect(() => {
    if (!mounted) return
    
    // Apply theme to document
    const root = document.documentElement
    if (theme === 'light') {
      root.classList.remove('dark')
      root.classList.add('light')
    } else {
      root.classList.remove('light')
      root.classList.add('dark')
    }
    
    // Save theme preference
    localStorage.setItem('slywriter-theme', theme)
  }, [theme, mounted])

  const toggleTheme = () => {
    // Theme toggle disabled - dark mode only
  }

  if (!mounted) {
    return <>{children}</>
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    // Return a default fallback during SSR or when context is not available
    console.warn('useTheme: ThemeProvider not found, using fallback')
    return {
      theme: 'dark' as const,
      toggleTheme: () => {
        console.warn('Theme toggle called but ThemeProvider not available')
      }
    }
  }
  return context
}