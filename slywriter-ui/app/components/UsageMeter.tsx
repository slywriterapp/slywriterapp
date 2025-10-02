'use client'

import { motion } from 'framer-motion'
import { AlertCircleIcon, CrownIcon, ZapIcon } from 'lucide-react'

interface UsageMeterProps {
  label: string
  used: number
  limit: number | string
  icon?: React.ReactNode
  showUpgrade?: boolean
  onUpgradeClick?: () => void
}

export default function UsageMeter({
  label,
  used,
  limit,
  icon,
  showUpgrade = false,
  onUpgradeClick
}: UsageMeterProps) {
  const isUnlimited = limit === 'Unlimited' || limit === -1
  const numLimit = typeof limit === 'number' ? limit : 0
  const percentage = isUnlimited ? 100 : Math.min((used / numLimit) * 100, 100)
  const remaining = isUnlimited ? '∞' : Math.max(0, numLimit - used)

  // Color based on usage
  const getColor = () => {
    if (isUnlimited) return 'from-green-500 to-emerald-500'
    if (percentage >= 90) return 'from-red-500 to-rose-600'
    if (percentage >= 70) return 'from-yellow-500 to-orange-500'
    return 'from-blue-500 to-indigo-500'
  }

  const getTextColor = () => {
    if (isUnlimited) return 'text-green-400'
    if (percentage >= 90) return 'text-red-400'
    if (percentage >= 70) return 'text-yellow-400'
    return 'text-blue-400'
  }

  return (
    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-medium text-gray-300">{label}</span>
        </div>
        {isUnlimited && (
          <div className="flex items-center gap-1 text-green-400">
            <CrownIcon className="w-4 h-4" />
            <span className="text-xs font-semibold">Unlimited</span>
          </div>
        )}
      </div>

      {/* Progress bar */}
      {!isUnlimited && (
        <div className="relative h-2 bg-gray-700 rounded-full overflow-hidden mb-2">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className={`absolute inset-y-0 left-0 bg-gradient-to-r ${getColor()} rounded-full`}
          />
        </div>
      )}

      {/* Stats */}
      <div className="flex items-center justify-between text-sm">
        <span className={`font-medium ${getTextColor()}`}>
          {used} / {isUnlimited ? '∞' : numLimit} used
        </span>
        <span className="text-gray-400">
          {remaining} remaining
        </span>
      </div>

      {/* Upgrade prompt */}
      {showUpgrade && !isUnlimited && percentage >= 80 && (
        <motion.button
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={onUpgradeClick}
          className="mt-3 w-full py-2 px-4 bg-gradient-to-r from-yellow-400 to-orange-500 hover:from-yellow-500 hover:to-orange-600 text-gray-900 font-semibold rounded-lg transition-all duration-200 flex items-center justify-center gap-2 text-sm"
        >
          <ZapIcon className="w-4 h-4" />
          Upgrade for more
        </motion.button>
      )}

      {/* Warning */}
      {!isUnlimited && remaining === 0 && (
        <div className="mt-2 flex items-center gap-2 text-red-400 text-xs">
          <AlertCircleIcon className="w-4 h-4" />
          <span>Limit reached - resets Monday</span>
        </div>
      )}
    </div>
  )
}
