# Spring AI PR Review Automation

Intelligent automation tools for reviewing Spring AI project pull requests with conflict resolution and AI assistance.

**⚡ Now powered by Python for maximum reliability and performance!**

## 🚀 Quick Start

```bash
# Complete PR review workflow (recommended) - NEW Python implementation
python3 pr_workflow.py 3386

# With automatic conflict resolution
python3 pr_workflow.py --auto-resolve 3386

# With force flag to overwrite existing branches
python3 pr_workflow.py --auto-resolve --force 3386

# Skip report generation (preparation only)
python3 pr_workflow.py --skip-report 3386

# Generate only the analysis report (assumes PR already prepared)
python3 pr_workflow.py --report-only 3386

# Or use the standalone report generator
python3 generate_report.py 3386

# Preview what would happen (dry run)
python3 pr_workflow.py --dry-run 3386
```

### Shell Wrapper (for compatibility)
```bash
# Use the shell wrapper for familiar interface
./review-workflow.py.sh --auto-resolve --force 3386
```

## 📁 Repository Structure

```
pr-review/
├── pr_workflow.py          # 🎯 MAIN ENTRY POINT - Complete Python workflow  
├── conflict_analyzer.py    # Python conflict analysis with Jinja2 templates
├── review-workflow.py.sh   # Shell wrapper for compatibility
├── templates/              # Jinja2 templates for conflict plans and prompts
│   ├── conflict-plan.md    # Main conflict resolution plan template  
│   └── claude-prompt.txt   # Claude Code prompt template
├── spring-ai/              # Local Spring AI repository (auto-created)
├── plans/                  # Generated conflict resolution plans
├── reports/                # Generated review reports (future)
├── prompt-pr-review.md     # PR review prompt template
│
├── pr-prepare.sh           # Legacy shell script (deprecated)
├── resolve-conflicts.sh    # Legacy conflict resolution (deprecated)
└── README.md              # This file
```

### 🆕 Python Implementation Benefits

- **✅ Zero syntax errors** - No more shell heredoc issues
- **🚀 Faster execution** - Native Python performance
- **🛡️ Robust error handling** - Proper exception management  
- **📊 Structured data** - Type-safe analysis with dataclasses
- **🎨 Professional templates** - Jinja2 template engine
- **💾 Smart caching** - Intelligent build caching system
- **📋 Automated reports** - AI-powered PR analysis with Claude Code integration
- **🔧 Easy maintenance** - Object-oriented, modular design

## 🛠️ Scripts Overview

### `review-workflow.sh` - 🎯 Main Entry Point

**This is the primary script you should use!** Combines the entire workflow:

1. **PR Preparation** - Checkout, compile, squash, rebase (via `pr-prepare.sh`)
2. **Conflict Resolution** - Automatic or AI-assisted resolution when needed
3. **Code Analysis** - Runs comprehensive PR review (via `run-review.sh`)
4. **Report Generation** - Creates detailed review report in `reports/`

```bash
# One command does it all
./review-workflow.sh 1234
```

### `pr-prepare.sh` - PR Preparation Component

Used by the workflow script to handle PR preparation:

1. **Repository Setup** - Ensures spring-ai repo exists and is updated
2. **PR Checkout** - Uses `gh pr checkout` to fetch the PR
3. **Compilation Check** - Runs fast build check with `mvnd`
4. **Commit Squashing** - Interactive rebase to squash multiple commits (optional)
5. **Upstream Rebase** - Rebases against upstream main with intelligent conflict handling

### `resolve-conflicts.sh` - Conflict Resolution Helper

Provides intelligent conflict resolution for PRs already checked out:

- **Conflict Analysis** - Categorizes conflicts by complexity and type
- **Auto-resolution** - Attempts to resolve simple conflicts automatically
- **AI Assistance** - Integrates with Claude Code for complex conflicts
- **Plan Generation** - Creates detailed resolution strategies

### `run-review.sh` - Code Analysis Component

Used by the workflow script to perform the actual PR analysis and generate reports.

## 📋 Usage Instructions

### Complete Workflow (Recommended)

