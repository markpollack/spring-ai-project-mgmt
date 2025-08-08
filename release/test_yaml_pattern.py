#!/usr/bin/env python3
"""
Test script to verify the Spring AI BOM regex pattern
"""

import re

# Sample YAML content matching the start.spring.io structure
sample_yaml = """
      spring-ai:
        groupId: org.springframework.ai
        artifactId: spring-ai-bom
        versionProperty: spring-ai.version
        mappings:
          - compatibilityRange: "[3.4.0,4.0.0-M1)"
            version: 1.0.0
      spring-cloud:
        groupId: org.springframework.cloud
"""

def test_find_version():
    """Test finding current version"""
    pattern = r'spring-ai:\s*\n\s*groupId:\s*org\.springframework\.ai\s*\n\s*artifactId:\s*spring-ai-bom.*?mappings:\s*\n\s*-\s*compatibilityRange:.*?\n\s*version:\s*([0-9]+\.[0-9]+\.[0-9]+)'
    match = re.search(pattern, sample_yaml, re.DOTALL)
    
    if match:
        version = match.group(1)
        print(f"✅ Found version: {version}")
        return version
    else:
        print("❌ Pattern did not match")
        return None

def test_replace_version(new_version="1.0.1"):
    """Test replacing version"""
    pattern = r'(spring-ai:\s*\n\s*groupId:\s*org\.springframework\.ai\s*\n\s*artifactId:\s*spring-ai-bom.*?mappings:\s*\n\s*-\s*compatibilityRange:.*?\n\s*version:\s*)([0-9]+\.[0-9]+\.[0-9]+)'
    new_content = re.sub(pattern, f'\\g<1>{new_version}', sample_yaml, flags=re.DOTALL)
    
    if sample_yaml != new_content:
        print(f"✅ Version replacement successful!")
        print("Changed lines:")
        old_lines = sample_yaml.splitlines()
        new_lines = new_content.splitlines()
        
        for i, (old, new) in enumerate(zip(old_lines, new_lines)):
            if old != new:
                print(f"  Line {i+1}:")
                print(f"    - {old}")
                print(f"    + {new}")
        return True
    else:
        print("❌ No changes made - pattern didn't match")
        return False

if __name__ == "__main__":
    print("Testing Spring AI BOM regex pattern...")
    print("="*50)
    
    print("Sample YAML:")
    print(sample_yaml)
    print("="*50)
    
    print("\n1. Testing version detection:")
    current_version = test_find_version()
    
    print("\n2. Testing version replacement:")
    if current_version:
        test_replace_version("1.0.1")
    
    print("\nTest complete!")