# Release Notes Generation Prompt

## Context
I have uploaded a zip file containing comprehensive data about all commits, pull requests, and issues for an upcoming release of a Spring OSS project. The data includes:

- Complete commit metadata (messages, authors, dates)
- Associated Pull Requests with titles, descriptions, and labels
- Related Issues that were closed by the PRs
- Full text content for analysis

## Task
Please analyze this release data and generate professional release notes following Spring Boot conventions. Focus on:

### 1. Categorization
Group the changes into these standard Spring categories:
- **✨ New Features** - New functionality and enhancements
- **🐛 Bug Fixes** - Bug fixes and corrections  
- **📚 Documentation** - Documentation improvements
- **⚡ Performance** - Performance improvements and optimizations
- **🔧 Internal Changes** - Refactoring, build improvements, dependency updates
- **💥 Breaking Changes** - Any backward-incompatible changes (highlight prominently)
- **🔐 Security** - Security-related fixes and improvements
- **♿ Accessibility** - Accessibility improvements

### 2. Analysis Guidelines
For each change:
- Use the PR title as the primary description (it's usually well-formatted)
- Include the PR number and issue numbers in format: `(#PR via #issue1, #issue2)`
- Look for breaking changes indicators: "breaking", "remove", "deprecate", "change"
- Identify security fixes from labels or descriptions
- Group related changes together (e.g., multiple commits for one feature)
- Exclude routine maintenance unless significant (dependency bumps, CI fixes)

### 3. Output Format
Structure the release notes as:

```markdown
# Release Notes v[VERSION]

## 🎯 Highlights
[2-3 sentence summary of the most significant changes]

## 💥 Breaking Changes
[List any breaking changes first - this is critical for Spring projects]

## ✨ New Features
- Feature description (#PR via #issue)
- Another feature (#PR)

## 🐛 Bug Fixes  
- Bug fix description (#PR via #issue)

[Continue with other categories...]

## 🙏 Contributors
Thanks to all contributors who made this release possible:
[List unique contributors from the data]

## 📈 Statistics
- X commits from Y contributors
- Z pull requests merged
- W issues resolved
```

### 4. Spring-Specific Considerations
- Highlight any new starters, auto-configurations, or properties
- Note dependency version updates (especially Spring Framework, security libraries)
- Mention any new @ConfigurationProperties or @ConditionalOn* annotations
- Call out changes to application.properties/yaml configuration
- Identify changes affecting Spring Boot actuator endpoints
- Note any changes to testing support or test slices

### 5. Quality Guidelines
- Use clear, user-focused language (avoid internal jargon)
- Be concise but informative
- Prioritize changes that affect end users
- Group minor related fixes under a single bullet point when appropriate
- Ensure breaking changes are prominently featured and well-explained

## Additional Notes
- If you notice any commits that seem like duplicates or reverts, please consolidate them appropriately
- Focus on the "what" and "why" rather than the "how"
- If there are a large number of dependency updates, group them under a single entry
- Highlight any changes that improve developer experience or ease of use

Please analyze the uploaded data and generate comprehensive release notes following these guidelines.