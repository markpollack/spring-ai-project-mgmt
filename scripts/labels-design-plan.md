# JBang Label Analysis Script Plan

## Goal: Automated Label Analysis and Filtering Tool

Create `LabelAnalyzer.java` - A comprehensive JBang script to automate label collection, analysis, and filtering for Spring repositories to improve issue classification accuracy.

## Problem Statement

Based on analysis of existing label files, we need to:
1. **Remove problematic labels** that hurt F1 scores (like 'bug' at 40% precision, 'enhancement' at 29.7% precision)
2. **Identify zero-assignment labels** that exist but have no issues assigned
3. **Categorize administrative labels** for potential removal (status tracking, process management)
4. **Standardize across repositories** (spring-ai, spring-framework, spring-boot)
5. **Automate the filtering process** instead of manual curation

## Current State Analysis

### Existing Files and Their Roles:
- **labels.json**: 117 labels from spring-ai repository
- **github-labels-mapping*.json**: Enhanced metadata with codebase analysis
- **training_labels_analysis.json**: Usage frequency and patterns
- **analyze_training_labels.py**: Current analysis tool (Python-based)

### Identified Problem Categories:
- **Low F1 Score Labels**: bug (40% precision), enhancement (29.7% precision)
- **Administrative Labels**: status: backported, status: to-discuss, follow up
- **Process Labels**: for: backport-to-1.0.x, good first issue, help wanted
- **Zero-Assignment Labels**: agents, nomic, openrouter, reasoning, vllm, wordlift

## Hierarchical Taxonomy Analysis

### Goal: Extract and Standardize Issue Taxonomy

The primary goal of implementing a hierarchical labeling scheme for GitHub issues is to achieve enhanced organization, clarity, and discoverability within a project's issue tracker. By analyzing the top Spring open source projects, we will extract and standardize their taxonomies to create a unified approach.

### Benefits of Hierarchical Labeling

1. **Categorize Issues**: Labels allow issues to be categorized based on:
   - **Type** (e.g., `type: bug`, `type: feature`, `type: enhancement`)
   - **Priority** (e.g., `priority: high`, `priority: low`, `priority: critical`)
   - **Status** (e.g., `state: in progress`, `state: needs review`, `status: waiting-for-feedback`)
   - **Component** (e.g., `area: security`, `component: web`, `area: data`)

2. **Improve Prioritization and Workflow Management**: Structured organization simplifies:
   - Process of prioritizing tasks
   - Managing workflow by providing quick overview of critical issues
   - Tracking tasks in progress and those awaiting review

3. **Enhance Search and Filtering**: The hierarchy allows for:
   - More precise filtering and searching of issues
   - Teams to easily find and focus on specific sets of issues
   - Category-based issue discovery

4. **Promote Consistency**: Well-defined hierarchical scheme encourages:
   - Consistent labeling across the project
   - Clearer and more uniform understanding of issue characteristics
   - Standardized communication among team members

5. **Facilitate Collaboration**: The structure makes it easier for:
   - Team members to understand the context of issues
   - Effective collaboration and improved communication
   - Enhanced problem-solving processes

### Target Repositories for Taxonomy Analysis

We will analyze the following top Spring projects to extract their hierarchical labeling patterns:

1. **spring-projects/spring-framework** (Primary reference - most mature taxonomy)
2. **spring-projects/spring-boot** (High-volume, well-organized labels)
3. **spring-projects/spring-security** (Security-specific taxonomy patterns)
4. **spring-projects/spring-data** (Data access patterns and modularity)
5. **spring-projects/spring-ai** (Target for standardization)

### Taxonomy Extraction Process

1. **Pattern Recognition**: Identify common prefixes and hierarchical structures:
   - `type:` (bug, feature, enhancement, task, documentation)
   - `status:` (waiting-for-feedback, backported, to-discuss, in-progress)  
   - `priority:` (high, medium, low, critical)
   - `area:` (web, security, data, testing, documentation)
   - `component:` (specific module or functionality areas)
   - `severity:` (blocker, major, minor, trivial)
   - `kind:` (regression, improvement, cleanup)

2. **Cross-Repository Analysis**: Compare taxonomies across projects to identify:
   - Common patterns and best practices
   - Inconsistencies that should be standardized
   - Missing categories that could improve organization

