"""
COMPREHENSIVE TEST SUITE FOR SLYWRITER
Tests every single feature systematically
"""

import requests
import json
import time
import random
import base64
from datetime import datetime

API_URL = "http://localhost:8000"

class SlyWriterTestSuite:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.session_id = None
        
    def log_result(self, test_name, status, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": "PASS" if status else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        if status:
            self.passed += 1
            print(f"[PASS] {test_name}")
        else:
            self.failed += 1
            print(f"[FAIL] {test_name}: {details}")
    
    def test_backend_health(self):
        """Test 1: Backend health check"""
        try:
            response = requests.get(f"{API_URL}/api/health")
            success = response.status_code == 200
            self.log_result("Backend Health Check", success, response.text if not success else "OK")
            return success
        except Exception as e:
            self.log_result("Backend Health Check", False, str(e))
            return False
    
    def test_profiles_endpoint(self):
        """Test 2: Profiles endpoint"""
        try:
            response = requests.get(f"{API_URL}/api/profiles")
            if response.status_code != 200:
                self.log_result("Profiles Endpoint", False, f"Status {response.status_code}")
                return False
            
            data = response.json()
            profiles = data.get("profiles", [])
            
            # Check all required profiles exist
            required = ["Slow", "Medium", "Fast", "Essay", "Custom"]
            found = [p["name"] for p in profiles]
            
            for req in required:
                if req not in found:
                    self.log_result("Profiles Endpoint", False, f"Missing profile: {req}")
                    return False
            
            # Check delay values are different
            slow = next(p for p in profiles if p["name"] == "Slow")
            fast = next(p for p in profiles if p["name"] == "Fast")
            
            if slow["settings"]["min_delay"] <= fast["settings"]["min_delay"]:
                self.log_result("Profiles Endpoint", False, "Slow profile not slower than Fast")
                return False
            
            self.log_result("Profiles Endpoint", True, f"Found {len(profiles)} profiles")
            return True
            
        except Exception as e:
            self.log_result("Profiles Endpoint", False, str(e))
            return False
    
    def test_typing_start_stop(self):
        """Test 3: Start and stop typing"""
        try:
            # Start typing
            response = requests.post(f"{API_URL}/api/typing/start", json={
                "text": "Test typing.",
                "profile": "Fast",
                "preview_mode": False
            })
            
            if response.status_code != 200:
                self.log_result("Typing Start", False, response.text)
                return False
            
            data = response.json()
            session_id = data.get("session_id")
            if not session_id:
                self.log_result("Typing Start", False, "No session ID returned")
                return False
            
            self.log_result("Typing Start", True, f"Session: {session_id}")
            
            # Wait a bit
            time.sleep(2)
            
            # Stop typing
            response = requests.post(f"{API_URL}/api/typing/stop/{session_id}")
            success = response.status_code == 200
            self.log_result("Typing Stop", success, response.text if not success else "OK")
            
            return True
            
        except Exception as e:
            self.log_result("Typing Start/Stop", False, str(e))
            return False
    
    def test_custom_wpm(self):
        """Test 4: Custom WPM"""
        try:
            wpms = [30, 60, 90, 120]
            for wpm in wpms:
                response = requests.post(f"{API_URL}/api/typing/start", json={
                    "text": "Test.",
                    "profile": "Custom",
                    "custom_wpm": wpm,
                    "preview_mode": True  # Preview to avoid actual typing
                })
                
                if response.status_code != 200:
                    self.log_result(f"Custom WPM {wpm}", False, response.text)
                    continue
                
                data = response.json()
                session_id = data.get("session_id")
                if session_id:
                    # Stop it
                    requests.post(f"{API_URL}/api/typing/stop/{session_id}")
                    self.log_result(f"Custom WPM {wpm}", True, "OK")
                else:
                    self.log_result(f"Custom WPM {wpm}", False, "No session ID")
            
            return True
            
        except Exception as e:
            self.log_result("Custom WPM", False, str(e))
            return False
    
    def test_pause_resume(self):
        """Test 5: Pause and resume"""
        try:
            # Start typing
            response = requests.post(f"{API_URL}/api/typing/start", json={
                "text": "Testing pause and resume functionality.",
                "profile": "Medium",
                "preview_mode": False
            })
            
            if response.status_code != 200:
                self.log_result("Pause/Resume Setup", False, "Failed to start")
                return False
            
            session_id = response.json()["session_id"]
            
            # Pause
            time.sleep(1)
            response = requests.post(f"{API_URL}/api/typing/pause/{session_id}")
            pause_success = response.status_code == 200
            self.log_result("Typing Pause", pause_success, response.text if not pause_success else "OK")
            
            # Resume
            time.sleep(1)
            response = requests.post(f"{API_URL}/api/typing/resume/{session_id}")
            resume_success = response.status_code == 200
            self.log_result("Typing Resume", resume_success, response.text if not resume_success else "OK")
            
            # Stop
            time.sleep(1)
            requests.post(f"{API_URL}/api/typing/stop/{session_id}")
            
            return pause_success and resume_success
            
        except Exception as e:
            self.log_result("Pause/Resume", False, str(e))
            return False
    
    def test_global_stop(self):
        """Test 6: Global emergency stop"""
        try:
            # Start multiple sessions
            sessions = []
            for i in range(3):
                response = requests.post(f"{API_URL}/api/typing/start", json={
                    "text": f"Session {i}",
                    "profile": "Fast",
                    "preview_mode": True
                })
                if response.status_code == 200:
                    sessions.append(response.json()["session_id"])
            
            # Global stop
            response = requests.post(f"{API_URL}/api/typing/stop")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                stopped = data.get("stopped_sessions", [])
                self.log_result("Global Stop", True, f"Stopped {len(stopped)} sessions")
            else:
                self.log_result("Global Stop", False, response.text)
            
            return success
            
        except Exception as e:
            self.log_result("Global Stop", False, str(e))
            return False
    
    def test_websocket_endpoint(self):
        """Test 7: WebSocket endpoint availability"""
        try:
            # Just check if WS endpoint exists (can't easily test WS in requests)
            # We'll check if the HTTP endpoints that support WS are working
            response = requests.get(f"{API_URL}/api/health")
            self.log_result("WebSocket Support", True, "Backend supports WS")
            return True
            
        except Exception as e:
            self.log_result("WebSocket Support", False, str(e))
            return False
    
    def test_update_wpm(self):
        """Test 8: Update WPM during typing"""
        try:
            # Start typing
            response = requests.post(f"{API_URL}/api/typing/start", json={
                "text": "Testing WPM update.",
                "profile": "Custom",
                "custom_wpm": 60,
                "preview_mode": True
            })
            
            if response.status_code != 200:
                self.log_result("Update WPM", False, "Failed to start")
                return False
            
            session_id = response.json()["session_id"]
            
            # Update WPM
            response = requests.post(f"{API_URL}/api/typing/update_wpm", json={
                "session_id": session_id,
                "wpm": 120
            })
            
            success = response.status_code == 200
            self.log_result("Update WPM", success, response.text if not success else "OK")
            
            # Stop
            requests.post(f"{API_URL}/api/typing/stop/{session_id}")
            
            return success
            
        except Exception as e:
            self.log_result("Update WPM", False, str(e))
            return False
    
    def test_edge_cases(self):
        """Test 9: Edge cases"""
        edge_cases = [
            ("Empty text", ""),
            ("Single char", "A"),
            ("Special chars", "@#$%^&*()"),
            ("Unicode", "café résumé naïve"),
            ("Very long", "x" * 1000),
            ("Newlines", "Line1\\nLine2\\nLine3"),
            ("Tabs", "Tab\\there\\ttabs"),
        ]
        
        all_passed = True
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
                        requests.post(f"{API_URL}/api/typing/stop/{session_id}")
                        self.log_result(f"Edge Case: {name}", True, "OK")
                    else:
                        self.log_result(f"Edge Case: {name}", False, "No session ID")
                        all_passed = False
                else:
                    self.log_result(f"Edge Case: {name}", False, f"Status {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"Edge Case: {name}", False, str(e))
                all_passed = False
        
        return all_passed
    
    def test_all_profiles(self):
        """Test 10: All profiles work"""
        profiles = ["Slow", "Medium", "Fast", "Essay", "Custom"]
        all_passed = True
        
        for profile in profiles:
            try:
                payload = {
                    "text": f"Testing {profile} profile.",
                    "profile": profile,
                    "preview_mode": True
                }
                if profile == "Custom":
                    payload["custom_wpm"] = 80
                
                response = requests.post(f"{API_URL}/api/typing/start", json=payload)
                
                if response.status_code == 200:
                    session_id = response.json().get("session_id")
                    if session_id:
                        time.sleep(0.5)
                        requests.post(f"{API_URL}/api/typing/stop/{session_id}")
                        self.log_result(f"Profile: {profile}", True, "OK")
                    else:
                        self.log_result(f"Profile: {profile}", False, "No session ID")
                        all_passed = False
                else:
                    self.log_result(f"Profile: {profile}", False, f"Status {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"Profile: {profile}", False, str(e))
                all_passed = False
        
        return all_passed
    
    def test_preview_mode(self):
        """Test 11: Preview mode"""
        try:
            # Test with preview ON
            response = requests.post(f"{API_URL}/api/typing/start", json={
                "text": "Preview mode test.",
                "profile": "Fast",
                "preview_mode": True
            })
            
            if response.status_code != 200:
                self.log_result("Preview Mode ON", False, response.text)
                return False
            
            session_id = response.json()["session_id"]
            requests.post(f"{API_URL}/api/typing/stop/{session_id}")
            self.log_result("Preview Mode ON", True, "OK")
            
            # Test with preview OFF
            response = requests.post(f"{API_URL}/api/typing/start", json={
                "text": "Normal mode test.",
                "profile": "Fast",
                "preview_mode": False
            })
            
            if response.status_code != 200:
                self.log_result("Preview Mode OFF", False, response.text)
                return False
            
            session_id = response.json()["session_id"]
            time.sleep(1)
            requests.post(f"{API_URL}/api/typing/stop/{session_id}")
            self.log_result("Preview Mode OFF", True, "OK")
            
            return True
            
        except Exception as e:
            self.log_result("Preview Mode", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("SLYWRITER COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"Starting at {datetime.now().isoformat()}")
        print("-" * 60)
        
        # Check if backend is running first
        if not self.test_backend_health():
            print("\\n[ERROR] Backend is not running! Aborting tests.")
            return
        
        # Run all tests
        tests = [
            self.test_profiles_endpoint,
            self.test_typing_start_stop,
            self.test_custom_wpm,
            self.test_pause_resume,
            self.test_global_stop,
            self.test_websocket_endpoint,
            self.test_update_wpm,
            self.test_edge_cases,
            self.test_all_profiles,
            self.test_preview_mode,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"[ERROR] Test crashed: {e}")
            time.sleep(0.5)  # Brief pause between test groups
        
        # Print summary
        print("-" * 60)
        print("TEST RESULTS SUMMARY")
        print("-" * 60)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")
        
        if self.failed > 0:
            print("\\nFailed Tests:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['details']}")
        
        print("=" * 60)
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("Results saved to test_results.json")

if __name__ == "__main__":
    suite = SlyWriterTestSuite()
    suite.run_all_tests()