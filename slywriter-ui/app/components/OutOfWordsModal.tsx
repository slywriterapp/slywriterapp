'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { X, Crown, Users, ArrowRight, Sparkles } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'

interface OutOfWordsModalProps {
  isOpen: boolean
  onClose: () => void
  wordsRemaining: number
  userEmail: string
  referralCode: string
}

export default function OutOfWordsModal({ isOpen, onClose, wordsRemaining, userEmail, referralCode }: OutOfWordsModalProps) {
  const [copied, setCopied] = useState(false)

  const copyReferralCode = () => {
    navigator.clipboard.writeText(referralCode)
    setCopied(true)
    toast.success('Referral code copied!')
    setTimeout(() => setCopied(false), 2000)
  }

  const openUpgradeLink = (plan: 'pro' | 'premium') => {
    const proLink = process.env.NEXT_PUBLIC_STRIPE_PRO_PAYMENT_LINK
    const premiumLink = process.env.NEXT_PUBLIC_STRIPE_PREMIUM_PAYMENT_LINK
    const url = `${plan === 'pro' ? proLink : premiumLink}?prefilled_email=${encodeURIComponent(userEmail)}`

    // Open in system browser (Electron will intercept this)
    window.open(url, '_blank')
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999]"
          />

          {/* Modal */}
          <div className="fixed inset-0 flex items-center justify-center z-[10000] p-4">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl shadow-2xl max-w-2xl w-full border border-purple-500/30 overflow-hidden"
            >
              {/* Header */}
              <div className="relative bg-gradient-to-r from-red-500/20 to-orange-500/20 border-b border-red-500/30 p-6">
                <button
                  onClick={onClose}
                  className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>

                <div className="flex items-center gap-3 mb-2">
                  <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center">
                    <Sparkles className="w-6 h-6 text-red-400" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">You're Out of Words!</h2>
                    <p className="text-red-300 text-sm">Current balance: {wordsRemaining} words</p>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-6 space-y-6">
                <p className="text-gray-300">
                  Don't worry! You have two ways to get more words and keep typing:
                </p>

                {/* Option 1: Upgrade */}
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Crown className="w-5 h-5 text-yellow-400" />
                    Option 1: Upgrade Your Plan
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Pro Plan */}
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => openUpgradeLink('pro')}
                      className="bg-gradient-to-br from-blue-900/40 to-purple-900/40 border border-blue-500/50 rounded-xl p-5 text-left hover:border-blue-400 transition-all group"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <h4 className="text-blue-400 font-bold text-lg">Pro</h4>
                        <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">Popular</span>
                      </div>
                      <p className="text-3xl font-bold text-white mb-3">
                        $8.99<span className="text-sm text-gray-400 font-normal">/mo</span>
                      </p>
                      <ul className="space-y-2 text-sm text-gray-300 mb-4">
                        <li className="flex items-center gap-2">
                          <span className="text-blue-400">✓</span> 5,000 words/week
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="text-blue-400">✓</span> AI generation
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="text-blue-400">✓</span> 3 humanizer uses/week
                        </li>
                      </ul>
                      <div className="flex items-center text-blue-400 text-sm font-medium group-hover:text-blue-300">
                        Upgrade Now <ArrowRight className="w-4 h-4 ml-1" />
                      </div>
                    </motion.button>

                    {/* Premium Plan */}
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => openUpgradeLink('premium')}
                      className="bg-gradient-to-br from-purple-900/40 to-pink-900/40 border border-purple-500/50 rounded-xl p-5 text-left hover:border-purple-400 transition-all group relative overflow-hidden"
                    >
                      <div className="absolute top-0 right-0 bg-gradient-to-l from-purple-500 to-pink-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
                        BEST VALUE
                      </div>
                      <div className="flex items-start justify-between mb-3">
                        <h4 className="text-purple-400 font-bold text-lg">Premium</h4>
                        <Crown className="w-5 h-5 text-yellow-400" />
                      </div>
                      <p className="text-3xl font-bold text-white mb-3">
                        $14.99<span className="text-sm text-gray-400 font-normal">/mo</span>
                      </p>
                      <ul className="space-y-2 text-sm text-gray-300 mb-4">
                        <li className="flex items-center gap-2">
                          <span className="text-purple-400">✓</span> Unlimited words
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="text-purple-400">✓</span> Unlimited AI humanizer
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="text-purple-400">✓</span> Priority support
                        </li>
                      </ul>
                      <div className="flex items-center text-purple-400 text-sm font-medium group-hover:text-purple-300">
                        Upgrade Now <ArrowRight className="w-4 h-4 ml-1" />
                      </div>
                    </motion.button>
                  </div>
                </div>

                {/* Divider */}
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-px bg-gray-700" />
                  <span className="text-gray-500 text-sm font-medium">OR</span>
                  <div className="flex-1 h-px bg-gray-700" />
                </div>

                {/* Option 2: Refer Friends */}
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Users className="w-5 h-5 text-green-400" />
                    Option 2: Refer Friends (Free!)
                  </h3>

                  <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-5">
                    <p className="text-green-300 text-sm mb-4">
                      Share your referral code and earn <span className="font-bold">500 bonus words</span> for each friend who signs up!
                    </p>

                    <div className="flex gap-2">
                      <div className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 font-mono text-lg text-white">
                        {referralCode}
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={copyReferralCode}
                        className={`px-6 py-3 rounded-lg font-medium transition-all ${
                          copied
                            ? 'bg-green-500 text-white'
                            : 'bg-purple-500 hover:bg-purple-600 text-white'
                        }`}
                      >
                        {copied ? '✓ Copied!' : 'Copy Code'}
                      </motion.button>
                    </div>

                    <p className="text-gray-400 text-xs mt-3">
                      Your friend gets 500 words too! Share on Discord, Twitter, or with classmates.
                    </p>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="bg-gray-800/50 border-t border-gray-700 px-6 py-4">
                <p className="text-gray-400 text-xs text-center">
                  Need help? Visit our{' '}
                  <a href="https://slywriterapp.com/support" target="_blank" className="text-purple-400 hover:text-purple-300">
                    support page
                  </a>{' '}
                  or contact us.
                </p>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
