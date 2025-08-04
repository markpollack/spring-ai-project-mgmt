# Spring AI PR Review Automation

Comprehensive AI-powered automation for reviewing Spring AI project pull requests with intelligent conflict resolution, compilation error fixing, and detailed analysis reporting.

## 🚀 Quick Start - High Level Commands

### Complete PR Review Workflow (Most Common)
```bash
# Full end-to-end PR review with all features
python3 pr_workflow.py 3386

# Clean workspace first, then run full workflow
python3 pr_workflow.py --cleanup 3386 && python3 pr_workflow.py 3386
```

### Individual Workflow Components
```bash
# Generate comprehensive reports only (assumes PR already prepared)
python3 pr_workflow.py --report-only 3386

# Run tests only (assumes PR already prepared) 
python3 pr_workflow.py --test-only 3386

# Generate workflow plan only (smart analysis & progress tracking)
python3 pr_workflow.py --plan-only 3386

# Clean up all generated files and repositories
python3 pr_workflow.py --cleanup 3386

# Granular cleanup control
python3 pr_workflow.py --cleanup 3386 --cleanup-mode light  # Keep spring-ai repo, delete PR branch
python3 pr_workflow.py --cleanup 3386 --cleanup-mode full   # Remove everything

# Preview what would happen without executing
python3 pr_workflow.py --dry-run 3386
```

#### Plan-Only Mode: Smart Pre-Analysis

The `--plan-only` mode is a lightweight analysis tool that generates an intelligent workflow plan without executing any changes:

**What it does:**
- 🔍 **Smart Analysis**: Detects compilation errors, merge conflicts, and potential issues
- 📋 **Progress Tracking**: Creates a detailed checklist plan in `/plans/enhanced-plan-pr-XXXX.md`
- ⚡ **Fast Execution**: Completes in seconds (no compilation, testing, or heavy operations)
- 🎯 **Issue Preview**: Shows exactly what problems need to be addressed before full workflow

**When to use:**
- **Before full workflow**: Preview what issues exist and estimate time needed
- **After cleanup**: Verify PR branch is properly set up (as demonstrated in cleanup testing)
- **Troubleshooting**: Quick check of current PR state without making changes
- **Planning**: Understand scope and complexity before committing to full workflow

**Example output location:** `/plans/enhanced-plan-pr-3914.md`

**Perfect for:**
- Quick PR assessment and planning
- Validating clean workspace state after cleanup
- Understanding workflow requirements before execution
- Team coordination and issue prioritization

### Workflow Step Control Options
```bash
# Skip individual steps if needed
python3 pr_workflow.py --skip-squash 3386           # Skip commit squashing
python3 pr_workflow.py --skip-compile 3386          # Skip compilation check
python3 pr_workflow.py --skip-tests 3386            # Skip test execution
python3 pr_workflow.py --skip-docs 3386             # Skip Antora documentation build
python3 pr_workflow.py --skip-report 3386           # Skip report generation
python3 pr_workflow.py --skip-commit-message 3386   # Skip AI-powered commit message generation

# Conflict resolution control
python3 pr_workflow.py --no-auto-resolve 3386       # Disable automatic conflict resolution

# Force operations
python3 pr_workflow.py --force 3386                 # Force overwrite existing branches
```

## 📋 What This Solution Provides

The Spring AI PR Review system provides a **complete automated workflow** for efficiently reviewing pull requests with AI assistance. It transforms a complex, error-prone manual process into a reliable, comprehensive automated analysis.

### 🎯 Core Value Proposition

**Before**: Manual PR review required multiple complex steps, frequent conflicts, manual error resolution, and inconsistent analysis quality.

**After**: Single command provides complete PR preparation, intelligent conflict resolution, automated compilation fixes, comprehensive testing, professional AI-generated commit messages, and professional-grade AI-powered analysis reports.

## 🔄 Complete Workflow Overview

### Visual Workflow Diagram

