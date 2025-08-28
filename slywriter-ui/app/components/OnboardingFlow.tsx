'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  RocketIcon, MousePointerClickIcon, ZapIcon, KeyboardIcon,
  CheckCircleIcon, ArrowRightIcon, SparklesIcon, ClockIcon,
  TrophyIcon, GiftIcon, PlayIcon, XIcon
} from 'lucide-react'

interface OnboardingProps {
  isVisible: boolean
  onComplete: (selectedProfile?: string, triggerWpmTest?: boolean) => void
}

export default function OnboardingFlow({ isVisible, onComplete }: OnboardingProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [hasSeenOnboarding, setHasSeenOnboarding] = useState(false)
  const [demoText, setDemoText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [selectedProfile, setSelectedProfile] = useState<string | null>(null)

  useEffect(() => {
    const seen = localStorage.getItem('slywriter-onboarding-complete')
    if (seen) {
      setHasSeenOnboarding(true)
    }
  }, [])

  const completeOnboarding = (profile?: string, triggerTest?: boolean) => {
    localStorage.setItem('slywriter-onboarding-complete', 'true')
    if (profile) {
      localStorage.setItem('slywriter-selected-profile', profile)
    }
    onComplete(profile, triggerTest)
  }

  const steps = [
    {
      id: 'welcome',
      title: 'Welcome to SlyWriter',
      subtitle: 'The AI That Types FOR You',
      content: (
        <div className="space-y-6">
          <div className="text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", duration: 0.5 }}
              className="w-24 h-24 mx-auto bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center mb-4"
            >
              <ZapIcon className="w-12 h-12 text-white" />
            </motion.div>
            <p className="text-lg text-gray-300 mb-6">
              SlyWriter isn't a typing tutor. It's your personal AI assistant that automatically types for you with human-like patterns.
            </p>
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            {[
              { icon: ClockIcon, label: 'Save Hours', value: 'Auto-types everything' },
              { icon: SparklesIcon, label: 'Undetectable', value: 'Human-like patterns' },
              { icon: TrophyIcon, label: 'AI Powered', value: 'Creates content too' }
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + i * 0.1 }}
                className="bg-gray-800 bg-gray-900/50 rounded-lg p-4 text-center"
              >
                <stat.icon className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                <div className="text-xs text-gray-400">{stat.label}</div>
                <div className="text-sm font-semibold text-white">{stat.value}</div>
              </motion.div>
            ))}
          </div>
        </div>
      ),
      action: 'Get Started'
    },
    {
      id: 'how-it-works',
      title: 'How It Works',
      subtitle: 'Three Simple Steps',
      content: (
        <div className="space-y-4">
          {[
            {
              step: 1,
              title: 'Copy or Create Text',
              desc: 'Paste any text or let our AI generate it for you',
              icon: MousePointerClickIcon
            },
            {
              step: 2,
              title: 'Choose Your Style',
              desc: 'Select typing speed and human-like patterns',
              icon: SparklesIcon
            },
            {
              step: 3,
              title: 'Watch It Type',
              desc: 'SlyWriter types it for you automatically',
              icon: KeyboardIcon
            }
          ].map((item, i) => (
            <motion.div
              key={i}
              initial={{ x: -50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: i * 0.2 }}
              className="flex items-start gap-4 p-4 bg-gray-800 bg-gray-900/30 rounded-lg border border-gray-700/50"
            >
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold">{item.step}</span>
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-white mb-1">{item.title}</h4>
                <p className="text-sm text-gray-400">{item.desc}</p>
              </div>
              <item.icon className="w-6 h-6 text-purple-400 flex-shrink-0" />
            </motion.div>
          ))}
        </div>
      ),
      action: 'See Demo'
    },
    {
      id: 'demo',
      title: 'Watch SlyWriter in Action',
      subtitle: 'It Types FOR You',
      content: (
        <div className="space-y-4">
          <div className="bg-gray-900 rounded-lg p-4 border border-purple-500/30">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-gray-400">Demo Text Area</span>
              {isTyping && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-xs text-green-400">Typing...</span>
                </div>
              )}
            </div>
            <div className="bg-black/50 rounded p-3 min-h-[100px] font-mono text-sm text-white">
              {demoText || (
                <span className="text-gray-400">Click "Start Demo" to see automated typing...</span>
              )}
              {isTyping && (
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                  className="inline-block w-0.5 h-4 bg-purple-400 ml-0.5"
                />
              )}
            </div>
          </div>
          
          {!isTyping ? (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                setIsTyping(true)
                setDemoText('')
                const text = "Hello! I'm SlyWriter, and I type for you automatically with human-like patterns. No more manual typing!"
                let index = 0
                
                const typeChar = () => {
                  if (index < text.length) {
                    setDemoText(prev => prev + text[index])
                    index++
                    setTimeout(typeChar, 50 + Math.random() * 100)
                  } else {
                    setIsTyping(false)
                  }
                }
                
                setTimeout(typeChar, 500)
              }}
              className="w-full py-3 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg font-medium text-white flex items-center justify-center gap-2"
            >
              <PlayIcon className="w-5 h-5" />
              Start Demo
            </motion.button>
          ) : (
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-gray-800 bg-gray-900/50 rounded p-2">
                <div className="text-2xl font-bold text-purple-400">
                  {Math.round(60 + Math.random() * 20)}
                </div>
                <div className="text-xs text-gray-400">WPM</div>
              </div>
              <div className="bg-gray-800 bg-gray-900/50 rounded p-2">
                <div className="text-2xl font-bold text-green-400">98%</div>
                <div className="text-xs text-gray-400">Human Score</div>
              </div>
              <div className="bg-gray-800 bg-gray-900/50 rounded p-2">
                <div className="text-2xl font-bold text-blue-400">0%</div>
                <div className="text-xs text-gray-400">Detection</div>
              </div>
            </div>
          )}
        </div>
      ),
      action: 'Next'
    },
    {
      id: 'ai-power',
      title: 'AI-Powered Features',
      subtitle: 'More Than Just Typing',
      content: (
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 rounded-lg p-4 border border-purple-500/30">
            <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
              <SparklesIcon className="w-5 h-5 text-purple-400" />
              The Magic Workflow
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="w-4 h-4 text-green-400 flex-shrink-0" />
                <span className="text-gray-300">
                  <span className="text-white font-medium">Highlight</span> any question or prompt
                </span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="w-4 h-4 text-green-400 flex-shrink-0" />
                <span className="text-gray-300">
                  Press <kbd className="px-2 py-0.5 bg-gray-700 bg-gray-800 rounded text-xs">Ctrl+Alt+G</kbd> for AI answer
                </span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="w-4 h-4 text-green-400 flex-shrink-0" />
                <span className="text-gray-300">
                  <span className="text-white font-medium">Humanize</span> to make undetectable
                </span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="w-4 h-4 text-green-400 flex-shrink-0" />
                <span className="text-gray-300">
                  <span className="text-white font-medium">Auto-types</span> with human patterns
                </span>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'AI Writer', desc: 'Generate essays & content' },
              { label: 'Humanizer', desc: 'Make AI undetectable' },
              { label: 'Smart Learn', desc: 'AI explains anything' },
              { label: 'Schedules', desc: 'Automate typing tasks' }
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: i * 0.1 }}
                className="bg-gray-800 bg-gray-900/30 rounded-lg p-3 text-center"
              >
                <div className="font-medium text-white text-sm">{feature.label}</div>
                <div className="text-xs text-gray-400 mt-1">{feature.desc}</div>
              </motion.div>
            ))}
          </div>
        </div>
      ),
      action: 'Setup Profile'
    },
    {
      id: 'calibrate',
      title: 'Quick Setup',
      subtitle: 'Calibrate Your Typing Style',
      content: (
        <div className="space-y-4">
          <div className="bg-gray-800 bg-gray-900/50 rounded-lg p-4">
            <h4 className="font-medium text-white mb-3">Choose Your Default Speed</h4>
            <div className="space-y-2">
              {[
                { name: 'Slow', desc: '~60 WPM - Very natural, lots of pauses', color: 'blue' },
                { name: 'Medium', desc: '~80 WPM - Balanced speed and realism', color: 'green' },
                { name: 'Fast', desc: '~120 WPM - Quick but still human-like', color: 'purple' },
                { name: 'Custom', desc: 'Take a test to match YOUR speed', color: 'orange' }
              ].map((profile) => (
                <button
                  key={profile.name}
                  className="w-full p-3 bg-gray-700/50 hover:bg-gray-700 bg-gray-800 rounded-lg border border-gray-600 hover:border-purple-500 transition-all text-left"
                  onClick={() => {
                    setSelectedProfile(profile.name)
                    if (profile.name === 'Custom') {
                      // Custom needs WPM test, so complete onboarding with test flag
                      completeOnboarding(profile.name, true)
                    } else {
                      // Other profiles can be set directly
                      completeOnboarding(profile.name, false)
                    }
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-white">{profile.name}</div>
                      <div className="text-xs text-gray-400">{profile.desc}</div>
                    </div>
                    <ArrowRightIcon className="w-4 h-4 text-gray-400" />
                  </div>
                </button>
              ))}
            </div>
          </div>
          
          <div className="flex items-start gap-3 p-3 bg-blue-500/10 rounded-lg border border-blue-500/30">
            <SparklesIcon className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="text-blue-300 font-medium">Pro Tip</p>
              <p className="text-gray-400 mt-1">
                All profiles include realistic typos and corrections by default to avoid detection.
              </p>
            </div>
          </div>
        </div>
      ),
      action: 'Finish Setup'
    }
  ]

  if (hasSeenOnboarding || !isVisible) {
    return null
  }

  const currentStepData = steps[currentStep]

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="w-full max-w-2xl bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl shadow-2xl border border-purple-500/30 overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-white">{currentStepData.title}</h2>
                <p className="text-purple-100 mt-1">{currentStepData.subtitle}</p>
              </div>
              <button
                onClick={completeOnboarding}
                className="text-white/70 hover:text-white transition-colors"
              >
                <XIcon className="w-6 h-6" />
              </button>
            </div>
            
            {/* Progress */}
            <div className="flex gap-2">
              {steps.map((_, i) => (
                <div
                  key={i}
                  className={`h-1 flex-1 rounded-full transition-all ${
                    i <= currentStep ? 'bg-gray-900' : 'bg-gray-900/30'
                  }`}
                />
              ))}
            </div>
          </div>
          
          {/* Content */}
          <div className="p-6">
            {currentStepData.content}
          </div>
          
          {/* Actions */}
          <div className="p-6 pt-0 flex gap-3">
            {currentStep > 0 && (
              <button
                onClick={() => setCurrentStep(currentStep - 1)}
                className="px-6 py-3 bg-gray-700 bg-gray-800 hover:bg-gray-600 rounded-lg font-medium text-white transition-colors"
              >
                Back
              </button>
            )}
            
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                if (currentStep < steps.length - 1) {
                  setCurrentStep(currentStep + 1)
                } else {
                  completeOnboarding()
                }
              }}
              className="flex-1 py-3 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg font-medium text-white flex items-center justify-center gap-2"
            >
              {currentStepData.action}
              {currentStep < steps.length - 1 ? (
                <ArrowRightIcon className="w-5 h-5" />
              ) : (
                <CheckCircleIcon className="w-5 h-5" />
              )}
            </motion.button>
            
            <button
              onClick={completeOnboarding}
              className="px-6 py-3 text-gray-400 hover:text-white transition-colors"
            >
              Skip
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}