# Generate Release Notes Script Implementation Plan v1.0

## 🔧 **DEBUGGING GITHUB API INTEGRATION IN PROGRESS**

**Status**: Core implementation completed - GitHub API debugging in progress  
**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/release/generate-release-notes.py`  
**Current Issue**: GitHub API returning 0 PRs and 0 issues for commit enrichment  
**Next Steps**: Manual testing and debugging of GraphQL queries required  

**Related Scripts Status**: 
- ✅ `update-start-spring-io.py` - Fork workflow, DCO compliance, precise BOM targeting
- ✅ `update-spring-website.py` - Array JSON handling, diff preview, direct repository access  

## Overview
Create a `generate-release-notes.py` script that leverages existing infrastructure to generate comprehensive GitHub-ready release notes with categorized PR and issue links.

## Key Architecture Decisions

### 1. **Claude Code CLI Integration**
- **Primary AI Analysis**: Use `ClaudeCodeWrapper` from `/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/claude_code_wrapper.py`
- **Proven Pattern**: Follow the same pattern as `ai_conversation_analyzer.py`, `ai_risk_assessor.py`, etc.
- **JSON Structured Output**: Use `analyze_from_file_with_json()` for reliable structured responses
- **Cost Control**: Default to `model="sonnet"` for cost-effective analysis

### 2. **Reuse Existing Components**
- **Git Operations**: Extract and enhance logic from `get-contributors.py`
- **Date/Version Resolution**: Reuse `determine_since_date()` and release detection logic
- **GitHub API**: Leverage existing `GitHubAPIHelper` pattern
- **Configuration Management**: Follow existing dataclass patterns

### 3. **Data Flow Strategy**
```
git commits → GitHub GraphQL enrichment → AI categorization → Markdown generation
     ↓                    ↓                        ↓                    ↓
 Commit SHAs        PR/Issue links         Categories/Priority    GitHub Release Notes
```

## Related: Release Process Scripts ✅ **COMPLETED**

### start.spring.io Update Requirements ✅ **COMPLETED**

#### Spring AI BOM Version Mapping
The `update-start-spring-io.py` script must target the specific Spring AI BOM mapping in `application.yml`:

```yaml
# Located around line 80 in start-site/src/main/resources/application.yml
spring-ai:
  groupId: org.springframework.ai
  artifactId: spring-ai-bom
  versionProperty: spring-ai.version
  mappings:
    - compatibilityRange: "[3.4.0,4.0.0-M1)"
      version: 1.0.0  # <-- This needs updating
```

**Key Requirements:**
- ✅ Target the specific `version:` field under the Spring AI BOM mappings section
- ✅ Preserve the YAML structure and indentation exactly
- ✅ Handle the large file size (~1000+ lines) efficiently
- ✅ Use precise regex patterns to avoid unintended changes
- ✅ Validate the compatibility range remains correct

### spring-website-content Update Requirements ✅ **COMPLETED & TESTED**

#### Spring AI Documentation JSON Updates
The `update-spring-website.py` script must update Spring AI project documentation at:

```json
# Located at project/spring-ai/documentation.json
[
  {
    "version": "1.1.0-SNAPSHOT",
    "status": "SNAPSHOT",
    "current": false,
    "api": "https://docs.spring.io/spring-ai/docs/1.1.0-SNAPSHOT/api/",
    "ref": "https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/index.html"
  },
  {
    "version": "1.0.0",  // <-- Update to new point release (e.g., 1.0.1)
    "status": "GENERAL_AVAILABILITY",
    "current": true,
    "api": "https://docs.spring.io/spring-ai/docs/1.0.0/api/",  // <-- Update version path
    "ref": "https://docs.spring.io/spring-ai/reference/1.0/index.html"  // <-- Unchanged (major.minor)
  }
]
```

**Key Requirements:**
- ✅ **COMPLETED** - Find GENERAL_AVAILABILITY entry with `"current": true`
- ✅ **COMPLETED** - Update version field to new point release
- ✅ **COMPLETED** - Update API documentation URL to reference new version
- ✅ **COMPLETED** - Keep reference documentation URL at major.minor level
- ✅ **COMPLETED** - Add DCO sign-off support for commits  
- ✅ **COMPLETED** - Direct repository access (no fork needed)
- ✅ **COMPLETED** - Add testing and debugging options
- ✅ **COMPLETED** - Enhanced diff preview showing ALL changes with context

## Implementation Architecture

### Core Classes

#### 1. **ReleaseNotesConfig** (Configuration Management)
```python
@dataclass
class ReleaseNotesConfig:
    # Repository settings (from get-contributors.py pattern)
    repo_owner: str = "spring-projects"
    repo_name: str = "spring-ai"
    repo_path: Path = Path("/home/mark/projects/spring-ai")
    
    # Version/date settings (reuse get-contributors.py logic)
    since_version: Optional[str] = None
    since_date: Optional[str] = None
    target_version: Optional[str] = None
    
    # AI analysis settings (follow claude_code_wrapper pattern)
    ai_model: str = "sonnet"  # Cost control
    ai_timeout: int = 300
    claude_logs_dir: Path = Path("./logs")
    
    # Output settings
    output_file: Path = Path("RELEASE_NOTES.md")
    include_stats: bool = True
    include_contributors: bool = True
    group_related_changes: bool = True
    dry_run: bool = False