```
🚀 START: python3 pr_workflow.py 3386
    │
    ▼
┌─ Check Prerequisites ─────────────────────┐
│  • GitHub CLI authenticated              │
│  • Claude Code CLI available             │
│  • Maven/Java environment ready          │
└───────────────────────────────────────────┘
    │
    ▼
📁 PHASE 1: Repository Setup & PR Preparation
    │
    ├─► Clone/Update spring-ai repository
    ├─► Fetch PR branch via GitHub CLI  
    ├─► Create clean isolated PR branch
    └─► Validate PR state and structure
    │
    ▼
🔧 PHASE 2: Initial Compilation & Error Fixing
    │
    ├─► Run initial Maven compilation check
    │
    ├─ Compilation errors found? ────┐
    │                                ▼
    │                           🤖 AI-powered compilation fixing
    │                           │   (Claude Code + templates)
    │                           ├─► Detect error types (type mismatch, etc.)
    │                           ├─► Apply template-based fixes
    │                           ├─► Add type casts, fix imports
    │                           └─► Iterative resolution (up to 3 attempts)
    │                                │
    │                                ├─ More errors? ─┐
    │                                │                ▼
    │                                │            (Loop back)
    │                                │                │
    └─ Clean compilation ◄───────────┴────────────────┘
    │
    ├─► Run Java formatter on modified files
    ├─► Commit compilation fixes if any were applied
    └─► Validate clean build state
    │
    ▼
📝 PHASE 3: Intelligent Commit Management
    │
    ├─► Analyze existing commit structure
    ├─► 🤖 AI-powered intelligent squashing
    ├─► 🤖 Generate professional commit message (Claude Code)
    └─► Prepare for upstream integration
    │
    ▼
⚡ PHASE 4: Conflict Resolution & Integration
    │
    ├─► Rebase against upstream main branch
    │
    ├─ Merge conflicts detected? ────┐
    │                                ▼
    │                           🤖 AI conflict resolution
    │                           │   (Claude Code analysis)
    │                           ├─► Apply semantic fixes
    │                           └─► Verify resolution
    │                                │
    └─ No conflicts ◄────────────────┘
    │
    ▼
🔧 PHASE 5: Post-Rebase Compilation Check
    │
    ├─► Run Maven compilation after rebase
    │
    ├─ New compilation errors from rebase? ──┐
    │                                        ▼
    │                                   🤖 AI-powered error fixing
    │                                   │   (Claude Code templates)
    │                                   ├─► Handle API conflicts from upstream
    │                                   ├─► Fix dependency version issues
    │                                   └─► Apply rebase-specific fixes
    │                                        │
    │                                        ├─ More errors? ─┐
    │                                        │                ▼
    │                                        │            (Loop back)
    │                                        │                │
    └─ Clean post-rebase compilation ◄───────┴────────────────┘
    │
    ├─► Run Java formatter on any new fixes
    └─► Commit post-rebase fixes if needed
    │
    ▼
🧪 PHASE 6: Comprehensive Testing
    │
    ├─► Discover tests affected by PR changes
    ├─► Execute modular Maven test suites
    ├─► Handle container-based tests (Ollama, etc.)
    ├─► Collect detailed test results and logs
    └─► Generate test execution summary
    │
    ▼
📊 PHASE 7: AI Analysis & Report Generation
    │
    ├─► Collect comprehensive PR context & metadata
    ├─► 🤖 AI conversation analysis (Claude Code)
    │    └─► Analyze GitHub discussions & requirements
    ├─► 🤖 Technical solution assessment (Claude Code)  
    │    └─► Evaluate architecture impact & patterns
    ├─► 🤖 Security & quality risk analysis (Claude Code)
    │    └─► Identify risks & breaking changes
    └─► Generate comprehensive markdown report
    │
    ▼
✅ WORKFLOW COMPLETE
    │
    ├─► Professional analysis report: /reports/review-pr-XXXX.md
    ├─► Detailed test logs: /reports/test-logs-pr-XXXX/
    ├─► PR ready for review with clean state
    └─► All conflicts resolved, compilation clean, tests executed

═══════════════════════════════════════════════════════════════════

🤖 AI INTEGRATION POINTS (Claude Code):
┌────────────────────────────────────────────────────────────────┐
│  1. Initial compilation error fixing (Phase 2)               │
│  2. Professional commit message generation (Phase 3)         │
│  3. Intelligent merge conflict resolution (Phase 4)          │  
│  4. Post-rebase compilation fixes (Phase 5)                  │
│  5. GitHub conversation & requirement analysis (Phase 7)     │
│  6. Technical solution assessment & risk analysis (Phase 7)  │
└────────────────────────────────────────────────────────────────┘

🔄 ITERATIVE LOOPS:
• Compilation errors: Fixed until clean build achieved
• Conflict resolution: Continues until all conflicts resolved  
• Testing: Retries failed tests with different strategies

⚠️  ERROR HANDLING:
• Prerequisites missing → Exit with guidance
• Merge conflicts → AI resolution → Manual fallback if needed
• Compilation errors → AI fixing → Template-based repair
• Test failures → Detailed logging → Continue with warnings
```

### Detailed Step-by-Step Process

When you run `python3 pr_workflow.py 3386`, here's what happens automatically:

