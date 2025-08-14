# Plans Directory - GitHub Issues Collection Project

## Active Documents

### 📊 Current Status
- **CONSOLIDATED_STATUS.md** - Master implementation status and roadmap
  - Current architecture overview
  - Completed phases (1-5)
  - Remaining work (Phases 6-7)
  - Success metrics and next steps

### 📚 Lessons Learned (Critical Knowledge)
Essential safety protocols and implementation insights from each phase:

- **phase1_lessons_learned.md** - DataModels extraction
  - Namespace conflict resolution
  - Testing without Spring context
  - Record behavior insights

- **phase2_lessons_learned.md** - ConfigurationSupport extraction  
  - **CRITICAL**: Avoiding @SpringBootTest with CommandLineRunner
  - Safe Spring configuration testing patterns
  - Emergency procedures for production operations

- **phase3_lessons_learned.md** - ArgumentParser extraction
  - Pure Java testing strategies
  - CLI validation patterns
  - Parameterized testing approaches

- **phase4_lessons_learned.md** - GitHubServices extraction
  - API mocking strategies
  - RestClient testing challenges
  - Service integration patterns

- **phase5_lessons_learned.md** - IssueCollectionService extraction
  - **HIGHEST RISK PHASE** safety protocols
  - File system testing with @TempDir
  - Business logic isolation techniques

### 🚀 Future Features
- **pull-request-support-implementation-plan.md** - Comprehensive plan for adding PR collection
  - 8-phase implementation roadmap
  - Data model extensions
  - API service enhancements
  - Backward compatibility strategy

## Archived Documents

Located in `archived/` subdirectory:

- **refactoring_implementation_plan.md** - Original JBang to Maven plan (superseded by actual implementation)
- **jbang_export_lessons_learned.md** - JBang export issues (incorporated into Phase 0)
- **spring_dependency_injection_fix.md** - Spring config fixes (incorporated into Phase 0)

## Key Safety Reminders

### ⚠️ Critical Warning
**NEVER use @SpringBootTest** in this codebase. The application implements CommandLineRunner, which will trigger real GitHub API calls and data collection during tests.

### ✅ Safe Testing Patterns
1. Use plain JUnit for pure Java components
2. Use @SpringJUnitConfig with minimal context for Spring components
3. Always use @TempDir for file operations
4. Mock all external dependencies
5. Test with --dry-run flag for integration scenarios

## Quick Reference

### To understand current status:
Read `CONSOLIDATED_STATUS.md`

### Before modifying code:
Review relevant `phase*_lessons_learned.md` files

### For future enhancements:
Consult `pull-request-support-implementation-plan.md`

### For historical context:
Check `archived/` directory

## Navigation

- [Back to Scripts README](../README.md)
- [Main Project README](../../README.md)
- [Project CLAUDE.md](../../CLAUDE.md)