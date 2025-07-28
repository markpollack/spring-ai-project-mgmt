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
# Test the release workflow without making changes
python3 spring-ai-point-release.py 1.0.1 --dry-run

# Execute the actual release
python3 spring-ai-point-release.py 1.0.1

# Use a different branch (if needed)
python3 spring-ai-point-release.py 1.0.1 --branch 1.0.x
```

## Command Line Options

```
python3 spring-ai-point-release.py [OPTIONS] VERSION

Arguments:
  VERSION               Target release version (e.g., 1.0.1, 1.0.2)

Options:
  --branch BRANCH       Branch to release from (default: 1.0.x)
  --dry-run            Preview commands without executing them
  --workspace PATH      Override workspace directory (default: ./spring-ai-release)
  --help               Show help message and exit
```

## Release Workflow Steps

The script executes the following steps in order, with user confirmation at each stage:

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
- **Action**: Updates all POM files to release version
- **Commands**:
  ```bash
  # Set main project version
  mvnd versions:set -DnewVersion=1.0.1 -DgenerateBackupPoms=false
  
  # Set BOM module version specifically
  mvnd versions:set -DnewVersion=1.0.1 -DgenerateBackupPoms=false -pl spring-ai-bom
  ```
- **Purpose**: Removes `-SNAPSHOT` suffix and sets exact release version in all modules including BOM

### 3. Build and Verify
- **Action**: Performs fast compilation and documentation verification
- **Commands**:
  ```bash
  # Fast build without tests and javadoc
  mvnd clean package -Dmaven.javadoc.skip=true -DskipTests
  
  # Verify documentation builds correctly
  ./mvnw -pl spring-ai-docs antora
  ```
- **Purpose**: Ensures code compiles and documentation generates successfully

### 4. Commit Release Version
- **Action**: Commits version changes
- **Commands**:
  ```bash
  git add -A
  git commit -m "Release version 1.0.1"
  ```
- **Purpose**: Creates commit with release version changes

### 5. Create Release Tag
- **Action**: Creates annotated Git tag
- **Commands**:
  ```bash
  git tag -a v1.0.1 -m "Release version 1.0.1"
  ```
- **Purpose**: Marks the exact commit for the release

### 6. Set Next Development Version
- **Action**: Updates POM files to next development version
- **Commands**:
  ```bash
  # Set main project version
  mvnd versions:set -DnewVersion=1.0.2-SNAPSHOT -DgenerateBackupPoms=false
  
  # Set BOM module version specifically
  mvnd versions:set -DnewVersion=1.0.2-SNAPSHOT -DgenerateBackupPoms=false -pl spring-ai-bom
  ```
- **Purpose**: Prepares branch for continued development with proper BOM versioning

### 7. Commit Development Version
- **Action**: Commits development version changes
- **Commands**:
  ```bash
  git add -A
  git commit -m "Next development version 1.0.2-SNAPSHOT"
  ```
- **Purpose**: Separates release and development version commits

### 8. Push Changes
- **Action**: Pushes commits and tags to remote repository
- **Commands**:
  ```bash
  git push origin 1.0.x
  git push origin v1.0.1
  ```
- **Purpose**: Makes release publicly available

### 9. Trigger Documentation Deployment
- **Action**: Triggers GitHub Actions workflow for reference documentation
- **Commands**:
  ```bash
  gh workflow run deploy-docs.yml --repo spring-projects/spring-ai --ref 1.0.x
  ```
- **Purpose**: Deploys updated documentation for the release

### 10. Trigger Javadoc Upload
- **Action**: Triggers GitHub Actions workflow for API documentation
- **Commands**:
  ```bash
  gh workflow run documentation-upload.yml --repo spring-projects/spring-ai --ref 1.0.x -f releaseVersion=1.0.1
  ```
- **Purpose**: Publishes javadocs for the specific release version

### 11. Trigger Maven Central Release
- **Action**: Triggers GitHub Actions workflow for artifact publishing
- **Commands**:
  ```bash
  gh workflow run new-maven-central-release.yml --repo spring-projects/spring-ai --ref 1.0.x
  ```
- **Purpose**: Uploads build artifacts to Maven Central (final step)

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
- **Branch-Specific**: All workflows triggered on correct branch (1.0.x)
- **Authentication Check**: Validates GitHub CLI availability
- **Graceful Fallback**: Continues if GitHub CLI unavailable
- **Interactive Control**: Step-by-step confirmation for each workflow

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
├── spring-ai-release/            # Fresh checkout (created automatically)
│   ├── pom.xml                   # Root POM with version updates
│   ├── spring-ai-docs/           # Documentation module
│   └── ...                       # Other Spring AI modules
└── README.md                     # This file
```

### Cleanup
The workspace directory (`spring-ai-release`) is automatically cleaned and recreated for each release to ensure a pristine environment.

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

### Getting Help
- Use `--help` for command options
- Check error messages for specific guidance
- Review the workflow steps above for understanding
- Test with `--dry-run` to preview actions