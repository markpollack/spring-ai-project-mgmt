# Full PR Review System Port to Java - Implementation Plan

**Date**: 2025-10-16
**Status**: Ready for Implementation
**Target**: ~/community/pr-samples/spring-ai-agents

## Executive Summary

Port the comprehensive Python PR review system (~21,787 lines) to Java using Spring AI Agents framework. The Java implementation will use shell command execution (zt-exec) for all external tools (gh, git, maven) to maintain proven CLI tooling behavior. The system will be deployable as a JBang script for easy execution.

**Key Decision**: Keep shell-based execution architecture using zt-exec library
- No Java GitHub API, no JGit - use proven CLI tools
- Direct port of Python subprocess patterns
- Simpler dependencies and maintenance

---

## Phase 1: Repository Setup & Structure Planning

### 1.1 New Working Directory Setup

```bash
# Create new working directory (separate from ~/community/spring-ai-agents)
mkdir -p ~/community/pr-samples
cd ~/community/pr-samples

# Clone spring-ai-agents repository
git clone https://github.com/spring-ai-community/spring-ai-agents.git
cd spring-ai-agents

# Create feature branch
git checkout -b feature/pr-review-automation
```

### 1.2 Module Architecture (Core Feature with JBang)

```
spring-ai-agents/
├── spring-ai-agents-pr-review/          # Core PR review module
│   ├── pom.xml
│   └── src/main/java/
│       └── org/springaicommunity/agents/pr/
│           ├── PrReviewAgent.java                    # Main orchestrator
│           ├── workflow/
│           │   ├── PrWorkflowExecutor.java          # 7-phase orchestration
│           │   ├── PhaseExecutor.java               # Base phase interface
│           │   ├── WorkflowContext.java             # Shared state
│           │   └── WorkflowConfig.java              # Configuration
│           ├── shell/
│           │   ├── ShellExecutor.java               # zt-exec wrapper
│           │   ├── GitCommands.java                 # Git command builder
│           │   ├── GhCommands.java                  # GitHub CLI commands
│           │   └── MavenCommands.java               # Maven commands
│           ├── phases/
│           │   ├── Phase1_RepositorySetup.java
│           │   ├── Phase2_Compilation.java
│           │   ├── Phase3_CommitManagement.java
│           │   ├── Phase4_ConflictResolution.java
│           │   ├── Phase5_Testing.java
│           │   ├── Phase6_AIAnalysis.java
│           │   └── Phase7_ReportGeneration.java
│           ├── analysis/
│           │   ├── ConversationAnalyzer.java       # AI conversation analysis
│           │   ├── RiskAssessor.java               # Security/quality risks
│           │   ├── SolutionAssessor.java           # Technical assessment
│           │   └── BackportAssessor.java           # Maintenance branch eval
│           ├── compilation/
│           │   ├── CompilationErrorResolver.java   # AI error fixing
│           │   ├── ErrorPatternMatcher.java
│           │   └── JavaFormatter.java
│           ├── conflict/
│           │   ├── ConflictDetector.java
│           │   └── ConflictResolver.java           # AI conflict resolution
│           ├── testing/
│           │   ├── TestDiscoveryEngine.java        # Find affected tests
│           │   ├── TestExecutor.java               # Maven test runner
│           │   └── TestResultCollector.java
│           ├── commit/
│           │   ├── CommitSquasher.java             # Intelligent squashing
│           │   └── CommitMessageGenerator.java     # AI-powered messages
│           ├── github/
│           │   ├── PrContextCollector.java         # PR metadata via gh
│           │   └── IssueDataCollector.java         # Issue data via gh
│           ├── report/
│           │   ├── ReportGenerator.java            # Markdown reports
│           │   ├── HtmlDashboardGenerator.java     # Interactive HTML
│           │   └── templates/                      # Mustache templates
│           └── util/
│               ├── JsonParser.java                 # JSON handling
│               ├── FileUtils.java
│               └── ProgressIndicator.java          # Braille spinner
│
├── spring-ai-agents-pr-review-cli/      # JBang executable module
│   ├── pom.xml
│   └── src/main/java/
│       └── org/springaicommunity/agents/pr/cli/
│           ├── PrReviewCli.java                    # Main JBang entry point
│           ├── CliOptions.java                     # Picocli configuration
│           ├── PrReviewCommand.java                # Main command
│           └── BatchPrReviewCommand.java           # Batch processing
│
└── jbang/
    ├── pr-review.java                   # JBang script (like coverage-agent.java)
    └── batch-pr-review.java             # Batch processing script
```

