# Java PR Review Implementation - Directory Structure

**Created**: 2025-10-16
**Purpose**: Keep Python and Java implementations completely separated

## Python Implementation (ORIGINAL - DO NOT MODIFY)
**Location**: `/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/`

```
pr-review/
├── context/           # PR context data and AI analysis cache
│   └── pr-3794/      # PRESERVE - existing data from August 8th
├── reports/          # Generated analysis reports
│   ├── review-pr-3794.md      # PRESERVE - original report
│   └── test-logs-pr-3794/     # PRESERVE - original test logs
├── spring-ai/        # Cloned Spring AI repository (managed by Python)
└── *.py              # All Python scripts
```

**Status**: Keep completely unchanged for demo tomorrow

---

## Java Implementation (NEW)
**Location**: `~/community/pr-samples/spring-ai-agents/`

### Workspace Structure
```
spring-ai-agents/
├── agents/pr-review-agent/          # Source code
│   ├── src/main/java/...
│   └── src/test/java/...
│
├── pr-review-workspace/             # Runtime workspace (NEW)
│   ├── context/                     # PR context and cache (Java version)
│   │   └── pr-XXXX/
│   │       ├── pr-data.json
│   │       ├── file-changes.json
│   │       ├── conversation.json
│   │       ├── ai-conversation-analysis.json
│   │       ├── ai-risk-assessment.json
│   │       ├── solution-assessment.json
│   │       └── backport-assessment.json
│   │
│   ├── reports/                     # Generated reports (Java version)
│   │   ├── review-pr-XXXX.md
│   │   ├── review-pr-XXXX.html
│   │   └── test-logs-pr-XXXX/
│   │
│   ├── spring-ai/                   # Cloned repository (Java version)
│   │   └── (managed by Java GitCommands)
│   │
│   ├── plans/                       # Workflow plans
│   │   └── enhanced-plan-pr-XXXX.md
│   │
│   └── logs/                        # Debug logs
│       ├── shell-commands.log
│       └── ai-interactions.log
│
└── jbang/
    └── pr-review.java               # JBang entry point
```

### Configuration
Default paths in Java implementation:

```java
public class WorkflowConfig {
    private Path workspaceRoot = Paths.get(System.getProperty("user.home"),
        "community/pr-samples/spring-ai-agents/pr-review-workspace");

    private Path contextDir = workspaceRoot.resolve("context");
    private Path reportsDir = workspaceRoot.resolve("reports");
    private Path springAiRepo = workspaceRoot.resolve("spring-ai");
    private Path plansDir = workspaceRoot.resolve("plans");
    private Path logsDir = workspaceRoot.resolve("logs");
}
```

### Benefits of Separation

1. **No Conflicts**: Python and Java never touch the same files
2. **Independent Testing**: Can run both implementations side-by-side
3. **Easy Comparison**: Compare outputs from same PR in different directories
4. **Safe Development**: Original Python data preserved for demo
5. **Clean Workspace**: Java starts fresh without Python artifacts

### Comparison Workflow

After Java implementation is complete:

```bash
# Run Python version (uses existing data)
cd /home/mark/project-mgmt/spring-ai-project-mgmt/pr-review
python3 pr_workflow.py --report-only 3794

# Run Java version (writes to new location)
cd ~/community/pr-samples/spring-ai-agents
jbang pr-review@spring-ai-community 3794

# Compare outputs
diff /home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/reports/review-pr-3794.md \
     ~/community/pr-samples/spring-ai-agents/pr-review-workspace/reports/review-pr-3794.md
```

### .gitignore Updates

Add to `~/community/pr-samples/spring-ai-agents/.gitignore`:
```
# PR Review workspace - runtime data only
pr-review-workspace/
```

This ensures workspace data is not committed to the repository.

---

**Note**: Python implementation at `/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/`
is FROZEN for comparison purposes. All new development happens in the Java workspace.