```bash
# Full end-to-end PR review workflow
./review-workflow.sh 1234

# With automatic conflict resolution
./review-workflow.sh --auto-resolve 1234

# With AI assistance for complex conflicts  
./review-workflow.sh --call-claude 1234

# Preview what would happen
./review-workflow.sh --dry-run 1234

# Output review directly to terminal (no report file)
./review-workflow.sh --direct 1234
```

### Individual Components (Advanced)

If you need to run components separately:

```bash
# Just prepare the PR
./pr-prepare.sh 1234

# Just run analysis (PR must already be prepared)
./run-review.sh 1234

# Just handle conflicts (PR must be checked out)
./resolve-conflicts.sh --status 1234
```

### Conflict Resolution

When the main script encounters conflicts, you have several options:

#### Option 1: Automatic Resolution (Recommended for simple conflicts)
```bash
# Auto-resolve simple conflicts (docs, configs, build files)
./pr-prepare.sh --auto-resolve 1234
```

#### Option 2: AI-Assisted Resolution (Recommended for complex conflicts)
```bash
# Get Claude Code assistance for complex conflicts
./pr-prepare.sh --call-claude 1234
```

#### Option 3: Manual Resolution with Generated Plan
```bash
# Generate detailed resolution plan
./resolve-conflicts.sh --plan-only 1234

# View conflict status
./resolve-conflicts.sh --status 1234
```

### Working with Existing Conflicts

If you already have a PR checked out with conflicts:

```bash
# Show current conflict status
./resolve-conflicts.sh --status 1234

# Try automatic resolution
./resolve-conflicts.sh --auto 1234

# Get AI assistance
./resolve-conflicts.sh --claude 1234

# Generate resolution plan only
./resolve-conflicts.sh --plan-only 1234
```

## 🔧 Configuration

### Environment Setup

The scripts expect the following setup:

```bash
# Spring AI repository location (default: ~/spring-ai)
export SPRING_AI_DIR="$HOME/spring-ai"

# Your build alias should be available
alias fb='mvnd clean compile test-compile'  # or your preferred Maven command

# GitHub CLI should be authenticated
gh auth status
```

### Prerequisites

1. **GitHub CLI** - Authenticated and configured
   ```bash
   gh auth login
   gh repo set-default spring-projects/spring-ai
   ```

2. **Build Tools** - Either `fb` alias or Maven available
   ```bash
   # Verify your build command works
   fb  # or mvnd/mvnw/mvn
   
   # Spring AI uses Maven (preferred: mvnd for speed)
   mvnd clean compile test-compile
   # or
   ./mvnw clean compile test-compile
   ```

3. **Claude Code CLI** (optional, for AI assistance)
   ```bash
   # Install Claude Code CLI for AI-assisted conflict resolution
   # Visit: https://claude.ai/code
   ```

## 🎯 Script Options

### pr-prepare.sh Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--skip-squash` | Skip the commit squashing step |
| `--skip-compile` | Skip the compilation check |
| `--auto-resolve` | Attempt automatic conflict resolution |
| `--call-claude` | Call Claude Code for AI assistance |
| `--force` | Force operations (overwrite existing branches) |
| `--dry-run` | Show what would be done without executing |

### resolve-conflicts.sh Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--auto` | Attempt automatic conflict resolution |
| `--claude` | Call Claude Code for AI assistance |
| `--plan-only` | Generate/show conflict resolution plan only |
| `--status` | Show current conflict status |
| `--dry-run` | Show what would be done without executing |

## 🧠 Intelligent Conflict Resolution

### Conflict Classification

The system automatically categorizes conflicts:

- **🟡 Simple Conflicts** - Can be auto-resolved
  - Markdown documentation files
  - Properties/configuration files
  - Build files (pom.xml, build.gradle)
  - Version files

- **🔴 Complex Conflicts** - Need manual review
  - Java source code
  - Multiple conflict markers
  - Logic conflicts

### Auto-Resolution Strategies

For simple conflicts, the system applies intelligent strategies:

- **Markdown files**: Merges content logically, removes conflict markers
- **Properties files**: Takes newer values (upstream preferred)
- **Build files**: Takes upstream version to avoid dependency conflicts
- **Version files**: Uses newer version numbers

### Generated Plans

When conflicts occur, detailed plans are created in `plans/plan-pr-{NUMBER}.md`:

