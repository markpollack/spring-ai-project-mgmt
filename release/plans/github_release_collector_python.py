#!/usr/bin/env python3
"""
GitHub Release Data Collector
Collects commit data, associated PRs, and issues for release note generation.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
import subprocess
import sys
from typing import Dict, List, Optional

class GitHubReleaseCollector:
    def __init__(self, repo_owner: str, repo_name: str, github_token: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.headers = {
            'Authorization': f'Bearer {github_token}',
            'Content-Type': 'application/json'
        }
        self.graphql_url = 'https://api.github.com/graphql'
        
    def get_commits_since_tag(self, since_tag: str) -> List[str]:
        """Get list of commit SHAs since the specified tag"""
        try:
            # Get commits since tag using git log
            result = subprocess.run([
                'git', 'log', f'{since_tag}..HEAD', '--pretty=format:%H'
            ], capture_output=True, text=True, check=True)
            
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError as e:
            print(f"Error getting commits: {e}")
            return []
    
    def get_commit_and_pr_data(self, commit_sha: str) -> Optional[Dict]:
        """Get commit data and associated PR using GraphQL"""
        query = """
        query($owner: String!, $name: String!, $oid: GitObjectID!) {
          repository(owner: $owner, name: $name) {
            object(oid: $oid) {
              ... on Commit {
                sha: oid
                message
                messageHeadline
                messageBody
                author {
                  name
                  email
                  date
                }
                committer {
                  name
                  email  
                  date
                }
                associatedPullRequests(first: 5) {
                  nodes {
                    number
                    title
                    body
                    url
                    state
                    createdAt
                    mergedAt
                    author {
                      login
                    }
                    labels(first: 20) {
                      nodes {
                        name
                        color
                      }
                    }
                    closingIssuesReferences(first: 10) {
                      nodes {
                        number
                        title
                        body
                        url
                        state
                        labels(first: 20) {
                          nodes {
                            name
                            color
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            'owner': self.repo_owner,
            'name': self.repo_name,
            'oid': commit_sha
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json={'query': query, 'variables': variables},
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            if 'errors' in data:
                print(f"GraphQL errors for commit {commit_sha}: {data['errors']}")
                return None
                
            commit_data = data.get('data', {}).get('repository', {}).get('object')
            if not commit_data:
                print(f"No commit data found for {commit_sha}")
                return None
                
            return commit_data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for commit {commit_sha}: {e}")
            return None
    
    def get_issue_data_batch(self, issue_numbers: List[int]) -> Dict[int, Dict]:
        """Get issue data for multiple issues in batch"""
        if not issue_numbers:
            return {}
            
        # Build dynamic GraphQL query for multiple issues
        issue_queries = []
        for i, issue_num in enumerate(issue_numbers):
            issue_queries.append(f"""
            issue{i}: issue(number: {issue_num}) {{
              number
              title
              body
              url
              state
              createdAt
              closedAt
              author {{
                login
              }}
              labels(first: 20) {{
                nodes {{
                  name
                  color
                }}
              }}
            }}
            """)
        
        query = f"""
        query($owner: String!, $name: String!) {{
          repository(owner: $owner, name: $name) {{
            {' '.join(issue_queries)}
          }}
        }}
        """
        
        variables = {
            'owner': self.repo_owner,
            'name': self.repo_name
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json={'query': query, 'variables': variables},
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            if 'errors' in data:
                print(f"GraphQL errors for issues: {data['errors']}")
                return {}
            
            repo_data = data.get('data', {}).get('repository', {})
            issues = {}
            
            for i, issue_num in enumerate(issue_numbers):
                issue_data = repo_data.get(f'issue{i}')
                if issue_data:
                    issues[issue_num] = issue_data
                    
            return issues
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching issue data: {e}")
            return {}
    
    def collect_release_data(self, since_tag: str, output_dir: str = 'release_data'):
        """Main method to collect all release data"""
        print(f"Collecting release data since tag: {since_tag}")
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        # Get commits
        commit_shas = self.get_commits_since_tag(since_tag)
        print(f"Found {len(commit_shas)} commits since {since_tag}")
        
        all_data = {
            'metadata': {
                'repository': f'{self.repo_owner}/{self.repo_name}',
                'since_tag': since_tag,
                'generated_at': datetime.now().isoformat(),
                'total_commits': len(commit_shas)
            },
            'commits': [],
            'summary': {
                'contributors': set(),
                'pr_count': 0,
                'issue_count': 0
            }
        }
        
        # Collect data for each commit
        for i, commit_sha in enumerate(commit_shas, 1):
            print(f"Processing commit {i}/{len(commit_shas)}: {commit_sha[:8]}")
            
            commit_data = self.get_commit_and_pr_data(commit_sha)
            if commit_data:
                # Track contributors
                if commit_data.get('author', {}).get('name'):
                    all_data['summary']['contributors'].add(commit_data['author']['name'])
                
                # Count PRs
                prs = commit_data.get('associatedPullRequests', {}).get('nodes', [])
                all_data['summary']['pr_count'] += len(prs)
                
                # Count issues from PRs
                for pr in prs:
                    issues = pr.get('closingIssuesReferences', {}).get('nodes', [])
                    all_data['summary']['issue_count'] += len(issues)
                
                all_data['commits'].append(commit_data)
        
        # Convert set to list for JSON serialization
        all_data['summary']['contributors'] = list(all_data['summary']['contributors'])
        
        # Save main data file
        main_file = Path(output_dir) / 'release_data.json'
        with open(main_file, 'w') as f:
            json.dump(all_data, f, indent=2, default=str)
        
        # Save individual commit files for easier analysis
        commits_dir = Path(output_dir) / 'commits'
        commits_dir.mkdir(exist_ok=True)
        
        for commit_data in all_data['commits']:
            if commit_data and commit_data.get('sha'):
                commit_file = commits_dir / f"{commit_data['sha'][:8]}.json"
                with open(commit_file, 'w') as f:
                    json.dump(commit_data, f, indent=2, default=str)
        
        # Create summary file
        summary_file = Path(output_dir) / 'summary.json'
        with open(summary_file, 'w') as f:
            json.dump(all_data['summary'], f, indent=2)
        
        # Create README for AI analysis
        readme_content = self._generate_readme(all_data)
        readme_file = Path(output_dir) / 'README.md'
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        print(f"\nData collection complete!")
        print(f"Output directory: {output_dir}")
        print(f"Total commits: {all_data['metadata']['total_commits']}")
        print(f"Contributors: {len(all_data['summary']['contributors'])}")
        print(f"Associated PRs: {all_data['summary']['pr_count']}")
        print(f"Related Issues: {all_data['summary']['issue_count']}")
        
        return all_data
    
    def _generate_readme(self, data: Dict) -> str:
        """Generate README for AI analysis"""
        contributors = ', '.join(data['summary']['contributors'])
        
        return f"""# Release Data for {data['metadata']['repository']}

## Overview
This directory contains comprehensive data for release notes generation since tag `{data['metadata']['since_tag']}`.

## Statistics
- **Total Commits**: {data['metadata']['total_commits']}
- **Contributors**: {len(data['summary']['contributors'])} ({contributors})
- **Associated Pull Requests**: {data['summary']['pr_count']}
- **Related Issues**: {data['summary']['issue_count']}
- **Generated**: {data['metadata']['generated_at']}

## File Structure
- `release_data.json` - Complete dataset with all commits, PRs, and issues
- `summary.json` - High-level statistics
- `commits/` - Individual commit files for detailed analysis
- `README.md` - This file

## Data Format
Each commit includes:
- Commit metadata (SHA, message, author, dates)
- Associated Pull Requests with labels and descriptions
- Closing Issues referenced by PRs
- Full text content for AI analysis

## Usage
This data is prepared for AI-powered analysis to:
1. Categorize changes (features, bug fixes, documentation, etc.)
2. Generate release notes
3. Identify breaking changes
4. Group related changes
5. Extract contributor acknowledgments
"""

def main():
    if len(sys.argv) != 5:
        print("Usage: python collect_release_data.py <repo_owner> <repo_name> <github_token> <since_tag>")
        print("Example: python collect_release_data.py spring-projects spring-boot $GITHUB_TOKEN v3.2.0")
        sys.exit(1)
    
    repo_owner, repo_name, github_token, since_tag = sys.argv[1:5]
    
    collector = GitHubReleaseCollector(repo_owner, repo_name, github_token)
    collector.collect_release_data(since_tag)

if __name__ == '__main__':
    main()
