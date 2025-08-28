# Plan: Create PR Review Demo Using Spring AI Agents

## Objective
Create a demonstration sample that showcases the PR review system's effectiveness using the AgentClient class from Spring AI Agents, allowing potential users to experience the automated PR analysis capabilities with real data from an actual Spring AI pull request.

## Directory Structure
```
/home/mark/community/spring-ai-agents/samples/
├── hello-world/           (existing)
└── pr-review-demo/        (new)
    ├── README.md
    ├── pom.xml
    ├── src/
    │   ├── main/
    │   │   ├── java/org/springaicommunity/agents/samples/prreview/
    │   │   │   ├── PrReviewDemoApplication.java
    │   │   │   ├── PrReviewDemoRunner.java
    │   │   │   └── PrReviewAnalyzer.java
    │   │   └── resources/
    │   │       ├── application.yml
    │   │       └── pr-data/
    │   │           ├── pr-3794/        (sample PR data)
    │   │           │   ├── pr-data.json
    │   │           │   ├── conversation.json
    │   │           │   ├── file-changes.json
    │   │           │   └── issue-data.json
    │   │           └── templates/
    │   │               ├── ai_conversation_analysis_prompt.md
    │   │               ├── ai_risk_assessment_prompt.md
    │   │               └── solution_assessment_prompt.md
    │   └── test/
    └── demo-output/           (generated during demo)
```

## Implementation Steps

### Phase 1: Setup Sample Project Structure
1. **Create new Maven module** `pr-review-demo` under `/samples/`
2. **Copy pom.xml structure** from hello-world, update artifact ID and description
3. **Add dependencies**:
   - spring-ai-agent-client
   - spring-ai-claude-code
   - jackson-databind (for JSON handling)
   - spring-boot-starter

### Phase 2: Copy Sample PR Data
1. **Select PR #3794** as demo PR (MCP Sync Server servlet context - simple, focused change)
2. **Copy context data** from `/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/context/pr-3794/`:
   - pr-data.json (PR metadata)
   - conversation.json (GitHub discussions)
   - file-changes.json (code changes)
   - issue-data.json (linked issue)
3. **Copy key templates** from `/home/mark/project-mgmt/spring-ai-project-mgmt/pr-review/templates/`:
   - ai_conversation_analysis_prompt.md
   - ai_risk_assessment_prompt.md
   - solution_assessment_prompt.md

### Phase 3: Implement Core Demo Classes

#### PrReviewDemoApplication.java
```java
@SpringBootApplication
public class PrReviewDemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(PrReviewDemoApplication.class, args);
    }
}
```

#### PrReviewAnalyzer.java
```java
@Component
public class PrReviewAnalyzer {
    // Core analysis methods
    - loadPrData()
    - performConversationAnalysis()
    - performRiskAssessment()
    - performSolutionAssessment()
    - generateReport()
}
```

#### PrReviewDemoRunner.java
```java
@Component
public class PrReviewDemoRunner implements CommandLineRunner {
    
    @Override
    public void run(String... args) {
        // 1. Setup Claude Code client
        // 2. Create AgentClient
        // 3. Load PR data from resources
        // 4. Execute analysis goals:
        //    - Conversation analysis
        //    - Risk assessment
        //    - Solution assessment
        // 5. Generate markdown report
        // 6. Display results
    }
    
    private void executeConversationAnalysis(AgentClient client) {
        String goal = "Analyze the PR conversation from pr-data/pr-3794/conversation.json " +
                     "and provide insights on requirements and stakeholder concerns";
        AgentClientResponse response = client.goal(goal).run();
    }
    
    private void executeRiskAssessment(AgentClient client) {
        String goal = "Review the code changes in pr-data/pr-3794/file-changes.json " +
                     "and assess security risks and breaking changes";
        AgentClientResponse response = client.goal(goal).run();
    }
    
    private void generateReport(Map<String, String> analyses) {
        // Combine all analyses into professional markdown report
        // Save to demo-output/pr-3794-review.md
    }
}
```

### Phase 4: Create Demo Script and Documentation

#### README.md Content
```markdown
# PR Review Demo - Spring AI Agents

This demo showcases how Spring AI Agents can automate pull request reviews with AI-powered analysis.

## What This Demo Does
- Analyzes a real Spring AI pull request (#3794 - MCP Sync Server enhancement)
- Performs conversation analysis to understand requirements
- Assesses technical risks and breaking changes
- Generates a professional markdown review report

## Quick Start
1. Set API key: `export ANTHROPIC_API_KEY="your-key"`
2. Run demo: `mvn spring-boot:run`
3. View report: `cat demo-output/pr-3794-review.md`

## Sample Output
The demo generates a comprehensive review report including:
- Problem & solution overview
- Requirements analysis from GitHub discussions
- Technical risk assessment
- Code quality analysis
- Recommendations and action items
```

### Phase 5: Create Simplified Templates
Simplify the templates for demo purposes:
1. **Reduce template complexity** - focus on key analysis points
2. **Add clear instructions** for Claude Code
3. **Include example outputs** in templates

