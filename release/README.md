# Spring AI Point Release Automation

This directory contains automation tools for managing Spring AI point releases on the 1.0.x branch.

## Overview

The `spring-ai-point-release.py` script automates the complete workflow for creating point releases (1.0.1, 1.0.2, etc.) for Spring AI. It handles version updates, builds, testing, tagging, and pushing changes to the repository.

## Prerequisites

- Python 3.7+
- Git configured with push access to `spring-projects/spring-ai`
- Maven or Maven Daemon (`mvnd`) for builds
- GitHub CLI (`gh`) authenticated for post-release automation

## Quick Start

```bash
# Test the main release workflow without making changes
python3 spring-ai-point-release.py 1.0.1 --dry-run

# Execute the main release workflow (stops at Maven Central trigger)
python3 spring-ai-point-release.py 1.0.1

# After Maven Central deployment succeeds, complete the development version setup
python3 spring-ai-point-release.py 1.0.1 --post-maven-central

# Use a different branch (if needed)
python3 spring-ai-point-release.py 1.0.1 --branch 1.0.x
```

## Command Line Options

```
python3 spring-ai-point-release.py [OPTIONS] VERSION

Arguments:
  VERSION               Target release version (e.g., 1.0.1, 1.0.2)

Options:
  --branch BRANCH              Branch to release from (default: 1.0.x)
  --dry-run                   Preview commands without executing them
  --workspace PATH             Override workspace directory (default: ./spring-ai-release)
  --post-maven-central         Complete development version setup after Maven Central success
  --check-maven-status         Check Maven Central infrastructure status and exit
  --skip-maven-status-check    Skip Maven Central status check before deployment
  --skip-to STEP              Skip to specific workflow step (setup, set-version, build, start-spring-io, spring-website, etc.)
  --cleanup                   Clean up state files and workspace directory before starting
  --skip-start-spring-io      Skip start.spring.io update in post-Maven Central workflow
  --cleanup-start-spring-io   Clean up start.spring.io repository and exit
  --skip-spring-website       Skip spring-website-content update in post-Maven Central workflow
  --cleanup-spring-website    Clean up spring-website-content repository and exit
  --help                      Show help message and exit
```

## Two-Phase Release Process

The script implements a **two-phase workflow** for safer Maven Central integration:

### Phase 1: Main Release Workflow (10 steps)
Executes release steps up to Maven Central trigger and **stops**:
```bash
python3 spring-ai-point-release.py 1.0.1
```

### Phase 2: Post-Maven Central Workflow (5 steps)  
Completes development version setup **only after Maven Central success**:
```bash
python3 spring-ai-point-release.py 1.0.1 --post-maven-central
```

**Why Two Phases?**
- **Risk Reduction**: Prevents development version changes before Maven Central deployment is confirmed
- **Manual Verification**: Allows human verification of Maven Central success
- **State Recovery**: Uses persistent state in `./state/` directory for workflow continuity

## Release Workflow Steps

### Phase 1: Main Release Workflow

The main workflow executes steps 1-10 and stops at Maven Central trigger:

### 1. Setup Workspace
- **Action**: Creates fresh checkout in `./spring-ai-release`
- **Commands**:
  ```bash
  git clone https://github.com/spring-projects/spring-ai.git spring-ai-release
  cd spring-ai-release
  git checkout 1.0.x
  git pull origin 1.0.x
  ```
- **Purpose**: Ensures clean working directory isolated from development checkouts

### 2. Set Release Version
- **Action**: Updates all POM files to release version with comprehensive verification
- **Commands**:
  ```bash
  # Set main project version
  mvnd versions:set -DnewVersion=1.0.1 -DgenerateBackupPoms=false
  
  # Set BOM module version specifically
  mvnd versions:set -DnewVersion=1.0.1 -DgenerateBackupPoms=false -pl spring-ai-bom
  
  # Verify versions were set correctly
  # - Check root pom.xml has version 1.0.1
  # - Check spring-ai-bom/pom.xml has version 1.0.1  
  # - Grep all POM files for SNAPSHOT versions (should find none)
  ```
