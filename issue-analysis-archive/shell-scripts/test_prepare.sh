#!/bin/bash

# Test script to diagnose the hanging issue
echo "Testing issue processing..."

file="issues/raw/closed/batch_2025-07-16_14-13-50/issues_batch_001.json"

echo "File exists: $(test -f "$file" && echo "yes" || echo "no")"
echo "File size: $(wc -c < "$file") bytes"
echo "Issue count: $(jq '.issues | length' "$file")"
echo "First issue number: $(jq '.issues[0].number' "$file")"

echo "Testing comment processing..."
jq '.issues[0].comments // []' "$file" > /dev/null && echo "Comments OK" || echo "Comments failed"

echo "Testing author processing..."
jq '.issues[0].comments // [] | map(.author) | unique' "$file" > /dev/null && echo "Authors OK" || echo "Authors failed"

echo "Done"