### Phase 6: Add Interactive Options
```java
// Add command-line options for different demo modes
if (args.length > 0) {
    switch(args[0]) {
        case "--quick":
            runQuickDemo();  // Just conversation analysis
            break;
        case "--full":
            runFullDemo();    // All analyses
            break;
        case "--compare":
            compareWithManualReview();  // Show time/quality comparison
            break;
    }
}
```

### Phase 7: Performance Metrics
Add timing and metrics to demonstrate effectiveness:
```java
private void displayMetrics(long startTime, long endTime) {
    System.out.println("=== Performance Metrics ===");
    System.out.println("Analysis time: " + (endTime - startTime) / 1000 + " seconds");
    System.out.println("Manual review time (estimated): 2-3 hours");
    System.out.println("Time saved: 99.5%");
    System.out.println("Analyses performed: 3 (conversation, risk, solution)");
}
```

## Expected Demo Flow

1. **User runs**: `mvn spring-boot:run`
2. **System displays**: 
   ```
   🚀 Spring AI Agents - PR Review Demo
   📋 Analyzing PR #3794: MCP Sync Server - Servlet Context Support
   
   ⏳ Loading PR data from resources...
   ✅ Loaded: 2 file changes, 0 conversations, 0 linked issues
   
   🧠 Performing AI analysis...
   [1/3] Conversation analysis... ✅ (10s)
   [2/3] Risk assessment... ✅ (12s)
   [3/3] Solution assessment... ✅ (15s)
   
   📊 Generating review report...
   ✅ Report saved: demo-output/pr-3794-review.md
   
   === Summary ===
   Total analysis time: 45 seconds
   Manual review estimate: 2-3 hours
   Time saved: 99.5%
   ```

3. **Generated report** shows professional PR analysis similar to actual system output

## Success Criteria
- ✅ Demo runs in < 60 seconds
- ✅ Uses real PR data for authenticity
- ✅ Generates professional-looking analysis report
- ✅ Shows clear value proposition (time savings, quality)
- ✅ Simple to run (single command)
- ✅ Self-contained (includes all necessary data)

## Files to Copy from PR Review System
1. `/pr-review/context/pr-3794/*` → `/samples/pr-review-demo/src/main/resources/pr-data/pr-3794/`
2. Key templates from `/pr-review/templates/` (simplified versions)
3. Report generation logic (adapted from enhanced_report_generator.py)

## Key Implementation Details

### Working Directory Configuration
The demo should configure the working directory for Claude Code to be the resources folder:
```java
ClaudeCodeClient claudeClient = ClaudeCodeClient.create(
    Path.of("src/main/resources/pr-data")
);
```

### Goal Formulation Strategy
Goals should be specific and reference the actual JSON files:
```java
String conversationGoal = """
    Read and analyze the GitHub PR conversation in pr-3794/conversation.json.
    Identify:
    1. The main problem being solved
    2. Key requirements from the discussion
    3. Any concerns raised by reviewers
    4. Consensus reached on the approach
    
    Format your response as structured JSON with these sections.
    """;
```

### Error Handling
Include proper error handling for demo robustness:
```java
try {
    AgentClientResponse response = client.goal(analysisGoal).run();
    if (response.isSuccessful()) {
        return response.getResult();
    } else {
        log.warn("Analysis failed: {}", response.getResult());
        return "Analysis unavailable";
    }
} catch (Exception e) {
    log.error("Error during analysis", e);
    return "Error: " + e.getMessage();
}
```

### Report Template Structure
```markdown
# PR Review Report - #3794: MCP Sync Server - Servlet Context Support

## Executive Summary
- **Analysis Time**: 45 seconds
- **Automated Assessments**: 3
- **Key Finding**: [High-level summary]

## Conversation Analysis
[AI-generated insights from GitHub discussions]

## Risk Assessment
[AI-identified risks and concerns]

## Solution Assessment
[Technical evaluation of the implementation]

## Recommendations
[Prioritized action items]

---
*Generated by Spring AI Agents PR Review Demo*
```

## Demo Variations

### Quick Demo (--quick)
- Only runs conversation analysis
- Takes ~15 seconds
- Good for live presentations

### Full Demo (--full)
- Runs all three analyses
- Takes ~45 seconds
- Shows complete capabilities

### Comparison Demo (--compare)
- Shows side-by-side manual vs automated metrics
- Includes cost analysis (time saved)
- Demonstrates ROI

## Marketing Points to Highlight

1. **Speed**: 45 seconds vs 2-3 hours manual review
2. **Consistency**: Every PR gets same depth of analysis
3. **Comprehensiveness**: Multiple AI assessments covering different aspects
4. **Integration**: Works with existing Spring AI Agents framework
5. **Real Data**: Uses actual Spring AI PR for authenticity

## Next Steps After Demo Implementation

1. Create video walkthrough of demo
2. Add to Spring AI Agents documentation
3. Present at Spring AI community meetings
4. Use as basis for conference talks
5. Extend with additional PR examples

This demo will provide a compelling, hands-on experience of the PR review system's capabilities using the Spring AI Agents framework.