- **Purpose**: Removes `-SNAPSHOT` suffix and sets exact release version in all modules including BOM
- **Safety**: Comprehensive verification ensures all POMs have correct versions before proceeding

### 3. Build and Verify
- **Action**: Performs fast compilation and documentation verification with comprehensive logging
- **Commands**:
  ```bash
  # Fast build without tests and javadoc (output logged to file)
  mvnd clean package -Dmaven.javadoc.skip=true -DskipTests -q -Dmvnd.rollingWindowSize=0
  
  # Verify documentation builds correctly (output logged to file)
  ./mvnw -pl spring-ai-docs antora -q
  ```
- **Purpose**: Ensures code compiles and documentation generates successfully
- **Output Management**: 
  - No scrolling Maven output during interactive execution
  - Build logs saved to `./logs/fast-build-{timestamp}.log`
  - Documentation logs saved to `./logs/docs-build-{timestamp}.log`
  - Last 10 lines shown on build failures for immediate debugging

### 4. Commit Release Version
- **Action**: Commits version changes on the maintenance branch
- **Commands**:
  ```bash
  git add -A
  git commit -m "Release version 1.0.1"
  ```
- **Purpose**: Creates commit with release version changes

### 5. Create Release Tag
- **Action**: Creates annotated Git tag on the release commit
- **Commands**:
  ```bash
  git tag -a v1.0.1 -m "Release version 1.0.1"
  ```
- **Purpose**: Marks the exact release commit (tag points to release version)

### 6. Create Release Branch
- **Action**: Creates new local branch from the release tag
- **Commands**:
  ```bash
  git checkout -b 1.0.1 v1.0.1
  ```
- **Purpose**: Creates dedicated branch for release work, containing the release commit

### 7. Push Changes
- **Action**: Pushes tag and release branch to remote repository
- **Commands**:
  ```bash
  git push origin v1.0.1
  git push origin 1.0.1
  ```
- **Purpose**: Makes release tag and dedicated release branch available for GitHub Actions
- **Note**: Maintenance branch `1.0.x` stays local (not pushed)

### 8. Trigger Documentation Deployment
- **Action**: Triggers GitHub Actions workflow for reference documentation
- **Commands**:
  ```bash
  gh workflow run deploy-docs.yml --repo spring-projects/spring-ai --ref 1.0.1
  ```
- **Purpose**: Deploys updated documentation for the release
- **Target**: Runs on dedicated release branch `1.0.1`

### 9. Trigger Javadoc Upload
- **Action**: Triggers GitHub Actions workflow for API documentation
- **Commands**:
  ```bash
  gh workflow run documentation-upload.yml --repo spring-projects/spring-ai --ref 1.0.1 -f releaseVersion=1.0.1
  ```
- **Purpose**: Publishes javadocs for the specific release version
- **Target**: Runs on dedicated release branch `1.0.1`

### 10. Trigger Maven Central Release
- **Action**: Triggers GitHub Actions workflow for artifact publishing
- **Commands**:
  ```bash
  gh workflow run new-maven-central-release.yml --repo spring-projects/spring-ai --ref 1.0.1
  ```
- **Purpose**: Uploads build artifacts to Maven Central
- **Target**: Runs on dedicated release branch `1.0.1`
- **🛑 WORKFLOW STOPS HERE**: Phase 1 complete, state saved

### Phase 2: Post-Maven Central Workflow

After Maven Central deployment succeeds, run with `--post-maven-central`:

### 11. Set Next Development Version  
- **Action**: Updates POM files to next development version
- **Commands**:
  ```bash
  # Set main project version
  mvnd versions:set -DnewVersion=1.0.2-SNAPSHOT -DgenerateBackupPoms=false
  
  # Set BOM module version specifically
  mvnd versions:set -DnewVersion=1.0.2-SNAPSHOT -DgenerateBackupPoms=false -pl spring-ai-bom
  ```
- **Purpose**: Prepares branch for continued development with proper BOM versioning

### 12. Commit Development Version
- **Action**: Commits development version changes
- **Commands**:
  ```bash
  git add -A
  git commit -m "Next development version 1.0.2-SNAPSHOT"
  ```
- **Purpose**: Records development version changes

