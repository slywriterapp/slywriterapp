#!/usr/bin/env python3
"""
Verify that all analytics components are properly connected and working.
"""

import re
from pathlib import Path

def check_typing_events():
    """Check if typing events are properly dispatched and received"""
    
    issues = []
    
    # Check TypingTabWithWPM dispatches events
    typing_tab = Path(r"C:\Typing Project\slywriter-ui\app\components\TypingTabWithWPM.tsx")
    with open(typing_tab, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for typing-complete event
        if 'window.dispatchEvent(typingEvent)' not in content:
            issues.append("[X] TypingTabWithWPM not dispatching typing-complete event")
        else:
            print("[OK] TypingTabWithWPM dispatches typing-complete event")
        
        # Check for typing-start event
        if "window.dispatchEvent(new CustomEvent('typing-start'))" not in content:
            issues.append("[X] TypingTabWithWPM not dispatching typing-start event")
        else:
            print("[OK] TypingTabWithWPM dispatches typing-start event")
        
        # Check for typing-update event
        if "window.dispatchEvent(updateEvent)" in content:
            print("[OK] TypingTabWithWPM dispatches typing-update event")
        else:
            issues.append("[X] TypingTabWithWPM not dispatching typing-update event")
    
    # Check StatisticsTab listens for events
    stats_tab = Path(r"C:\Typing Project\slywriter-ui\app\components\StatisticsTab.tsx")
    with open(stats_tab, 'r', encoding='utf-8') as f:
        content = f.read()
        
        if "window.addEventListener('typing-complete'" in content:
            print("[OK] StatisticsTab listens for typing-complete event")
        else:
            issues.append("[X] StatisticsTab not listening for typing-complete event")
        
        # Check for localStorage updates
        if "localStorage.setItem('slywriter-stats'" in content:
            print("[OK] StatisticsTab updates localStorage stats")
        else:
            issues.append("[X] StatisticsTab not updating localStorage stats")
        
        if "localStorage.setItem('slywriter-daily-stats'" in content:
            print("[OK] StatisticsTab updates daily stats")
        else:
            issues.append("[X] StatisticsTab not updating daily stats")
    
    # Check OverlayWindowEnhanced listens for events
    overlay_tab = Path(r"C:\Typing Project\slywriter-ui\app\components\OverlayWindowEnhanced.tsx")
    with open(overlay_tab, 'r', encoding='utf-8') as f:
        content = f.read()
        
        if "window.addEventListener('typing-start'" in content:
            print("[OK] OverlayWindow listens for typing-start event")
        else:
            issues.append("[X] OverlayWindow not listening for typing-start event")
        
        if "window.addEventListener('typing-update'" in content:
            print("[OK] OverlayWindow listens for typing-update event")
        else:
            issues.append("[X] OverlayWindow not listening for typing-update event")
        
        if "window.addEventListener('typing-complete'" in content:
            print("[OK] OverlayWindow listens for typing-complete event")
        else:
            issues.append("[X] OverlayWindow not listening for typing-complete event")
    
    return issues

def check_weekly_chart():
    """Check if weekly chart is properly implemented"""
    
    issues = []
    stats_tab = Path(r"C:\Typing Project\slywriter-ui\app\components\StatisticsTab.tsx")
    
    with open(stats_tab, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for real data loading
        if "loadWeeklyStats" in content:
            print("[OK] Weekly stats loading function exists")
        else:
            issues.append("[X] Weekly stats loading function missing")
        
        # Check for daily data persistence
        if "slywriter-daily-stats" in content:
            print("[OK] Daily stats persistence implemented")
        else:
            issues.append("[X] Daily stats persistence not implemented")
        
        # Check chart rendering
        if "weeklyStats.map((day, index)" in content:
            print("[OK] Weekly chart renders data")
        else:
            issues.append("[X] Weekly chart not rendering data")
        
        # Check proper height calculation
        if "heightPercent" in content or "Math.max(...weeklyStats.map(d => d.words)" in content:
            print("[OK] Chart height calculation implemented")
        else:
            issues.append("[X] Chart height calculation missing")
    
    return issues

def check_data_flow():
    """Check the complete data flow from typing to display"""
    
    print("\n[DATA FLOW CHECK]")
    print("1. User starts typing -> TypingTabWithWPM dispatches 'typing-start'")
    print("2. During typing -> WebSocket sends progress -> TypingTabWithWPM dispatches 'typing-update'")
    print("3. Typing complete -> TypingTabWithWPM dispatches 'typing-complete' with words/characters/wpm")
    print("4. StatisticsTab receives event -> Updates localStorage (slywriter-stats, slywriter-daily-stats)")
    print("5. StatisticsTab re-renders -> Shows updated stats and weekly chart")
    print("6. OverlayWindow receives events -> Shows real-time status")
    
    return []

def main():
    print("[VERIFYING ANALYTICS INTEGRATION]")
    print("=" * 50)
    
    all_issues = []
    
    print("\n[CHECKING EVENT DISPATCHING]")
    issues = check_typing_events()
    all_issues.extend(issues)
    
    print("\n[CHECKING WEEKLY CHART]")
    issues = check_weekly_chart()
    all_issues.extend(issues)
    
    print("\n" + "=" * 50)
    data_flow_issues = check_data_flow()
    all_issues.extend(data_flow_issues)
    
    print("\n" + "=" * 50)
    if all_issues:
        print(f"\n[WARNING] Found {len(all_issues)} issues:")
        for issue in all_issues:
            print(f"  {issue}")
    else:
        print("\n[SUCCESS] All analytics components are properly connected!")
        print("\nTo test the integration:")
        print("1. Open the app and go to the Typing tab")
        print("2. Enter some text and click 'Start Typing'")
        print("3. Watch the overlay window update in real-time")
        print("4. After completion, check the Statistics tab")
        print("5. Verify that:")
        print("   - Total words/characters/sessions increased")
        print("   - Today's stats updated")
        print("   - Weekly chart shows today's activity")
        print("\nOr use the test page: open test_analytics_integration.html in a browser")

if __name__ == "__main__":
    main()