### Phase 1: Repository Setup & PR Preparation
1. **Repository Management**: Clones/updates Spring AI repository in isolated workspace
2. **PR Checkout**: Uses GitHub CLI to fetch the specific PR branch
3. **Branch Management**: Creates clean PR branch with proper upstream tracking
4. **Initial Validation**: Ensures PR is in valid state for processing

### Phase 2: Intelligent Commit Management  
1. **Commit Analysis**: Analyzes PR commit structure and history
2. **Intelligent Squashing**: Automatically squashes multiple commits into clean single commit
3. **AI-Powered Commit Messages**: Uses Claude Code AI to generate comprehensive, professional commit messages based on PR context, changes, and discussions
4. **Conflict-Aware Rebase**: Rebases against latest upstream with intelligent conflict detection

### Phase 3: AI-Powered Conflict Resolution
1. **Conflict Detection**: Identifies and categorizes merge conflicts by complexity
2. **Claude Code Integration**: Uses Claude Code AI for intelligent conflict resolution
   - Analyzes conflict context and intent
   - Applies semantic understanding to resolve conflicts
   - Maintains code integrity and functionality
3. **Verification**: Ensures all conflicts are properly resolved and code compiles

### Phase 4: Compilation Error Resolution
1. **Compilation Validation**: Runs full compilation check before proceeding
2. **Error Detection**: Identifies compilation errors and issues
3. **AI-Powered Fixes**: Uses Claude Code to automatically fix compilation errors
   - Understands Java/Spring patterns and conventions
   - Fixes method signature issues, import problems, API changes
   - Maintains code quality and Spring Framework best practices
4. **Iterative Resolution**: Repeats fix cycle up to 3 times until clean compilation

### Phase 5: Comprehensive Testing
1. **Test Discovery**: Identifies all tests affected by PR changes
2. **Modular Execution**: Runs tests by Maven module for efficient execution
3. **Container Management**: Handles Docker container tests (like Ollama) appropriately
4. **Result Collection**: Captures detailed test results, logs, and failure analysis
5. **Performance Tracking**: Records execution times and success rates

### Phase 6: AI-Powered Analysis & Reporting
1. **Context Collection**: Gathers comprehensive PR metadata, issue discussions, and code changes
2. **AI Conversation Analysis**: Analyzes GitHub issue discussions and PR conversations to understand:
   - Problem being solved and requirements
   - Design decisions and stakeholder feedback  
   - Outstanding concerns and risks
3. **Solution Assessment**: AI evaluates the technical solution for:
   - Architecture impact and breaking changes
   - Implementation quality and patterns
   - Testing adequacy and coverage
4. **Report Generation**: Creates comprehensive AI-powered analysis report with:
   - Full conversation insights and problem understanding
   - Technical solution assessment and risk analysis  
   - Code quality analysis with recommendations
   - Strategic recommendations and action items

## 📊 Generated Outputs

### Reports Directory Structure
```
reports/
├── review-pr-3386.md              # Comprehensive AI-powered analysis report
└── test-logs-pr-3386/            # Detailed test execution logs and results
    ├── test-summary.md            # Test execution summary
    └── *.log                      # Individual test execution logs
```

### Report Contents

**AI-Powered Analysis Report includes**:
- 🎯 **Problem & Solution Overview**: AI-generated summary of what the PR solves
- 📝 **Issue Context Analysis**: Understanding from GitHub discussions and requirements
- 🔍 **Solution Assessment**: Technical analysis of implementation approach
- ⚠️ **Risk Assessment**: Identified concerns and mitigation strategies  
- 🧪 **Test Results**: Comprehensive test execution analysis with success/failure details
- 💡 **Recommendations**: Prioritized action items and improvement suggestions
- 📊 **Technical Metrics**: Complexity scores, file analysis, and quality indicators

## 🧠 AI Integration Features

### Claude Code AI Capabilities
- **Intelligent Conflict Resolution**: Understands code context and intent for semantic conflict resolution
- **Compilation Error Fixing**: Automatically fixes Java/Spring compilation issues with proper API usage
- **Professional Commit Messages**: Generates comprehensive commit messages that explain the "why" and "what" of changes
- **Conversation Analysis**: Analyzes GitHub discussions to understand requirements and concerns
- **Solution Assessment**: Evaluates technical approach, architecture impact, and implementation quality
- **Risk Analysis**: Identifies potential issues, breaking changes, and integration concerns
- **Progress Animations**: Real-time visual feedback during long-running AI operations (13-15+ seconds)

### Smart Automation
- **Context-Aware Processing**: Understands Spring AI project patterns and conventions
- **Iterative Problem Solving**: Continues fixing issues until resolution or maximum attempts
- **Quality Preservation**: Maintains code quality while making automated fixes
- **Learning Integration**: Improves based on project-specific patterns and requirements

