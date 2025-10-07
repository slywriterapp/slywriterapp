import axios from 'axios'

// Comprehensive Beta Testing Telemetry System
interface SystemInfo {
  platform: string
  userAgent: string
  screenResolution: string
  timezone: string
  language: string
  electronVersion?: string
  nodeVersion?: string
}

interface UserAction {
  action: string
  component: string
  details: any
  timestamp: string
  sessionTime: number // Time since session start
}

interface ErrorEvent {
  error: string
  stack?: string
  component: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: string
  context: any
}

interface FeatureUsage {
  feature: string
  usageCount: number
  totalTime: number
  lastUsed: string
  settings: any
}

interface PerformanceMetric {
  metric: string
  value: number
  unit: string
  timestamp: string
}

class BetaTelemetryService {
  private userId: string
  private sessionId: string
  private sessionStart: number
  private actions: UserAction[] = []
  private errors: ErrorEvent[] = []
  private featureUsage: Map<string, FeatureUsage> = new Map()
  private performanceMetrics: PerformanceMetric[] = []
  private systemInfo: SystemInfo
  private isEnabled: boolean = true // Auto-enabled for beta
  private uploadInterval: NodeJS.Timeout | null = null
  private actionBuffer: UserAction[] = []
  private lastActivity: number = Date.now()

  // Cloud telemetry endpoint
  private TELEMETRY_API_URL = 'https://slywriterapp.onrender.com'
  
  constructor() {
    this.userId = this.getOrCreateUserId()
    this.sessionId = this.generateSessionId()
    this.sessionStart = Date.now()
    this.systemInfo = this.collectSystemInfo()
    
    // Initialize from localStorage
    this.loadStoredData()
    
    // Check if we're in development mode
    const isDevelopment = process.env.NODE_ENV === 'development' || 
                         (typeof window !== 'undefined' && (
                           window.location.hostname === 'localhost' ||
                           window.location.hostname === '127.0.0.1'
                         ))
    
    if (!isDevelopment) {
      // Only auto-enable for production/beta builds
      this.enableBetaTelemetry()
      
      // Start upload interval (every 30 seconds)
      this.startUploadInterval()
      
      // Track page visibility
      this.trackPageVisibility()
      
      // Track errors globally
      this.setupErrorTracking()
      
      // Track performance
      this.initPerformanceMonitoring()
    } else {
      // In development, telemetry is off by default
      this.isEnabled = false
      console.log('[Telemetry] Disabled in development mode')
    }
  }

  private getOrCreateUserId(): string {
    if (typeof window === 'undefined') return 'server'
    
    let userId = localStorage.getItem('betaUserId')
    if (!userId) {
      // Generate anonymous but persistent ID
      userId = `beta_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`
      localStorage.setItem('betaUserId', userId)
    }
    return userId
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
  }

