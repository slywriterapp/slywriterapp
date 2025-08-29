#!/usr/bin/env python3
"""Test 200 WPM through API"""

import asyncio
import aiohttp
import json
import time

async def test_200wpm():
    # Connect to WebSocket
    session = aiohttp.ClientSession()
    
    try:
        # Connect WebSocket
        ws = await session.ws_connect('ws://localhost:8000/ws/test_user')
        print("WebSocket connected")
        
        # Start typing with 200 WPM
        test_text = "The quick brown fox jumps over the lazy dog. " * 2  # 20 words
        
        data = {
            "text": test_text,
            "profile": "Custom",
            "custom_wpm": 200,
            "user_id": "test_user", 
            "session_id": "test_200wpm"
        }
        
        # Send start command
        await ws.send_str(json.dumps({
            "action": "start_typing",
            **data
        }))
        
        print(f"Started typing at 200 WPM")
        print(f"Text: {len(test_text)} characters, {len(test_text.split())} words")
        print(f"Expected time: {len(test_text.split()) * 60 / 200:.1f} seconds")
        
        start_time = time.time()
        char_count = 0
        
        # Listen for progress updates
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                
                if data.get('type') == 'typing_progress':
                    progress = data.get('progress', 0)
                    char_count = int(len(test_text) * progress / 100)
                    elapsed = time.time() - start_time
                    
                    if elapsed > 0:
                        actual_cps = char_count / elapsed
                        actual_wpm = actual_cps * 60 / 5
                        print(f"Progress: {progress:.1f}% | Chars: {char_count}/{len(test_text)} | "
                              f"Time: {elapsed:.1f}s | WPM: {actual_wpm:.0f}")
                
                elif data.get('type') == 'typing_complete':
                    elapsed = time.time() - start_time
                    actual_wpm = (len(test_text) / elapsed) * 60 / 5
                    print(f"\nTyping complete!")
                    print(f"Total time: {elapsed:.1f} seconds")
                    print(f"Actual WPM: {actual_wpm:.0f}")
                    break
                    
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(f"WebSocket error: {ws.exception()}")
                break
                
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_200wpm())