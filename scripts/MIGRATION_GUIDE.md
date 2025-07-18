# GitHub Issues Collection - Migration Guide

## Overview

This guide helps you migrate from the Bash implementation (`collect_github_issues.sh`) to the Java implementation (`CollectGithubIssues.java`) of the GitHub Issues Collection tool.

## Quick Start

### For Existing Bash Users

If you're currently using the bash script:
```bash
./collect_github_issues.sh --repo spring-projects/spring-ai --batch-size 100
```

The equivalent Java command is:
```bash
jbang CollectGithubIssues.java --repo spring-projects/spring-ai --batch-size 100
```

## Installation Requirements

### Java Implementation Prerequisites

1. **JBang** - Java scripting tool
   ```bash
   # Install JBang
   curl -Ls https://sh.jbang.dev | bash -s - app install --fresh --force jbang
   
   # Or using package managers
   # macOS: brew install jbang
   # Linux: sdk install jbang
   ```

2. **Java 17+** - Required by Spring Boot 3.x
   ```bash
   # Check Java version
   java -version
   
   # Install if needed (using SDKMAN)
   sdk install java 17.0.7-oracle
   ```

3. **Environment Variables**
   ```bash
   export GITHUB_TOKEN=your_github_personal_access_token
   ```

## Feature Comparison

### Command Line Arguments

| Feature | Bash Script | Java Implementation | Notes |
|---------|-------------|-------------------|-------|
| Repository | `--repo` / `-r` | `--repo` / `-r` | ✅ Identical |
| Batch Size | `--batch-size` / `-b` | `--batch-size` / `-b` | ✅ Identical |
| Dry Run | `--dry-run` / `-d` | `--dry-run` / `-d` | ✅ Identical |
| Incremental | `--incremental` / `-i` | `--incremental` / `-i` | ✅ Identical |
| Verbose | `--verbose` / `-v` | `--verbose` / `-v` | ✅ Identical |
| Clean | `--clean` | `--clean` | ✅ Identical |
| Resume | `--resume` | `--resume` | ✅ Identical |
| Compress | `--compress` / `-c` | `--compress` / `-c` | ❌ Not implemented in Java |

### Configuration

| Feature | Bash Script | Java Implementation |
|---------|-------------|-------------------|
| Environment Variables | ✅ Multiple env vars | ✅ GITHUB_TOKEN only |
| Config File | ❌ Not supported | ✅ application.yaml |
| Default Values | ✅ Hardcoded | ✅ Configurable |
| Validation | ✅ Basic | ✅ Comprehensive |

### Output Format

| Feature | Bash Script | Java Implementation |
|---------|-------------|-------------------|
| JSON Structure | ✅ Batch files | ✅ Identical structure |
| Metadata | ✅ metadata.json | ✅ Compatible format |
| File Naming | ✅ issues_batch_XXX.json | ✅ Identical |
| Directory Structure | ✅ issues/raw/closed/ | ✅ Identical |

## Migration Steps

### Step 1: Verify Prerequisites

```bash
# Check if jbang is installed
jbang --version

# Check if Java 17+ is available
java -version

# Verify GitHub token
echo $GITHUB_TOKEN
```

### Step 2: Test with Dry Run

```bash
# Test the Java implementation
jbang CollectGithubIssues.java --repo spring-projects/spring-ai --dry-run --verbose

# Compare with bash version
./collect_github_issues.sh --repo spring-projects/spring-ai --dry-run --verbose
```

### Step 3: Run Side-by-Side Comparison

```bash
# Use provided comparison script
./compare_implementations.sh
```

### Step 4: Verify Data Compatibility

```bash
# Use provided verification script
./verify_data_compatibility.sh
```

### Step 5: Performance Benchmarking

```bash
# Run performance comparison
./benchmark_performance.sh
```

### Step 6: Full Migration

Once satisfied with testing, replace your bash script usage with Java:

```bash
# Old way
./collect_github_issues.sh --repo spring-projects/spring-ai --batch-size 100

# New way
jbang CollectGithubIssues.java --repo spring-projects/spring-ai --batch-size 100
```

## Configuration Migration

### Environment Variables

**Bash script supports:**
```bash
export ISSUE_BATCH_SIZE=100
export ISSUE_MAX_RETRIES=3
export ISSUE_RETRY_DELAY=5
export ISSUE_LARGE_THRESHOLD=50
export ISSUE_SIZE_THRESHOLD=102400
```

**Java implementation uses application.yaml:**
```yaml
github:
  issues:
    batch-size: 100
    max-retries: 3
    retry-delay: 5
    large-issue-threshold: 50
    size-threshold: 102400
```

### Creating Your Configuration

1. **Copy the default configuration:**
   ```bash
   cp application.yaml my-config.yaml
   ```

2. **Customize settings:**
   ```yaml
   github:
     issues:
       default-repository: my-org/my-repo
       batch-size: 200
       max-retries: 5
   ```