  private collectSystemInfo(): SystemInfo {
    if (typeof window === 'undefined') {
      return {
        platform: 'server',
        userAgent: 'server',
        screenResolution: 'N/A',
        timezone: 'UTC',
        language: 'en'
      }
    }

    return {
      platform: navigator.platform || 'unknown',
      userAgent: navigator.userAgent,
      screenResolution: `${window.screen.width}x${window.screen.height}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: navigator.language,
      electronVersion: (window as any).electron?.version,
      nodeVersion: (window as any).electron?.nodeVersion
    }
  }

  private enableBetaTelemetry() {
    // Check if first time beta user
    const betaAcknowledged = localStorage.getItem('betaTelemetryAcknowledged')
    if (!betaAcknowledged) {
      // Will be acknowledged when user sees the disclosure
      this.isEnabled = true
      localStorage.setItem('betaTelemetryEnabled', 'true')
    } else {
      // Check user preference
      this.isEnabled = localStorage.getItem('betaTelemetryEnabled') !== 'false'
    }
  }

  // Track every user action
  public trackAction(action: string, component: string, details: any = {}) {
    if (!this.isEnabled) return

    const userAction: UserAction = {
      action,
      component,
      details,
      timestamp: new Date().toISOString(),
      sessionTime: Date.now() - this.sessionStart
    }

    this.actions.push(userAction)
    this.actionBuffer.push(userAction)
    this.lastActivity = Date.now()

    // Update feature usage
    this.updateFeatureUsage(component, details)

    // If buffer is large, upload immediately
    if (this.actionBuffer.length >= 50) {
      this.uploadData()
    }
  }

  // Track errors with context
  public trackError(error: Error | string, component: string, context: any = {}, severity: 'low' | 'medium' | 'high' | 'critical' = 'medium') {
    const errorEvent: ErrorEvent = {
      error: error instanceof Error ? error.message : error,
      stack: error instanceof Error ? error.stack : undefined,
      component,
      severity,
      timestamp: new Date().toISOString(),
      context: {
        ...context,
        sessionTime: Date.now() - this.sessionStart,
        lastAction: this.actions[this.actions.length - 1]
      }
    }

    this.errors.push(errorEvent)
    
    // Upload critical errors immediately
    if (severity === 'critical' || severity === 'high') {
      this.uploadData()
    }
  }

  // Track feature usage patterns
  private updateFeatureUsage(feature: string, settings: any) {
    const existing = this.featureUsage.get(feature) || {
      feature,
      usageCount: 0,
      totalTime: 0,
      lastUsed: new Date().toISOString(),
      settings: {}
    }

    existing.usageCount++
    existing.lastUsed = new Date().toISOString()
    existing.settings = { ...existing.settings, ...settings }

    this.featureUsage.set(feature, existing)
  }

  // Track performance metrics
  public trackPerformance(metric: string, value: number, unit: string = 'ms') {
    if (!this.isEnabled) return

    this.performanceMetrics.push({
      metric,
      value,
      unit,
      timestamp: new Date().toISOString()
    })
  }

  // Setup global error tracking
  private setupErrorTracking() {
    if (typeof window === 'undefined') return

    window.addEventListener('error', (event) => {
      this.trackError(
        event.error || event.message,
        'window',
        {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno
        },
        'high'
      )
    })

    window.addEventListener('unhandledrejection', (event) => {
      this.trackError(
        event.reason,
        'promise',
        { promise: event.promise },
        'high'
      )
    })
  }

  // Track page visibility
  private trackPageVisibility() {
    if (typeof document === 'undefined') return

    document.addEventListener('visibilitychange', () => {
      this.trackAction(
        document.hidden ? 'page_hidden' : 'page_visible',
        'document',
        { hidden: document.hidden }
      )
    })
  }

  // Initialize performance monitoring
  private initPerformanceMonitoring() {
    if (typeof window === 'undefined' || !window.performance) return

    // Track page load performance
    window.addEventListener('load', () => {
      const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      if (perfData) {
        this.trackPerformance('page_load', perfData.loadEventEnd - perfData.fetchStart)
        this.trackPerformance('dom_ready', perfData.domContentLoadedEventEnd - perfData.fetchStart)
      }
    })

    // Track long tasks (blocking main thread)
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) { // Tasks longer than 50ms
              this.trackPerformance('long_task', entry.duration)
            }
          }
        })
        observer.observe({ entryTypes: ['longtask'] })
      } catch (e) {
        // Some browsers don't support longtask
      }
    }
  }

  // Upload data to server
  private async uploadData() {
    if (!this.isEnabled || this.actionBuffer.length === 0) return

    const data = {
      userId: this.userId,
      sessionId: this.sessionId,
      systemInfo: this.systemInfo,
      actions: [...this.actionBuffer],
      errors: this.errors.slice(-10), // Last 10 errors
      featureUsage: Array.from(this.featureUsage.values()),
      performanceMetrics: this.performanceMetrics.slice(-50), // Last 50 metrics
      sessionDuration: Date.now() - this.sessionStart,
      lastActivity: this.lastActivity,
      timestamp: new Date().toISOString()
    }

    try {
      // Upload to cloud server
      await this.uploadToCloud(data)
      
      // Clear buffer after successful upload
      this.actionBuffer = []
      
      // Remove local backup after successful cloud upload
      this.clearLocalBackup()
    } catch (error) {
      console.debug('Telemetry upload failed, saving locally as backup', error)
      this.saveToLocalStorage(data)
    }
  }

  // Upload to cloud server
  private async uploadToCloud(data: any) {
    try {
      await axios.post(`${this.TELEMETRY_API_URL}/api/beta-telemetry`, data, {
        timeout: 3000, // Reduced to 3 seconds - fail fast, don't block UI
        headers: {
          'Content-Type': 'application/json'
        }
      })
    } catch (error) {
      // Silently fail - telemetry is non-critical
      console.debug('Telemetry upload failed (non-critical)', error)
      throw error
    }
  }

  // Save to localStorage as backup
  private saveToLocalStorage(data: any) {
    if (typeof window === 'undefined') return

    // Get existing data
    const existing = localStorage.getItem('betaTelemetryData')
    const allData = existing ? JSON.parse(existing) : []
    
    // Add new data
    allData.push(data)
    
    // Keep only last 100 uploads
    if (allData.length > 100) {
      allData.shift()
    }
    
    localStorage.setItem('betaTelemetryData', JSON.stringify(allData))
  }

  // Load stored data on init and upload to cloud (non-blocking)
  private loadStoredData() {
    if (typeof window === 'undefined') return

    const stored = localStorage.getItem('betaTelemetryData')
    if (stored) {
      try {
        const data = JSON.parse(stored)
        // Upload stored data in background - don't block page load
        setTimeout(() => {
          data.forEach((d: any) => {
            this.uploadToCloud(d).catch(() => {
              // Silently fail - data will retry next session
            })
          })
        }, 5000) // Wait 5 seconds after page load
      } catch (e) {
        console.debug('Failed to load stored telemetry', e)
      }
    }
  }
  
  // Clear local backup after successful upload
  private clearLocalBackup() {
    if (typeof window === 'undefined') return
    
    // Keep only last 10 entries as emergency backup
    const stored = localStorage.getItem('betaTelemetryData')
    if (stored) {
      const data = JSON.parse(stored)
      if (data.length > 10) {
        localStorage.setItem('betaTelemetryData', JSON.stringify(data.slice(-10)))
      }
    }
  }

  // Start automatic upload interval
  private startUploadInterval() {
    if (this.uploadInterval) clearInterval(this.uploadInterval)
    
    this.uploadInterval = setInterval(() => {
      if (this.actionBuffer.length > 0) {
        this.uploadData()
      }
    }, 30000) // Every 30 seconds
  }

  // Get telemetry status
  public getStatus() {
    return {
      enabled: this.isEnabled,
      userId: this.userId,
      sessionId: this.sessionId,
      actionsTracked: this.actions.length,
      errorsTracked: this.errors.length,
      sessionDuration: Date.now() - this.sessionStart,
      bufferSize: this.actionBuffer.length
    }
  }

  // Enable/disable telemetry
  public setEnabled(enabled: boolean) {
    this.isEnabled = enabled
    localStorage.setItem('betaTelemetryEnabled', enabled.toString())
    
    if (enabled) {
      this.startUploadInterval()
    } else {
      if (this.uploadInterval) {
        clearInterval(this.uploadInterval)
        this.uploadInterval = null
      }
    }
  }

  // Export all data for user
  public async exportUserData() {
    const allData = {
      userId: this.userId,
      sessions: [
        {
          sessionId: this.sessionId,
          systemInfo: this.systemInfo,
          actions: this.actions,
          errors: this.errors,
          featureUsage: Array.from(this.featureUsage.values()),
          performanceMetrics: this.performanceMetrics,
          sessionDuration: Date.now() - this.sessionStart
        }
      ],
      storedData: JSON.parse(localStorage.getItem('betaTelemetryData') || '[]'),
      exportDate: new Date().toISOString()
    }

    return allData
  }

  // Clear all data
  public clearAllData() {
    this.actions = []
    this.errors = []
    this.featureUsage.clear()
    this.performanceMetrics = []
    this.actionBuffer = []
    localStorage.removeItem('betaTelemetryData')
  }
}

// Create singleton instance only on client
export const betaTelemetry = typeof window !== 'undefined' ? new BetaTelemetryService() : null as any

// Auto-track common actions
if (typeof window !== 'undefined' && typeof document !== 'undefined' && betaTelemetry) {
  // Track clicks
  document.addEventListener('click', (e) => {
    const target = e.target as HTMLElement
    const id = target.id || target.className || 'unknown'
    betaTelemetry?.trackAction('click', id, {
      tag: target.tagName,
      text: target.textContent?.substring(0, 50)
    })
  })

  // Track route changes (for Next.js)
  const originalPushState = history.pushState
  history.pushState = function() {
    originalPushState.apply(history, arguments as any)
    betaTelemetry?.trackAction('navigation', 'route', {
      url: window.location.pathname
    })
  }
}

export default betaTelemetry