---

## Phase 2: Core Shell Execution Infrastructure

### 2.1 Shell Executor with zt-exec

**Purpose**: Unified shell command execution
**Library**: `org.zeroturnaround:zt-exec:1.12`

```java
@Component
public class ShellExecutor {

    public ProcessResult execute(String... command) {
        return execute(null, command);
    }

    public ProcessResult execute(Path workingDir, String... command) {
        try {
            ProcessExecutor executor = new ProcessExecutor()
                .command(command)
                .readOutput(true);

            if (workingDir != null) {
                executor.directory(workingDir.toFile());
            }

            ProcessResult result = executor.execute();
            return result;

        } catch (Exception e) {
            throw new ShellExecutionException(
                "Command failed: " + String.join(" ", command), e);
        }
    }

    public String executeForOutput(Path workingDir, String... command) {
        ProcessResult result = execute(workingDir, command);
        return result.outputUTF8();
    }
}
```

### 2.2 Git Command Wrapper

**Purpose**: All git operations via shell
**Replaces**: Python subprocess git calls

```java
@Component
public class GitCommands {

    private final ShellExecutor shell;
    private final Path repoPath;

    public void clone(String repoUrl, Path destination) {
        shell.execute("git", "clone", repoUrl, destination.toString());
    }

    public void checkout(String branch) {
        shell.execute(repoPath, "git", "checkout", branch);
    }

    public void fetch(String remote, String prRef, String localBranch) {
        shell.execute(repoPath, "git", "fetch", remote,
            prRef + ":" + localBranch);
    }

    public void rebase(String upstream) {
        shell.execute(repoPath, "git", "rebase", upstream);
    }

    public String status() {
        return shell.executeForOutput(repoPath, "git", "status");
    }

    public List<String> conflictedFiles() {
        String output = shell.executeForOutput(repoPath,
            "git", "diff", "--name-only", "--diff-filter=U");
        return Arrays.asList(output.split("\n"));
    }

    public String diff(String... args) {
        List<String> command = new ArrayList<>();
        command.add("git");
        command.add("diff");
        command.addAll(Arrays.asList(args));
        return shell.executeForOutput(repoPath,
            command.toArray(new String[0]));
    }
}
```

### 2.3 GitHub CLI Wrapper

**Purpose**: All GitHub API calls via gh CLI
**Replaces**: Python subprocess gh calls

```java
@Component
public class GhCommands {

    private final ShellExecutor shell;

    public JsonNode getPrData(int prNumber) {
        String json = shell.executeForOutput(null,
            "gh", "pr", "view", String.valueOf(prNumber),
            "--repo", "spring-projects/spring-ai",
            "--json", "title,body,author,state,labels,additions,deletions,changedFiles");
        return parseJson(json);
    }

    public JsonNode getFileChanges(int prNumber) {
        String json = shell.executeForOutput(null,
            "gh", "api",
            "/repos/spring-projects/spring-ai/pulls/" + prNumber + "/files");
        return parseJson(json);
    }

    public JsonNode getConversation(int prNumber) {
        String json = shell.executeForOutput(null,
            "gh", "api",
            "/repos/spring-projects/spring-ai/issues/" + prNumber + "/comments");
        return parseJson(json);
    }

    public JsonNode getLinkedIssues(int prNumber) {
        // Extract issue numbers from PR body and fetch each
        // Implementation similar to Python pr_context_collector.py
    }
}
```