3. **Use custom configuration:**
   ```bash
   jbang CollectGithubIssues.java --spring.config.location=my-config.yaml
   ```

## Feature Equivalency

### Bash-only Features

These features are **not available** in the Java implementation:

1. **Compression** (`--compress` flag)
   - **Reason**: Deemed unnecessary - focus on other features
   - **Workaround**: Use external compression tools if needed

2. **Individual Large Issue Files**
   - **Reason**: Java uses adaptive batching instead
   - **Benefit**: Better performance and simpler file management

### Java-only Features

These features are **only available** in the Java implementation:

1. **Configuration File Support**
   - **Benefit**: Centralized configuration management
   - **Usage**: `application.yaml` with Spring Boot properties

2. **Enhanced Input Validation**
   - **Benefit**: Better error messages and validation
   - **Features**: Format validation, range checking, detailed errors

3. **Comprehensive Logging**
   - **Benefit**: Better debugging and monitoring
   - **Features**: Structured logging, log levels, file rotation

4. **Rate Limiting with Exponential Backoff**
   - **Benefit**: More robust API handling
   - **Features**: Intelligent retry, backoff strategies, jitter

5. **Progress Reporting**
   - **Benefit**: Better visibility into collection progress
   - **Features**: Real-time statistics, performance metrics

## Troubleshooting

### Common Migration Issues

1. **JBang not found**
   ```bash
   # Solution: Install JBang
   curl -Ls https://sh.jbang.dev | bash -s - app install --fresh --force jbang
   ```

2. **Java version too old**
   ```bash
   # Solution: Install Java 17+
   sdk install java 17.0.7-oracle
   ```

3. **Spring Boot startup issues**
   ```bash
   # Solution: Ensure no web server conflicts
   # Java implementation uses WebApplicationType.NONE
   ```

4. **Configuration not loading**
   ```bash
   # Solution: Check application.yaml location
   # Must be in same directory as CollectGithubIssues.java
   ```

5. **GitHub API rate limits**
   ```bash
   # Solution: Java implementation has better rate limiting
   # Configure in application.yaml:
   github:
     issues:
       max-retries: 5
       retry-delay: 10
   ```

### Performance Considerations

1. **Startup Time**
   - **Bash**: Faster startup (immediate)
   - **Java**: Slower startup (JVM initialization)
   - **Recommendation**: Java better for large collections

2. **Memory Usage**
   - **Bash**: Lower memory footprint
   - **Java**: Higher memory usage but better garbage collection
   - **Recommendation**: Java better for production use

3. **Error Recovery**
   - **Bash**: Basic error handling
   - **Java**: Comprehensive error recovery with resume capability
   - **Recommendation**: Java better for reliability

## Testing Your Migration

### Validation Checklist

- [ ] JBang installed and working
- [ ] Java 17+ available
- [ ] GitHub token configured
- [ ] Dry run test successful
- [ ] Data format compatibility verified
- [ ] Performance acceptable
- [ ] Configuration migrated
- [ ] Error handling tested
- [ ] Resume functionality tested

### Test Commands

```bash
# Basic functionality test
jbang CollectGithubIssues.java --help

# Configuration test
jbang CollectGithubIssues.java --repo spring-projects/spring-ai --dry-run

# Resume test (interrupt and restart)
jbang CollectGithubIssues.java --repo spring-projects/spring-ai --resume

# Error handling test (invalid repo)
jbang CollectGithubIssues.java --repo invalid/repo --dry-run
```

## Rollback Plan

If you need to rollback to the bash implementation:

1. **Keep both implementations** during migration period
2. **Maintain existing bash scripts** until fully validated
3. **Document any custom configurations** used with Java
4. **Test rollback procedure** before full migration

```bash
# Rollback command
./collect_github_issues.sh --repo spring-projects/spring-ai --batch-size 100
```

## Support and Next Steps

### Getting Help

1. **Documentation**: Check this migration guide
2. **Comparison Tools**: Use provided scripts to compare implementations
3. **Logs**: Check application logs for detailed error information
4. **Configuration**: Verify application.yaml settings

### Best Practices

1. **Start with dry runs** to test functionality
2. **Use provided comparison scripts** to verify compatibility
3. **Keep both implementations** during transition period
4. **Test resume functionality** with actual data
5. **Monitor performance** in your environment
6. **Update any automation** that depends on the tool

### Future Enhancements

The Java implementation provides a foundation for:
- **Web UI**: Potential Spring Boot web interface
- **Database Storage**: Direct database integration
- **Metrics**: Enhanced monitoring and metrics
- **API**: RESTful API for programmatic access
- **Scheduling**: Built-in scheduling capabilities

## Conclusion

The Java implementation provides enhanced reliability, better error handling, and more configuration options while maintaining full compatibility with the bash version's data format and core functionality.

The migration process is designed to be gradual and safe, with comprehensive testing tools to ensure compatibility and performance meet your requirements.

---

**Migration Support**: For questions or issues during migration, refer to the comparison and verification scripts provided, or check the detailed logs generated by the Java implementation.