### Progress Animation System
Long-running AI operations now include visual progress indicators to show the system is actively working:

```
⠋ 🧠 Claude Code analyzing... 7.3s
⠙ 🧠 Claude Code analyzing... 7.8s  
⠹ 🧠 Claude Code analyzing... 8.3s
```

**Features**:
- Professional Braille spinner animation with real-time elapsed time
- Appears during all major AI analysis operations (risk assessment, solution analysis, etc.)
- Thread-safe implementation that doesn't interfere with Claude Code processing
- Configurable and can be disabled if needed

**Benefits**:
- No more wondering if the system is frozen during long AI operations
- Visual confirmation that complex analysis is progressing
- Professional appearance with Unicode-based animations

### AI Failure Tracking & Debugging
The system now includes comprehensive debugging capabilities for AI analysis issues:

**AI Failure Tracker** (`ai_failure_tracker.py`):
- Tracks and categorizes AI component failures during batch processing
- Provides detailed debugging recommendations for common issues
- Generates failure analysis reports to identify patterns and root causes

**Claude Code Wrapper Test Suite** (`test_claude_code_wrapper.py`):
- Comprehensive test suite for systematic Claude Code integration debugging
- Tests availability, simple prompts, JSON output, file reading, and complex scenarios
- Reproduces and isolates specific "Execution error" issues

**Enhanced Error Handling**:
- Improved CompilationErrorResolver with semicolon error patterns and Claude Code integration
- Better JSON parsing from Claude Code markdown responses
- File-based prompt handling to avoid temporary file issues in debugging

## 🔧 Prerequisites

1. **GitHub CLI**: Authenticated with Spring AI repository access
   ```bash
   gh auth login
   gh repo set-default spring-projects/spring-ai
   ```

2. **Claude Code CLI**: For AI-powered analysis and conflict resolution
   ```bash
   # Install from https://claude.ai/code
   claude --version
   ```

3. **Maven Daemon (mvnd)**: For fast compilation and testing
   ```bash
   # Install mvnd for optimal performance
   mvnd --version
   ```

4. **Java 17+**: Required for Spring AI compilation

## 📁 Project Structure

```
pr-review/
├── pr_workflow.py                 # 🎯 Main workflow orchestrator
├── enhanced_report_generator.py   # AI-powered report generation
├── commit_message_generator.py    # AI-powered commit message generation
├── conflict_analyzer.py           # Conflict detection and analysis
├── compilation_error_resolver.py  # AI-powered compilation fixing
├── intelligent_squash.py          # Smart commit squashing
├── templates/                     # Report and prompt templates
├── context/                       # PR context data and analysis cache
├── reports/                       # Generated analysis reports  
├── plans/                         # Workflow plans and progress tracking
└── spring-ai/                     # Isolated Spring AI repository workspace
```

## 🎯 Use Cases

### Daily PR Review Workflow
- **Spring AI Maintainers**: Complete automated PR analysis with professional reports
- **Feature Review**: Comprehensive analysis of new feature implementations  
- **Bug Fix Validation**: Automated testing and impact analysis of fixes
- **Breaking Change Assessment**: AI-powered analysis of API changes and compatibility

### Batch Processing
```bash
# Basic batch processing (recommended)
python3 batch_pr_workflow.py 3386 3387 3388

# Batch processing with options
python3 batch_pr_workflow.py --dry-run 3386 3387 3388           # Preview what would happen
python3 batch_pr_workflow.py --report-only 3386 3387 3388       # Generate reports only
python3 batch_pr_workflow.py --no-cleanup 3386 3387 3388        # Skip cleanup between PRs
python3 batch_pr_workflow.py --stop-on-error 3386 3387 3388     # Stop on first error
python3 batch_pr_workflow.py --force-reprocess 3386 3387 3388   # Force reprocessing existing reports
python3 batch_pr_workflow.py --open-browser 3386 3387 3388      # Auto-open HTML dashboard
python3 batch_pr_workflow.py --from-scratch 3386 3387 3388      # Fresh start - remove all data first

# Manual batch processing (alternative approach)
for pr in 3386 3387 3388; do
    python3 pr_workflow.py --cleanup $pr
    python3 pr_workflow.py $pr
done
```

### Integration with Review Process
- Generate comprehensive reports for technical leadership review
- Provide AI insights for complex architectural decisions
- Automate repetitive conflict resolution and testing tasks
- Maintain consistent analysis quality across all PRs

## 🚀 Getting Started

1. **Clone and Setup**:
   ```bash
   git clone https://github.com/markpollack/spring-ai-project-mgmt.git
   cd spring-ai-project-mgmt/pr-review
   ```