### 2.4 Maven Command Wrapper

**Purpose**: Maven compilation and test execution
**Replaces**: Python subprocess maven calls

```java
@Component
public class MavenCommands {

    private final ShellExecutor shell;
    private final Path projectPath;

    public CompilationResult compile() {
        try {
            ProcessResult result = shell.execute(projectPath,
                "./mvnw", "clean", "compile",
                "-Dmaven.javadoc.skip=true", "-DskipTests");
            return CompilationResult.success();
        } catch (ShellExecutionException e) {
            return CompilationResult.failure(parseErrors(e.getOutput()));
        }
    }

    public TestResult runTests(String module) {
        ProcessResult result = shell.execute(projectPath,
            "./mvnw", "test",
            "-pl", module,
            "-Dmaven.test.failure.ignore=true");
        return parseTestResults(result);
    }

    public void format(List<Path> files) {
        shell.execute(projectPath,
            "./mvnw", "spring-javaformat:apply",
            "-Dformat.files=" + joinPaths(files));
    }
}
```

---

## Phase 3: Workflow Phase Implementation

### 3.1 Phase Executor Interface

```java
public interface PhaseExecutor {
    String getPhaseName();
    PhaseResult execute(WorkflowContext context, WorkflowConfig config);
    boolean shouldExecute(WorkflowConfig config);
}
```

### 3.2 Phase 1: Repository Setup

**Python Source**: Lines 1-300 of pr_workflow.py
**Purpose**: Clone/update repo, checkout PR branch

```java
@Component
public class Phase1_RepositorySetup implements PhaseExecutor {

    private final GitCommands git;
    private final GhCommands gh;

    @Override
    public PhaseResult execute(WorkflowContext context, WorkflowConfig config) {
        log.info("Phase 1: Repository Setup & PR Preparation");

        // Clone or update repository
        Path repoPath = ensureRepository();
        context.setRepoPath(repoPath);

        // Fetch PR branch via gh
        fetchPrBranch(context.getPrNumber());

        // Create clean PR branch
        git.checkout("-b", "pr-" + context.getPrNumber());

        // Validate PR state
        validatePrState(context);

        return PhaseResult.success("Repository setup complete");
    }
}
```

### 3.3 Phase 2: Compilation & Error Fixing

**Python Source**: compilation_error_resolver.py (1,000 lines)
**Purpose**: Compile code, use AI to fix errors

```java
@Component
public class Phase2_Compilation implements PhaseExecutor {

    private final MavenCommands maven;
    private final CompilationErrorResolver errorResolver;
    private final JavaFormatter formatter;
    private final GitCommands git;

    @Override
    public PhaseResult execute(WorkflowContext context, WorkflowConfig config) {
        log.info("Phase 2: Compilation & Error Fixing");

        // Initial compilation attempt
        CompilationResult result = maven.compile();

        if (result.hasErrors()) {
            log.info("Compilation errors found, attempting AI resolution...");

            // AI-powered error fixing (up to 3 attempts)
            for (int attempt = 1; attempt <= 3 && result.hasErrors(); attempt++) {
                result = errorResolver.resolveErrors(context.getRepoPath(),
                    result.getErrors());

                if (result.isFixed()) {
                    // Format and commit fixes
                    formatter.format(result.getModifiedFiles());
                    git.add(result.getModifiedFiles());
                    git.commit("Fix compilation errors (AI-assisted)");
                }
            }
        }

        context.setCompilationResult(result);
        return result.hasErrors()
            ? PhaseResult.failure("Compilation errors remain")
            : PhaseResult.success("Compilation successful");
    }
}
```

### 3.4 Phase 3: Commit Management

**Python Source**: intelligent_squash.py (800 lines)
**Purpose**: Squash commits, generate AI commit messages

