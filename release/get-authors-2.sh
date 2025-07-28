#!/bin/bash

REPO_PATH="/home/mark/projects/spring-ai"
OUTPUT_DIR="/home/mark/scripts/output-rc1"

cd "$REPO_PATH" || { echo "Failed to change to $REPO_PATH"; exit 1; }

# Get repository owner and name
REPO_INFO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
if [ -z "$REPO_INFO" ]; then
    echo "Failed to get repository info. Please ensure you're authenticated with 'gh auth login'"
    exit 1
fi

echo "Repository: $REPO_INFO"
echo "Getting commits since April 31, 2025..."

# Create fresh files with full paths
: > "$OUTPUT_DIR/contributors_raw.md"
: > "$OUTPUT_DIR/contributors_temp.md"
: > "$OUTPUT_DIR/contributors.md"

# Check file creation
for file in contributors_raw.md contributors_temp.md contributors.md; do
    if [ ! -f "$OUTPUT_DIR/$file" ]; then
        echo "Failed to create $file"
        exit 1
    fi
done

# Get all commit hashes and authors since the date
git log --since="2025-04-31" --format="%H|%aN|%aE" | while IFS='|' read -r commit name email; do
    commit_url="https://github.com/${REPO_INFO}/commit/${commit}"
    echo "Processing commit: ${commit:0:7} by $name ($commit_url)"
    
    # Use GitHub CLI to get additional info about the commit
    echo "  Fetching GitHub info for commit..."
    author_info=$(gh api "/repos/${REPO_INFO}/commits/${commit}" --jq '.author.login // .commit.author.email')
    
    if [[ $author_info == *"@"* ]]; then
        username=$(echo $author_info | sed 's/@.*$//')
        echo "  Extracted username from email: $username"
    else
        username=$author_info
        echo "  Got username directly: $username"
    fi
    
    # Save raw entry with commit
    printf -- "- %s (%s)\n  - [GitHub Profile](https://github.com/%s)\n  - [Commit](%s)\n" \
        "$name" "$username" "$username" "$commit_url" >> "$OUTPUT_DIR/contributors_raw.md"
    
    # Save deduplicated entry
    printf -- "- %s (%s)\n    - [GitHub Profile](https://github.com/%s)\n\n" \
       "$name" "$username" "$username" >> "$OUTPUT_DIR/contributors_temp.md"
    
    echo "----------------------------------------"
done

echo "Deduplicating entries..."
awk -v RS='\n\n' '{arr[$0]=1} END{for (i in arr) print i}' "$OUTPUT_DIR/contributors_temp.md" | sort > "$OUTPUT_DIR/contributors.md"

echo "Files created:"
ls -l "$OUTPUT_DIR"/contributors*.md

echo "Final deduplicated output:"
cat "$OUTPUT_DIR/contributors.md"