### 13. Push All Changes
- **Action**: Pushes both release commit and development version changes to remote
- **Commands**:
  ```bash
  git push origin 1.0.x
  ```
- **Purpose**: Makes both release commit and development version available on maintenance branch
- **Note**: This pushes both commits that were accumulated locally during Phase 2

### 14. Update start.spring.io
- **Action**: Updates Spring Initializr with new Spring AI version
- **Commands**:
  ```bash
  git clone https://github.com/spring-io/start.spring.io.git ./start-spring-io
  cd ./start-spring-io && git checkout -b update-spring-ai-1.0.1
  # Update application.yml: spring-ai version → 1.0.1
  git add application.yml && git commit -m "Update Spring AI to 1.0.1"
  gh pr create --title "Update Spring AI to 1.0.1" --body "..."
  ```
- **Purpose**: Makes new Spring AI version available in Spring Initializr for new projects
- **Interactive**: Shows diff preview and PR details before creating pull request

### 15. Update spring-website-content
- **Action**: Updates Spring AI project documentation on the Spring website
- **Commands**:
  ```bash
  git clone https://github.com/spring-io/spring-website-content.git ./spring-website-content
  cd ./spring-website-content && git checkout -b update-spring-ai-1.0.1
  # Update content/projects/spring-ai/documentation.json:
  #   - version: 1.0.0 → 1.0.1
  #   - api.url: updated to reference 1.0.1
  #   - reference.url: unchanged (stays at major.minor level)
  git add content/projects/spring-ai/documentation.json && git commit -m "Update Spring AI documentation to 1.0.1"
  gh pr create --title "Update Spring AI documentation to 1.0.1" --body "..."
  ```
- **Purpose**: Updates Spring AI project page to reflect latest point release information
- **Interactive**: Shows changes preview and confirmation before creating pull request

## Interactive Workflow

The script provides step-by-step confirmation with **full command transparency**:

```
============================================================
SPRING AI POINT RELEASE SUMMARY
============================================================
[INFO] Target Version: 1.0.1
[INFO] Next Dev Version: 1.0.2-SNAPSHOT
[INFO] Branch: 1.0.x
[INFO] Tag: v1.0.1
[INFO] Workspace: ./spring-ai-release
[INFO] Dry Run: False
============================================================

[STEP] Start release workflow
Proceed? (Y/n): y

[STEP] Execute: Setup workspace
[INFO] Commands that will be executed:
  1. git clone https://github.com/spring-projects/spring-ai.git ./spring-ai-release
  2. cd ./spring-ai-release
  3. git checkout 1.0.x
  4. git pull origin 1.0.x
  5. Initialize Maven and GitHub helpers

Proceed? (Y/n): y
[STEP] Execute: Set release version
[INFO] Commands that will be executed:
  1. mvnd versions:set -DnewVersion=1.0.1 -DgenerateBackupPoms=false
  2. mvnd versions:set -DnewVersion=1.0.1 -DgenerateBackupPoms=false -pl spring-ai-bom

Proceed? (Y/n): y
[STEP] Execute: Build and verify
[INFO] Commands that will be executed:
  1. mvnd clean package -Dmaven.javadoc.skip=true -DskipTests
  2. ./mvnw -pl spring-ai-docs antora

Proceed? (Y/n): y
[STEP] Execute: Commit release version
[INFO] Commands that will be executed:
  1. git add -A
  2. git commit -m 'Release version 1.0.1'

Proceed? (Y/n): y
... (continues with command transparency for all steps)
[STEP] Execute: Trigger Maven Central release
[INFO] Commands that will be executed:
  1. gh workflow run new-maven-central-release.yml --repo spring-projects/spring-ai --ref 1.0.x

Proceed? (Y/n): y
```

## Safety Features

### Dry Run Mode
- Use `--dry-run` to preview all commands without execution
- Shows exactly what would be done
- Safe for testing and validation

### Version Validation
- Validates version format (X.Y.Z pattern)
- Calculates next development version automatically
- Prevents invalid version formats

### Build Verification
- **Fast Build**: Compiles code without running tests for speed
- **Documentation**: Verifies Antora documentation builds successfully
- **Failure Handling**: Stops workflow if builds fail