3. **Standardization Recommendations**: Generate recommendations for:
   - Unified taxonomy structure across Spring ecosystem
   - Migration paths from flat labels to hierarchical structure
   - Best practices for new label creation

## Architecture Design

### Core Components

#### 1. **LabelCollector** 
- Fetch labels from GitHub API with multi-repository support
- Support for spring-ai, spring-framework, spring-boot
- Configurable repository endpoints
- Rate limiting and error handling
- Output standardized label data structure

#### 2. **LabelCategorizer**
- **Technical Labels**: Vector stores, AI providers, core features
- **Administrative Labels**: Status tracking, process management
- **Community Labels**: good first issue, help wanted
- **Quality Labels**: bug, enhancement, documentation
- **Zero-Assignment Labels**: Labels with no associated issues

#### 3. **UsageAnalyzer**
- Analyze issue assignment frequency for each label
- Identify labels with zero assignments
- Calculate usage statistics and trends
- Detect rarely-used labels (configurable threshold)

#### 4. **FilterRecommendations**
- Rule-based filtering recommendations
- F1 score impact analysis using historical data
- Configurable filtering criteria
- Generate keep/remove recommendations with justifications

#### 5. **TaxonomyAnalyzer**
- Extract hierarchical patterns from multiple repositories
- Identify common prefixes and naming conventions
- Analyze taxonomy consistency across Spring projects
- Generate standardization recommendations
- Create migration mappings for flat-to-hierarchical conversion

#### 6. **ReportGenerator**
- Comprehensive analysis reports in multiple formats (JSON, Markdown, CSV)
- Label categorization summaries with taxonomy analysis
- Zero-assignment and low-usage reports
- Filtering recommendations with impact analysis
- Comparative analysis across repositories with hierarchical insights
- Taxonomy standardization reports and migration guides

### Data Flow

```
GitHub API → LabelCollector → LabelCategorizer → UsageAnalyzer → TaxonomyAnalyzer → FilterRecommendations → ReportGenerator
     ↓              ↓              ↓              ↓              ↓                    ↓                 ↓
 Raw Labels → Normalized → Categorized → Usage Stats → Taxonomy → Filter Rules → Analysis Reports
              (5 repos)      (rules)       (frequency)   (hierarchy)    (recommendations)   (comprehensive)
```

## Configuration-Driven Approach

### YAML Configuration Structure

```yaml
repositories:
  - name: "spring-projects/spring-ai"
    primary: true
  - name: "spring-projects/spring-framework"
  - name: "spring-projects/spring-boot"
  - name: "spring-projects/spring-security"
    analysis_only: true
  - name: "spring-projects/spring-data"
    analysis_only: true

filtering:
  administrative_patterns:
    - "status: *"
    - "for: *"
    - "type: backport*"
  
  problematic_labels:
    - name: "bug"
      reason: "Low precision (40%)"
      f1_impact: -0.114
    - name: "enhancement" 
      reason: "Low precision (29.7%)"
      f1_impact: -0.134
  
  zero_assignment:
    remove_threshold: 0
    grace_period_days: 90
  
  low_usage:
    threshold: 3
    action: "review"

categorization:
  technical:
    ai_providers: ["anthropic", "azure", "bedrock", "openai", "ollama"]
    vector_stores: ["pinecone", "qdrant", "chromadb", "weaviate"]
    features: ["RAG", "embedding", "streaming", "tool/function calling"]
  
  administrative:
    status_tracking: ["status: *", "follow up"]
    process_management: ["for: backport-to-*", "next priorities"]
    community: ["good first issue", "help wanted"]

hierarchical_taxonomy:
  extract_patterns: true
  common_prefixes:
    - "type:"
    - "priority:" 
    - "state:"
    - "status:"
    - "area:"
    - "component:"
    - "severity:"
    - "kind:"
  analyze_hierarchy: true
  suggest_standardization: true

output:
  formats: ["json", "markdown", "csv"]
  include_zero_assignments: true
  include_recommendations: true
  generate_migration_script: true
```

## Implementation Plan

### Phase 1: Core Infrastructure
1. **JBang Script Setup** with Spring Boot integration
2. **GitHub API Client** with authentication and rate limiting
3. **Configuration Management** using Spring Boot properties
4. **Basic Label Collection** from single repository

