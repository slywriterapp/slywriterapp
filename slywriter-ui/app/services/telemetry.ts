import axios from 'axios'
import { RENDER_API_URL } from '../config/api'

interface TelemetryEvent {
  event: string
  data: any
  timestamp: string
  userId: string
  sessionId: string
  betaTester: boolean
}

interface TypingSession {
  sessionId: string
  startTime: string
  endTime?: string
  textLength: number
  wordsTyped: number
  avgWpm?: number
  accuracy?: number
  pauseCount: number
  typoCount: number
  aiFiller: boolean
  profile: string
}

class TelemetryService {
  private sessionId: string
  private userId: string
  private events: TelemetryEvent[] = []
  private sessions: TypingSession[] = []
  private currentSession: TypingSession | null = null
  private collectData: boolean = false
  private betaTester: boolean = false

  constructor() {
    this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    this.userId = this.getUserId()
    this.loadSettings()
    this.loadStoredData()
    
    // Auto-save every 30 seconds if data collection is enabled
    if (this.collectData && typeof window !== 'undefined') {
      setInterval(() => this.saveToLocalStorage(), 30000)
    }
  }

  private getUserId(): string {
    if (typeof window === 'undefined') {
      return 'server-render'
    }
    let userId = localStorage.getItem('userId')
    if (!userId) {
      userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      localStorage.setItem('userId', userId)
    }
    return userId
  }

  private loadSettings() {
    if (typeof window === 'undefined') return
    this.collectData = localStorage.getItem('dataCollection') === 'true'
    this.betaTester = localStorage.getItem('betaTester') === 'true'
  }

  private loadStoredData() {
    if (typeof window === 'undefined') return
    const storedEvents = localStorage.getItem('telemetryEvents')
    if (storedEvents) {
      this.events = JSON.parse(storedEvents)
    }
    
    const storedSessions = localStorage.getItem('typingSessions')
    if (storedSessions) {
      this.sessions = JSON.parse(storedSessions)
    }
  }

  private saveToLocalStorage() {
    if (!this.collectData || typeof window === 'undefined') return
    
    localStorage.setItem('telemetryEvents', JSON.stringify(this.events))
    localStorage.setItem('typingSessions', JSON.stringify(this.sessions))
    
    // Update stats
    const stats = this.calculateStats()
    localStorage.setItem('typingStats', JSON.stringify(stats))
  }

  public trackEvent(event: string, data: any) {
    if (!this.collectData) return
    
    const telemetryEvent: TelemetryEvent = {
      event,
      data,
      timestamp: new Date().toISOString(),
      userId: this.userId,
      sessionId: this.sessionId,
      betaTester: this.betaTester
    }
    
    this.events.push(telemetryEvent)
    
    // Send to server if online
    this.sendToServer(telemetryEvent)
    
    // Save locally
    this.saveToLocalStorage()
  }

  public startTypingSession(textLength: number, profile: string, aiFiller: boolean) {
    if (!this.collectData) return
    
    this.currentSession = {
      sessionId: `typing_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      startTime: new Date().toISOString(),
      textLength,
      wordsTyped: 0,
      pauseCount: 0,
      typoCount: 0,
      aiFiller,
      profile
    }
    
    this.trackEvent('typing_session_started', {
      sessionId: this.currentSession.sessionId,
      textLength,
      profile,
      aiFiller
    })
  }

  public endTypingSession(wpm: number, accuracy: number) {
    if (!this.collectData || !this.currentSession) return
    
    this.currentSession.endTime = new Date().toISOString()
    this.currentSession.avgWpm = wpm
    this.currentSession.accuracy = accuracy
    
    this.sessions.push(this.currentSession)
    
    this.trackEvent('typing_session_ended', {
      sessionId: this.currentSession.sessionId,
      duration: new Date(this.currentSession.endTime).getTime() - new Date(this.currentSession.startTime).getTime(),
      wpm,
      accuracy,
      wordsTyped: this.currentSession.wordsTyped,
      pauseCount: this.currentSession.pauseCount,
      typoCount: this.currentSession.typoCount
    })
    
    this.currentSession = null
    this.saveToLocalStorage()
  }

  public trackTypingMetric(metric: string, value: any) {
    if (!this.collectData || !this.currentSession) return
    
    switch (metric) {
      case 'pause':
        this.currentSession.pauseCount++
        break
      case 'typo':
        this.currentSession.typoCount++
        break
      case 'words':
        this.currentSession.wordsTyped = value
        break
    }
    
    this.trackEvent(`typing_${metric}`, { value })
  }

  private async sendToServer(event: TelemetryEvent) {
    if (!this.collectData) return
    
    try {
      await axios.post(`${RENDER_API_URL}/api/telemetry`, event, {
        timeout: 5000 // 5 second timeout
      })
    } catch (error) {
      // Silently fail - data is saved locally
      console.debug('Telemetry send failed, saved locally', error)
    }
  }

  public calculateStats() {
    const totalSessions = this.sessions.length
    const totalWords = this.sessions.reduce((acc, s) => acc + s.wordsTyped, 0)
    const avgWpm = this.sessions.reduce((acc, s) => acc + (s.avgWpm || 0), 0) / (totalSessions || 1)
    const avgAccuracy = this.sessions.reduce((acc, s) => acc + (s.accuracy || 0), 0) / (totalSessions || 1)
    const totalTypos = this.sessions.reduce((acc, s) => acc + s.typoCount, 0)
    const totalPauses = this.sessions.reduce((acc, s) => acc + s.pauseCount, 0)
    
    return {
      totalSessions,
      totalWords,
      avgWpm: Math.round(avgWpm),
      avgAccuracy: Math.round(avgAccuracy * 10) / 10,
      totalTypos,
      totalPauses,
      lastUpdated: new Date().toISOString()
    }
  }

  public async exportData() {
    const data = {
      userId: this.userId,
      betaTester: this.betaTester,
      events: this.events,
      sessions: this.sessions,
      stats: this.calculateStats(),
      exportDate: new Date().toISOString()
    }
    
    if (this.collectData) {
      try {
        await axios.post(`${RENDER_API_URL}/api/beta-data/export`, data)
      } catch (error) {
        console.error('Failed to export data to server:', error)
      }
    }
    
    return data
  }

  public clearData() {
    this.events = []
    this.sessions = []
    this.currentSession = null
    localStorage.removeItem('telemetryEvents')
    localStorage.removeItem('typingSessions')
    localStorage.removeItem('typingStats')
  }

  public setDataCollection(enabled: boolean) {
    this.collectData = enabled
    localStorage.setItem('dataCollection', enabled.toString())
    
    if (enabled && !this.userId) {
      this.userId = this.getUserId()
    }
  }

  public setBetaTester(enabled: boolean) {
    this.betaTester = enabled
    localStorage.setItem('betaTester', enabled.toString())
  }
}

// Export singleton instance
export const telemetry = new TelemetryService()
export default telemetry