### Git Safety
- **Non-interactive**: Prevents git editor popups
- **Fresh Checkout**: Isolated workspace prevents conflicts
- **Atomic Operations**: Each step can be confirmed individually

### GitHub Actions Integration
- **Branch-Specific**: All workflows triggered on correct branch (1.0.1)
- **Authentication Check**: Validates GitHub CLI availability
- **Graceful Fallback**: Continues if GitHub CLI unavailable
- **Interactive Control**: Step-by-step confirmation for each workflow

### Maven Central Status Monitoring
- **Automatic Checking**: Checks Maven Central infrastructure before deployment
- **Proactive Warnings**: Alerts about active incidents or service issues
- **Publishing Health**: Specifically monitors publishing-related services
- **User Choice**: Allows proceeding despite warnings or canceling deployment

### Command Transparency
- **Full Disclosure**: Shows exact commands before execution
- **Numbered Lists**: Clear enumeration of all commands per step
- **Security Focused**: Perfect for paranoid users who need full visibility
- **Both Modes**: Works in normal and dry-run modes with appropriate labeling

## Error Handling

The script provides detailed error reporting:

```bash
[ERROR] Git command failed: git push origin 1.0.x
[ERROR] Exit code: 1
[ERROR] Stderr: Permission denied
[ERROR] Step failed: Push changes
```

### Common Issues and Solutions

**Permission Denied on Push**:
- Ensure GitHub authentication is configured
- Check repository access permissions
- Verify remote repository URL

**Build Failures**:
- Check compilation errors in Maven output
- Ensure all dependencies are available
- Verify documentation sources are valid

**Version Format Errors**:
- Use format: `X.Y.Z` (e.g., `1.0.1`, `1.0.2`)
- Avoid prefixes or suffixes
- Numbers only for each component

**GitHub CLI Issues**:
- Ensure `gh` is installed and authenticated (`gh auth login`)
- Check repository access permissions for workflow dispatch
- Verify correct repository and branch access

## Workspace Management

### Directory Structure
```
release/
├── spring-ai-point-release.py    # Main script
├── logs/                         # Build and documentation logs (gitignored)
│   ├── fast-build-{timestamp}.log  # Compilation build logs
│   └── docs-build-{timestamp}.log  # Documentation build logs
├── spring-ai-release/            # Fresh checkout (created automatically, gitignored)
│   ├── pom.xml                   # Root POM with version updates
│   ├── spring-ai-docs/           # Documentation module
│   └── ...                       # Other Spring AI modules
├── state/                        # Release state persistence (gitignored)
│   └── release-1.0.1.json        # State file for version 1.0.1
└── README.md                     # This file
```

### Cleanup
- The workspace directory (`spring-ai-release`) is automatically cleaned and recreated for each release to ensure a pristine environment
- State files in `./state/` directory persist between phases and can be manually cleaned after successful releases
- Log files in `./logs/` directory accumulate over time and can be cleaned manually or automatically archived
- All generated directories (`logs/`, `state/`, `spring-ai-release/`) are gitignored and won't be committed

## Version Strategy

### Point Release Versioning
- **Current**: `1.0.1-SNAPSHOT` (development)
- **Release**: `1.0.1` (remove snapshot)
- **Next**: `1.0.2-SNAPSHOT` (next development)

### Branch Strategy
- **Target Branch**: `1.0.x` (maintenance branch)
- **Release Commits**: Two commits per release (version + next dev)
- **Tags**: Annotated tags with `v` prefix (e.g., `v1.0.1`)

## Integration with Spring Release Process

This script handles the **technical release steps** and **automated post-release actions**:

**Automated by Script**:
- Version management and Git operations
- Build verification and documentation checks
- GitHub Actions triggering for documentation and artifacts
- Maven Central release initiation

**Manual Steps Still Required**:
- **Release Notes**: Manual creation and publishing
- **Announcement**: Communication to community
- **Verification**: Monitor GitHub Actions completion

## Development and Maintenance

### Script Architecture
- **Modular Design**: Separate classes for Git, Maven, GitHub Actions, and workflow
- **Proven Patterns**: Based on existing pr-review automation
- **Error Recovery**: Robust error handling and reporting
- **Extensible**: Easy to add new steps or modify existing ones

