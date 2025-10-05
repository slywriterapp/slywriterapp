'use client'

import React, { Component, ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'
import { RENDER_API_URL } from '../config/api'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    
    // Log to telemetry if available
    if (typeof window !== 'undefined') {
      try {
        fetch(${RENDER_API_URL}/api/telemetry/error', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            error: error.toString(),
            stack: error.stack,
            component: errorInfo.componentStack,
            timestamp: new Date().toISOString()
          })
        }).catch(() => {})
      } catch {}
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
          <AlertTriangle className="w-16 h-16 text-red-500 mb-4" />
          <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4 text-center max-w-md">
            An unexpected error occurred. The issue has been logged and we'll look into it.
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false })
              window.location.reload()
            }}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            Reload App
          </button>
        </div>
      )
    }

    return this.props.children
  }
}