```java
@Component
public class Phase3_CommitManagement implements PhaseExecutor {

    private final CommitSquasher squasher;
    private final CommitMessageGenerator messageGenerator;
    private final GitCommands git;

    @Override
    public PhaseResult execute(WorkflowContext context, WorkflowConfig config) {
        log.info("Phase 3: Intelligent Commit Management");

        // Analyze commit structure
        CommitAnalysis analysis = squasher.analyzeCommits(context.getRepoPath());

        // Intelligent squashing
        if (analysis.shouldSquash()) {
            squasher.squashCommits(context.getRepoPath());
        }

        // AI-powered commit message generation
        if (!config.isSkipCommitMessage()) {
            String commitMessage = messageGenerator.generate(
                context.getPrContext(), context.getChangedFiles());
            git.commitAmend(commitMessage);
        }

        return PhaseResult.success("Commit management complete");
    }
}
```

### 3.5 Phase 4: Conflict Resolution

**Python Source**: conflict_analyzer.py (500 lines)
**Purpose**: Rebase and resolve conflicts with AI

```java
@Component
public class Phase4_ConflictResolution implements PhaseExecutor {

    private final GitCommands git;
    private final ConflictResolver conflictResolver;
    private final AgentClient agentClient;

    @Override
    public PhaseResult execute(WorkflowContext context, WorkflowConfig config) {
        log.info("Phase 4: Conflict Resolution & Integration");

        // Rebase against main
        try {
            git.rebase("origin/main");
            return PhaseResult.success("Clean rebase");
        } catch (RebaseConflictException e) {

            if (!config.isAutoResolveConflicts()) {
                return PhaseResult.failure("Merge conflicts detected - manual resolution required");
            }

            // AI-powered conflict resolution
            List<String> conflictedFiles = git.conflictedFiles();
            ConflictResolution resolution = conflictResolver.resolve(
                conflictedFiles, agentClient);

            if (resolution.isResolved()) {
                git.add(conflictedFiles);
                git.rebaseContinue();
                return PhaseResult.success("Conflicts resolved via AI");
            } else {
                return PhaseResult.failure("Could not resolve conflicts automatically");
            }
        }
    }
}
```

### 3.6 Phase 5: Testing

**Python Source**: test_discovery.py (500 lines)
**Purpose**: Discover and run affected tests

```java
@Component
public class Phase5_Testing implements PhaseExecutor {

    private final TestDiscoveryEngine discovery;
    private final MavenCommands maven;
    private final TestResultCollector collector;

    @Override
    public PhaseResult execute(WorkflowContext context, WorkflowConfig config) {
        log.info("Phase 5: Comprehensive Testing");

        // Discover affected tests
        List<String> modules = discovery.findAffectedModules(
            context.getChangedFiles());

        log.info("Running tests for {} modules", modules.size());

        List<TestResult> results = new ArrayList<>();
        for (String module : modules) {
            TestResult result = maven.runTests(module);
            results.add(result);

            log.info("  {} - {} tests, {} failures",
                module, result.getTestCount(), result.getFailureCount());
        }

        TestSummary summary = collector.aggregate(results);
        context.setTestResults(summary);

        return PhaseResult.success("Testing complete: " + summary.toString());
    }
}
```

### 3.7 Phase 6: AI Analysis

**Python Source**:
- ai_conversation_analyzer.py (600 lines)
- ai_risk_assessor.py (1,200 lines)
- solution_assessor.py (2,000 lines)
- backport_assessor.py (900 lines)

