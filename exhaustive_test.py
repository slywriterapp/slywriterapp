"""
EXHAUSTIVE TEST SUITE - Tests EVERY feature in the application
"""

import requests
import json
import time
import websocket
import threading
from datetime import datetime

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

class ExhaustiveTestSuite:
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
        
    def log(self, category, test, status, details=""):
        """Log test result"""
        if status == "PASS":
            self.results["passed"].append(f"{category}: {test}")
            print(f"[OK] {category}: {test}")
        elif status == "FAIL":
            self.results["failed"].append(f"{category}: {test} - {details}")
            print(f"[FAIL] {category}: {test} - {details}")
        else:  # WARNING
            self.results["warnings"].append(f"{category}: {test} - {details}")
            print(f"[WARN] {category}: {test} - {details}")
    
    def test_backend_endpoints(self):
        """Test all backend API endpoints"""
        print("\n" + "="*60)
        print("TESTING BACKEND ENDPOINTS")
        print("="*60)
        
        endpoints = [
            ("GET", "/api/health", None, "Health Check"),
            ("GET", "/api/profiles", None, "Get Profiles"),
            ("POST", "/api/typing/start", {"text": "Test", "profile": "Medium"}, "Start Typing"),
            ("POST", "/api/typing/pause", None, "Global Pause"),
            ("POST", "/api/typing/stop", None, "Global Stop"),
        ]
        
        for method, endpoint, data, name in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{API_URL}{endpoint}")
                else:
                    response = requests.post(f"{API_URL}{endpoint}", json=data)
                
                if response.status_code in [200, 201]:
                    self.log("Backend", name, "PASS")
                else:
                    self.log("Backend", name, "FAIL", f"Status {response.status_code}")
            except Exception as e:
                self.log("Backend", name, "FAIL", str(e))
        
        # Test session-specific endpoints
        try:
            # Start a session
            response = requests.post(f"{API_URL}/api/typing/start", json={
                "text": "Session test",
                "profile": "Fast"
            })
            if response.status_code == 200:
                session_id = response.json()["session_id"]
                
                # Test pause/resume
                pause_resp = requests.post(f"{API_URL}/api/typing/pause/{session_id}")
                self.log("Backend", f"Pause Session", "PASS" if pause_resp.status_code == 200 else "FAIL")
                
                resume_resp = requests.post(f"{API_URL}/api/typing/resume/{session_id}")
                self.log("Backend", f"Resume Session", "PASS" if resume_resp.status_code == 200 else "FAIL")
                
                # Test WPM update
                wpm_resp = requests.post(f"{API_URL}/api/typing/update_wpm", json={
                    "session_id": session_id,
                    "wpm": 100
                })
                self.log("Backend", f"Update WPM", "PASS" if wpm_resp.status_code == 200 else "FAIL")
                
                # Stop session
                stop_resp = requests.post(f"{API_URL}/api/typing/stop/{session_id}")
                self.log("Backend", f"Stop Session", "PASS" if stop_resp.status_code == 200 else "FAIL")
        except Exception as e:
            self.log("Backend", "Session Operations", "FAIL", str(e))
    
    def test_profiles(self):
        """Test all typing profiles"""
        print("\n" + "="*60)
        print("TESTING TYPING PROFILES")
        print("="*60)
        
        try:
            response = requests.get(f"{API_URL}/api/profiles")
            if response.status_code != 200:
                self.log("Profiles", "Fetch Profiles", "FAIL", "Cannot get profiles")
                return
            
            profiles = response.json()["profiles"]
            required_profiles = ["Slow", "Medium", "Fast", "Essay", "Custom"]
            
            for required in required_profiles:
                found = any(p["name"] == required for p in profiles)
                self.log("Profiles", f"Profile '{required}'", "PASS" if found else "FAIL")
            
            # Check speed differences
            slow = next((p for p in profiles if p["name"] == "Slow"), None)
            fast = next((p for p in profiles if p["name"] == "Fast"), None)
            
            if slow and fast:
                slow_delay = slow["settings"]["min_delay"]
                fast_delay = fast["settings"]["min_delay"]
                
                if slow_delay > fast_delay * 2:  # Slow should be at least 2x slower
                    self.log("Profiles", "Speed Differentiation", "PASS", 
                            f"Slow: {slow_delay:.3f}s, Fast: {fast_delay:.3f}s")
                else:
                    self.log("Profiles", "Speed Differentiation", "FAIL", 
                            "Insufficient speed difference")
                
                # Check typos are enabled
                for profile in profiles:
                    if profile["settings"]["typos_enabled"]:
                        self.log("Profiles", f"Typos enabled for {profile['name']}", "PASS")
                    else:
                        self.log("Profiles", f"Typos enabled for {profile['name']}", "WARNING", 
                                "Typos disabled")
                        
        except Exception as e:
            self.log("Profiles", "Profile Testing", "FAIL", str(e))
    
    def test_custom_wpm(self):
        """Test custom WPM functionality"""
        print("\n" + "="*60)
        print("TESTING CUSTOM WPM")
        print("="*60)
        
        test_speeds = [20, 50, 80, 120, 150, 200]
        
        for wpm in test_speeds:
            try:
                response = requests.post(f"{API_URL}/api/typing/start", json={
                    "text": "WPM test",
                    "profile": "Custom",
                    "custom_wpm": wpm,
                    "preview_mode": True
                })
                
                if response.status_code == 200:
                    session_id = response.json()["session_id"]
                    self.log("Custom WPM", f"{wpm} WPM", "PASS")
                    
                    # Clean up
                    requests.post(f"{API_URL}/api/typing/stop/{session_id}")
                else:
                    self.log("Custom WPM", f"{wpm} WPM", "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log("Custom WPM", f"{wpm} WPM", "FAIL", str(e))
    
    def test_websocket(self):
        """Test WebSocket connectivity"""
        print("\n" + "="*60)
        print("TESTING WEBSOCKET")
        print("="*60)
        
        try:
            ws = websocket.create_connection(f"{WS_URL}/test_user")
            self.log("WebSocket", "Connection", "PASS")
            
            # Send a test message
            ws.send(json.dumps({"type": "ping"}))
            
            # Try to receive with timeout
            ws.settimeout(2)
            try:
                result = ws.recv()
                self.log("WebSocket", "Message Exchange", "PASS")
            except:
                self.log("WebSocket", "Message Exchange", "WARNING", "No response to ping")
            
            ws.close()
            self.log("WebSocket", "Clean Disconnect", "PASS")
            
        except Exception as e:
            self.log("WebSocket", "Connection", "FAIL", str(e))
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n" + "="*60)
        print("TESTING EDGE CASES")
        print("="*60)
        
        edge_cases = [
            ("Empty Text", ""),
            ("Single Char", "A"),
            ("Very Long", "x" * 5000),
            ("Special Chars", "!@#$%^&*()_+-={}[]|\\:\";<>?,./"),
            ("Unicode", "café résumé naïve 你好 مرحبا"),
            ("Newlines", "Line1\nLine2\n\nParagraph2"),
            ("Mixed Case", "HeLLo WoRLd"),
            ("Numbers", "1234567890"),
            ("HTML Tags", "<script>alert('test')</script>"),
            ("SQL Injection", "'; DROP TABLE users; --"),
        ]
        
        for name, text in edge_cases:
            try:
                response = requests.post(f"{API_URL}/api/typing/start", json={
                    "text": text,
                    "profile": "Fast",
                    "preview_mode": True
                })
                
                if response.status_code == 200:
                    session_id = response.json().get("session_id")
                    if session_id:
                        self.log("Edge Cases", name, "PASS")
                        requests.post(f"{API_URL}/api/typing/stop/{session_id}")
                    else:
                        self.log("Edge Cases", name, "WARNING", "No session ID returned")
                else:
                    self.log("Edge Cases", name, "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log("Edge Cases", name, "FAIL", str(e))
    
    def test_concurrent_sessions(self):
        """Test multiple concurrent typing sessions"""
        print("\n" + "="*60)
        print("TESTING CONCURRENT SESSIONS")
        print("="*60)
        
        sessions = []
        
        try:
            # Start 5 concurrent sessions
            for i in range(5):
                response = requests.post(f"{API_URL}/api/typing/start", json={
                    "text": f"Session {i}",
                    "profile": "Fast",
                    "preview_mode": True
                })
                
                if response.status_code == 200:
                    sessions.append(response.json()["session_id"])
            
            self.log("Concurrent", f"Started {len(sessions)} sessions", 
                    "PASS" if len(sessions) == 5 else "WARNING")
            
            # Test global stop
            response = requests.post(f"{API_URL}/api/typing/stop")
            if response.status_code == 200:
                stopped = response.json().get("stopped_sessions", [])
                self.log("Concurrent", "Global Stop", "PASS", f"Stopped {len(stopped)} sessions")
            else:
                self.log("Concurrent", "Global Stop", "FAIL")
                
        except Exception as e:
            self.log("Concurrent", "Session Management", "FAIL", str(e))
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n" + "="*60)
        print("TESTING ERROR HANDLING")
        print("="*60)
        
        # Test invalid session ID
        try:
            response = requests.post(f"{API_URL}/api/typing/stop/invalid-session-id")
            if response.status_code in [200, 404]:
                self.log("Error Handling", "Invalid Session ID", "PASS")
            else:
                self.log("Error Handling", "Invalid Session ID", "WARNING", 
                        f"Unexpected status {response.status_code}")
        except Exception as e:
            self.log("Error Handling", "Invalid Session ID", "FAIL", str(e))
        
        # Test invalid profile
        try:
            response = requests.post(f"{API_URL}/api/typing/start", json={
                "text": "Test",
                "profile": "InvalidProfile"
            })
            # Should fallback to default profile
            if response.status_code == 200:
                self.log("Error Handling", "Invalid Profile Fallback", "PASS")
                session_id = response.json().get("session_id")
                if session_id:
                    requests.post(f"{API_URL}/api/typing/stop/{session_id}")
            else:
                self.log("Error Handling", "Invalid Profile", "WARNING")
        except Exception as e:
            self.log("Error Handling", "Invalid Profile", "FAIL", str(e))
        
        # Test missing parameters
        try:
            response = requests.post(f"{API_URL}/api/typing/start", json={})
            if response.status_code == 422:  # Validation error
                self.log("Error Handling", "Missing Parameters", "PASS")
            else:
                self.log("Error Handling", "Missing Parameters", "WARNING", 
                        f"Expected 422, got {response.status_code}")
        except Exception as e:
            self.log("Error Handling", "Missing Parameters", "FAIL", str(e))
    
    def test_performance(self):
        """Test performance metrics"""
        print("\n" + "="*60)
        print("TESTING PERFORMANCE")
        print("="*60)
        
        # Test response times
        endpoints = [
            ("/api/health", "Health Check"),
            ("/api/profiles", "Profiles"),
        ]
        
        for endpoint, name in endpoints:
            try:
                start = time.time()
                response = requests.get(f"{API_URL}{endpoint}")
                elapsed = (time.time() - start) * 1000  # ms
                
                if elapsed < 100:  # Should respond in under 100ms
                    self.log("Performance", f"{name} Response Time", "PASS", f"{elapsed:.1f}ms")
                else:
                    self.log("Performance", f"{name} Response Time", "WARNING", f"{elapsed:.1f}ms")
                    
            except Exception as e:
                self.log("Performance", name, "FAIL", str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("EXHAUSTIVE TEST SUITE - SLYWRITER")
        print("="*80)
        print(f"Started: {datetime.now().isoformat()}")
        
        # Check backend is running
        try:
            response = requests.get(f"{API_URL}/api/health")
            if response.status_code != 200:
                print("\n[ERROR] Backend is not healthy!")
                return
        except:
            print("\n[ERROR] Cannot connect to backend!")
            return
        
        # Run all test categories
        self.test_backend_endpoints()
        self.test_profiles()
        self.test_custom_wpm()
        self.test_websocket()
        self.test_edge_cases()
        self.test_concurrent_sessions()
        self.test_error_handling()
        self.test_performance()
        
        # Print summary
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        print(f"[OK] Passed: {len(self.results['passed'])}")
        print(f"[FAIL] Failed: {len(self.results['failed'])}")
        print(f"[WARN] Warnings: {len(self.results['warnings'])}")
        
        if self.results['failed']:
            print("\nFAILED TESTS:")
            for fail in self.results['failed']:
                print(f"  - {fail}")
        
        if self.results['warnings']:
            print("\nWARNINGS:")
            for warn in self.results['warnings']:
                print(f"  - {warn}")
        
        # Save detailed results
        with open("exhaustive_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed results saved to exhaustive_test_results.json")
        print(f"Completed: {datetime.now().isoformat()}")
        
        # Overall status
        if len(self.results['failed']) == 0:
            print("\n" + "="*80)
            print("[SUCCESS] ALL CRITICAL TESTS PASSED - READY FOR PRODUCTION")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("[ERROR] SOME TESTS FAILED - REVIEW REQUIRED")
            print("="*80)

if __name__ == "__main__":
    suite = ExhaustiveTestSuite()
    suite.run_all_tests()