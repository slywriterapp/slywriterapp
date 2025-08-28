#!/usr/bin/env python3
"""
Fix the analytics tab to properly track and display data.
"""

import re
from pathlib import Path

def fix_statistics_tab():
    """Fix the StatisticsTab component to properly track and display real data"""
    
    file_path = Path(r"C:\Typing Project\slywriter-ui\app\components\StatisticsTab.tsx")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the sample weekly stats with real data tracking
    old_weekly_stats = '''    // Generate sample weekly stats (move before return)
    const today = new Date()
    const weekStats: DailyStats[] = []
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
      weekStats.push({
        date: date.toLocaleDateString('en', { weekday: 'short' }),
        words: Math.floor(Math.random() * 2000) + 500,
        characters: Math.floor(Math.random() * 10000) + 2500,
        sessions: Math.floor(Math.random() * 10) + 1,
        avgSpeed: Math.floor(Math.random() * 50) + 30,
      })
    }
    setWeeklyStats(weekStats)'''
    
    new_weekly_stats = '''    // Load real weekly stats from localStorage
    const loadWeeklyStats = () => {
      const today = new Date()
      const weekStats: DailyStats[] = []
      const dailyData = JSON.parse(localStorage.getItem('slywriter-daily-stats') || '{}')
      
      for (let i = 6; i >= 0; i--) {
        const date = new Date(today)
        date.setDate(date.getDate() - i)
        const dateKey = date.toISOString().split('T')[0]
        
        const dayData = dailyData[dateKey] || { words: 0, characters: 0, sessions: 0, avgSpeed: 0 }
        
        weekStats.push({
          date: date.toLocaleDateString('en', { weekday: 'short' }),
          words: dayData.words || 0,
          characters: dayData.characters || 0,
          sessions: dayData.sessions || 0,
          avgSpeed: dayData.avgSpeed || 0,
        })
      }
      setWeeklyStats(weekStats)
    }
    
    loadWeeklyStats()'''
    
    content = content.replace(old_weekly_stats, new_weekly_stats)
    
    # Update the typing complete handler to also save daily stats
    old_handler = '''      // Update stats
      const newStats = {
        ...currentStats,
        totalWords: (currentStats.totalWords || 0) + words,
        totalCharacters: (currentStats.totalCharacters || 0) + characters,
        totalSessions: (currentStats.totalSessions || 0) + 1,
        todayWords: (currentStats.todayWords || 0) + words,
        todaySessions: (currentStats.todaySessions || 0) + 1,
        bestWpm: Math.max(currentStats.bestWpm || 0, wpm),
        avgSpeed: Math.round(((currentStats.avgSpeed || 0) * (currentStats.totalSessions || 0) + wpm) / ((currentStats.totalSessions || 0) + 1)),
        timeSaved: (currentStats.timeSaved || 0) + Math.round(words / 40) // Assuming manual typing is 40 WPM
      }
      
      localStorage.setItem('slywriter-stats', JSON.stringify(newStats))
      loadStats()'''
    
    new_handler = '''      // Update stats
      const newStats = {
        ...currentStats,
        totalWords: (currentStats.totalWords || 0) + words,
        totalCharacters: (currentStats.totalCharacters || 0) + characters,
        totalSessions: (currentStats.totalSessions || 0) + 1,
        todayWords: (currentStats.todayWords || 0) + words,
        todaySessions: (currentStats.todaySessions || 0) + 1,
        bestWpm: Math.max(currentStats.bestWpm || 0, wpm),
        avgSpeed: Math.round(((currentStats.avgSpeed || 0) * (currentStats.totalSessions || 0) + wpm) / ((currentStats.totalSessions || 0) + 1)),
        timeSaved: (currentStats.timeSaved || 0) + Math.round(words / 40) // Assuming manual typing is 40 WPM
      }
      
      localStorage.setItem('slywriter-stats', JSON.stringify(newStats))
      
      // Also update daily stats for weekly chart
      const today = new Date().toISOString().split('T')[0]
      const dailyStats = JSON.parse(localStorage.getItem('slywriter-daily-stats') || '{}')
      
      if (!dailyStats[today]) {
        dailyStats[today] = { words: 0, characters: 0, sessions: 0, totalWpm: 0 }
      }
      
      dailyStats[today].words = (dailyStats[today].words || 0) + words
      dailyStats[today].characters = (dailyStats[today].characters || 0) + characters
      dailyStats[today].sessions = (dailyStats[today].sessions || 0) + 1
      dailyStats[today].totalWpm = (dailyStats[today].totalWpm || 0) + wpm
      dailyStats[today].avgSpeed = Math.round(dailyStats[today].totalWpm / dailyStats[today].sessions)
      
      localStorage.setItem('slywriter-daily-stats', JSON.stringify(dailyStats))
      
      loadStats()
      loadWeeklyStats()'''
    
    content = content.replace(old_handler, new_handler)
    
    # Fix the chart height calculation
    old_chart_height = '''                animate={{ height: `${(day.words / 2000) * 100}%` }}'''
    new_chart_height = '''                animate={{ height: `${Math.min(100, (day.words / Math.max(...weeklyStats.map(d => d.words), 1)) * 100)}%` }}'''
    
    content = content.replace(old_chart_height, new_chart_height)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[FIXED] StatisticsTab.tsx - Real data tracking and weekly chart")