### Testing
Always test with `--dry-run` before executing actual releases:

```bash
# Test different scenarios
python3 spring-ai-point-release.py 1.0.1 --dry-run
python3 spring-ai-point-release.py 1.0.2 --dry-run
python3 spring-ai-point-release.py 1.1.0 --dry-run  # Should fail validation
```

## Support and Troubleshooting

### Logs and Debugging
- Script provides colored output for easy reading
- Commands are logged before execution
- Error messages include full command and output

### Recovery from Failures
If the script fails mid-process:

1. **Check the error message** for specific failure reason
2. **Manual cleanup** may be required in workspace directory
3. **Restart** from beginning after fixing issues
4. **Use dry-run** to verify fixes before re-execution

### Skip to Specific Steps

**Skip directly to Maven Central deployment (useful for re-running failed deployments):**
```bash
python3 spring-ai-point-release.py 1.0.1 --skip-to maven-central
```

**Other commonly used skip options:**
```bash
# Skip to documentation deployment
python3 spring-ai-point-release.py 1.0.1 --skip-to docs

# Skip to start.spring.io update (Phase 2 only)
python3 spring-ai-point-release.py 1.0.1 --skip-to start-spring-io

# Skip to spring-website-content update (Phase 2 only)
python3 spring-ai-point-release.py 1.0.1 --skip-to spring-website
```

## Maven Central Status Monitoring

The script automatically checks Maven Central's infrastructure status before triggering deployments to help avoid failures due to service issues.

### Automatic Status Checking

**Before Maven Central Deployment:**
The script automatically checks https://status.maven.org/ and displays warnings about:
- Active incidents affecting publishing services
- Components under maintenance or experiencing issues
- Overall system degradation

**Example Output:**
```
[INFO] Checking Maven Central infrastructure status...
⚠️  MAVEN CENTRAL STATUS WARNINGS:
  - Publishing services: Under Maintenance
  - Active incident (critical): search.maven.org is down
  - CDN - repo1.maven.org: Degraded Performance

📍 Check https://status.maven.org/ for details
💡 Consider waiting if publishing services are affected

⚠️  Publishing services may be affected - deployment could fail
Proceed with Maven Central deployment anyway? (y/N):
```

### Manual Status Check

**Check status without running release:**
```bash
python3 spring-ai-point-release.py 1.0.1 --check-maven-status
```

**Example healthy status:**
```
🔍 MAVEN CENTRAL STATUS CHECK
===================================
✅ Maven Central infrastructure appears healthy
✅ Maven Central appears ready for deployment
```

### Skip Status Check

**For urgent releases or when status API is unavailable:**
```bash
python3 spring-ai-point-release.py 1.0.1 --skip-maven-status-check
```

### Status Check Behavior

- **Network Issues**: Gracefully handles API timeouts or unavailability
- **Missing Dependencies**: Falls back gracefully if `requests` library unavailable
- **Parsing Errors**: Assumes healthy status if API response can't be parsed
- **User Control**: Always allows proceeding despite warnings

## start.spring.io Integration

The script automatically updates start.spring.io (Spring Initializr) to make new Spring AI releases available for new projects.

### Automatic Update Process

**Part of Phase 2 Workflow:**
After Maven Central deployment succeeds, the script automatically:
1. Clones https://github.com/spring-io/start.spring.io repository
2. Creates feature branch `update-spring-ai-{version}`
3. Updates `application.yml` to change Spring AI BOM version
4. Shows interactive diff preview for user confirmation
5. Creates pull request with standardized title and description

**Example Interactive Preview:**
```
📋 CHANGES PREVIEW:
File: application.yml
@@ -83,7 +83,7 @@
       spring-ai:
         groupId: org.springframework.ai
         artifactId: spring-ai-bom
         versionProperty: spring-ai.version
         mappings:
           - compatibilityRange: "[3.4.0,4.0.0-M1)"
-            version: 1.0.0
+            version: 1.0.1

🔍 Commit Message:
Update Spring AI to 1.0.1

🎯 PR Title: Update Spring AI to 1.0.1
📝 PR Body:
Updates Spring AI BOM version to 1.0.1 for compatibility with latest point release.
- Updated spring-ai version mapping from 1.0.0 to 1.0.1
- Maintains compatibility range [3.4.0,4.0.0-M1)

This change makes Spring AI 1.0.1 available in Spring Initializr for new projects.

Proceed with creating PR? (Y/n):
```

