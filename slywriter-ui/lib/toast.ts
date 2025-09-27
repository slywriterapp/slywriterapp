// Toast compatibility wrapper for react-hot-toast
import { toast as hotToast } from 'react-hot-toast'

// Extend toast with success, error, info methods
const toast = Object.assign(
  hotToast,
  {
    success: (message: string, options?: any) =>
      hotToast(message, { ...options, icon: '✅' }),

    error: (message: string, options?: any) =>
      hotToast(message, { ...options, icon: '❌' }),

    info: (message: string, options?: any) =>
      hotToast(message, { ...options, icon: 'ℹ️' }),

    warning: (message: string, options?: any) =>
      hotToast(message, { ...options, icon: '⚠️' })
  }
)

export { toast }