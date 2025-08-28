"""
Complete integration test for SlyWriter typing functionality
Tests typing, WebSocket updates, pause/resume, and stop features
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/typing"

class TypingIntegrationTester:
    def __init__(self):
        self.test_results = []
        self.ws_messages = []
        
    async def test_typing_session(self):
        """Test a complete typing session with WebSocket monitoring"""
        print("=" * 60)
        print("TYPING INTEGRATION TEST")
        print("=" * 60)
        print()
        
        session_id = f"test_{int(time.time())}"
        test_text = "This is a test message for typing automation."
        
        # Start WebSocket connection to monitor updates
        print("1. Connecting to WebSocket...")
        ws_session = aiohttp.ClientSession()
        try:
            ws = await ws_session.ws_connect(WS_URL)
            print("   [PASS] WebSocket connected")
            
            # Start monitoring WebSocket in background
            monitor_task = asyncio.create_task(self.monitor_websocket(ws))
            
            # Start typing session
            print("\n2. Starting typing session...")
            async with aiohttp.ClientSession() as http_session:
                # Add more specific request data
                request_data = {
                    "text": test_text,
                    "profile": "Custom",
                    "custom_wpm": 150,
                    "session_id": session_id,
                    "typos_enabled": False,
                    "auto_clear_after_clipboard": False,
                    "paste_mode": False,
                    "delayed_typo_correction": False,
                    "typo_correction_delay": 2.0
                }
                async with http_session.post(
                    f"{API_URL}/api/typing/start",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   [PASS] Typing started - Session: {data['session_id']}")
                        self.test_results.append({"test": "Start Typing", "status": "PASS"})
                    else:
                        print(f"   [FAIL] Failed to start typing: HTTP {response.status}")
                        try:
                            error_text = await response.text()
                            print(f"   Error details: {error_text}")
                        except:
                            pass
                        self.test_results.append({"test": "Start Typing", "status": "FAIL"})
                        return
            
            # Wait for typing to progress
            print("\n3. Monitoring typing progress...")
            await asyncio.sleep(2)
            
            # Check status
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(f"{API_URL}/api/typing/status/{session_id}") as response:
                    if response.status == 200:
                        status = await response.json()
                        print(f"   Status: {status['status']}")
                        print(f"   Progress: {status.get('progress', 0):.1f}%")
                        print(f"   Chars typed: {status.get('chars_typed', 0)}")
                        self.test_results.append({"test": "Status Check", "status": "PASS"})
                    else:
                        print(f"   [FAIL] Failed to get status")
                        self.test_results.append({"test": "Status Check", "status": "FAIL"})
            
            # Test pause
            print("\n4. Testing pause functionality...")
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(f"{API_URL}/api/typing/pause") as response:
                    if response.status == 200:
                        print("   [PASS] Typing paused")
                        self.test_results.append({"test": "Pause Typing", "status": "PASS"})
                    else:
                        print(f"   [FAIL] Failed to pause")
                        self.test_results.append({"test": "Pause Typing", "status": "FAIL"})
            
            await asyncio.sleep(1)
            
            # Test resume
            print("\n5. Testing resume functionality...")
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(f"{API_URL}/api/typing/resume") as response:
                    if response.status == 200:
                        print("   [PASS] Typing resumed")
                        self.test_results.append({"test": "Resume Typing", "status": "PASS"})
                    else:
                        print(f"   [FAIL] Failed to resume")
                        self.test_results.append({"test": "Resume Typing", "status": "FAIL"})
            
            await asyncio.sleep(1)
            
            # Stop typing
            print("\n6. Stopping typing session...")
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(f"{API_URL}/api/typing/stop") as response:
                    if response.status == 200:
                        print("   [PASS] Typing stopped")
                        self.test_results.append({"test": "Stop Typing", "status": "PASS"})
                    else:
                        print(f"   [FAIL] Failed to stop")
                        self.test_results.append({"test": "Stop Typing", "status": "FAIL"})
            
            # Stop monitoring
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
            
            # Check WebSocket messages
            print("\n7. WebSocket messages received:")
            if self.ws_messages:
                print(f"   Total messages: {len(self.ws_messages)}")
                typing_updates = [m for m in self.ws_messages if m.get('type') == 'typing_update']
                print(f"   Typing updates: {len(typing_updates)}")
                if typing_updates:
                    print("   [PASS] WebSocket updates working")
                    self.test_results.append({"test": "WebSocket Updates", "status": "PASS"})
                else:
                    print("   [WARN] No typing updates received")
                    self.test_results.append({"test": "WebSocket Updates", "status": "WARN"})
            else:
                print("   [FAIL] No WebSocket messages received")
                self.test_results.append({"test": "WebSocket Updates", "status": "FAIL"})
            
        finally:
            await ws_session.close()
        
        # Print summary
        self.print_summary()
    
    async def monitor_websocket(self, ws):
        """Monitor WebSocket for messages"""
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        self.ws_messages.append(data)
                    except json.JSONDecodeError:
                        pass
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
        except asyncio.CancelledError:
            pass
    
    def print_summary(self):
        """Print test results summary"""
        print()
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        warnings = sum(1 for r in self.test_results if r["status"] == "WARN")
        
        for result in self.test_results:
            symbol = "[PASS]" if result["status"] == "PASS" else "[FAIL]" if result["status"] == "FAIL" else "[WARN]"
            print(f"{symbol} {result['test']}")
        
        print("-" * 60)
        print(f"Total: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Warnings: {warnings}")
        
        if passed == len(self.test_results):
            print("\n[SUCCESS] All typing features working correctly!")
        elif failed == 0:
            print("\n[SUCCESS] Typing features working with minor warnings")
        else:
            print("\n[WARNING] Some typing features are not working properly")

async def main():
    tester = TypingIntegrationTester()
    await tester.test_typing_session()

if __name__ == "__main__":
    asyncio.run(main())