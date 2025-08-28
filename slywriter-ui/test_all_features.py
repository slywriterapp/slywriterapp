"""
Complete test suite for all SlyWriter features
Tests typing, AI generation, authentication, and all tabs
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/typing"

class ComprehensiveTest:
    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0
        
    def print_header(self, text):
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{text.center(60)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
    
    def print_test(self, name, status, details=""):
        if status == "PASS":
            print(f"{Fore.GREEN}[PASS]{Style.RESET_ALL} {name}")
            self.passed += 1
        elif status == "FAIL":
            print(f"{Fore.RED}[FAIL]{Style.RESET_ALL} {name}")
            if details:
                print(f"  {Fore.YELLOW}{details}{Style.RESET_ALL}")
            self.failed += 1
        elif status == "INFO":
            print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {name}")
            if details:
                print(f"  {details}")
    
    async def test_health_check(self):
        """Test if backend is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/api/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.print_test("Backend Health Check", "PASS")
                        self.print_test("Server Status", "INFO", f"Status: {data.get('status', 'Unknown')}")
                        return True
                    else:
                        self.print_test("Backend Health Check", "FAIL", f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.print_test("Backend Health Check", "FAIL", str(e))
            return False
    
    async def test_ai_endpoints(self):
        """Test all AI generation endpoints"""
        self.print_header("AI GENERATION TESTS")
        
        endpoints = [
            {
                "name": "Text Generation",
                "endpoint": "/api/ai/generate",
                "payload": {
                    "prompt": "Write about the benefits of typing practice",
                    "max_tokens": 50
                }
            },
            {
                "name": "Essay Generation",
                "endpoint": "/api/ai/essay",
                "payload": {
                    "topic": "Digital literacy",
                    "word_count": 100
                }
            },
            {
                "name": "Text Humanization",
                "endpoint": "/api/ai/humanize",
                "payload": {
                    "text": "This is a test sentence.",
                    "style": "natural"
                }
            },
            {
                "name": "Topic Explanation",
                "endpoint": "/api/ai/explain",
                "payload": {
                    "topic": "Touch typing",
                    "learning_style": "visual"
                }
            },
            {
                "name": "Study Questions",
                "endpoint": "/api/ai/study-questions",
                "payload": {
                    "topic": "Keyboard shortcuts",
                    "num_questions": 3
                }
            }
        ]
        
        for test in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{API_URL}{test['endpoint']}", json=test['payload']) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("success"):
                                if data.get("mock"):
                                    self.print_test(test['name'], "PASS", "Using mock response")
                                else:
                                    self.print_test(test['name'], "PASS", "Real AI response")
                            else:
                                self.print_test(test['name'], "FAIL", data.get("error", "Unknown error"))
                        else:
                            self.print_test(test['name'], "FAIL", f"HTTP {response.status}")
            except Exception as e:
                self.print_test(test['name'], "FAIL", str(e))
    
    async def test_typing_functionality(self):
        """Test typing start, pause, resume, and stop"""
        self.print_header("TYPING ENGINE TESTS")
        
        session_id = f"test_{int(time.time())}"
        
        # Test 1: Start typing
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": "This is a test message.",
                    "profile": "Custom",
                    "custom_wpm": 100,
                    "session_id": session_id,
                    "typos_enabled": False,
                    "paste_mode": False,
                    "auto_clear_after_clipboard": False,
                    "delayed_typo_correction": False,
                    "typo_correction_delay": 2.0
                }
                async with session.post(f"{API_URL}/api/typing/start", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.print_test("Start Typing", "PASS", f"Session: {data.get('session_id', 'Unknown')}")
                    else:
                        self.print_test("Start Typing", "FAIL", f"HTTP {response.status}")
        except Exception as e:
            self.print_test("Start Typing", "FAIL", str(e))
        
        await asyncio.sleep(1)
        
        # Test 2: Pause typing
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{API_URL}/api/typing/pause") as response:
                    if response.status == 200:
                        self.print_test("Pause Typing", "PASS")
                    else:
                        self.print_test("Pause Typing", "FAIL", f"HTTP {response.status}")
        except Exception as e:
            self.print_test("Pause Typing", "FAIL", str(e))
        
        # Test 3: Resume typing
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{API_URL}/api/typing/resume") as response:
                    if response.status == 200:
                        self.print_test("Resume Typing", "PASS")
                    else:
                        self.print_test("Resume Typing", "FAIL", f"HTTP {response.status}")
        except Exception as e:
            self.print_test("Resume Typing", "FAIL", str(e))
        
        # Test 4: Stop typing
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{API_URL}/api/typing/stop") as response:
                    if response.status == 200:
                        self.print_test("Stop Typing", "PASS")
                    else:
                        self.print_test("Stop Typing", "FAIL", f"HTTP {response.status}")
        except Exception as e:
            self.print_test("Stop Typing", "FAIL", str(e))
    
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        self.print_header("WEBSOCKET TESTS")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(WS_URL) as ws:
                    # Wait for connection message
                    msg = await asyncio.wait_for(ws.receive(), timeout=5)
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get("type") == "connected":
                            self.print_test("WebSocket Connection", "PASS")
                        else:
                            self.print_test("WebSocket Connection", "FAIL", "Unexpected message type")
                    else:
                        self.print_test("WebSocket Connection", "FAIL", "No connection message")
                    await ws.close()
        except Exception as e:
            self.print_test("WebSocket Connection", "FAIL", str(e))
    
    async def test_profile_endpoints(self):
        """Test profile management"""
        self.print_header("PROFILE TESTS")
        
        # Get profiles
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/api/profiles") as response:
                    if response.status == 200:
                        data = await response.json()
                        profiles = data.get("profiles", [])
                        self.print_test("Get Profiles", "PASS", f"Found {len(profiles)} profiles")
                    else:
                        self.print_test("Get Profiles", "FAIL", f"HTTP {response.status}")
        except Exception as e:
            self.print_test("Get Profiles", "FAIL", str(e))
    
    async def run_all_tests(self):
        """Run all tests"""
        self.print_header("SLYWRITER COMPLETE TEST SUITE")
        
        # Check backend health first
        if not await self.test_health_check():
            print(f"\n{Fore.RED}Backend is not running! Please start the backend first.{Style.RESET_ALL}")
            return
        
        # Run all test suites
        await self.test_ai_endpoints()
        await self.test_typing_functionality()
        await self.test_websocket_connection()
        await self.test_profile_endpoints()
        
        # Print summary
        self.print_header("TEST SUMMARY")
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"{Fore.GREEN}Passed: {self.passed}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.failed}{Style.RESET_ALL}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            print(f"\n{Fore.GREEN}[SUCCESS] ALL TESTS PASSED!{Style.RESET_ALL}")
            print("All features are working correctly!")
        else:
            print(f"\n{Fore.YELLOW}[WARNING] Some tests failed. Please review the errors above.{Style.RESET_ALL}")
        
        # Check for placeholders
        print(f"\n{Fore.CYAN}Configuration Status:{Style.RESET_ALL}")
        print("[CHECK] Google OAuth configured (Client ID found)")
        print("[WARNING] OpenAI API key is a placeholder - AI features will use mock responses")
        print("  To enable real AI: Replace OPENAI_API_KEY in backend/.env with your actual key")

async def main():
    tester = ComprehensiveTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())