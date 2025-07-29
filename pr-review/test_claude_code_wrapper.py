#!/usr/bin/env python3
"""
Claude Code Wrapper Test Suite

Comprehensive testing for ClaudeCodeWrapper to isolate and debug 
Claude Code execution issues systematically.
"""

import json
import tempfile
from pathlib import Path
from claude_code_wrapper import ClaudeCodeWrapper

class ClaudeCodeWrapperTests:
    """Test suite for ClaudeCodeWrapper functionality"""
    
    def __init__(self):
        self.wrapper = ClaudeCodeWrapper()
        self.test_results = []
        self.failed_tests = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
        if not success:
            self.failed_tests.append(test_name)
    
    def test_availability(self):
        """Test if Claude Code is available and responds"""
        print("\n🔍 Testing Claude Code Availability...")
        
        is_available = self.wrapper.is_available()
        self.log_test("Claude Code availability", is_available, 
                     f"Available: {is_available}")
        
        if is_available:
            version = self.wrapper.get_version()
            self.log_test("Version retrieval", version is not None, 
                         f"Version: {version}")
        else:
            self.log_test("Version retrieval", False, "Claude Code not available")
    
    def test_simple_prompt(self):
        """Test simple text prompt"""
        print("\n🔍 Testing Simple Text Prompt...")
        
        simple_prompt = "What is 2 + 2? Just return the number."
        
        result = self.wrapper.analyze_from_text(
            prompt_text=simple_prompt,
            timeout=30,
            use_json_output=False,
            show_progress=False
        )
        
        success = result['success']
        response = result.get('response', '')
        
        self.log_test("Simple prompt execution", success, 
                     f"Response: '{response[:100]}...' (length: {len(response)})")
        
        if not success:
            self.log_test("Simple prompt error", False,
                         f"Error: {result.get('error', 'Unknown')}")
    
    def test_json_prompt(self):
        """Test JSON-structured prompt"""
        print("\n🔍 Testing JSON Output Prompt...")
        
        json_prompt = """
Please analyze this simple task and return your response in JSON format:
Task: "What is the capital of France?"

Return your response as JSON with this structure:
{
    "question": "What is the capital of France?",
    "answer": "Paris",
    "confidence": "high"
}
"""
        
        result = self.wrapper.analyze_from_text(
            prompt_text=json_prompt,
            timeout=60,
            use_json_output=True,
            show_progress=False
        )
        
        success = result['success']
        response = result.get('response', '')
        
        self.log_test("JSON prompt execution", success,
                     f"Response length: {len(response)}")
        
        if success:
            try:
                # Try to parse as JSON
                if isinstance(response, str) and response.strip():
                    json_data = json.loads(response)
                    self.log_test("JSON parsing", True,
                                 f"Parsed keys: {list(json_data.keys())}")
                else:
                    self.log_test("JSON parsing", False,
                                 f"Empty or invalid response: '{response}'")
            except json.JSONDecodeError as e:
                self.log_test("JSON parsing", False,
                             f"JSON parse error: {e}")
        else:
            self.log_test("JSON prompt error", False,
                         f"Error: {result.get('error', 'Unknown')}")
    
    def test_file_reading_prompt(self):
        """Test prompt that reads a file"""
        print("\n🔍 Testing File Reading Prompt...")
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test file for Claude Code wrapper testing.\n")
            f.write("Line 2: Testing file read capabilities.\n")
            f.write("Line 3: End of test file.\n")
            test_file_path = f.name
        
        try:
            file_prompt = f"""
Please read the file at {test_file_path} and summarize its contents.
Return a JSON response with:
{{
    "file_path": "{test_file_path}",
    "line_count": <number of lines>,
    "summary": "<brief summary of contents>"
}}
"""
            
            result = self.wrapper.analyze_from_text(
                prompt_text=file_prompt,
                timeout=60,
                use_json_output=True,
                show_progress=False
            )
            
            success = result['success']
            response = result.get('response', '')
            
            self.log_test("File reading prompt", success,
                         f"Response length: {len(response)}")
            
            if success and response:
                try:
                    json_data = json.loads(response)
                    has_expected_keys = all(key in json_data for key in ['file_path', 'summary'])
                    self.log_test("File reading JSON structure", has_expected_keys,
                                 f"Keys found: {list(json_data.keys())}")
                except json.JSONDecodeError:
                    self.log_test("File reading JSON structure", False,
                                 "Could not parse JSON response")
            else:
                self.log_test("File reading error", False,
                             f"Error: {result.get('error', 'Unknown')}")
        
        finally:
            # Clean up test file
            Path(test_file_path).unlink(missing_ok=True)
    
    def test_problematic_scenarios(self):
        """Test scenarios that might cause 'Execution error'"""
        print("\n🔍 Testing Problematic Scenarios...")
        
        # Test 1: Very long prompt
        long_prompt = "Analyze this: " + "word " * 1000 + "\nReturn JSON: {\"status\": \"analyzed\"}"
        
        result = self.wrapper.analyze_from_text(
            prompt_text=long_prompt,
            timeout=30,
            use_json_output=True,
            show_progress=False
        )
        
        self.log_test("Long prompt handling", result['success'],
                     f"Response: '{result.get('response', 'None')[:50]}...'")
        
        # Test 2: Prompt with special characters
        special_prompt = '''
Analyze this text with special chars: "quotes", 'apostrophes', <brackets>, [arrays], {objects}
Return: {"result": "analyzed special characters"}
'''
        
        result = self.wrapper.analyze_from_text(
            prompt_text=special_prompt,
            timeout=30,
            use_json_output=True,
            show_progress=False
        )
        
        self.log_test("Special characters handling", result['success'],
                     f"Response: '{result.get('response', 'None')[:50]}...'")
        
        # Test 3: Empty prompt
        result = self.wrapper.analyze_from_text(
            prompt_text="",
            timeout=30,
            use_json_output=False,
            show_progress=False
        )
        
        self.log_test("Empty prompt handling", not result['success'],  # Should fail gracefully
                     f"Expected failure, got: {result.get('error', 'Unknown')}")
    
    def test_real_world_scenario(self):
        """Test scenario similar to our failing PR analysis"""
        print("\n🔍 Testing Real-World PR Analysis Scenario...")
        
        pr_analysis_prompt = """
Analyze this hypothetical PR for Spring AI:

PR Title: Fix JSON parsing issue in BeanOutputConverter
Files Changed: 1 file, +1/-0 lines
Change: Added regex to strip <think> tags before JSON parsing

Please provide analysis in JSON format:
{
    "problem_summary": "Brief description of the problem",
    "solution_quality": "Assessment of the solution",
    "complexity_score": 3,
    "recommendations": ["List of recommendations"]
}
"""
        
        result = self.wrapper.analyze_from_text(
            prompt_text=pr_analysis_prompt,
            timeout=120,  # Longer timeout like real scenario
            use_json_output=True,
            show_progress=False
        )
        
        success = result['success']
        response = result.get('response', '')
        
        self.log_test("PR analysis scenario", success,
                     f"Response length: {len(response)}")
        
        if success:
            try:
                json_data = json.loads(response)
                required_keys = ['problem_summary', 'solution_quality', 'complexity_score']
                has_required = all(key in json_data for key in required_keys)
                self.log_test("PR analysis JSON structure", has_required,
                             f"Keys: {list(json_data.keys())}")
            except json.JSONDecodeError as e:
                self.log_test("PR analysis JSON parsing", False,
                             f"Parse error: {e}")
        else:
            error_msg = result.get('error', 'Unknown')
            stderr_msg = result.get('stderr', 'None')
            self.log_test("PR analysis failure details", False,
                         f"Error: {error_msg}, Stderr: {stderr_msg}")
    
    def test_execution_error_mystery(self):
        """Test to reproduce the mysterious 'Execution error' issue"""
        print("\n🔍 Testing 'Execution Error' Mystery...")
        
        # Test exact scenario from our failing PR analysis
        failing_prompt = """
Analyze this Spring AI PR change and provide comprehensive solution assessment:

PR #3927: Update BeanOutputConverter.java
Files changed: 1 (+1/-0)
Change: Added regex to strip <think> tags before JSON parsing

Please analyze and return JSON:
{
    "scope_analysis": "Analysis of change scope",
    "solution_fitness": "Assessment of solution appropriateness",
    "code_quality_score": 7,
    "recommendations": ["List", "of", "recommendations"]
}
"""
        
        print("    Testing with exact failing scenario...")
        result = self.wrapper.analyze_from_text(
            prompt_text=failing_prompt,
            timeout=120,
            use_json_output=True,
            show_progress=True  # Show progress to see what happens
        )
        
        success = result['success']
        response = result.get('response', '')
        error = result.get('error', '')
        stderr = result.get('stderr', '')
        
        print(f"    Raw result details:")
        print(f"      Success: {success}")
        print(f"      Response: '{response}'")
        print(f"      Error: '{error}'")
        print(f"      Stderr: '{stderr}'")
        
        # Check for the specific "Execution error" pattern
        is_execution_error = response == "Execution error"
        
        self.log_test("Execution error reproduction", not is_execution_error,
                     f"Got 'Execution error': {is_execution_error}")
        
        if is_execution_error:
            print(f"\n💥 REPRODUCED THE ISSUE!")
            print(f"    This confirms 'Execution error' comes from Claude Code CLI")
            print(f"    Response length: {len(response)} chars")
            print(f"    Wrapper error: {error}")
            print(f"    Stderr: {stderr}")
            
            # Try direct CLI call to see raw output
            print(f"\n🔍 Testing direct Claude CLI call...")
            try:
                import subprocess
                import tempfile
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(failing_prompt)
                    temp_prompt_file = f.name
                
                # Direct CLI call like the wrapper does
                cmd = ['claude', '-p', '--dangerously-skip-permissions', '--verbose', '--output-format', 'json']
                cmd.append(f"Please read the file {temp_prompt_file} and follow the instructions contained within it.")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, 
                                      cwd='/home/mark/.nvm/versions/node/v22.15.0/lib/node_modules/@anthropic-ai/claude-code')
                
                print(f"    Direct CLI returncode: {result.returncode}")
                print(f"    Direct CLI stdout: '{result.stdout[:200]}...'")
                print(f"    Direct CLI stderr: '{result.stderr[:200]}...'")
                
                # Clean up
                Path(temp_prompt_file).unlink()
                
            except Exception as cli_error:
                print(f"    Direct CLI test failed: {cli_error}")
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🧪 Claude Code Wrapper Test Suite")
        print("=" * 50)
        
        self.test_availability()
        self.test_simple_prompt()
        self.test_json_prompt()
        self.test_file_reading_prompt()
        self.test_problematic_scenarios()
        self.test_real_world_scenario()
        self.test_execution_error_mystery()  # Add the mystery test
        
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['success']])
        failed_tests = len(self.failed_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test_name in self.failed_tests:
                print(f"  - {test_name}")
        
        # Save detailed results
        report_file = Path(__file__).parent / "logs" / "claude_wrapper_test_results.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "test_results": self.test_results,
                "failed_tests": self.failed_tests
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {report_file}")
        
        return failed_tests == 0


def main():
    """Run the test suite"""
    from datetime import datetime
    
    tester = ClaudeCodeWrapperTests()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print(f"\n💥 {len(tester.failed_tests)} test(s) failed - see details above")
        exit(1)


if __name__ == "__main__":
    main()