```

#### 2. **GitCommitCollector** (Extracted from get-contributors.py)
```python
class GitCommitCollector:
    def __init__(self, config: ReleaseNotesConfig):
        self.config = config
        self.github = GitHubAPIHelper(f"{config.repo_owner}/{config.repo_name}")
    
    def determine_since_date(self) -> Optional[str]:
        # Reuse exact logic from get-contributors.py lines 206-250
        
    def collect_commits_with_metadata(self) -> List[CommitData]:
        # Enhanced version of get-contributors.py git log logic
        # Returns structured commit data with basic metadata
```

#### 3. **GitHubDataEnricher** (New - GraphQL Integration)
```python
class GitHubDataEnricher:
    def __init__(self, config: ReleaseNotesConfig):
        self.config = config
        self.github = GitHubAPIHelper(f"{config.repo_owner}/{config.repo_name}")
    
    def enrich_commits_with_prs_and_issues(self, commits: List[CommitData]) -> List[EnrichedCommit]:
        # GraphQL batch queries to get PR and issue associations
        # Returns commits with PR/issue links, labels, etc.
    
    def create_linking_strategy(self, enriched_commit: EnrichedCommit) -> LinkInfo:
        # Primary: Link to PR if available
        # Fallback: Link to commit
        # Handle multiple PRs, reverts, etc.
```

#### 4. **ReleaseNotesAIAnalyzer** (Claude Code Integration)
```python
class ReleaseNotesAIAnalyzer:
    def __init__(self, config: ReleaseNotesConfig):
        self.config = config
        self.claude = ClaudeCodeWrapper(logs_dir=config.claude_logs_dir)
    
    def analyze_changes(self, enriched_commits: List[EnrichedCommit]) -> AnalysisResult:
        # Generate comprehensive prompt with all commit/PR/issue data
        # Use claude.analyze_from_file_with_json() for structured output
        # Follow pattern from ai_conversation_analyzer.py:297
        
        prompt_content = self._generate_analysis_prompt(enriched_commits)
        result = self.claude.analyze_from_file_with_json(
            prompt_file_path=self._create_prompt_file(prompt_content),
            timeout=self.config.ai_timeout,
            model=self.config.ai_model,
            show_progress=True
        )
        
        return self._parse_analysis_result(result)
```

#### 5. **ReleaseNotesGenerator** (Markdown Output)
```python
class ReleaseNotesGenerator:
    def __init__(self, config: ReleaseNotesConfig):
        self.config = config
    
    def generate_markdown(self, analysis: AnalysisResult, contributors: List[Contributor]) -> str:
        # Generate GitHub-flavored markdown
        # Include proper PR/issue linking
        # Add contributor acknowledgments (reuse get-contributors.py logic)
        # Include statistics and metrics