### Phase 2: Analysis Engine
1. **Label Categorization Logic** based on patterns and rules
2. **Usage Analysis** with issue assignment frequency
3. **Zero-Assignment Detection** with configurable thresholds
4. **Filter Recommendation Engine** with justification logic

### Phase 3: Multi-Repository Support & Taxonomy Analysis
1. **Repository Configuration** for top 5 Spring projects (spring-ai, spring-framework, spring-boot, spring-security, spring-data)
2. **Hierarchical Taxonomy Extraction** from established Spring projects
3. **Comparative Analysis** across repositories with taxonomy mapping
4. **Label Standardization** recommendations based on hierarchical best practices
5. **Cross-Repository Migration** suggestions with taxonomy alignment

### Phase 4: Advanced Features
1. **F1 Score Impact Analysis** using classification history
2. **Trend Analysis** for label usage over time
3. **Automated Filter Application** with preview mode
4. **Integration** with existing classification pipeline

### Phase 5: Reporting and Output
1. **Comprehensive Report Generation** in multiple formats
2. **Migration Scripts** for label cleanup
3. **Dashboard-Style Reports** for stakeholder review
4. **Integration Documentation** for existing workflows

## Key Features

### Intelligent Filtering
- **Rule-based categorization** with configurable patterns
- **Usage-based filtering** with statistical thresholds
- **F1 score impact assessment** for ML classification accuracy
- **Administrative label detection** for process-related cleanup

### Multi-Repository Analysis
- **Unified label analysis** across Spring ecosystem
- **Comparative reporting** between repositories
- **Standardization recommendations** for consistency
- **Migration planning** for label harmonization
- **Hierarchical taxonomy extraction** from top Spring projects

### Automated Recommendations
- **Data-driven filtering** based on usage statistics
- **Impact analysis** for classification accuracy
- **Justification documentation** for each recommendation
- **Preview mode** for safe filter application

### Comprehensive Reporting
- **Executive summaries** for high-level decisions
- **Detailed analysis** for technical teams
- **Migration guides** for implementation
- **Performance metrics** for classification improvement

## Expected Outputs

### Primary Reports
1. **Label Analysis Report**: Comprehensive categorization and usage analysis
2. **Hierarchical Taxonomy Report**: Analysis of label patterns across top 5 Spring projects
3. **Filter Recommendations**: Data-driven removal suggestions with justifications
4. **Zero Assignment Report**: Labels with no issues and cleanup recommendations
5. **Cross-Repository Comparison**: Standardization opportunities with taxonomy insights
6. **Taxonomy Standardization Guide**: Recommendations for hierarchical label migration
7. **Migration Script**: Automated label cleanup and hierarchy implementation commands

### Success Metrics
- **Classification Accuracy Improvement**: Target F1 score improvement of 10%+
- **Label Portfolio Reduction**: Remove 20-30% of administrative/problematic labels
- **Zero-Assignment Cleanup**: Identify and remove unused labels
- **Standardization Score**: Measure consistency across repositories
- **Automation Level**: Replace manual curation with automated recommendations

## Implementation Details

### Technology Stack
- **JBang** for single-file Java execution
- **Spring Boot 3.x** for configuration and HTTP clients
- **Jackson** for JSON processing
- **GitHub API v4 (GraphQL)** for efficient data fetching
- **YAML** configuration for flexibility

### Command Line Interface
```bash
# Basic analysis for spring-ai
jbang LabelAnalyzer.java --repo spring-projects/spring-ai

# Multi-repository taxonomy analysis (all top 5 Spring projects)
jbang LabelAnalyzer.java --analyze-taxonomy --all-spring-repos

# Generate hierarchical taxonomy report
jbang LabelAnalyzer.java --extract-taxonomy --repo spring-projects/spring-framework --repo spring-projects/spring-boot --repo spring-projects/spring-security

# Generate filter recommendations with taxonomy insights
jbang LabelAnalyzer.java --repo spring-projects/spring-ai --generate-filters --include-taxonomy

# Apply filters with hierarchical migration (preview mode)
jbang LabelAnalyzer.java --repo spring-projects/spring-ai --apply-filters --migrate-to-hierarchy --preview

# Custom configuration with taxonomy analysis
jbang LabelAnalyzer.java --config custom-config.yaml --analyze-taxonomy --target-repo spring-projects/spring-ai
```

This automated approach will replace manual label curation with data-driven analysis, significantly improving the efficiency and accuracy of the issue classification system.