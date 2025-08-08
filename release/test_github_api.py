#!/usr/bin/env python3
"""
Simple test script to debug GitHub GraphQL API for PR associations
"""

import os
import requests
import json
from typing import List, Dict, Optional

def test_github_api(commit_shas: List[str], repo: str = "spring-projects/spring-ai"):
    """Test GitHub GraphQL API for commit PR associations"""
    
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("❌ No GitHub token found in environment")
        return
    
    print(f"✅ GitHub token found: {token[:10]}...")
    print(f"🎯 Testing with {len(commit_shas)} commits")
    print(f"📦 Repository: {repo}")
    
    # GraphQL endpoint
    graphql_url = 'https://api.github.com/graphql'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # Test with just the first commit
    test_sha = commit_shas[0]
    print(f"🔍 Testing with commit: {test_sha}")
    
    # Build GraphQL query
    owner, name = repo.split('/')
    query = f'''
    query {{
        repository(owner: "{owner}", name: "{name}") {{
            object(oid: "{test_sha}") {{
                ... on Commit {{
                    oid
                    associatedPullRequests(first: 5) {{
                        nodes {{
                            number
                            title
                            url
                            state
                            labels(first: 10) {{
                                nodes {{
                                    name
                                }}
                            }}
                            closingIssuesReferences(first: 10) {{
                                nodes {{
                                    number
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
    '''
    
    print(f"\n📤 GraphQL Query:")
    print(query)
    
    try:
        response = requests.post(
            graphql_url,
            json={'query': query},
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.text}")
            return
        
        data = response.json()
        print(f"\n📋 Raw Response:")
        print(json.dumps(data, indent=2))
        
        # Parse the response
        if 'errors' in data:
            print(f"\n❌ GraphQL Errors: {data['errors']}")
            return
        
        repo_data = data.get('data', {}).get('repository', {})
        commit_data = repo_data.get('object')
        
        if not commit_data:
            print(f"\n❌ No commit data found for {test_sha}")
            return
        
        prs = commit_data.get('associatedPullRequests', {}).get('nodes', [])
        print(f"\n🎉 Found {len(prs)} associated PRs:")
        
        for pr in prs:
            labels = [label['name'] for label in pr.get('labels', {}).get('nodes', [])]
            issues = [issue['number'] for issue in pr.get('closingIssuesReferences', {}).get('nodes', [])]
            print(f"  • PR #{pr['number']}: {pr['title']}")
            print(f"    URL: {pr['url']}")
            print(f"    State: {pr['state']}")
            print(f"    Labels: {labels}")
            print(f"    Closes issues: {issues}")
        
        if not prs:
            print("⚠️  No associated PRs found - this could mean:")
            print("  1. The commit was made directly to the branch (not via PR)")
            print("  2. The commit SHA is incorrect")
            print("  3. The commit is from a different repository")
            print("  4. There's an issue with the GraphQL query")
            
        return len(prs)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

if __name__ == "__main__":
    # Test with a few real commits from v1.0.0..v1.0.1
    test_commits = [
        "469ca5447f2538c7cd88beca40193e6d5daf4b1c",  # Next development version 1.0.2-SNAPSHOT
        "f21e8d8e4c6a31b46b2e0b9b7e5f3c2d1a0e9c8b",  # A real commit (example)
        "8d13903f4b2e1c6d7a9e3f8c1b5e2d4a7c0f9e8b",  # Another real commit (example)
    ]
    
    # Use only the first commit for initial testing
    test_github_api([test_commits[0]])