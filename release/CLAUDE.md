# Spring AI Release Scripts

This directory contains scripts and tooling for managing Spring AI project releases.

## Directory Purpose

The `/release` directory houses specialized scripts for:
- Release preparation and management
- Contributor acknowledgment generation
- Release documentation automation
- Version-specific workflow automation

## Available Scripts

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

- Support Milestone (M1, M2, M3) releases
- Support Release Candidate (RC) releases  
- Support General Availability (GA) releases
- Generate contributor acknowledgments for release notes
- Automate repetitive release preparation tasks

## Usage Notes

- Scripts should be run from the Spring AI repository directory
- Ensure GitHub CLI is authenticated before running scripts
- Review generated contributor lists before including in release notes
- Scripts use hardcoded paths - verify paths match your environment

## Future Enhancements

Additional release automation scripts may be added for:
- Changelog generation
- Version tagging automation
- Release note templating
- Cross-project dependency updates