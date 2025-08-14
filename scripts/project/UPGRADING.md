# Upgrading to Multi-Module GitHub Issues Collection

This document provides guidance for migrating from the single-module to the multi-module architecture of the GitHub Issues Collection project.

## Overview

The project has been refactored from a single Maven module to a multi-module structure:

**Previous Structure:**
```
project/
├── pom.xml
└── src/
    ├── main/java/.../collection/
    │   └── [All classes in single module]
    └── test/java/.../collection/
        └── [All tests in single module]
```

**New Structure:**
```
project/
├── pom.xml (parent)
├── collection-library/
│   ├── pom.xml
│   └── src/
│       ├── main/java/.../collection/
│       │   └── [Reusable library classes]
│       └── test/java/.../collection/
│           └── [Library tests]
└── collection-app/
    ├── pom.xml
    └── src/
        ├── main/java/.../collection/app/
        │   └── CollectGithubIssuesApp.java
        └── test/java/.../collection/app/
            └── [Integration tests]
```

## Breaking Changes

### 1. Nested Classes Removed

All nested classes have been extracted to individual files to eliminate `$` notation in compiled code:

**DataModels.java → Individual Record Classes:**
- `DataModels.Issue` → `Issue`
- `DataModels.Comment` → `Comment`
- `DataModels.Author` → `Author`
- `DataModels.Label` → `Label`
- `DataModels.CollectionMetadata` → `CollectionMetadata`
- `DataModels.CollectionRequest` → `CollectionRequest`
- `DataModels.CollectionResult` → `CollectionResult`
- `DataModels.BatchData` → `BatchData`
- `DataModels.CollectionStats` → `CollectionStats`
- `DataModels.ResumeState` → `ResumeState`

**Other Separated Classes:**
- `ArgumentParser.ParsedConfiguration` → `ParsedConfiguration`
- `ConfigurationSupport.GitHubConfig` → `GitHubConfig`
- `ConfigurationSupport.CollectionProperties` → `CollectionProperties`
- `GitHubServices.GitHubRestService` → `GitHubRestService`
- `GitHubServices.GitHubGraphQLService` → `GitHubGraphQLService`
- `GitHubServices.JsonNodeUtils` → `JsonNodeUtils`

### 2. Package Changes

- **Library classes**: `org.springaicommunity.github.ai.collection.*`
- **CLI application**: `org.springaicommunity.github.ai.collection.app.*`

### 3. Main Class Changes

- **Old**: `CollectGithubIssues`
- **New**: `CollectGithubIssuesApp` (in app module)

## Migration Guide

### For Library Users

If you were using this project as a dependency, update your dependency coordinates:

**Old (Single Module):**
```xml
<dependency>
    <groupId>org.springaicommunity.github.ai</groupId>
    <artifactId>collection</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
```

**New (Library Module):**
```xml
<dependency>
    <groupId>org.springaicommunity.github.ai</groupId>
    <artifactId>collection-library</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
```

### For Code Using Old Classes

Update import statements to use individual classes instead of nested classes:

**Old:**
```java
import static org.springaicommunity.github.ai.collection.DataModels.*;
import org.springaicommunity.github.ai.collection.ArgumentParser.ParsedConfiguration;
```

**New:**
```java
import org.springaicommunity.github.ai.collection.Issue;
import org.springaicommunity.github.ai.collection.Comment;
import org.springaicommunity.github.ai.collection.Author;
import org.springaicommunity.github.ai.collection.Label;
import org.springaicommunity.github.ai.collection.CollectionRequest;
import org.springaicommunity.github.ai.collection.CollectionResult;
import org.springaicommunity.github.ai.collection.ParsedConfiguration;
// ... other individual imports as needed
```

### For CLI Users

**Running the Application:**

**Old:**
```bash
java -jar collection-1.0.0-SNAPSHOT.jar [options]
```

**New:**
```bash
java -jar collection-app-1.0.0-SNAPSHOT.jar [options]
```

The command-line interface and all options remain identical.

## Build Instructions

### Library Module

To build just the library (for use as a dependency):

```bash
mvnd clean install -pl collection-library
```

### CLI Application

To build the complete CLI application with uber jar:

```bash
mvnd clean package
# Uber jar: collection-app/target/collection-app-1.0.0-SNAPSHOT.jar
```

### Multi-Module Build

To build everything:

```bash
# Unit tests only
mvnd clean test

# Full build with integration tests
mvnd clean verify -Pintegration-tests

# Package without tests
mvnd clean package -DskipTests
```

## Module Responsibilities

### collection-library

**Purpose**: Reusable library for GitHub API integration
**Packaging**: Standard JAR
**Dependencies**: Spring Framework (not Spring Boot)

**Contains:**
- Data models (records)
- Service classes
- Configuration classes
- Argument parsing utilities

**For external projects that want to:**
- Integrate GitHub issue collection functionality
- Use the data models
- Leverage the service components

### collection-app

**Purpose**: CLI application for direct use
**Packaging**: Spring Boot executable JAR (uber jar)
**Dependencies**: Spring Boot + collection-library

**Contains:**
- Command-line application
- Integration tests
- Complete runtime environment

**For users who want to:**
- Run the tool directly
- Use as a standalone application

## Configuration

Configuration remains unchanged - use the same `application.yaml` properties and command-line arguments.

## Testing

### Unit Tests
Run library unit tests:
```bash
mvnd test -pl collection-library
```

### Integration Tests  
Run real API integration tests:
```bash
mvnd clean verify -Pintegration-tests
```

Integration tests require:
- `GITHUB_TOKEN` environment variable
- Internet connectivity
- Access to GitHub API

## Installation to Local Repository

Install both modules to local Maven repository:

```bash
mvnd clean install
```

This installs:
- `collection-library-1.0.0-SNAPSHOT.jar` (for dependencies)
- `collection-app-1.0.0-SNAPSHOT.jar` (for CLI usage)

## Compatibility

### Fully Compatible
- Command-line interface and arguments
- Configuration files and properties
- Environment variables
- Output formats and file structures

### Requires Updates
- Import statements (if using as library)
- Dependency coordinates in `pom.xml`
- Main class references in scripts

## Troubleshooting

### Common Issues

1. **Import errors after upgrade**
   - Remove static imports of `DataModels.*`
   - Add individual imports for record classes

2. **ClassNotFoundException for nested classes**
   - Update to use individual class names
   - Check package names for app classes

3. **Wrong JAR file for CLI**
   - Use `collection-app/target/collection-app-1.0.0-SNAPSHOT.jar`
   - Not the `.jar.original` file

4. **Dependency resolution issues**
   - Ensure you're using `collection-library` artifact
   - Verify version matches your local install
   - Check Maven local repository: `~/.m2/repository/org/springaicommunity/github/ai/`

### Support

- Check the multi-module build with: `mvnd clean compile`
- Run tests to verify everything works: `mvnd test`
- For integration issues: `mvnd clean verify -Pintegration-tests`

## Benefits of Multi-Module Structure

1. **Clean separation**: Library vs. application concerns
2. **Reusability**: Library can be used by other projects
3. **No $ notation**: Individual classes eliminate nested class artifacts
4. **Better dependency management**: Library has minimal dependencies
5. **Flexible deployment**: Use library-only or full application as needed
6. **Maintainability**: Clear module boundaries and responsibilities