```markdown
# Conflict Resolution Plan for PR #1234

## Conflict Summary
- 🟡 Simple conflicts: 2 (can potentially auto-resolve)
- 🔴 Complex conflicts: 1 (need manual review)

## Recommended Actions
1. Auto-resolve simple conflicts
2. Get AI assistance for complex conflicts
3. Complete rebase

## Claude Code Integration
Specific commands to get AI assistance...
```

## 🌙 Overnight Batch Processing

Perfect for processing multiple PRs overnight:

```bash
#!/bin/bash
# Batch process multiple PRs
for pr in 1234 1235 1236; do
    echo "Processing PR #$pr..."
    ./pr-prepare.sh --auto-resolve "$pr" || {
        echo "PR #$pr needs manual review - plan generated"
        # Plan file created at plans/plan-pr-$pr.md
    }
done
```

## 🔍 Integration with PR Review

After PR preparation, use the generated environment:

```bash
# Environment is set up automatically
export PR_NUMBER=1234
cd ~/spring-ai

# Your PR review workflow continues here...
# The prompt-pr-review.md template can now be used
```

## 📝 Examples

### Example 1: Simple PR without conflicts
```bash
$ ./pr-prepare.sh 1234
[INFO] Setting up Spring AI repository...
[INFO] Checking out PR #1234...
[INFO] Running compilation check with 'fb' alias...
[INFO] Squashing commits...
[INFO] Rebasing against upstream/main...
[SUCCESS] PR #1234 is ready for review!
```

### Example 2: PR with simple conflicts (auto-resolved)
```bash
$ ./pr-prepare.sh --auto-resolve 1234
[INFO] Setting up Spring AI repository...
[INFO] Checking out PR #1234...
[INFO] Running compilation check with 'fb' alias...
[INFO] Rebasing against upstream/main...
[WARN] Rebase conflicts detected for PR #1234
[INFO] Attempting automatic resolution...
[SUCCESS] Some conflicts auto-resolved
[SUCCESS] Rebase completed successfully after auto-resolution
[SUCCESS] PR #1234 is ready for review!
```

### Example 3: PR with complex conflicts (plan generated)
```bash
$ ./pr-prepare.sh 1234
[INFO] Setting up Spring AI repository...
[INFO] Checking out PR #1234...
[INFO] Rebasing against upstream/main...
[WARN] Rebase conflicts detected for PR #1234
[ERROR] Rebase conflicts detected. Resolution options:

📋 Conflict resolution plan generated: plans/plan-pr-1234.md

Resolution options:
  1. Auto-resolve simple conflicts: ./pr-prepare.sh --auto-resolve 1234
  2. Get AI assistance: ./pr-prepare.sh --call-claude 1234
  3. Manual resolution:
     - Review plan file: plans/plan-pr-1234.md
     - Edit conflicted files manually
     - Run: git add <resolved-files> && git rebase --continue
```

## 🐛 Troubleshooting

### Common Issues

1. **GitHub CLI not authenticated**
   ```bash
   gh auth login
   gh auth status
   ```

2. **Spring AI repository not found**
   ```bash
   # The script will clone it automatically, or:
   git clone https://github.com/spring-projects/spring-ai.git ~/spring-ai
   ```

3. **Build command not found**
   ```bash
   # Make sure your 'fb' alias is set up, or use:
   ./pr-prepare.sh --skip-compile 1234
   ```

4. **Claude Code not available**
   ```bash
   # Install Claude Code CLI or use manual resolution
   # The script will generate detailed plans regardless
   ```

### Getting Help

```bash
# Show detailed help for any script
./pr-prepare.sh --help
./resolve-conflicts.sh --help

# Check conflict status
./resolve-conflicts.sh --status 1234

# Generate resolution plan
./resolve-conflicts.sh --plan-only 1234
```

## 🤝 Contributing

The scripts follow bash best practices:
- Strict mode (`set -Eeuo pipefail`)
- Comprehensive error handling
- Detailed logging with colors
- Dry-run support for testing
- Extensive help documentation

## 📚 Related Files

- `prompt-pr-review.md` - Detailed PR review prompt for AI analysis
- `../CLAUDE.md` - Parent project instructions and GitHub CLI commands
- `plans/` - Directory containing generated conflict resolution plans

---

*Part of the Spring AI Project Management toolkit*