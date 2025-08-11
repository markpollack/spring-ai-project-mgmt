#!/usr/bin/env python3
"""
Test JSON parsing from Claude Code response for solution assessor debugging
"""

import json
import re

def test_json_parsing():
    """Test JSON parsing from the Claude Code response"""
    
    # Read the response file
    with open('logs/claude-response-solution-assessor.txt', 'r') as f:
        content = f.read()
    
    print(f"Response file length: {len(content)} characters")
    
    # Use the same logic as the fixed backport assessor
    try:
        # Try to extract JSON from markdown code block first
        json_pattern = r'```json\s*\n(.*?)\n```'
        json_match = re.search(json_pattern, content, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
            print(f"Found JSON block, length: {len(json_str)} characters")
            print(f"First 200 chars: {json_str[:200]}")
            
            try:
                ai_data = json.loads(json_str)
                print("✅ Successfully parsed JSON from markdown code block")
                print(f"Fields: {list(ai_data.keys())}")
                
                # Check key fields
                print(f"Code quality score: {ai_data.get('code_quality_score', 'N/A')}")
                print(f"Final complexity score: {ai_data.get('final_complexity_score', 'N/A')}")
                print(f"Scope analysis: {ai_data.get('scope_analysis', 'N/A')[:100]}...")
                
                return ai_data
                
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON code block parse error: {e}")
                print(f"Error position: {e.pos}")
                if e.pos < len(json_str):
                    print(f"Context around error: ...{json_str[max(0, e.pos-50):e.pos+50]}...")
        else:
            print("No JSON block found with standard pattern")
            
        # Try alternative parsing if first attempt failed
        print("Trying direct JSON parsing from response...")
        lines = content.split('\n')
        json_lines = []
        in_json = False
        brace_count = 0
        
        for line in lines:
            if line.strip().startswith('{') and not in_json:
                in_json = True
                brace_count = 0
            
            if in_json:
                json_lines.append(line)
                # Count braces to handle nested objects
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0 and line.strip().endswith('}'):
                    break
        
        if json_lines:
            json_str = '\n'.join(json_lines)
            print(f"Found direct JSON, length: {len(json_str)} characters")
            print(f"First 200 chars: {json_str[:200]}")
            
            try:
                ai_data = json.loads(json_str)
                print("✅ Successfully parsed JSON from direct parsing")
                print(f"Fields: {list(ai_data.keys())}")
                return ai_data
            except json.JSONDecodeError as e:
                print(f"⚠️  Direct JSON parse error: {e}")
        else:
            print("No valid JSON structure found")
            
        return None
        
    except Exception as e:
        print(f"❌ General parsing error: {e}")
        return None

if __name__ == "__main__":
    result = test_json_parsing()
    if result:
        print("\n✅ JSON parsing test successful!")
        print(f"Assessment contains {len(result)} fields")
    else:
        print("\n❌ JSON parsing test failed")