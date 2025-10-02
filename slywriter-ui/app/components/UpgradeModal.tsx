'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { XIcon, CrownIcon, ZapIcon, CheckIcon, SparklesIcon } from 'lucide-react'

interface UpgradeModalProps {
  isOpen: boolean
  onClose: () => void
  feature: string
  currentPlan: string
  requiredPlan: 'Pro' | 'Premium'
  usageInfo?: {
    used: number
    limit: number
    type: string
  }
}

export default function UpgradeModal({
  isOpen,
  onClose,
  feature,
  currentPlan,
  requiredPlan,
  usageInfo
}: UpgradeModalProps) {
  const proFeatures = [
    '5,000 words per week',
    'Unlimited AI text generation',
    '3 AI humanizer uses per week',
    'Premium typing modes',
    'Advanced typo patterns',
    'Custom delay ranges'
  ]

  const premiumFeatures = [
    'Unlimited word count',
    'Unlimited AI generation',
    'Unlimited AI humanizer',
    'Bulk text processing',
    'Priority support',
    'All future features'
  ]

  const features = requiredPlan === 'Pro' ? proFeatures : premiumFeatures
  const price = requiredPlan === 'Pro' ? '$8.99' : '$15.00'
  const paymentLink = requiredPlan === 'Pro'
    ? process.env.NEXT_PUBLIC_STRIPE_PRO_LINK || 'https://buy.stripe.com/8x228r9rT5sCfnt5IHdjO01'
    : process.env.NEXT_PUBLIC_STRIPE_PREMIUM_LINK || 'https://buy.stripe.com/8x2bJ1bA18EOb7d9YXdjO00'

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl shadow-2xl max-w-md w-full border border-gray-700"
          >
            {/* Close button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 rounded-lg hover:bg-white/10 transition-colors"
            >
              <XIcon className="w-5 h-5 text-gray-400" />
            </button>

            {/* Content */}
            <div className="p-8">
              {/* Icon */}
              <div className="flex justify-center mb-6">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center">
                  <CrownIcon className="w-8 h-8 text-white" />
                </div>
              </div>

              {/* Title */}
              <h2 className="text-2xl font-bold text-center mb-2 bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
                Upgrade to {requiredPlan}
              </h2>

              {/* Usage info if provided */}
              {usageInfo && (
                <div className="mb-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <p className="text-sm text-red-400 text-center">
                    You've used {usageInfo.used} of {usageInfo.limit} {usageInfo.type} this week
                  </p>
                </div>
              )}

              {/* Description */}
              <p className="text-gray-300 text-center mb-6">
                {currentPlan === 'Free'
                  ? `Unlock ${feature} and more premium features`
                  : `Upgrade to Premium for unlimited ${feature}`}
              </p>

              {/* Features list */}
              <div className="space-y-3 mb-6">
                {features.map((feat, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <CheckIcon className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-300 text-sm">{feat}</span>
                  </div>
                ))}
              </div>

              {/* Price */}
              <div className="text-center mb-6">
                <div className="text-4xl font-bold text-white mb-1">{price}</div>
                <div className="text-gray-400 text-sm">per month</div>
              </div>

              {/* CTA Button */}
              <a
                href={paymentLink}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full py-3 px-6 bg-gradient-to-r from-yellow-400 to-orange-500 hover:from-yellow-500 hover:to-orange-600 text-gray-900 font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 text-center"
              >
                Upgrade to {requiredPlan}
              </a>

              {/* Cancel */}
              <button
                onClick={onClose}
                className="w-full mt-3 py-2 text-gray-400 hover:text-white transition-colors text-sm"
              >
                Maybe later
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
