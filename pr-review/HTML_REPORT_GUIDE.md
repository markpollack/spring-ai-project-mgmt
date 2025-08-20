# HTML Report Generation Guide

## Quick Start - Generate HTML Dashboard

To generate an interactive HTML dashboard for PR analysis:

```bash
# Analyze multiple PRs and generate dashboard
python3 batch_pr_workflow.py 4174 4164 4177 4166 4172

# Generate dashboard only (no analysis, uses existing data)
python3 batch_pr_workflow.py --report-only 4174 4164 4177 4166 4172
```

The HTML dashboard will be generated at:
`runs/run-{N}/pr_orchard_dashboard.html`

## Dashboard Features

### 🔍 Interactive Elements
- **View Assessments** - Detailed AI analysis in modal popup
- **Checkout & Merge** - Copy-paste commands for git operations  
- **View on GitHub** - Direct links to GitHub PRs
- **Filter by type** - Click summary cards to filter PRs

### 📊 PR Analysis Sections
- **📦 Backport Candidates** - PRs approved for 1.0.x backport
- **🍃 Easy Picks** - Low-risk, ready to merge
- **🌿 Requires Ladder** - Medium complexity 
- **🌲 Top Shelf** - High risk/complex PRs

### 🤖 AI Analysis Data
Each PR shows:
- Risk level assessment
- Problem summary 
- Backport recommendation
- Technical concerns
- Solution quality analysis
- Generated commit messages

## Single PR HTML Report

Generate individual PR report:
```bash
python3 enhanced_report_generator.py 4174
```

Output: `reports/review-pr-4174.html`

## Workflow Integration

The HTML dashboard is automatically generated after:
1. Context collection from GitHub
2. AI-powered analysis (risk, conversation, solution)
3. Backport assessment
4. Test discovery

## Browser Access

Open the generated file directly:
```bash
# Example path - adjust run number
file:///home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/runs/run-16/pr_orchard_dashboard.html
```

Or use the path shown in the script output.

## Troubleshooting

**Modal buttons not working?**
- Ensure you're using a recent dashboard (run-16+)
- Check browser console for JavaScript errors
- Try refreshing the page

**Missing PR data?**
- Run analysis first: `python3 batch_pr_workflow.py <pr_numbers>`
- Use `--report-only` only after analysis is complete

**Empty dashboard?**
- Verify PRs exist and have analysis data in `context/pr-{number}/`
- Check `state/pr-branch-mapping.json` for branch mapping