```

### AI Analysis Integration

#### Prompt Template Strategy
Following the pattern from `ai_analysis_prompt.md` but adapted for release notes:

```markdown
# Release Notes Analysis Prompt

## Context
I have collected comprehensive data about all commits, pull requests, and issues for Spring AI release since [VERSION]. 

## Data Structure
[Structured JSON with commits, PRs, issues, labels, etc.]

## Analysis Task
Analyze this data and categorize changes into:
- ✨ New Features
- 🐛 Bug Fixes  
- 💥 Breaking Changes (critical)
- 📚 Documentation
- ⚡ Performance
- 🔧 Internal Changes
- 🔐 Security
- ♿ Accessibility

## Required Output Format
```json
{
  "highlights": "2-3 sentence summary",
  "breaking_changes": [...],
  "features": [...],
  "bug_fixes": [...],
  // etc.
}
```

## Spring AI Specific Considerations
- Highlight new starters, auto-configurations
- Note dependency updates (especially OpenAI, Azure)
- Identify configuration property changes
- Call out vector database integrations
- Note chat model provider changes
```

#### Claude Code Integration Pattern
```python
# Follow exact pattern from existing scripts
def analyze_with_claude(self, commits_data: str) -> Dict[str, Any]:
    prompt_file = self._create_analysis_prompt_file(commits_data)
    
    result = self.claude.analyze_from_file_with_json(
        prompt_file_path=str(prompt_file),
        timeout=300,
        model="sonnet",  # Cost control
        show_progress=True
    )
    
    if not result['success']:
        raise ReleaseNotesError(f"AI analysis failed: {result['error']}")
    
    return result['json_data']
```

## Data Structures

### Core Data Types
```python
@dataclass
class CommitData:
    sha: str
    message: str
    author: str
    date: str
    
@dataclass  
class PullRequest:
    number: int
    title: str
    url: str
    labels: List[str]
    closing_issues: List[int]
    
@dataclass
class EnrichedCommit:
    commit: CommitData
    prs: List[PullRequest]
    primary_link: str  # PR URL or commit URL
    category_hints: List[str]  # from labels
    
@dataclass
class CategorizedChange:
    title: str
    description: str
    link_text: str  # e.g., "(#123 via #456, #789)"
    category: str
    breaking: bool
    impact: str
```

## Command Line Interface

```bash
# Basic usage - auto-detect since last release
python3 generate-release-notes.py

# Specific version range  
python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1

# Custom output
python3 generate-release-notes.py --output RELEASE_NOTES_v1.0.1.md

# Skip AI analysis (use rule-based categorization)
python3 generate-release-notes.py --no-ai

# Dry run mode
python3 generate-release-notes.py --dry-run --verbose

# Include raw debug data
python3 generate-release-notes.py --include-debug-data
```

## Implementation Phases

### Phase 1: Foundation ✅ **COMPLETED**
1. ✅ **Extract reusable components from get-contributors.py**:
   - ✅ `determine_since_date()` logic
   - ✅ `GitHubAPIHelper` enhancements  
   - ✅ Configuration and CLI patterns

2. ✅ **Create core data structures**:
   - ✅ `CommitData`, `EnrichedCommit`, `CategorizedChange`
   - ✅ `ReleaseNotesConfig` with proper defaults

3. ✅ **Basic commit collection workflow**:
   - ✅ Reuse git log logic
   - ✅ Basic GitHub API integration for PR associations

### Phase 2: GitHub Integration ✅ **COMPLETED**
1. ✅ **Enhanced GitHub API client**:
   - ✅ GraphQL queries for commit → PR → issue mapping
   - ✅ Batch processing for efficiency
   - ✅ Rate limiting (reuse existing patterns)

2. ✅ **Data enrichment pipeline**:
   - ✅ Associate commits with PRs
   - ✅ Extract labels, milestones, closing issues
   - ✅ Build linking strategy (PR preferred, commit fallback)

### Phase 3: Claude Code AI Integration ✅ **COMPLETED**
1. ✅ **AI analysis framework**:
   - ✅ Follow `ai_conversation_analyzer.py` pattern exactly
   - ✅ Use `ClaudeCodeWrapper.analyze_from_file_with_json()`
   - ✅ Implement robust JSON parsing with fallbacks

2. ✅ **Prompt engineering**:
   - ✅ Adapt `ai_analysis_prompt.md` for release notes
   - ✅ Spring AI specific context and categories
   - ✅ Structured JSON output format

3. ✅ **Fallback categorization**:
   - ✅ Rule-based system using labels and keywords
   - ✅ When AI analysis fails or --no-ai flag used

### Phase 4: Output Generation ✅ **COMPLETED**
1. ✅ **Markdown generation**:
   - ✅ GitHub-compatible format
   - ✅ Proper linking with fallback strategy
   - ✅ Template-based approach

2. ✅ **Integration features**:
   - ✅ Contributor acknowledgments (reuse get-contributors.py)
   - ✅ Statistics generation
   - ✅ Debug data inclusion option

## Expected Output Format

```markdown
# Spring AI 1.0.1 Release Notes