def ensure_typing_events():
    """Ensure typing events are properly dispatched"""
    
    file_path = Path(r"C:\Typing Project\slywriter-ui\app\components\TypingTabWithWPM.tsx")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if typing-complete event is properly dispatched
    if 'window.dispatchEvent(typingEvent)' not in content:
        # Find the typing event creation and ensure it's dispatched
        pattern = r"const typingEvent = new CustomEvent\('typing-complete'.*?\}\s*\)\s*\}"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            event_code = match.group(0)
            if 'window.dispatchEvent(typingEvent)' not in content[match.end():match.end()+100]:
                # Add dispatch right after event creation
                new_content = content[:match.end()] + '\n          window.dispatchEvent(typingEvent)' + content[match.end():]
                content = new_content
                print("[FIXED] TypingTabWithWPM.tsx - Added event dispatch")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def add_manual_test_button():
    """Add a manual test button to simulate typing completion for testing"""
    
    file_path = Path(r"C:\Typing Project\slywriter-ui\app\components\StatisticsTab.tsx")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add test button in the header
    test_button = '''        </div>
        <p className="text-gray-400">Track your typing progress and achievements</p>
        
        {/* Test Button for Development */}
        {process.env.NODE_ENV === 'development' && (
          <button
            onClick={() => {
              const testEvent = new CustomEvent('typing-complete', {
                detail: {
                  words: Math.floor(Math.random() * 500) + 100,
                  characters: Math.floor(Math.random() * 2500) + 500,
                  wpm: Math.floor(Math.random() * 50) + 80
                }
              })
              window.dispatchEvent(testEvent)
            }}
            className="mt-2 px-3 py-1 bg-purple-500 hover:bg-purple-600 rounded text-sm text-white"
          >
            Simulate Typing (Dev Only)
          </button>
        )}'''
    
    if 'Simulate Typing' not in content:
        content = content.replace(
            '        </div>\n        <p className="text-gray-400">Track your typing progress and achievements</p>',
            test_button
        )
        print("[ADDED] Test button for development")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    print("Fixing Analytics Tab...")
    print("-" * 40)
    
    fix_statistics_tab()
    ensure_typing_events()
    add_manual_test_button()
    
    print("-" * 40)
    print("Analytics fixes complete!")
    print("\nImprovements:")
    print("- Weekly chart now uses real data instead of random")
    print("- Daily stats are tracked and persisted")
    print("- Chart height scales properly based on actual data")
    print("- Added development test button for easy testing")

if __name__ == "__main__":
    main()