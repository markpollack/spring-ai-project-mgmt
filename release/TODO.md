# Spring AI Point Release Automation - TODO List

## High Priority Issues

### ✅ RESOLVED: Documentation Push Timing Issue  
**Problem**: Documentation was pushed to live sites (spring.io, start.spring.io) immediately in Phase 1, but should only be published after Maven Central deployment succeeds.

**Resolution**: ✅ **ALREADY IMPLEMENTED CORRECTLY**
- **Phase 1**: Steps 1-10, stops at "Trigger Maven Central release"
- **Phase 2**: Steps 11-15, includes documentation updates after Maven Central success:
  - Step 14: `start.spring.io` update (✅ correctly in Phase 2)
  - Step 15: `spring-website-content` update (✅ correctly in Phase 2)

**Implementation Status**:
- [x] ✅ `_update_start_spring_io` already in Phase 2 
- [x] ✅ README workflow documentation is correct
- [x] ✅ `_trigger_deploy_docs` can stay in Phase 1 (reference docs, not dependency listings)
- [x] ✅ Tested with dry-run - workflow correctly stops at Maven Central

**Note**: The current implementation already prevents the documentation timing issue. Documentation updates (start.spring.io, spring-website-content) only happen in Phase 2 after Maven Central deployment succeeds.

## Medium Priority Enhancements

### 📈 Release Metrics and Monitoring
- [ ] Add timing metrics for each workflow step
- [ ] Create release summary report with duration, success rates
- [ ] Add optional Slack/Teams notification integration
- [ ] Track Maven Central deployment status polling

### 🔍 Enhanced Validation
- [ ] Add pre-flight checks for GitHub CLI permissions
- [ ] Validate repository access before starting workflows
- [ ] Check for existing PRs before creating new ones
- [ ] Add Maven dependency version consistency checks

### 🎯 User Experience Improvements
- [ ] Add progress bar for long-running operations (builds, clones)
- [ ] Implement rollback functionality for failed releases
- [ ] Add release notes template generation
- [ ] Create wizard mode for first-time users

## Low Priority Features

### 🔧 Technical Debt
- [ ] Refactor common repository management code into base class
- [ ] Add comprehensive unit tests for all updater classes
- [ ] Implement async operations for parallel repository cloning
- [ ] Add configuration file support (YAML/JSON) for default settings

### 📋 Documentation and Tooling
- [ ] Create video walkthrough of release process
- [ ] Add troubleshooting guide with common error scenarios
- [ ] Create GitHub Actions workflow for testing script changes
- [ ] Add shell completion for CLI arguments

### 🚀 Future Integrations
- [ ] Support for other Spring project releases (not just Spring AI)
- [ ] Integration with Spring release train coordination
- [ ] Support for milestone (M1, M2) and RC releases
- [ ] Add support for major version releases (different workflow)

## Known Issues

### 🐛 Minor Bugs
- [ ] Skip-to functionality doesn't initialize helpers for early steps
- [ ] Log file timestamps could be more human-readable
- [ ] Error messages for network failures could be more specific
- [ ] Cleanup operations don't handle permission errors gracefully

### ⚠️ Edge Cases
- [ ] Handle case where release branch already exists remotely
- [ ] Better handling of Maven Central status API timeouts
- [ ] Support for releases when GitHub Actions are disabled
- [ ] Handle case where documentation.json structure changes

## Architecture Improvements

### 🏗️ Code Structure
- [ ] Extract configuration management into separate module
- [ ] Create plugin system for different repository updaters
- [ ] Add proper logging framework (replace print statements)
- [ ] Implement proper exit codes for different failure types

### 🔒 Security Enhancements
- [ ] Add GPG signing verification for release commits
- [ ] Implement secure credential storage for API tokens
- [ ] Add audit logging for all release operations
- [ ] Validate repository URLs to prevent malicious redirects

## Notes

### Documentation Push Timing Priority
The documentation push timing issue is marked as **Critical** because:
1. It creates user confusion when docs are live but artifacts unavailable
2. It violates the principle of atomic releases
3. It's currently affecting production releases (1.0.1 case mentioned)

### Implementation Order
Suggested order for addressing TODOs:
1. **Fix documentation push timing** (breaks atomicity)
2. **Add enhanced validation** (prevents common user errors)  
3. **Improve user experience** (makes tool more accessible)
4. **Address technical debt** (long-term maintainability)

### Contributing
When implementing items from this TODO list:
- Update this file to mark items as completed
- Add new items as they're discovered
- Include implementation notes for complex changes
- Update README.md with new features and workflows