## 🎯 Highlights
This release focuses on OpenAI integration improvements and vector store enhancements, with 23 changes from 15 contributors including 3 new features and 12 bug fixes.

## 💥 Breaking Changes
- Updated OpenAI client to v4.0 requiring configuration changes (#234 via #225)

## ✨ New Features  
- Add Claude-3 integration with Anthropic provider (#240 via #235, #238)
- New Pinecone vector store implementation (#245)
- Enhanced prompt template system with variables (#251 via #249)

## 🐛 Bug Fixes
- Fix memory leak in embedding cache (#244 via #241) 
- Resolve thread safety issues in chat client (#248 via #246, #247)
- Correct Azure OpenAI endpoint handling (#252 via #250)

## 📚 Documentation
- Updated getting started guide with Claude examples (#255)
- API documentation improvements for vector stores (#258 via #253)

## 🙏 Contributors
Thanks to all contributors who made this release possible:
[Auto-generated from get-contributors.py logic]

## 📈 Statistics
- 45 commits from 15 contributors
- 18 pull requests merged  
- 25 issues resolved
```

## Integration with Existing Infrastructure

### File Locations
- **Main script**: `/home/mark/project-mgmt/spring-ai-project-mgmt/release/generate-release-notes.py`
- **Plan document**: `/home/mark/project-mgmt/spring-ai-project-mgmt/release/plans/generate-release-notes-plan-v1.0.md`
- **Reuse**: `/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/claude_code_wrapper.py`
- **Extract from**: `/home/mark/project-mgmt/spring-ai-project-mgmt/release/get-contributors.py`

### Dependencies
- **Existing**: `claude_code_wrapper.py`, components from `get-contributors.py`
- **New**: Enhanced GraphQL GitHub integration
- **Libraries**: pathlib, dataclasses, typing, json, subprocess (already used)

### Success Criteria
1. ✅ **COMPLETED** - Reuses existing `ClaudeCodeWrapper` integration pattern
2. ✅ **COMPLETED** - Extracts and enhances logic from `get-contributors.py`  
3. ✅ **COMPLETED** - Automatically detects commits since last release
4. ✅ **COMPLETED** - Links changes to PRs (preferred) or commits (fallback)
5. ✅ **COMPLETED** - Uses AI analysis for intelligent categorization
6. ✅ **COMPLETED** - Generates professional GitHub-compatible markdown
7. ✅ **COMPLETED** - Includes contributor acknowledgments
8. ✅ **COMPLETED** - Handles Spring AI project conventions
9. ✅ **COMPLETED** - Provides comprehensive CLI options
10. ✅ **COMPLETED** - Supports both automated and manual workflows

This plan leverages the proven `ClaudeCodeWrapper` pattern while building on the solid foundation of `get-contributors.py` for a robust, maintainable release notes generation system.

## ⚠️ **CRITICAL ALGORITHM FIX - Tag-Based Collection**

### **Problem Identified**: Date-Based Collection is Unreliable
- **Issue**: Date-based filtering (`--since=2024-01-01`) is imprecise and can miss commits
- **Root Cause**: Commits can have different author dates vs commit dates, timezone issues
- **Evidence**: Should find 160 commits between v1.0.0..v1.0.1, but was finding inconsistent counts with date filtering
- **Solution**: **REMOVED** all date-based collection - now **tag-only**

### **Corrected Algorithm**: Tag-to-Tag Collection
```bash
# CORRECT: Use tag-to-tag commit range
git log v1.0.0..v1.0.1 --format=%H|%s|%aN|%aE|%aI

# VERIFICATION: Count should match
git rev-list --count v1.0.0..v1.0.1  # Should return 160
```

### **Why Tag-Based Is Accurate**:
1. **Exact Commit Range**: Collects commits between specific release points
2. **No Date Ambiguity**: Uses actual commit history, not timestamps
3. **Release Process Aligned**: Tags contain the actual release commits
4. **Branch Independent**: Works regardless of maintenance branch state

### **Implementation Changes Required**:
1. **Simplify commit collection**: Remove complex date/commit-hash lookup
2. **Consistent approach**: Make both get-contributors.py and generate-release-notes.py use same logic
3. **Add testing flags**: `--count-only` for verification without AI costs
4. **Tag validation**: Ensure tags exist before attempting collection

### **Testing Strategy** (Tag-Only):
```bash
# 1. COUNT VERIFICATION: Verify correct commit collection (no costs)
python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1 --count-only
# Expected output: "Found 160 commits (matches expected count)"

# 2. SMALL BATCH AI TESTING: Test AI categorization on first 5 commits only  
python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1 --limit 5 --skip-github --verbose
# Costs: ~$0.01-0.02 for 5 commits

# 3. RANDOM SAMPLING: Test AI on random sample of 10 commits
python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1 --sample 10 --skip-github
# Costs: ~$0.02-0.04 for 10 commits

# 4. GITHUB API TESTING: Test with real PR/issue data on small batch
python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1 --limit 3 --verbose
# Costs: ~$0.01 for 3 commits + minimal GitHub API usage

# 5. FULL RUN: Only after iterative testing confirms accuracy
python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1
# Costs: ~$0.10-0.15 for all 160 commits
```

### **Iterative Development Flags**:
- **`--count-only`**: Verify commit collection without any processing
- **`--limit N`**: Process only first N commits (chronological order)
- **`--sample N`**: Randomly select N commits for testing
- **`--skip-github`**: Skip GitHub API calls, test AI categorization only
- **`--no-ai`**: Skip AI analysis, test everything else
- **`--save-ai-input`**: Save AI prompt input to logs for debugging
- **`--logs-dir PATH`**: Custom directory for debug logs (default: ./logs/release-notes)
- **`--verbose`**: Show detailed logging for debugging

### **🔍 Debugging and Verification Strategy**:

#### **1. Verify AI Input Content**
```bash
# Save AI input for inspection to verify PR/issue data is included  
python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1 --limit 3 --save-ai-input --verbose

# Check the saved input file
ls -la ./logs/release-notes/ai_input_*.md
cat ./logs/release-notes/ai_input_20250107_143022.md
```

**What to verify in AI input**:
- ✅ Commit messages and metadata
- ✅ PR titles, descriptions, and discussion content
- ✅ Issue titles, descriptions, and comments
- ✅ GitHub labels and milestones
- ✅ Author information and contribution context

#### **2. Cost Tracking and Management**
```bash
# All runs automatically track costs and save to logs
python3 generate-release-notes.py --limit 5 --skip-github
# Output: 💰 AI Analysis cost: $0.0234
# Saves to: ./logs/release-notes/costs_20250107_143022.txt

# Grand total calculation across multiple runs
cat ./logs/release-notes/costs_*.txt | grep "TOTAL COST" | awk '{sum+=$3} END {print "Grand Total: $" sum}'
```

**Cost tracking features**:
- ✅ Real-time cost display during execution
- ✅ Automatic cost file saving with timestamps
- ✅ Cost breakdown by operation type
- ✅ Commit count per operation for cost-per-commit analysis
- ✅ Grand total calculation across multiple test runs

#### **3. Logging Directory Structure**
```
./logs/release-notes/
├── claude/                          # Claude Code CLI logs (automatic)
│   ├── prompt_20250107_143022.md     # Raw prompts sent to Claude
│   └── response_20250107_143022.json # Raw responses from Claude
├── ai_input_20250107_143022.md       # Human-readable AI input (--save-ai-input)
├── costs_20250107_143022.txt         # Cost tracking report
└── debug.log                         # General debug logging
```

#### **4. Progressive Development Workflow** (Tag-Only)
```bash
# Step 1: Verify 160 commits with PR/issue enrichment (FREE)
python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1 --count-only

# Step 2: Check AI input quality on 2 commits (~$0.005)
python3 generate-release-notes.py --since-version 1.0.0 --limit 2 --save-ai-input --verbose
# Inspect: ./logs/release-notes/ai_input_*.md

# Step 3: Test AI categorization on 5 commits (~$0.015)  
python3 generate-release-notes.py --since-version 1.0.0 --limit 5 --skip-github
# Check output quality and adjust prompts if needed

# Step 4: Test full GitHub enrichment on 3 commits (~$0.010)
python3 generate-release-notes.py --since-version 1.0.0 --limit 3 --verbose
# Verify PR/issue data is properly included in AI input

# Step 5: Random sampling for variety (~$0.020)
python3 generate-release-notes.py --since-version 1.0.0 --sample 8 --save-ai-input
# Test different types of commits (features, bugs, docs, etc.)

# Step 6: Calculate total development costs
cat ./logs/release-notes/costs_*.txt | grep "TOTAL COST"

# Step 7: Full production run (~$0.150)
python3 generate-release-notes.py --since-version 1.0.0 --target-version 1.0.1
```

#### **5. Verification Checklist**
Before full production run, verify:
- [ ] **Commit Collection**: Exactly 160 commits found
- [ ] **GitHub Enrichment**: PR titles, descriptions, and issue links present
- [ ] **AI Input Quality**: Saved input contains rich PR/issue discussion context
- [ ] **Categorization Accuracy**: AI properly categorizes different commit types
- [ ] **Cost Tracking**: All test runs tracked, total development cost < $0.10
- [ ] **Output Format**: Markdown generates correctly with proper PR/issue linking

## Technical Implementation Notes

### Claude Code Integration Best Practices
Based on analysis of existing scripts in `/pr-review/`:

1. **Import Pattern**:
```python
from claude_code_wrapper import ClaudeCodeWrapper
```

2. **Initialization**:
```python
claude = ClaudeCodeWrapper(logs_dir=Path("./logs"))
```

3. **Analysis Pattern**:
```python
result = claude.analyze_from_file_with_json(
    prompt_file_path=str(prompt_file),
    timeout=300,
    model="sonnet",  # Cost control
    show_progress=True
)

if result['success']:
    analysis_data = result['json_data']
else:
    handle_error(result['error'])
```

4. **Error Handling**:
- Always check `result['success']` 
- Log errors with `result['error']` and `result['stderr']`
- Provide fallback mechanisms when AI analysis fails

5. **File Management**:
- Use `logs_dir` for prompt files and responses
- Files are automatically preserved for debugging
- Use descriptive prompt file names with timestamps

### GitHub API Integration
Reuse patterns from `get-contributors.py`:

1. **Authentication**: Use `gh` CLI authentication
2. **Rate Limiting**: Follow existing delay patterns
3. **Error Handling**: Graceful fallbacks for API failures
4. **GraphQL Queries**: Batch operations for efficiency

### Output Quality Assurance
1. **Linking Strategy**: Always prefer PR links over commit links
2. **Duplicate Detection**: Group related commits/PRs
3. **Category Accuracy**: Use both AI and rule-based validation
4. **Format Consistency**: Follow established Spring project conventions