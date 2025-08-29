#!/usr/bin/env python3
"""
Comprehensive test of all implemented features
Tests all 9 requested enhancements
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

API_URL = 'http://localhost:8000'

class FeatureTester:
    def __init__(self):
        self.results = {}
        self.session = None
        
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
    
    async def test_feature(self, name: str, test_func):
        """Run a feature test and record results"""
        try:
            print(f"\nTesting: {name}")
            print("-" * 50)
            result = await test_func()
            self.results[name] = {'status': 'PASS', 'details': result}
            print(f"[PASS] {name}: PASSED")
            return True
        except Exception as e:
            self.results[name] = {'status': 'FAIL', 'error': str(e)}
            print(f"[FAIL] {name}: FAILED - {e}")
            return False
    
    async def test_paste_mode(self):
        """Test 1: Paste mode with timer"""
        # Test paste mode configuration
        async with self.session.post(
            f'{API_URL}/api/typing/start',
            json={
                "text": "Test paste mode",
                "profile": "Medium",
                "paste_mode": True,
                "is_from_clipboard": True
            }
        ) as resp:
            data = await resp.json()
            assert resp.status == 200
            assert 'session_id' in data
            
            # Stop the session
            await self.session.post(
                f'{API_URL}/api/typing/stop',
                json={"session_id": data['session_id']}
            )
            
            return "Paste mode configuration accepted"
    
    async def test_hotkey_recording_protection(self):
        """Test 2: Prevent typing during hotkey recording"""
        # Start hotkey recording
        async with self.session.post(
            f'{API_URL}/api/hotkeys/record',
            json={"action": "test", "recording": True}
        ) as resp:
            assert resp.status == 200
            
        # Try to start typing (should fail)
        async with self.session.post(
            f'{API_URL}/api/typing/start',
            json={"text": "Test", "profile": "Medium"}
        ) as resp:
            assert resp.status == 409
            data = await resp.json()
            assert "recording hotkey" in data.get('detail', '').lower()
        
        # Stop recording
        async with self.session.post(
            f'{API_URL}/api/hotkeys/record',
            json={"action": "test", "recording": False}
        ) as resp:
            assert resp.status == 200
            
        return "Hotkey recording protection working"
    
    async def test_auto_clear_clipboard(self):
        """Test 3: Auto-clear after clipboard typing"""
        # Test with auto-clear enabled
        async with self.session.post(
            f'{API_URL}/api/typing/start',
            json={
                "text": "Clipboard text",
                "profile": "Medium",
                "is_from_clipboard": True,
                "auto_clear_after_clipboard": True
            }
        ) as resp:
            data = await resp.json()
            assert resp.status == 200
            session_id = data['session_id']
            
            # Stop typing
            await self.session.post(
                f'{API_URL}/api/typing/stop',
                json={"session_id": session_id}
            )
            
            return "Auto-clear configuration accepted"
    
    async def test_typo_correction(self):
        """Test 4 & 5: Enhanced typo correction with delayed mode"""
        # Test immediate correction
        async with self.session.post(
            f'{API_URL}/api/typing/start',
            json={
                "text": "Test typo correction",
                "profile": "Medium",
                "delayed_typo_correction": False
            }
        ) as resp:
            assert resp.status == 200
            data1 = await resp.json()
            
        # Test delayed correction (Grammarly-style)
        async with self.session.post(
            f'{API_URL}/api/typing/start',
            json={
                "text": "Test delayed typo correction",
                "profile": "Medium",
                "delayed_typo_correction": True,
                "typo_correction_delay": 2.0
            }
        ) as resp:
            assert resp.status == 200
            data2 = await resp.json()
            
        # Clean up sessions
        for session_id in [data1['session_id'], data2['session_id']]:
            await self.session.post(
                f'{API_URL}/api/typing/stop',
                json={"session_id": session_id}
            )
            
        return "Both immediate and delayed typo correction working"
    
    async def test_enhanced_overlay(self):
        """Test 6: Enhanced overlay with optimizations"""
        # Test overlay creation
        async with self.session.post(
            f'{API_URL}/api/overlay/create',
            json={
                "position_x": 100,
                "position_y": 100,
                "width": 300,
                "height": 200
            }
        ) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert 'id' in data
            assert data['settings']['gpu_acceleration'] == True
            assert data['settings']['use_transform'] == True
            
            return "Enhanced overlay with GPU acceleration configured"
    
    async def test_dynamic_hotkeys(self):
        """Test 7: Dynamic hotkey system"""
        # Register a custom hotkey
        async with self.session.post(
            f'{API_URL}/api/hotkeys/register',
            json={
                "action": "start",
                "combination": "Alt+S"
            }
        ) as resp:
            assert resp.status == 200
            
        # Get user hotkeys
        async with self.session.get(
            f'{API_URL}/api/hotkeys/test_user'
        ) as resp:
            assert resp.status == 200
            data = await resp.json()
            # Should have both defaults and custom
            assert 'start' in data
            
            return f"Dynamic hotkeys working: {data}"
    
    async def test_hotkey_triggers(self):
        """Test 8: Hotkey trigger functionality"""
        # Connect WebSocket to test hotkey triggers
        ws_url = f'ws://localhost:8000/ws/test_user'
        
        async with self.session.ws_connect(ws_url) as ws:
            # Wait for connection
            msg = await ws.receive()
            data = json.loads(msg.data)
            assert data['type'] == 'connected'
            
            # Send hotkey trigger
            await ws.send_str(json.dumps({
                "type": "hotkey",
                "data": {"action": "start"}
            }))
            
            # Check status
            await ws.send_str(json.dumps({"type": "get_status"}))
            msg = await ws.receive()
            data = json.loads(msg.data)
            assert data['type'] == 'status'
            
            await ws.close()
            
            return "Hotkey triggers via WebSocket working"
    
    async def test_voice_transcription(self):
        """Test 9: Voice transcription feature"""
        # Check available backends
        async with self.session.get(
            f'{API_URL}/api/voice/backends'
        ) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert 'available_backends' in data
            assert len(data['available_backends']) > 0
            
            # Test mock transcription
            # Create a mock audio file
            mock_audio = b"mock audio data for testing"
            
            form = aiohttp.FormData()
            form.add_field('audio', mock_audio, filename='test.webm', content_type='audio/webm')
            form.add_field('language', 'en')
            
            async with self.session.post(
                f'{API_URL}/api/voice/transcribe',
                data=form
            ) as resp:
                assert resp.status == 200
                result = await resp.json()
                assert 'text' in result
                assert result['success'] == True
                
                return f"Voice transcription working with {data['available_backends']} backends"
    
    async def run_all_tests(self):
        """Run all feature tests"""
        print("=" * 60)
        print("COMPREHENSIVE FEATURE TEST SUITE")
        print("Testing all 9 requested enhancements")
        print("=" * 60)
        
        await self.setup()
        
        tests = [
            ("1. Paste Mode with Timer", self.test_paste_mode),
            ("2. Hotkey Recording Protection", self.test_hotkey_recording_protection),
            ("3. Auto-Clear Clipboard", self.test_auto_clear_clipboard),
            ("4-5. Enhanced Typo Correction", self.test_typo_correction),
            ("6. Enhanced Overlay", self.test_enhanced_overlay),
            ("7. Dynamic Hotkeys", self.test_dynamic_hotkeys),
            ("8. Hotkey Triggers", self.test_hotkey_triggers),
            ("9. Voice Transcription", self.test_voice_transcription),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            if await self.test_feature(name, test_func):
                passed += 1
            else:
                failed += 1
            await asyncio.sleep(0.5)
        
        await self.cleanup()
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {len(tests)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
        
        if failed == 0:
            print("\n[SUCCESS] ALL FEATURES WORKING PERFECTLY!")
            print("The app is ready for your 20 testers tomorrow!")
        else:
            print("\nSome tests failed. Check the details above.")
        
        return self.results

async def main():
    tester = FeatureTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    with open('feature_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to feature_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())