### Manual Operation

**Run only start.spring.io update:**
```bash
python3 spring-ai-point-release.py 1.0.1 --skip-to start-spring-io
```

**Skip start.spring.io update in Phase 2:**
```bash
python3 spring-ai-point-release.py 1.0.1 --post-maven-central --skip-start-spring-io
```

**Clean up repository:**
```bash
python3 spring-ai-point-release.py 1.0.1 --cleanup-start-spring-io
```

### Error Handling

- **Repository Issues**: Automatic cleanup of existing directory before clone
- **Version Already Updated**: Detects if version is already current, skips gracefully
- **GitHub CLI Issues**: Clear error messages about authentication or permissions
- **Network Problems**: Robust handling of clone and push failures
- **User Cancellation**: Allows canceling at any confirmation prompt

### Benefits

- **Immediate Availability**: New releases instantly available in Spring Initializr
- **Consistent PRs**: Standardized commit messages and PR descriptions
- **User Control**: Full transparency with diff preview before submission
- **Error Recovery**: Automatic cleanup and clear error reporting

## spring-website-content Integration

The script automatically updates spring-website-content to update Spring AI project documentation after releases.

### Automatic Update Process

**Part of Phase 2 Workflow:**
After Maven Central deployment succeeds, the script automatically:
1. Clones https://github.com/spring-io/spring-website-content repository
2. Creates feature branch `update-spring-ai-{version}`
3. Updates `content/projects/spring-ai/documentation.json` for point releases:
   - Updates `version` field (e.g., `1.0.0` → `1.0.1`)
   - Updates `api.url` to reference new version
   - Keeps `reference.url` unchanged (stays at major.minor level)
4. Shows interactive changes preview for user confirmation
5. Creates pull request with standardized title and description

**Example Interactive Preview:**
```
📋 SPRING WEBSITE CHANGES PREVIEW:
File: content/projects/spring-ai/documentation.json
  version: 1.0.0 → 1.0.1
  api.url: updated to reference 1.0.1
  reference.url: unchanged (stays at major.minor level)

Proceed with documentation.json update? (Y/n):
```

### Manual Operation

**Run only spring-website-content update:**
```bash
python3 spring-ai-point-release.py 1.0.1 --skip-to spring-website
```

**Skip spring-website-content update in Phase 2:**
```bash
python3 spring-ai-point-release.py 1.0.1 --post-maven-central --skip-spring-website
```

**Clean up repository:**
```bash
python3 spring-ai-point-release.py 1.0.1 --cleanup-spring-website
```

### Point Release Documentation Updates

For Spring AI point releases, the documentation.json file is updated with:
- **Version Field**: Updated to new point release version
- **API Documentation URL**: Updated to point to new version-specific javadocs
- **Reference Documentation URL**: Unchanged (remains at major.minor level)

This ensures the Spring AI project page shows the latest point release while maintaining stable reference documentation links.

### Error Handling

- **Repository Issues**: Automatic cleanup of existing directory before clone
- **Version Already Updated**: Detects if version is already current, skips gracefully
- **JSON Parsing**: Robust handling of documentation.json structure changes
- **GitHub CLI Issues**: Clear error messages about authentication or permissions
- **Network Problems**: Robust handling of clone and push failures
- **User Cancellation**: Allows canceling at any confirmation prompt

### Benefits

- **Immediate Documentation Updates**: Project page reflects new releases instantly
- **Consistent PRs**: Standardized commit messages and PR descriptions
- **Point Release Optimization**: Specialized handling for point vs major releases
- **User Control**: Full transparency with changes preview before submission
- **Error Recovery**: Automatic cleanup and clear error reporting

### Getting Help
- Use `--help` for command options
- Check error messages for specific guidance
- Review the workflow steps above for understanding
- Test with `--dry-run` to preview actions