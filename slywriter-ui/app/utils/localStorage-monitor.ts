export class LocalStorageMonitor {
  private static instance: LocalStorageMonitor | null = null
  private originalSetItem: typeof Storage.prototype.setItem
  private originalRemoveItem: typeof Storage.prototype.removeItem
  private originalClear: typeof Storage.prototype.clear

  private constructor() {
    // Store original methods
    this.originalSetItem = localStorage.setItem.bind(localStorage)
    this.originalRemoveItem = localStorage.removeItem.bind(localStorage)
    this.originalClear = localStorage.clear.bind(localStorage)

    // Override localStorage methods
    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Monitor setItem
    localStorage.setItem = (key: string, value: string) => {
      console.log(`[LocalStorage Monitor] SET "${key}":`)
      console.log(`  - Value: ${key === 'auth_token' ? value.substring(0, 20) + '...' : value.substring(0, 100)}`)
      console.log(`  - Stack trace:`, new Error().stack?.split('\n').slice(2, 4).join('\n'))
      console.log(`  - Timestamp: ${new Date().toISOString()}`)
      
      // Call original method
      this.originalSetItem(key, value)
      
      // Verify it was set
      const verified = localStorage.getItem(key)
      console.log(`  - Verified: ${verified ? 'SUCCESS' : 'FAILED'}`)
    }

    // Monitor removeItem
    localStorage.removeItem = (key: string) => {
      console.log(`[LocalStorage Monitor] REMOVE "${key}"`)
      console.log(`  - Stack trace:`, new Error().stack?.split('\n').slice(2, 4).join('\n'))
      console.log(`  - Timestamp: ${new Date().toISOString()}`)
      
      // Call original method
      this.originalRemoveItem(key)
    }

    // Monitor clear
    localStorage.clear = () => {
      console.log(`[LocalStorage Monitor] CLEAR ALL`)
      console.log(`  - Stack trace:`, new Error().stack?.split('\n').slice(2, 4).join('\n'))
      console.log(`  - Timestamp: ${new Date().toISOString()}`)
      
      // Call original method
      this.originalClear()
    }
  }

  public static start() {
    if (!this.instance && typeof window !== 'undefined') {
      console.log('[LocalStorage Monitor] Starting monitoring...')
      this.instance = new LocalStorageMonitor()
    }
  }

  public static stop() {
    if (this.instance) {
      console.log('[LocalStorage Monitor] Stopping monitoring...')
      // Restore original methods
      localStorage.setItem = this.instance.originalSetItem
      localStorage.removeItem = this.instance.originalRemoveItem
      localStorage.clear = this.instance.originalClear
      this.instance = null
    }
  }

  public static logCurrentState() {
    console.log('[LocalStorage Monitor] Current state:')
    console.log(`  - auth_token: ${localStorage.getItem('auth_token') ? 'EXISTS' : 'MISSING'}`)
    console.log(`  - user_data: ${localStorage.getItem('user_data') ? 'EXISTS' : 'MISSING'}`)
    
    const token = localStorage.getItem('auth_token')
    if (token) {
      console.log(`  - Token preview: ${token.substring(0, 20)}...`)
    }
    
    const userData = localStorage.getItem('user_data')
    if (userData) {
      try {
        const parsed = JSON.parse(userData)
        console.log(`  - User email: ${parsed.email}`)
      } catch (e) {
        console.log(`  - User data parse error:`, e)
      }
    }
  }
}