class SoundService {
  private soundEnabled: boolean = true
  private notificationsEnabled: boolean = true
  private audioContext: AudioContext | null = null
  
  constructor() {
    this.loadSettings()
    
    // Listen for settings changes
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', (e) => {
        if (e.key === 'soundEnabled' || e.key === 'notifications') {
          this.loadSettings()
        }
      })
    }
  }
  
  private loadSettings() {
    if (typeof window !== 'undefined') {
      const soundSetting = localStorage.getItem('soundEnabled')
      this.soundEnabled = soundSetting !== 'false'
      
      const notificationsSetting = localStorage.getItem('notifications')
      this.notificationsEnabled = notificationsSetting !== 'false'
    }
  }
  
  private initAudioContext() {
    if (!this.audioContext && typeof window !== 'undefined') {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    }
  }
  
  public playKeySound() {
    if (!this.soundEnabled) return
    
    try {
      this.initAudioContext()
      if (!this.audioContext) return
      
      const oscillator = this.audioContext.createOscillator()
      const gainNode = this.audioContext.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(this.audioContext.destination)
      
      oscillator.frequency.value = 800 + Math.random() * 400 // Random frequency between 800-1200 Hz
      gainNode.gain.value = 0.02 // Very quiet
      
      oscillator.start()
      oscillator.stop(this.audioContext.currentTime + 0.01) // Very short sound
    } catch (error) {
      console.debug('Sound playback failed:', error)
    }
  }
  
  public playSuccessSound() {
    if (!this.soundEnabled) return
    
    try {
      this.initAudioContext()
      if (!this.audioContext) return
      
      const oscillator = this.audioContext.createOscillator()
      const gainNode = this.audioContext.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(this.audioContext.destination)
      
      // Success sound: ascending notes
      oscillator.frequency.setValueAtTime(523.25, this.audioContext.currentTime) // C5
      oscillator.frequency.setValueAtTime(659.25, this.audioContext.currentTime + 0.1) // E5
      oscillator.frequency.setValueAtTime(783.99, this.audioContext.currentTime + 0.2) // G5
      
      gainNode.gain.value = 0.1
      gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3)
      
      oscillator.start()
      oscillator.stop(this.audioContext.currentTime + 0.3)
    } catch (error) {
      console.debug('Sound playback failed:', error)
    }
  }
  
  public playErrorSound() {
    if (!this.soundEnabled) return
    
    try {
      this.initAudioContext()
      if (!this.audioContext) return
      
      const oscillator = this.audioContext.createOscillator()
      const gainNode = this.audioContext.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(this.audioContext.destination)
      
      // Error sound: descending notes
      oscillator.frequency.setValueAtTime(440, this.audioContext.currentTime) // A4
      oscillator.frequency.exponentialRampToValueAtTime(220, this.audioContext.currentTime + 0.2) // A3
      
      gainNode.gain.value = 0.1
      gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.2)
      
      oscillator.start()
      oscillator.stop(this.audioContext.currentTime + 0.2)
    } catch (error) {
      console.debug('Sound playback failed:', error)
    }
  }
  
  public showNotification(title: string, message: string, type: 'success' | 'error' | 'info' = 'info') {
    if (!this.notificationsEnabled) return
    
    // Check if browser supports notifications and permission is granted
    if (typeof window !== 'undefined' && 'Notification' in window) {
      if (Notification.permission === 'granted') {
        try {
          const notification = new Notification(title, {
            body: message,
            icon: type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️',
            tag: 'slywriter-notification',
            requireInteraction: false
          })
          
          // Auto-close after 5 seconds
          setTimeout(() => notification.close(), 5000)
        } catch (error) {
          console.debug('Notification failed:', error)
        }
      } else if (Notification.permission === 'default') {
        // Request permission
        Notification.requestPermission()
      }
    }
  }
  
  public setSoundEnabled(enabled: boolean) {
    this.soundEnabled = enabled
    if (typeof window !== 'undefined') {
      localStorage.setItem('soundEnabled', enabled.toString())
    }
  }
  
  public setNotificationsEnabled(enabled: boolean) {
    this.notificationsEnabled = enabled
    if (typeof window !== 'undefined') {
      localStorage.setItem('notifications', enabled.toString())
    }
    
    // Request permission if enabling
    if (enabled && typeof window !== 'undefined' && 'Notification' in window) {
      if (Notification.permission === 'default') {
        Notification.requestPermission()
      }
    }
  }
}

// Export singleton instance
export const soundService = new SoundService()
export default soundService