```java
@Component
public class Phase6_AIAnalysis implements PhaseExecutor {

    private final PrContextCollector contextCollector;
    private final ConversationAnalyzer conversationAnalyzer;
    private final RiskAssessor riskAssessor;
    private final SolutionAssessor solutionAssessor;
    private final BackportAssessor backportAssessor;
    private final AgentClient agentClient;

    @Override
    public PhaseResult execute(WorkflowContext context, WorkflowConfig config) {
        log.info("Phase 6: AI Analysis & Assessment");

        // Collect comprehensive PR context
        PrContext prContext = contextCollector.collect(context.getPrNumber());
        context.setPrContext(prContext);

        // Run AI analyses
        AnalysisResults results = new AnalysisResults();

        results.setConversation(
            conversationAnalyzer.analyze(prContext, agentClient));

        results.setRisk(
            riskAssessor.assess(prContext, agentClient));

        results.setSolution(
            solutionAssessor.assess(prContext, agentClient));

        if (!config.isSkipBackport()) {
            results.setBackport(
                backportAssessor.assess(prContext, agentClient));
        }

        context.setAnalysisResults(results);
        return PhaseResult.success("AI analysis complete");
    }
}
```

### 3.8 Phase 7: Report Generation

**Python Source**:
- enhanced_report_generator.py (1,800 lines)
- html_report_generator.py (3,300 lines)

```java
@Component
public class Phase7_ReportGeneration implements PhaseExecutor {

    private final ReportGenerator reportGenerator;
    private final HtmlDashboardGenerator htmlGenerator;

    @Override
    public PhaseResult execute(WorkflowContext context, WorkflowConfig config) {
        log.info("Phase 7: Report Generation");

        // Generate Markdown report
        Path reportPath = reportGenerator.generate(
            context.getPrContext(),
            context.getAnalysisResults(),
            context.getTestResults());

        log.info("Markdown report: {}", reportPath);

        // Generate HTML dashboard if enabled
        if (config.isGenerateHtml()) {
            Path htmlPath = htmlGenerator.generate(
                context.getPrContext(),
                context.getAnalysisResults(),
                context.getTestResults());

            log.info("HTML dashboard: {}", htmlPath);

            if (config.isOpenBrowser()) {
                openInBrowser(htmlPath);
            }
        }

        return PhaseResult.success("Reports generated");
    }
}
```

---

## Phase 4: JBang Script Implementation

### 4.1 Main JBang Script

**File**: `jbang/pr-review.java`

```java
///usr/bin/env jbang "$0" "$@" ; exit $?
//DEPS org.springaicommunity.agents:spring-ai-agents-pr-review-cli:0.1.0-SNAPSHOT
//DEPS info.picocli:picocli:4.7.6
//DEPS org.slf4j:slf4j-simple:2.0.9

import org.springaicommunity.agents.pr.cli.PrReviewCli;

/**
 * AI-powered PR review automation for Spring AI project.
 *
 * Usage examples:
 *   jbang pr-review@spring-ai-community 3794
 *   jbang pr-review@spring-ai-community --report-only 3794
 *   jbang pr-review@spring-ai-community --cleanup 3794
 *   jbang pr-review@spring-ai-community --skip-tests 3794
 */
public class pr_review {
    public static void main(String[] args) {
        System.exit(PrReviewCli.execute(args));
    }
}
```

### 4.2 CLI Command Structure with Picocli

