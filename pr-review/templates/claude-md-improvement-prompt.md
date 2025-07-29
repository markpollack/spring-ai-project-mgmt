# CLAUDE.md Improvement Prompt Template

## Objective
Transform the provided CLAUDE.md file to follow official Anthropic best practices and industry standards for Claude Code project documentation.

## Research-Based Best Practices (Sources: Anthropic Engineering Blog, API Dog, Maxitect Blog)

### Core Principles
- **Be lean and intentional**: Respect token budget, use short declarative bullet points
- **Keep concise and human-readable**: Anthropic's official recommendation
- **Structure for clarity**: Use standard Markdown headings
- **Stay under 150 lines**: Recommended maximum length
- **Focus on actionable directives**: Not implementation details or narratives

### Required Structure
1. **Project Overview** - Brief purpose and goals (2-3 lines)
2. **Essential Commands** - Primary workflow commands with examples
3. **Core Files** - Key components only, not exhaustive lists
4. **Code Style & Conventions** - Project-specific patterns and standards
5. **Development Workflow** - Branch strategy, commit format, review process
6. **Environment Setup** - Required setup steps and dependencies
7. **Integration Notes** - Tool-specific guidance (condensed)

### Content Guidelines
- Use bullet points over paragraphs
- Remove technical implementation details
- Focus on "what to do" not "how it works"
- Eliminate redundant information
- Make every line actionable for Claude
- Use imperative language ("Use X", "Run Y", "Follow Z")

### What to Remove
- Token calculation specifics
- Verbose technical explanations
- Implementation internals
- Repetitive information
- Long narrative sections

### What to Emphasize
- Practical commands Claude needs
- Project-specific conventions
- Clear workflow steps
- Essential file locations
- Critical constraints or requirements

## Task Instructions

1. **Analyze Current File**: Identify verbose sections, redundant content, missing elements
2. **Restructure**: Apply the required structure above
3. **Condense**: Convert paragraphs to bullet points, remove implementation details
4. **Verify**: Ensure final version is under 150 lines and follows all best practices
5. **Test Clarity**: Each section should be immediately actionable by Claude

## Output Format
IMPORTANT: You must provide the complete improved CLAUDE.md file content in a markdown code block like this:

```markdown
# Your improved CLAUDE.md content here
(... complete file content ...)
```

The improved file should have:
- Clear section headers using `#` and `##`
- Bullet points for all content
- Concise, directive language
- Essential information only
- Logical flow from overview to specific guidance

Do not just provide a summary - I need the actual file content to save.
Remember: Claude needs explicit prompting to reference CLAUDE.md - make it easy to scan and apply.