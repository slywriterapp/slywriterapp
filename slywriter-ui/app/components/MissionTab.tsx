'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  HeartIcon, UsersIcon, TrophyIcon, GiftIcon,
  StarIcon, ZapIcon, CrownIcon, RocketIcon,
  TargetIcon, FlagIcon, CheckCircleIcon, LockIcon,
  ShareIcon, CopyIcon, SparklesIcon, AwardIcon,
  TrendingUpIcon, ChevronRightIcon, DollarSignIcon,
  BrainIcon, KeyboardIcon
} from 'lucide-react'
import toast from 'react-hot-toast'

interface BattlePassTier {
  tier: number
  referrals: number
  reward: string
  icon: React.ElementType
  color: string
  unlocked: boolean
  claimed: boolean
}

export default function MissionTab() {
  const [referralCode, setReferralCode] = useState('')
  const [totalReferrals, setTotalReferrals] = useState(0)
  const [totalDonated, setTotalDonated] = useState(0)
  const [currentTier, setCurrentTier] = useState(0)
  const [copied, setCopied] = useState(false)
  
  // Load referral data from localStorage (synced from backend on login)
  useEffect(() => {
    const userData = localStorage.getItem('user_data')
    if (userData) {
      try {
        const user = JSON.parse(userData)
        setReferralCode(user.referrals?.code || '')
        setTotalReferrals(user.referrals?.count || 0)
        setCurrentTier(user.referrals?.tier_claimed || 0)

        // Calculate donations (10 cents per referral)
        const referralDonations = (user.referrals?.count || 0) * 0.1
        setTotalDonated(referralDonations)
      } catch (error) {
        console.error('Failed to parse user data:', error)
      }
    }
  }, [])
  
  // Battle Pass Tiers
  const battlePassTiers: BattlePassTier[] = [
    { tier: 1, referrals: 1, reward: 'Extra 1,000 words', icon: StarIcon, color: 'from-gray-400 to-gray-500', unlocked: false, claimed: false },
    { tier: 2, referrals: 2, reward: 'Extra 2,500 words', icon: ZapIcon, color: 'from-gray-400 to-gray-500', unlocked: false, claimed: false },
    { tier: 3, referrals: 3, reward: '1 week free Pro', icon: GiftIcon, color: 'from-green-400 to-green-500', unlocked: false, claimed: false },
    { tier: 4, referrals: 5, reward: 'Extra 5,000 words', icon: SparklesIcon, color: 'from-green-400 to-green-500', unlocked: false, claimed: false },
    { tier: 5, referrals: 7, reward: '2 weeks free Pro', icon: HeartIcon, color: 'from-blue-400 to-blue-500', unlocked: false, claimed: false },
    { tier: 6, referrals: 10, reward: 'Extra 10,000 words', icon: BrainIcon, color: 'from-blue-400 to-blue-500', unlocked: false, claimed: false },
    { tier: 7, referrals: 15, reward: '1 month free Pro', icon: CrownIcon, color: 'from-purple-400 to-purple-500', unlocked: false, claimed: false },
    { tier: 8, referrals: 20, reward: 'Extra 25,000 words', icon: RocketIcon, color: 'from-yellow-400 to-orange-500', unlocked: false, claimed: false },
    { tier: 9, referrals: 30, reward: '2 months free Pro', icon: AwardIcon, color: 'from-pink-400 to-red-500', unlocked: false, claimed: false },
    { tier: 10, referrals: 50, reward: '6 months free Pro', icon: TrophyIcon, color: 'from-yellow-300 to-yellow-500', unlocked: false, claimed: false },
  ]
  
  // Update unlocked tiers based on referrals
  const updatedTiers = battlePassTiers.map(tier => ({
    ...tier,
    unlocked: totalReferrals >= tier.referrals,
    claimed: totalReferrals >= tier.referrals && tier.tier <= currentTier
  }))
  
  // Copy referral code
  const copyReferralCode = () => {
    navigator.clipboard.writeText(referralCode)
    setCopied(true)
    toast.success('Referral code copied!')
    setTimeout(() => setCopied(false), 2000)
  }
  
  // Share referral
  const shareReferral = () => {
    const text = `Check out SlyWriter - AI-powered typing assistant! Use my code: ${referralCode}`
    if (navigator.share) {
      navigator.share({
        title: 'SlyWriter',
        text: text,
        url: 'https://slywriter.app'
      })
    } else {
      copyReferralCode()
    }
  }
  
  // Calculate progress to next tier
  const nextTier = updatedTiers.find(t => !t.unlocked)
  const progressToNext = nextTier 
    ? (totalReferrals / nextTier.referrals) * 100
    : 100
  
  return (
    <div className="space-y-6">
      {/* Mission Statement Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 backdrop-blur-sm rounded-2xl p-8 border border-purple-500/20"
      >
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-purple-500/20 rounded-xl">
            <HeartIcon className="w-8 h-8 text-purple-400" />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-white">Our Mission</h2>
            <p className="text-gray-400">Making a difference, one subscription at a time</p>
          </div>
        </div>
        
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-xl font-semibold text-white mb-3">What We Stand For</h3>
            <p className="text-gray-300 leading-relaxed mb-4">
              SlyWriter is built to enhance productivity and accessibility in digital writing. 
              We believe in empowering users with tools that make typing more natural and efficient.
            </p>
            <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
              <p className="text-sm text-yellow-300">
                <strong>Important:</strong> SlyWriter is designed for legitimate productivity, 
                content creation, and accessibility purposes. We do not condone or support 
                academic dishonesty or any form of cheating.
              </p>
            </div>
          </div>
          
          <div>
            <h3 className="text-xl font-semibold text-white mb-3">Our Commitment</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-green-400 rounded-full" />
                <p className="text-gray-300">
                  <strong className="text-purple-400">10%</strong> of every subscription goes directly to Gaza humanitarian aid
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-blue-400 rounded-full" />
                <p className="text-gray-300">
                  <strong className="text-purple-400">$0.10</strong> donated for every referral
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-purple-400 rounded-full" />
                <p className="text-gray-300">
                  <strong className="text-purple-400">100%</strong> transparency in donation tracking
                </p>
              </div>
            </div>
            
            {/* Donation Counter */}
            <div className="mt-6 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-white font-semibold">Total Donated</span>
                <span className="text-3xl font-bold text-white">${totalDonated.toFixed(2)}</span>
              </div>
              <div className="mt-2 text-sm text-purple-100">
                Supporting humanitarian efforts in Gaza
              </div>
            </div>
          </div>
        </div>
      </motion.div>
      
      {/* Referral System */}
      <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold text-white flex items-center gap-2">
            <UsersIcon className="w-7 h-7 text-purple-400" />
            Referral Program
          </h3>
          <div className="text-right">
            <div className="text-sm text-gray-400">Your Referrals</div>
            <div className="text-3xl font-bold text-purple-400">{totalReferrals}</div>
          </div>
        </div>
        
        {/* Referral Code */}
        <div className="bg-gray-800 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Your Referral Code</span>
            <div className="flex gap-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={copyReferralCode}
                className="p-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
              >
                <CopyIcon className={`w-4 h-4 ${copied ? 'text-green-300' : 'text-white'}`} />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={shareReferral}
                className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                <ShareIcon className="w-4 h-4" />
              </motion.button>
            </div>
          </div>
          <div className="text-2xl font-mono font-bold text-white">{referralCode || 'Loading...'}</div>
          {referralCode && (
            <p className="text-xs text-gray-500 mt-2">
              Share this code with friends. They get 500 bonus words, you unlock rewards, and $0.10 goes to charity!
            </p>
          )}
        </div>

        {/* Redeem Referral Code */}
        {totalReferrals === 0 && (
          <div className="bg-gradient-to-br from-green-900/30 to-blue-900/30 rounded-xl p-4 mb-6 border border-green-500/30">
            <h4 className="text-sm font-semibold text-white mb-2">Have a Referral Code?</h4>
            <p className="text-xs text-gray-400 mb-3">Enter a friend's code to get bonus words!</p>
            <div className="flex gap-2">
              <input
                type="text"
                id="redeem-referral-input"
                placeholder="Enter code..."
                className="flex-1 bg-gray-800 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500"
              />
              <button
                onClick={async () => {
                  const input = document.getElementById('redeem-referral-input') as HTMLInputElement
                  const code = input?.value.trim()
                  if (!code) {
                    toast.error('Please enter a referral code')
                    return
                  }

                  try {
                    const token = localStorage.getItem('token')
                    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/redeem-referral`, {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                      },
                      body: JSON.stringify({ code })
                    })

                    const data = await response.json()
                    if (response.ok) {
                      toast.success(`✨ Redeemed! You got ${data.bonus_words} bonus words!`)
                      if (input) input.value = ''
                    } else {
                      toast.error(data.detail || 'Invalid referral code')
                    }
                  } catch (error) {
                    console.error('Failed to redeem referral code:', error)
                    toast.error('Failed to redeem code')
                  }
                }}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white text-sm font-medium transition-colors"
              >
                Redeem
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Battle Pass */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-purple-900/30 via-blue-900/30 to-pink-900/30 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold text-white flex items-center gap-2">
            <TrophyIcon className="w-7 h-7 text-yellow-400" />
            Referral Battle Pass
          </h3>
          <div className="text-sm text-gray-400">
            Next Tier: {nextTier ? `${nextTier.referrals - totalReferrals} referrals away` : 'MAX LEVEL'}
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-400 mb-2">
            <span>Progress to Next Tier</span>
            <span>{Math.round(progressToNext)}%</span>
          </div>
          <div className="h-4 bg-gray-800 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progressToNext}%` }}
              className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
        
        {/* Battle Pass Grid */}
        <div className="grid gap-3">
          {updatedTiers.map((tier, index) => {
            const Icon = tier.icon
            const isUnlocked = tier.unlocked
            const isClaimed = tier.claimed
            const isNext = !isUnlocked && index === updatedTiers.findIndex(t => !t.unlocked)
            
            return (
              <motion.div
                key={tier.tier}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`
                  relative rounded-xl p-4 border transition-all
                  ${isUnlocked 
                    ? 'bg-gradient-to-r ' + tier.color + ' bg-opacity-10 border-purple-500/30' 
                    : 'bg-gray-900/50 border-gray-700/50'
                  }
                  ${isNext ? 'ring-2 ring-purple-500 ring-opacity-50' : ''}
                `}
              >
                {/* Tier Number */}
                <div className={`
                  absolute -left-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full
                  flex items-center justify-center font-bold text-sm
                  ${isUnlocked 
                    ? 'bg-gradient-to-r ' + tier.color + ' text-white' 
                    : 'bg-gray-800 text-gray-500'
                  }
                `}>
                  {tier.tier}
                </div>
                
                <div className="flex items-center justify-between pl-6">
                  <div className="flex items-center gap-4">
                    <div className={`
                      p-2 rounded-lg
                      ${isUnlocked ? 'bg-white/10' : 'bg-gray-800'}
                    `}>
                      <Icon className={`
                        w-6 h-6
                        ${isUnlocked ? 'text-white' : 'text-gray-600'}
                      `} />
                    </div>
                    
                    <div>
                      <div className={`font-semibold ${isUnlocked ? 'text-white' : 'text-gray-500'}`}>
                        {tier.reward}
                      </div>
                      <div className="text-sm text-gray-400">
                        {tier.referrals} referral{tier.referrals > 1 ? 's' : ''} required
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {isUnlocked ? (
                      isClaimed ? (
                        <div className="flex items-center gap-2 px-3 py-1 bg-green-500/20 rounded-lg">
                          <CheckCircleIcon className="w-5 h-5 text-green-400" />
                          <span className="text-sm font-semibold text-green-400">Claimed</span>
                        </div>
                      ) : (
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={async () => {
                            try {
                              const token = localStorage.getItem('token')
                              const userData = JSON.parse(localStorage.getItem('user_data') || '{}')
                              const email = userData.email

                              if (!email) {
                                toast.error('Please log in to claim rewards')
                                return
                              }

                              const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/referrals/claim-reward`, {
                                method: 'POST',
                                headers: {
                                  'Content-Type': 'application/json',
                                  'Authorization': `Bearer ${token}`
                                },
                                body: JSON.stringify({
                                  tier: tier.tier,
                                  email: email
                                })
                              })

                              const data = await response.json()
                              if (response.ok) {
                                setCurrentTier(tier.tier)
                                toast.success(`🎁 ${data.message}!`)

                                // Refresh user data to get updated bonus words and premium status
                                const userResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/login`, {
                                  method: 'POST',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({ email: email })
                                })
                                const userData = await userResponse.json()
                                if (userData.user) {
                                  localStorage.setItem('user_data', JSON.stringify(userData.user))
                                }
                              } else {
                                toast.error(data.detail || 'Failed to claim reward')
                              }
                            } catch (error) {
                              console.error('Failed to claim reward:', error)
                              toast.error('Failed to claim reward')
                            }
                          }}
                          className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg font-semibold"
                        >
                          Claim Reward
                        </motion.button>
                      )
                    ) : (
                      <div className="flex items-center gap-2 text-gray-500">
                        <LockIcon className="w-5 h-5" />
                        <span className="text-sm">Locked</span>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Special Effects for High Tiers */}
                {tier.tier >= 8 && isUnlocked && (
                  <div className="absolute inset-0 rounded-xl pointer-events-none">
                    <div className="absolute inset-0 bg-gradient-to-r from-yellow-400/10 to-orange-400/10 animate-pulse" />
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>
        
        {/* Motivational Footer */}
        <div className="mt-6 text-center">
          <p className="text-gray-400 text-sm">
            Every referral helps us grow and increases our donation to humanitarian causes
          </p>
          <p className="text-purple-400 font-semibold mt-2">
            Together, we've donated ${(totalReferrals * 0.10).toFixed(2)} through referrals!
          </p>
        </div>
      </motion.div>
    </div>
  )
}