```java
@Command(name = "pr-review",
         mixinStandardHelpOptions = true,
         version = "1.0",
         description = "AI-powered PR review automation for Spring AI")
public class PrReviewCommand implements Callable<Integer> {

    @Parameters(description = "PR number to review")
    private int prNumber;

    // Workflow Mode Options
    @Option(names = "--report-only", description = "Generate report only (skip workflow)")
    private boolean reportOnly = false;

    @Option(names = "--test-only", description = "Run tests only")
    private boolean testOnly = false;

    @Option(names = "--plan-only", description = "Generate workflow plan only")
    private boolean planOnly = false;

    @Option(names = "--cleanup", description = "Cleanup workspace")
    private boolean cleanup = false;

    @Option(names = "--cleanup-mode", description = "Cleanup mode: light (default) or full")
    private String cleanupMode = "light";

    // Step Control Options
    @Option(names = "--skip-squash", description = "Skip commit squashing")
    private boolean skipSquash = false;

    @Option(names = "--skip-compile", description = "Skip compilation check")
    private boolean skipCompile = false;

    @Option(names = "--skip-tests", description = "Skip test execution")
    private boolean skipTests = false;

    @Option(names = "--skip-report", description = "Skip report generation")
    private boolean skipReport = false;

    @Option(names = "--skip-backport", description = "Skip backport assessment")
    private boolean skipBackport = false;

    // Report Options
    @Option(names = "--html", defaultValue = "true", description = "Generate HTML report")
    private boolean html;

    @Option(names = "--no-html", description = "Skip HTML report generation")
    private boolean noHtml = false;

    @Option(names = "--html-only", description = "Generate HTML report only")
    private boolean htmlOnly = false;

    @Option(names = "--open-browser", description = "Auto-open HTML in browser")
    private boolean openBrowser = false;

    // Advanced Options
    @Option(names = "--force", description = "Force overwrite existing branches")
    private boolean force = false;

    @Option(names = "--force-fresh", description = "Force fresh AI analysis (ignore cache)")
    private boolean forceFresh = false;

    @Option(names = "--dry-run", description = "Preview actions without executing")
    private boolean dryRun = false;

    @Option(names = "--resume-after-compile", description = "Resume after manual compilation fixes")
    private boolean resumeAfterCompile = false;

    @Option(names = "--no-auto-resolve", description = "Disable automatic conflict resolution")
    private boolean noAutoResolve = false;

    @Override
    public Integer call() throws Exception {
        // Build configuration from options
        WorkflowConfig config = WorkflowConfig.builder()
            .reportOnly(reportOnly)
            .testOnly(testOnly)
            .planOnly(planOnly)
            .skipSquash(skipSquash)
            .skipCompile(skipCompile)
            .skipTests(skipTests)
            .skipReport(skipReport)
            .skipBackport(skipBackport)
            .generateHtml(!noHtml && (html || htmlOnly))
            .openBrowser(openBrowser)
            .force(force)
            .forceFresh(forceFresh)
            .dryRun(dryRun)
            .autoResolveConflicts(!noAutoResolve)
            .build();

        // Create and execute workflow
        PrReviewAgent agent = PrReviewAgent.create();

        if (cleanup) {
            agent.cleanup(prNumber, cleanupMode);
            return 0;
        }

        WorkflowResult result = agent.execute(prNumber, config);

        return result.isSuccess() ? 0 : 1;
    }
}
```

---

## Phase 5: AI Integration with AgentClient

### 5.1 Compilation Error Resolver

```java
@Component
public class CompilationErrorResolver {

    private final AgentClient agentClient;
    private final TemplateEngine templateEngine;

    public CompilationResult resolveErrors(Path projectPath,
                                          List<CompilationError> errors) {
        // Build goal from template
        String goal = templateEngine.render("compilation_error_prompt.md",
            Map.of("errors", errors, "projectPath", projectPath));

        // Execute with AgentClient
        AgentClientResponse response = agentClient.goal(goal).run();

        if (!response.isSuccessful()) {
            return CompilationResult.failure(errors);
        }

        // Re-compile to verify
        return verifyFixes(projectPath);
    }
}
```

### 5.2 Risk Assessor

```java
@Component
public class RiskAssessor {

    private final AgentClient agentClient;
    private final TemplateEngine templateEngine;

    public RiskAssessment assess(PrContext context, AgentClient client) {
        // Render prompt template
        String goal = templateEngine.render("ai_risk_assessment_prompt.md",
            Map.of(
                "prNumber", context.getPrNumber(),
                "prTitle", context.getTitle(),
                "fileChanges", context.getFileChanges(),
                "totalFilesChanged", context.getFileChanges().size()
            ));

        // Execute analysis
        AgentClientResponse response = client.goal(goal).run();

        // Parse JSON response
        return parseRiskAssessment(response.getResult());
    }

    private RiskAssessment parseRiskAssessment(String result) {
        // Extract JSON from markdown code blocks
        String json = extractJsonFromMarkdown(result);
        return objectMapper.readValue(json, RiskAssessment.class);
    }
}
```

