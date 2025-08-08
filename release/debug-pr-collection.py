#!/usr/bin/env python3
"""
Debug PR Collection Script
Find PRs associated with a specific release to verify GitHub API integration.
"""

import os
import sys
import json
import requests
import subprocess
from typing import List, Dict, Optional
from datetime import datetime

class PRCollectionDebugger:
    """Debug PR collection for release validation"""
    
    def __init__(self, repo: str = "spring-projects/spring-ai"):
        self.repo = repo
        self.token = os.environ.get('GITHUB_TOKEN')
        self.graphql_url = 'https://api.github.com/graphql'
        
        if not self.token:
            print("❌ No GitHub token found - export GITHUB_TOKEN")
            sys.exit(1)
        
        print(f"✅ GitHub token found: {self.token[:10]}...")
        print(f"📦 Repository: {self.repo}")
    
    @property
    def headers(self) -> Dict[str, str]:
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
    
    def find_prs_by_label(self, label: str = "1.0.1") -> List[Dict]:
        """Find PRs with specific label using GitHub CLI"""
        print(f"\n🔍 Searching for PRs labeled '{label}'...")
        
        try:
            cmd = [
                'gh', 'pr', 'list',
                '--repo', self.repo,
                '--label', label,
                '--state', 'merged',
                '--limit', '50',
                '--json', 'number,title,url,mergedAt,labels'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            prs = json.loads(result.stdout)
            
            print(f"✅ Found {len(prs)} PRs with label '{label}'")
            return prs
            
        except subprocess.CalledProcessError as e:
            print(f"❌ GitHub CLI error: {e}")
            print(f"   stderr: {e.stderr}")
            return []
    
    def find_prs_merged_between_tags(self, since_tag: str, until_tag: str) -> List[Dict]:
        """Find PRs merged between two tags using GraphQL"""
        print(f"\n🔍 Searching for PRs merged between {since_tag} and {until_tag}...")
        
        # Get tag dates first
        since_date = self.get_tag_date(since_tag)
        until_date = self.get_tag_date(until_tag)
        
        if not since_date or not until_date:
            print("❌ Could not get tag dates")
            return []
        
        print(f"📅 Date range: {since_date} to {until_date}")
        
        # GraphQL query to find merged PRs in date range
        query = f'''
        query {{
          repository(owner: "spring-projects", name: "spring-ai") {{
            pullRequests(first: 100, states: MERGED, orderBy: {{field: UPDATED_AT, direction: DESC}}) {{
              nodes {{
                number
                title
                url
                mergedAt
                baseRefName
                labels(first: 10) {{
                  nodes {{
                    name
                  }}
                }}
                closingIssuesReferences(first: 10) {{
                  nodes {{
                    number
                    title
                  }}
                }}
              }}
            }}
          }}
        }}
        '''
        
        try:
            response = requests.post(
                self.graphql_url,
                json={'query': query},
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if 'errors' in data:
                print(f"❌ GraphQL errors: {data['errors']}")
                return []
            
            all_prs = data['data']['repository']['pullRequests']['nodes']
            
            # Filter PRs by merge date
            filtered_prs = []
            for pr in all_prs:
                if pr['mergedAt']:
                    merged_date = datetime.fromisoformat(pr['mergedAt'].replace('Z', '+00:00'))
                    if since_date <= merged_date <= until_date:
                        filtered_prs.append(pr)
            
            print(f"✅ Found {len(filtered_prs)} PRs merged between tags")
            return filtered_prs
            
        except Exception as e:
            print(f"❌ GraphQL error: {e}")
            return []
    
    def get_tag_date(self, tag: str) -> Optional[datetime]:
        """Get the date of a git tag"""
        try:
            if not tag.startswith('v'):
                tag = f'v{tag}'
            
            cmd = ['gh', 'api', f'/repos/{self.repo}/git/refs/tags/{tag}']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            ref_data = json.loads(result.stdout)
            
            # Get the commit associated with the tag
            sha = ref_data['object']['sha']
            
            cmd = ['gh', 'api', f'/repos/{self.repo}/git/commits/{sha}']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commit_data = json.loads(result.stdout)
            
            date_str = commit_data['committer']['date']
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
        except Exception as e:
            print(f"❌ Error getting tag date for {tag}: {e}")
            return None
    
    def find_commits_for_prs(self, prs: List[Dict]) -> Dict[int, List[str]]:
        """Find commit SHAs for given PRs"""
        print(f"\n🔍 Finding commits for {len(prs)} PRs...")
        
        pr_commits = {}
        
        for pr in prs[:5]:  # Limit to first 5 for testing
            pr_number = pr['number']
            print(f"  📝 PR #{pr_number}: {pr['title'][:50]}...")
            
            try:
                cmd = ['gh', 'api', f'/repos/{self.repo}/pulls/{pr_number}/commits', '--jq', '.[].sha']
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                commits = result.stdout.strip().split('\n')
                pr_commits[pr_number] = [c for c in commits if c]
                print(f"    ✅ Found {len(pr_commits[pr_number])} commits")
                
            except subprocess.CalledProcessError as e:
                print(f"    ❌ Error getting commits for PR #{pr_number}: {e}")
                pr_commits[pr_number] = []
        
        return pr_commits
    
    def test_commit_pr_associations(self, commit_shas: List[str]) -> None:
        """Test the same GraphQL query as the main script"""
        print(f"\n🧪 Testing commit→PR associations for {len(commit_shas)} commits...")
        
        # Use the same GraphQL query as generate-release-notes.py
        commit_queries = []
        for i, sha in enumerate(commit_shas[:3]):  # Test first 3
            commit_queries.append(f'''
            commit{i}: object(oid: "{sha}") {{
                ... on Commit {{
                    oid
                    associatedPullRequests(first: 5) {{
                        nodes {{
                            number
                            title
                            url
                            state
                        }}
                    }}
                }}
            }}
            ''')
        
        query = f'''
        query {{
            repository(owner: "spring-projects", name: "spring-ai") {{
                {' '.join(commit_queries)}
            }}
        }}
        '''
        
        try:
            response = requests.post(
                self.graphql_url,
                json={'query': query},
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if 'errors' in data:
                print(f"❌ GraphQL errors: {data['errors']}")
                return
            
            repo_data = data['data']['repository']
            
            for i, sha in enumerate(commit_shas[:3]):
                commit_data = repo_data.get(f'commit{i}')
                if commit_data:
                    prs = commit_data.get('associatedPullRequests', {}).get('nodes', [])
                    print(f"  📍 Commit {sha[:8]}: {len(prs)} associated PRs")
                    for pr in prs:
                        print(f"    • PR #{pr['number']}: {pr['title']}")
                else:
                    print(f"  ❌ Commit {sha[:8]}: No data returned")
            
        except Exception as e:
            print(f"❌ GraphQL test error: {e}")
    
    def print_summary(self, prs: List[Dict], pr_commits: Dict[int, List[str]]) -> None:
        """Print a summary of findings"""
        print(f"\n📊 SUMMARY:")
        print(f"  • {len(prs)} PRs found")
        print(f"  • {sum(len(commits) for commits in pr_commits.values())} commits across tested PRs")
        
        if prs:
            print(f"\n📝 Sample PRs:")
            for pr in prs[:5]:
                # Handle both GraphQL format (nodes) and GitHub CLI format (direct list)
                labels_data = pr.get('labels', [])
                if isinstance(labels_data, dict) and 'nodes' in labels_data:
                    labels = [label['name'] for label in labels_data['nodes']]
                else:
                    labels = [label['name'] for label in labels_data]
                
                # GitHub CLI doesn't include closingIssuesReferences, skip for now
                issues = []
                print(f"  • PR #{pr['number']}: {pr['title']}")
                print(f"    📅 Merged: {pr.get('mergedAt', 'N/A')}")
                print(f"    🏷️  Labels: {labels}")
                print(f"    🔗 Closes: {issues}")
                if pr['number'] in pr_commits:
                    print(f"    📍 Commits: {len(pr_commits[pr['number']])} found")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug PR collection for Spring AI releases')
    parser.add_argument('--label', default='1.0.1', help='PR label to search for')
    parser.add_argument('--since-tag', default='v1.0.0', help='Start tag for date range')
    parser.add_argument('--until-tag', default='v1.0.1', help='End tag for date range')
    parser.add_argument('--test-commits', action='store_true', help='Test commit→PR associations')
    
    args = parser.parse_args()
    
    debugger = PRCollectionDebugger()
    
    # Method 1: Find PRs by label
    prs_by_label = debugger.find_prs_by_label(args.label)
    
    # Method 2: Find PRs by merge date between tags
    prs_by_date = debugger.find_prs_merged_between_tags(args.since_tag, args.until_tag)
    
    # Combine and deduplicate
    all_prs = prs_by_label + prs_by_date
    unique_prs = {pr['number']: pr for pr in all_prs}.values()
    unique_prs = list(unique_prs)
    
    print(f"\n🎯 TOTAL UNIQUE PRS: {len(unique_prs)}")
    
    # Find commits for these PRs
    pr_commits = debugger.find_commits_for_prs(unique_prs)
    
    # Test commit→PR associations if requested
    if args.test_commits and pr_commits:
        all_commits = []
        for commits in list(pr_commits.values())[:3]:  # First 3 PRs
            all_commits.extend(commits[:2])  # First 2 commits per PR
        
        debugger.test_commit_pr_associations(all_commits)
    
    # Print summary
    debugger.print_summary(unique_prs, pr_commits)


if __name__ == "__main__":
    main()