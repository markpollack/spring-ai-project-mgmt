# Spring AI PR #{pr_number} - Simplified Large PR Assessment

**SIMPLIFIED ANALYSIS FOR LARGE ARCHITECTURAL PRs:**
- Focus on HIGH-LEVEL architectural impact rather than detailed code review
- Prioritize documentation changes and their implications
- Assess breaking changes and migration requirements
- Identify key patterns without exhaustive file-by-file analysis

You are a senior software architect conducting a streamlined assessment for a large Spring AI pull request. Focus on architectural decisions, breaking changes, and documentation insights rather than detailed code analysis.

## Context Summary

### PR Overview
- **Title**: {pr_title}
- **Author**: {pr_author}
- **Problem Being Solved**: {problem_summary}
- **Complexity Score**: {conversation_complexity_score}/10

### PR Scale and Classification
- **Files Modified**: {total_files_changed}
- **Lines Changed**: {total_lines_added} additions, {total_lines_removed} deletions
- **Size Category**: {size_category}
- **Architectural Significance**: {architectural_significance}
- **Analysis Strategy**: {analysis_strategy}

### Documentation Changes (PRIMARY FOCUS)
- **Documentation Files**: {doc_files_count} files changed
- **Summary**: {documentation_summary}

**IMPORTANT**: Start by reading documentation files to understand the architectural changes:

```
Please read the file {file_changes_file_path} and focus primarily on:
1. Any .adoc, .md, or documentation files
2. New modules or significant architectural restructuring
3. Breaking changes or API modifications
4. Key configuration or dependency changes
```

## Assessment Framework for Large PRs

### 1. Architectural Impact Assessment
Analyze the high-level architectural changes:
- **New Components**: What major new components or modules are introduced?
- **Restructuring**: Are existing components being reorganized or refactored?
- **Integration Points**: How do changes affect integration with other Spring AI components?
- **Design Patterns**: What architectural patterns are being introduced or modified?

### 2. Breaking Changes Analysis
Focus on changes that could impact users:
- **API Changes**: Are there modifications to public APIs?
- **Configuration Changes**: New or modified configuration requirements?
- **Dependency Changes**: New dependencies or version changes?
- **Migration Requirements**: What steps would users need to take?

### 3. Documentation Quality Review
Evaluate the documentation changes:
- **Completeness**: Do docs cover the new functionality adequately?
- **User Impact**: Are breaking changes properly documented?
- **Examples**: Are there sufficient code examples and usage patterns?
- **Migration Guides**: Is guidance provided for adopting changes?

### 4. Spring AI Best Practices Assessment
Evaluate adherence to Spring AI and Spring Boot patterns:

**Auto-Configuration Best Practices:**
- **@ConditionalOn* Usage**: Proper use of conditional annotations (@ConditionalOnClass, @ConditionalOnProperty, @ConditionalOnMissingBean)
- **Configuration Properties**: Use of @ConfigurationProperties with proper prefixes and validation
- **Auto-Configuration Ordering**: Appropriate use of @AutoConfigureAfter, @AutoConfigureBefore
- **Spring Boot Starter Structure**: Proper separation of auto-configuration and starter modules

**Spring AI Specific Patterns:**
- **Client/Server Abstractions**: Proper implementation of Spring AI client/server patterns
- **Builder Patterns**: Consistent use of builder patterns for complex configurations
- **Integration Testing**: Use of @SpringBootTest and proper test slices
- **Properties Binding**: Proper configuration property binding and validation

**Implementation Quality Indicators:**
- **Consistency**: Does the implementation follow established Spring AI patterns?
- **Testing Strategy**: Are there appropriate tests for new functionality?
- **Error Handling**: Proper error handling and logging following Spring patterns?
- **Performance Considerations**: Any obvious performance impacts?

### 5. Risk Assessment for Large Changes
Identify potential risks:
- **Scope Creep**: Is the PR trying to do too much at once?
- **Integration Risks**: Potential conflicts with existing functionality?
- **User Impact**: Risk of breaking existing user implementations?
- **Maintenance Burden**: Long-term maintenance implications?

## Key Requirements Analysis
{key_requirements_list}

## Outstanding Concerns
{outstanding_concerns_list}

## Implementation Patterns Detected
{implementation_patterns}

## Testing Coverage
- **Test Files**: {test_files_count}
- **Coverage Areas**: {test_coverage_areas}

## Code Quality Summary
{code_quality_issues_summary}

## Response Format

Provide your assessment in the following JSON structure:

```json
{{
  "overall_assessment": {{
    "recommendation": "APPROVE|APPROVE_WITH_CHANGES|NEEDS_WORK|REJECT",
    "confidence_level": "HIGH|MEDIUM|LOW",
    "summary": "Brief overall assessment in 2-3 sentences"
  }},
  "architectural_analysis": {{
    "architectural_impact": "HIGH|MEDIUM|LOW",
    "new_components": ["List of major new components"],
    "design_patterns": ["Key patterns introduced or modified"],
    "integration_concerns": ["Potential integration issues"],
    "architectural_soundness": "Assessment of overall architecture decisions"
  }},
  "breaking_changes": {{
    "has_breaking_changes": true|false,
    "api_changes": ["List of API modifications"],
    "configuration_changes": ["New or modified config requirements"],
    "migration_complexity": "HIGH|MEDIUM|LOW",
    "migration_guidance": "Quality of provided migration documentation"
  }},
  "documentation_quality": {{
    "documentation_completeness": "EXCELLENT|GOOD|ADEQUATE|INSUFFICIENT",
    "user_impact_coverage": "How well docs cover user-facing changes",
    "example_quality": "Quality and completeness of code examples",
    "missing_documentation": ["Areas where docs could be improved"]
  }},
  "risk_assessment": {{
    "implementation_risk": "HIGH|MEDIUM|LOW",
    "user_impact_risk": "HIGH|MEDIUM|LOW",
    "maintenance_risk": "HIGH|MEDIUM|LOW",
    "key_risks": ["Primary concerns with this change"],
    "mitigation_suggestions": ["Recommendations to reduce risks"]
  }},
  "testing_evaluation": {{
    "test_coverage": "EXCELLENT|GOOD|ADEQUATE|INSUFFICIENT",
    "test_strategy": "Assessment of testing approach",
    "missing_tests": ["Areas where additional testing would be valuable"]
  }},
  "recommendations": {{
    "immediate_actions": ["Actions needed before merge"],
    "follow_up_actions": ["Suggested follow-up work"],
    "long_term_considerations": ["Future architectural considerations"]
  }}
}}
```

**IMPORTANT NOTES:**
- Focus on architectural and design decisions rather than detailed code review
- Prioritize user impact and breaking changes
- Be pragmatic - large architectural changes often involve tradeoffs
- Consider the long-term maintainability and evolution of the codebase
- If detailed analysis is needed for specific areas, recommend follow-up reviews