---

## Phase 6: Batch Processing

### 6.1 Batch JBang Script

**File**: `jbang/batch-pr-review.java`

```java
///usr/bin/env jbang "$0" "$@" ; exit $?
//DEPS org.springaicommunity.agents:spring-ai-agents-pr-review-cli:0.1.0-SNAPSHOT

import org.springaicommunity.agents.pr.cli.BatchPrReviewCommand;
import picocli.CommandLine;

public class batch_pr_review {
    public static void main(String[] args) {
        System.exit(new CommandLine(new BatchPrReviewCommand()).execute(args));
    }
}
```

### 6.2 Batch Command Implementation

```java
@Command(name = "batch-pr-review",
         description = "Batch process multiple PRs")
public class BatchPrReviewCommand implements Callable<Integer> {

    @Parameters(description = "PR numbers to process")
    private List<Integer> prNumbers;

    @Option(names = "--dry-run")
    private boolean dryRun = false;

    @Option(names = "--stop-on-error")
    private boolean stopOnError = false;

    @Option(names = "--no-cleanup")
    private boolean noCleanup = false;

    @Option(names = "--open-browser")
    private boolean openBrowser = false;

    @Override
    public Integer call() throws Exception {
        BatchPrWorkflowExecutor executor = new BatchPrWorkflowExecutor();

        BatchConfig config = BatchConfig.builder()
            .prNumbers(prNumbers)
            .dryRun(dryRun)
            .stopOnError(stopOnError)
            .cleanupBetweenPrs(!noCleanup)
            .openBrowser(openBrowser)
            .build();

        BatchResult result = executor.execute(config);

        return result.hasFailures() ? 1 : 0;
    }
}
```

---

## Phase 7: Key Dependencies

### 7.1 Maven Dependencies

```xml
<dependencies>
    <!-- Shell Execution -->
    <dependency>
        <groupId>org.zeroturnaround</groupId>
        <artifactId>zt-exec</artifactId>
        <version>1.12</version>
    </dependency>

    <!-- Spring AI Agents -->
    <dependency>
        <groupId>org.springaicommunity.agents</groupId>
        <artifactId>spring-ai-agent-client</artifactId>
    </dependency>

    <dependency>
        <groupId>org.springaicommunity.agents</groupId>
        <artifactId>spring-ai-claude-agent</artifactId>
    </dependency>

    <!-- CLI -->
    <dependency>
        <groupId>info.picocli</groupId>
        <artifactId>picocli</artifactId>
        <version>4.7.6</version>
    </dependency>

    <!-- Templating -->
    <dependency>
        <groupId>com.github.spullara.mustache.java</groupId>
        <artifactId>compiler</artifactId>
        <version>0.9.11</version>
    </dependency>

    <!-- JSON -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
    </dependency>

    <!-- Spring Boot -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter</artifactId>
    </dependency>
</dependencies>
```

---

## Phase 8: Implementation Roadmap

### Sprint 1: Foundation (Week 1)
- ✅ Repository setup at ~/community/pr-samples/spring-ai-agents
- ✅ Create feature branch: `feature/pr-review-automation`
- ✅ Create module structure in pom.xml
- ✅ ShellExecutor with zt-exec
- ✅ GitCommands, GhCommands, MavenCommands wrappers
- ✅ Basic CLI with Picocli
- ✅ WorkflowContext, WorkflowConfig, PhaseExecutor framework

### Sprint 2: Core Workflow (Week 2-3)
- ✅ Phase 1: Repository Setup
- ✅ Phase 2: Compilation (without AI yet)
- ✅ Phase 5: Testing (discovery + execution)
- ✅ PrWorkflowExecutor orchestration
- ✅ JBang script basic structure
- ✅ Test with simple PR