2. **Install Dependencies**:
   ```bash
   # Ensure GitHub CLI and Claude Code are installed
   gh auth status
   claude --version
   ```

3. **Run Your First PR Analysis**:
   ```bash
   # Complete analysis of PR 3386
   python3 pr_workflow.py 3386
   ```

4. **Review Generated Report**:
   ```bash
   # Check comprehensive AI-powered analysis report
   cat reports/review-pr-3386.md
   ```

## 🛠️ Troubleshooting

### AI Analysis Issues

**Problem**: AI assessments show "Manual assessment required due to AI parsing failure"
**Solution**: Use report-only mode to regenerate AI analysis:
```bash
python3 pr_workflow.py --report-only 3386
```

**Problem**: Claude Code returns "Execution error"
**Solution**: Run the diagnostic test suite:
```bash
python3 test_claude_code_wrapper.py
```

### Batch Processing Issues

**Problem**: Dashboard shows fewer PRs than processed
**Solution**: This was fixed in recent updates. Context data is now preserved during batch processing.

**Problem**: Compilation errors not being auto-fixed
**Solution**: The CompilationErrorResolver now includes enhanced patterns for common errors like missing semicolons. Re-run the workflow:
```bash
python3 pr_workflow.py --cleanup 3386 && python3 pr_workflow.py 3386
```

### Debug Information

All AI prompts and responses are saved to the `logs/` directory for debugging:
- `claude-prompt-*.txt` - Prompts sent to Claude Code
- `claude-response-*.txt` - Raw responses from Claude Code
- Debug logs include token estimation and performance metrics

### Cleanup Modes

The system supports two cleanup modes for different use cases:

#### Light Mode (Default)
```bash
python3 pr_workflow.py --cleanup 3914
# OR explicitly:
python3 pr_workflow.py --cleanup 3914 --cleanup-mode light
```

**What it cleans:**
- ✅ Switches back to `main` branch from PR branch
- ✅ **Deletes the PR branch** for fresh state
- ✅ Discards any uncommitted changes
- ✅ Removes generated reports, logs, and context files

**What it preserves:**
- ✅ Keeps the `spring-ai/` repository directory intact
- ✅ Preserves git history and remote configuration
- ✅ Maintains repository for efficient re-use

#### Full Mode (Complete Reset)
```bash
python3 pr_workflow.py --cleanup 3914 --cleanup-mode full
```

**What it does:**
- 🗑️ Completely removes the entire `spring-ai/` directory
- 🗑️ Forces fresh clone on next workflow run
- 🗑️ Use when troubleshooting repository issues

**Benefits of Light Mode:**
- **Faster subsequent runs** - No need to re-clone repository
- **Bandwidth savings** - Repository already available locally
- **Fresh PR state** - PR branch deleted and re-fetched cleanly
- **Efficient** - Optimal balance of cleanliness and performance

## 🔧 Individual Component Scripts

While most users will use the main workflows, you can also run individual components directly:

### Enhanced Report Generation
```bash
# Generate comprehensive AI-powered report for a PR
python3 enhanced_report_generator.py 3386

# Force fresh analysis (ignore cached assessments)
python3 enhanced_report_generator.py --force-fresh 3386

# Specify custom directories
python3 enhanced_report_generator.py 3386 --context-dir /path/to/context --reports-dir /path/to/reports
```

### AI Assessment Scripts
```bash
# Individual AI assessments (useful for debugging)
python3 ai_conversation_analyzer.py 3386      # Analyze PR conversations and requirements
python3 ai_risk_assessor.py 3386             # Security and quality risk assessment  
python3 backport_assessor.py 3386            # Backport candidate evaluation
python3 solution_assessor.py 3386            # Technical solution analysis
python3 commit_message_generator.py 3386     # AI-powered commit message generation
```

### Utility Scripts
```bash
# Intelligent commit squashing
python3 intelligent_squash.py 3386           # Analyze and squash commits automatically
python3 intelligent_squash.py --dry-run 3386 # Preview squash operations

# Test the Claude Code integration
python3 test_claude_code_wrapper.py          # Comprehensive integration testing
```

### Running with Custom Directories
Most AI assessment scripts support custom directory routing for batch processing:
```bash
python3 backport_assessor.py 3386 --context-dir /path/to/context --logs-dir /path/to/logs
python3 ai_conversation_analyzer.py 3386 --context-dir /path/to/context --logs-dir /path/to/logs
```

---

*This tool transforms Spring AI PR review from a complex manual process into an intelligent, automated workflow that provides insights comparable to senior engineer analysis.*