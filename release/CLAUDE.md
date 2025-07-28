# Spring AI Release Scripts

This directory contains scripts and tooling for managing Spring AI project releases.

## Directory Purpose

The `/release` directory houses specialized scripts for:
- Release preparation and management
- Contributor acknowledgment generation
- Release documentation automation
- Version-specific workflow automation

## Available Scripts

### spring-ai-point-release.py
**Purpose**: Automate complete point release workflow for Spring AI 1.0.x branch

**Functionality**:
- **Two-phase workflow** for safer Maven Central integration
- Fresh repository checkout in isolated workspace (`./spring-ai-release`)
- Interactive step-by-step workflow with user confirmations
- **Full command transparency** - shows exact commands before execution
- **State persistence** - saves progress between phases in `./state/` directory
- Dual version management (main project + spring-ai-bom module)
- Fast compilation with `mvnd` and documentation verification
- Git operations including tagging and pushing to 1.0.x branch
- GitHub Actions automation for post-release publishing
- Dry-run mode for safe testing and validation
- **Risk reduction** - development version changes only after Maven Central success

**Enhanced Build Output Management**:
- **Output Suppression**: No scrolling Maven output during interactive execution
- **Comprehensive Logging**: Timestamped log files in `./logs/` directory
- **mvnd Optimization**: Advanced suppression flags (`-q`, `-Dmvnd.rollingWindowSize=0`)
- **Environment Control**: `MVND_TERMINAL=false`, `CI=true`, `NO_COLOR=1`, `TERM=dumb`
- **Error Handling**: Log file previews (last 10 lines) on build failures

**Version Verification System**:
- **POM Validation**: Verifies root pom.xml and spring-ai-bom/pom.xml versions
- **SNAPSHOT Detection**: Comprehensive grep-based check for remaining SNAPSHOT references
- **Release Safety**: Workflow stops if version verification fails

**Key Commands Executed**:
```bash
# Version setting with verification (both main and BOM)
mvnd versions:set -DnewVersion=1.0.1 -DgenerateBackupPoms=false
mvnd versions:set -DnewVersion=1.0.1 -DgenerateBackupPoms=false -pl spring-ai-bom
# Verify pom.xml and spring-ai-bom/pom.xml have correct versions
# Check all POM files for SNAPSHOT versions (should find none)

# Fast build and docs verification (output logged to files)
mvnd clean package -Dmaven.javadoc.skip=true -DskipTests  # -> logs/fast-build-{timestamp}.log
./mvnw -pl spring-ai-docs antora                         # -> logs/docs-build-{timestamp}.log

# Git operations
git commit -m "Release version 1.0.1"
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin 1.0.x && git push origin v1.0.1

# GitHub Actions automation (post-release)
gh workflow run deploy-docs.yml --repo spring-projects/spring-ai --ref 1.0.x
gh workflow run documentation-upload.yml --repo spring-projects/spring-ai --ref 1.0.x -f releaseVersion=1.0.1
gh workflow run new-maven-central-release.yml --repo spring-projects/spring-ai --ref 1.0.x
```

**Two-Phase Usage**:
```bash
# Phase 1: Main release workflow (stops at Maven Central trigger)
python3 spring-ai-point-release.py 1.0.1 --dry-run
python3 spring-ai-point-release.py 1.0.1

# Phase 2: After Maven Central deployment succeeds
python3 spring-ai-point-release.py 1.0.1 --post-maven-central

# Custom branch
python3 spring-ai-point-release.py 1.0.2 --branch 1.0.x
```

**Requirements**:
- Python 3.7+
- Git with push access to spring-projects/spring-ai
- Maven or Maven Daemon (`mvnd`) for builds
- GitHub CLI (`gh`) authenticated for post-release automation
- Target version as required parameter (e.g., 1.0.1, 1.0.2)

### get-authors-2.sh
**Purpose**: Generate contributor acknowledgments for releases

**Functionality**:
- Extracts commit authors since a specified date (currently April 31, 2025)
- Fetches GitHub profile information for each contributor
- Creates deduplicated contributor lists with GitHub profile links
- Generates multiple output formats (raw, temp, final)

**Output Files** (created in `/home/mark/scripts/output-rc1`):
- `contributors_raw.md` - Raw commit data with full details
- `contributors_temp.md` - Intermediate processing file
- `contributors.md` - Final deduplicated contributor list

**Usage**:
```bash
./get-authors-2.sh
```

**Requirements**:
- GitHub CLI (`gh`) authenticated
- Access to Spring AI repository at `/home/mark/projects/spring-ai`
- Output directory `/home/mark/scripts/output-rc1` must be accessible

## Release Workflow Integration

These scripts integrate with the main Spring AI project management workflow documented in the parent directory's CLAUDE.md:

- **Point Releases**: Automated 1.0.x branch releases (1.0.1, 1.0.2, etc.)
- **Milestone Releases**: Support for M1, M2, M3 releases
- **Release Candidate**: Support for RC releases  
- **General Availability**: Support for GA releases
- **Contributor Acknowledgment**: Generate contributor lists for release notes
- **Release Automation**: Automate repetitive release preparation tasks

The `spring-ai-point-release.py` script specifically handles the technical release workflow for point releases, while other scripts support release documentation and contributor recognition.

## Usage Notes

- Scripts should be run from the Spring AI repository directory
- Ensure GitHub CLI is authenticated before running scripts
- Review generated contributor lists before including in release notes
- Scripts use hardcoded paths - verify paths match your environment

## Current Capabilities

**Implemented Features**:
- ✅ **Point Release Automation**: Complete 1.0.x workflow with `spring-ai-point-release.py`
- ✅ **Version Management**: Dual version setting (main + BOM module)
- ✅ **Version Verification**: Comprehensive POM validation and SNAPSHOT detection
- ✅ **Build Output Management**: No scrolling output with comprehensive logging
- ✅ **Build Verification**: Fast compilation and documentation builds with mvnd optimization
- ✅ **Git Operations**: Automated tagging and branch management
- ✅ **GitHub Actions Integration**: Post-release automation (docs, javadocs, Maven Central)
- ✅ **Two-Phase Workflow**: Safer Maven Central integration with state persistence
- ✅ **Interactive Workflow**: Step-by-step confirmations with dry-run mode
- ✅ **Command Transparency**: Full disclosure of exact commands before execution
- ✅ **Error Handling**: Build log previews and debugging support
- ✅ **Risk Reduction**: Development version changes only after Maven Central success
- ✅ **Contributor Acknowledgment**: Author extraction with `get-authors-2.sh`

## Future Enhancements

Additional release automation may include:
- Changelog generation from commit history
- Release note templating and automation
- Cross-project dependency updates
- Integration with CI/CD pipelines
- Automated artifact verification