### Sprint 3: AI Integration (Week 4-5)
- ✅ AgentClient integration setup
- ✅ CompilationErrorResolver with AI
- ✅ ConflictResolver with AI
- ✅ ConversationAnalyzer
- ✅ RiskAssessor
- ✅ SolutionAssessor
- ✅ Template engine integration

### Sprint 4: Advanced Features (Week 6-7)
- ✅ Phase 3: Commit Management
- ✅ Phase 4: Conflict Resolution
- ✅ BackportAssessor
- ✅ CommitMessageGenerator
- ✅ ReportGenerator (Markdown)
- ✅ Test with complex PR

### Sprint 5: Reporting & Batch (Week 8-9)
- ✅ HtmlDashboardGenerator
- ✅ Batch processing support
- ✅ Progress indicators (Braille spinner)
- ✅ Batch dashboard generation
- ✅ Browser integration

### Sprint 6: Testing & Polish (Week 9-10)
- ✅ Integration test suite
- ✅ Unit tests for all components
- ✅ JBang script finalization
- ✅ Error handling improvements
- ✅ Documentation

### Sprint 7: Production Ready (Week 10)
- ✅ Performance optimization
- ✅ Final testing with real Spring AI PRs
- ✅ JBang catalog integration
- ✅ Release preparation

---

## Success Criteria

### Functional
- ✅ JBang execution: `jbang pr-review@spring-ai-community 3794`
- ✅ All Python features ported and functional
- ✅ All shell commands (gh, git, maven) via zt-exec
- ✅ Same behavior as Python version

### Quality
- ✅ Clean Java architecture with proper OOP design
- ✅ Comprehensive test coverage (>80%)
- ✅ Production-ready error handling and logging
- ✅ Performance comparable or better than Python

### Documentation
- ✅ README with usage examples
- ✅ JavaDoc for all public APIs
- ✅ Architecture documentation

---

## Component Mapping: Python → Java

| Python File | Lines | Java Component | Package |
|------------|-------|----------------|---------|
| pr_workflow.py | 4,100 | PrWorkflowExecutor | workflow |
| compilation_error_resolver.py | 1,000 | CompilationErrorResolver | compilation |
| ai_conversation_analyzer.py | 600 | ConversationAnalyzer | analysis |
| ai_risk_assessor.py | 1,200 | RiskAssessor | analysis |
| solution_assessor.py | 2,000 | SolutionAssessor | analysis |
| backport_assessor.py | 900 | BackportAssessor | analysis |
| conflict_analyzer.py | 500 | ConflictResolver | conflict |
| intelligent_squash.py | 800 | CommitSquasher | commit |
| commit_message_generator.py | 600 | CommitMessageGenerator | commit |
| enhanced_report_generator.py | 1,800 | ReportGenerator | report |
| html_report_generator.py | 3,300 | HtmlDashboardGenerator | report |
| pr_context_collector.py | 600 | PrContextCollector | github |
| test_discovery.py | 500 | TestDiscoveryEngine | testing |
| batch_pr_workflow.py | 900 | BatchPrWorkflowExecutor | workflow |

**Total Python**: ~21,787 lines
**Estimated Java**: ~15,000-18,000 lines (better OOP structure, less boilerplate)

---

## Next Steps

**Ready to execute:**

1. Create ~/community/pr-samples/spring-ai-agents working directory
2. Clone spring-ai-agents repository
3. Create feature branch: `feature/pr-review-automation`
4. Set up initial module structure in root pom.xml
5. Begin Sprint 1: Foundation implementation

**First Tasks:**
- Create spring-ai-agents-pr-review module
- Create spring-ai-agents-pr-review-cli module
- Add zt-exec dependency
- Implement ShellExecutor base class
- Create GitCommands wrapper

---

**Plan Status**: Ready for Implementation
**Estimated Completion**: 10 weeks (with proper testing and polish)
**Primary Developer**: Mark Pollack with Claude Code assistance
