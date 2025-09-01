'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  AlertTriangleIcon, ShieldIcon, DatabaseIcon, 
  ToggleLeftIcon, ToggleRightIcon, ChevronDownIcon,
  ChevronUpIcon, CheckCircleIcon, InfoIcon, CopyIcon
} from 'lucide-react'
import betaTelemetry from '../services/betaTelemetry'

export default function BetaDisclosure() {
  const [isVisible, setIsVisible] = useState(false)
  const [telemetryEnabled, setTelemetryEnabled] = useState(true)
  const [showDetails, setShowDetails] = useState(false)
  const [userId, setUserId] = useState('')

  useEffect(() => {
    // Check if we're in development mode
    const isDevelopment = process.env.NODE_ENV === 'development' || 
                         window.location.hostname === 'localhost' ||
                         window.location.hostname === '127.0.0.1'
    
    // Don't show beta disclosure in development
    if (isDevelopment) {
      setIsVisible(false)
      return
    }
    
    // Check if user has acknowledged beta disclosure
    const acknowledged = localStorage.getItem('betaTelemetryAcknowledged')
    if (!acknowledged) {
      setIsVisible(true)
      // Auto-enable telemetry for beta
      betaTelemetry.setEnabled(true)
    } else {
      // Check user's telemetry preference
      const enabled = localStorage.getItem('betaTelemetryEnabled') !== 'false'
      setTelemetryEnabled(enabled)
      betaTelemetry.setEnabled(enabled)
    }

    // Get user ID for display
    setUserId(localStorage.getItem('betaUserId') || 'generating...')
  }, [])

  const handleAccept = () => {
    localStorage.setItem('betaTelemetryAcknowledged', 'true')
    localStorage.setItem('betaTelemetryEnabled', telemetryEnabled.toString())
    betaTelemetry.setEnabled(telemetryEnabled)
    betaTelemetry.trackAction('beta_disclosure_accepted', 'disclosure', {
      telemetryEnabled
    })
    setIsVisible(false)
  }

  const toggleTelemetry = () => {
    const newState = !telemetryEnabled
    setTelemetryEnabled(newState)
    betaTelemetry.trackAction('telemetry_toggled', 'disclosure', {
      enabled: newState
    })
  }

  const copyUserId = () => {
    navigator.clipboard.writeText(userId)
    betaTelemetry.trackAction('user_id_copied', 'disclosure', {})
  }

  if (!isVisible) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
      >
        <motion.div
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 20 }}
          className="relative max-w-2xl w-full bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 rounded-2xl shadow-2xl border border-purple-500/30 overflow-hidden"
        >
          {/* Animated background */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-600 to-pink-600 animate-pulse" />
          </div>

          {/* Content */}
          <div className="relative p-8">
            {/* Header */}
            <div className="flex items-start gap-4 mb-6">
              <div className="p-3 bg-orange-500/20 rounded-xl">
                <AlertTriangleIcon className="w-8 h-8 text-orange-400" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-white mb-2">
                  Welcome to SlyWriter Beta Testing! 🚀
                </h2>
                <p className="text-gray-300">
                  You're using a beta version with telemetry enabled to help improve the app
                </p>
              </div>
            </div>

            {/* Important Notice */}
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 mb-6">
              <div className="flex items-start gap-3">
                <InfoIcon className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-yellow-200">
                  <strong className="text-yellow-300">Beta Testing Notice:</strong> This version automatically collects 
                  usage data to identify bugs and improve features. Your actual typing content is <strong>NEVER</strong> collected 
                  - only app interactions, errors, and performance metrics.
                </div>
              </div>
            </div>

            {/* Telemetry Toggle */}
            <div className="bg-gray-800/50 rounded-xl p-5 mb-6 border border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <DatabaseIcon className="w-5 h-5 text-purple-400" />
                  <span className="font-semibold text-white">Anonymous Telemetry</span>
                </div>
                <button
                  onClick={toggleTelemetry}
                  className={`relative w-14 h-7 rounded-full transition-colors ${
                    telemetryEnabled ? 'bg-green-500' : 'bg-gray-600'
                  }`}
                >
                  <motion.div
                    animate={{ x: telemetryEnabled ? 28 : 2 }}
                    className="absolute top-1 w-5 h-5 bg-white rounded-full shadow-lg"
                  />
                  {telemetryEnabled ? (
                    <ToggleRightIcon className="w-4 h-4 absolute right-1 top-1.5 text-white" />
                  ) : (
                    <ToggleLeftIcon className="w-4 h-4 absolute left-1 top-1.5 text-gray-400" />
                  )}
                </button>
              </div>

              <div className="text-sm text-gray-300 space-y-2">
                {telemetryEnabled ? (
                  <>
                    <p className="text-green-400">✅ Telemetry is enabled (recommended for beta testing)</p>
                    <p className="text-xs text-gray-400">
                      Helps us fix bugs faster and understand which features need improvement
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-orange-400">⚠️ Telemetry is disabled</p>
                    <p className="text-xs text-gray-400">
                      You can still use the app, but we won't be able to identify and fix issues you encounter
                    </p>
                  </>
                )}
              </div>
            </div>

            {/* What We Collect */}
            <div className="mb-6">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="flex items-center gap-2 text-sm text-purple-300 hover:text-purple-200 transition-colors"
              >
                <ShieldIcon className="w-4 h-4" />
                <span>What data is collected?</span>
                {showDetails ? <ChevronUpIcon className="w-4 h-4" /> : <ChevronDownIcon className="w-4 h-4" />}
              </button>

              <AnimatePresence>
                {showDetails && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                      <div className="space-y-2">
                        <h4 className="font-semibold text-green-400">✅ What We Collect:</h4>
                        <ul className="space-y-1 text-gray-300">
                          <li>• Button clicks & feature usage</li>
                          <li>• Error messages & crashes</li>
                          <li>• Performance metrics (load times)</li>
                          <li>• Settings preferences</li>
                          <li>• Session duration & activity</li>
                          <li>• System info (OS, screen size)</li>
                        </ul>
                      </div>
                      <div className="space-y-2">
                        <h4 className="font-semibold text-red-400">❌ Never Collected:</h4>
                        <ul className="space-y-1 text-gray-300">
                          <li>• Your actual typed content</li>
                          <li>• Personal information</li>
                          <li>• Passwords or credentials</li>
                          <li>• Files or documents</li>
                          <li>• Clipboard contents</li>
                          <li>• Browsing history</li>
                        </ul>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* User ID */}
            <div className="bg-gray-800/30 rounded-lg p-3 mb-6 flex items-center justify-between">
              <div className="text-sm">
                <span className="text-gray-400">Your Anonymous Beta ID: </span>
                <code className="text-purple-300 font-mono">{userId}</code>
              </div>
              <button
                onClick={copyUserId}
                className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors"
                title="Copy ID"
              >
                <CopyIcon className="w-4 h-4 text-gray-400" />
              </button>
            </div>

            {/* Benefits */}
            <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-xl p-4 mb-6 border border-purple-500/20">
              <h4 className="text-sm font-semibold text-purple-300 mb-2">🎁 Beta Tester Benefits:</h4>
              <ul className="text-xs text-gray-300 space-y-1">
                <li>• Early access to new features</li>
                <li>• Direct impact on app development</li>
                <li>• Priority support for issues</li>
                <li>• Exclusive beta features before public release</li>
              </ul>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button
                onClick={handleAccept}
                className="flex-1 py-3 px-6 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold rounded-xl transition-all transform hover:scale-105 flex items-center justify-center gap-2"
              >
                <CheckCircleIcon className="w-5 h-5" />
                I Understand, Let's Go!
              </button>
            </div>

            {/* Footer note */}
            <p className="text-xs text-gray-500 text-center mt-4">
              You can change telemetry settings anytime in Settings → Privacy
            </p>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}