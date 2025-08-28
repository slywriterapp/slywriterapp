"""
Test script to verify AI integration is working properly
Tests both mock responses and real OpenAI integration
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

API_URL = "http://localhost:8000"

class AIIntegrationTester:
    def __init__(self):
        self.results = []
        
    async def test_endpoint(self, name: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single AI endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{API_URL}{endpoint}", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = {
                            "test": name,
                            "endpoint": endpoint,
                            "status": "PASS",
                            "success": data.get("success", False),
                            "mock": data.get("mock", False),
                            "has_text": bool(data.get("text")),
                            "text_preview": data.get("text", "")[:100] + "..." if data.get("text") else None
                        }
                    else:
                        result = {
                            "test": name,
                            "endpoint": endpoint,
                            "status": "FAIL",
                            "error": f"HTTP {response.status}",
                            "success": False
                        }
        except Exception as e:
            result = {
                "test": name,
                "endpoint": endpoint,
                "status": "ERROR",
                "error": str(e),
                "success": False
            }
        
        self.results.append(result)
        return result
    
    async def run_all_tests(self):
        """Run all AI integration tests"""
        print("=" * 60)
        print("AI INTEGRATION TEST SUITE")
        print("=" * 60)
        print()
        
        # Test 1: Basic text generation
        print("Test 1: Basic Text Generation...")
        await self.test_endpoint(
            "Basic Generation",
            "/api/ai/generate",
            {
                "prompt": "Write a short paragraph about the benefits of typing practice",
                "max_tokens": 100,
                "temperature": 0.7
            }
        )
        
        # Test 2: Essay generation
        print("Test 2: Essay Generation...")
        await self.test_endpoint(
            "Essay Generation",
            "/api/ai/essay",
            {
                "topic": "The importance of digital literacy",
                "word_count": 200,
                "tone": "professional",
                "academic_level": "college"
            }
        )
        
        # Test 3: Text humanization
        print("Test 3: Text Humanization...")
        await self.test_endpoint(
            "Humanize Text",
            "/api/ai/humanize",
            {
                "text": "The implementation of artificial intelligence systems has significantly impacted various sectors.",
                "style": "natural",
                "preserve_meaning": True
            }
        )
        
        # Test 4: Topic explanation
        print("Test 4: Topic Explanation...")
        await self.test_endpoint(
            "Explain Topic",
            "/api/ai/explain",
            {
                "topic": "Touch typing techniques",
                "learning_style": "visual",
                "complexity": "beginner"
            }
        )
        
        # Test 5: Study questions generation
        print("Test 5: Study Questions Generation...")
        await self.test_endpoint(
            "Study Questions",
            "/api/ai/study-questions",
            {
                "topic": "Keyboard ergonomics",
                "num_questions": 3,
                "difficulty": "intermediate"
            }
        )
        
        # Print results summary
        print()
        print("=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        print()
        
        passed = 0
        failed = 0
        errors = 0
        using_mock = 0
        
        for result in self.results:
            status_symbol = "[PASS]" if result["status"] == "PASS" else "[FAIL]" if result["status"] == "FAIL" else "[WARN]"
            mock_indicator = " (MOCK)" if result.get("mock") else " (REAL AI)" if result.get("success") and not result.get("mock") else ""
            
            print(f"{status_symbol} {result['test']}: {result['status']}{mock_indicator}")
            
            if result["status"] == "PASS":
                passed += 1
                if result.get("mock"):
                    using_mock += 1
                if result.get("text_preview"):
                    print(f"  Response preview: {result['text_preview']}")
            elif result["status"] == "FAIL":
                failed += 1
                print(f"  Error: {result.get('error', 'Unknown error')}")
            else:
                errors += 1
                print(f"  Error: {result.get('error', 'Unknown error')}")
            print()
        
        print("-" * 60)
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print(f"Using Mock Responses: {using_mock}")
        print("-" * 60)
        
        if using_mock == passed and passed > 0:
            print()
            print("[WARNING] ALL TESTS ARE USING MOCK RESPONSES")
            print("To enable real AI generation:")
            print("1. Get an OpenAI API key from https://platform.openai.com/api-keys")
            print("2. Create a .env file in the backend directory")
            print("3. Add: OPENAI_API_KEY=your_api_key_here")
            print("4. Restart the backend server")
        elif using_mock > 0:
            print()
            print(f"[INFO] {using_mock} tests are using mock responses")
            print("Real AI is partially configured")
        elif passed == len(self.results):
            print()
            print("[SUCCESS] ALL TESTS PASSED WITH REAL AI GENERATION!")
            print("OpenAI integration is working correctly")
        
        return passed == len(self.results)

async def main():
    tester = AIIntegrationTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)