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
- Fresh repository checkout in isolated workspace (`./spring-ai-release`)
- Interactive step-by-step workflow with user confirmations
- Dual version management (main project + spring-ai-bom module)
- Fast compilation with `mvnd` and documentation verification
- Git operations including tagging and pushing to 1.0.x branch
- Dry-run mode for safe testing and validation
- Automatic next development version calculation

**Key Commands Executed**:
```bash
# Version setting (both main and BOM)
mvnd versions:set -DnewVersion=1.0.1 -DgenerateBackupPoms=false
mvnd versions:set -DnewVersion=1.0.1 -DgenerateBackupPoms=false -pl spring-ai-bom

# Fast build and docs verification
mvnd clean package -Dmaven.javadoc.skip=true -DskipTests
./mvnw -pl spring-ai-docs antora

# Git operations
git commit -m "Release version 1.0.1"
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin 1.0.x && git push origin v1.0.1
```

**Usage**:
```bash
# Test with dry-run
python3 spring-ai-point-release.py 1.0.1 --dry-run

# Execute actual release
python3 spring-ai-point-release.py 1.0.1

# Custom branch
python3 spring-ai-point-release.py 1.0.2 --branch 1.0.x
```

**Requirements**:
- Python 3.7+
- Git with push access to spring-projects/spring-ai
- Maven or Maven Daemon (`mvnd`) for builds
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
- ✅ **Build Verification**: Fast compilation and documentation builds
- ✅ **Git Operations**: Automated tagging and branch management
- ✅ **Interactive Workflow**: Step-by-step confirmations with dry-run mode
- ✅ **Contributor Acknowledgment**: Author extraction with `get-authors-2.sh`

## Future Enhancements

Additional release automation may include:
- Changelog generation from commit history
- Release note templating and automation
- Cross-project dependency updates
- Integration with CI/CD pipelines
- Automated artifact verification