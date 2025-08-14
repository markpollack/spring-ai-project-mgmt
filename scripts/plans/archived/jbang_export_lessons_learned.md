# JBang to Maven Export - Lessons Learned and Best Practices

## Issue Summary

During Phase 0 of the JBang to Maven refactoring, we encountered limitations with JBang's export functionality that required manual intervention to achieve the desired Maven project structure.

## Original Plan vs Reality

### What We Expected
```bash
/home/mark/.sdkman/candidates/jbang/current/bin/jbang export portable CollectGithubIssues.java \
  --output-dir=project \
  --group=org.springaicommunity.github.ai \
  --artifact=collection \
  --version=1.0.0-SNAPSHOT \
  --deps=org.springframework.boot:spring-boot-starter-test,org.assertj:assertj-core \
  --force
```

### What Actually Works
```bash
/home/mark/.sdkman/candidates/jbang/current/bin/jbang export maven \
  --force \
  --group=org.springaicommunity.github.ai \
  --artifact=collection \
  --version=1.0.0-SNAPSHOT \
  --output=project \
  CollectGithubIssues.java
```

## Key Limitations Discovered

### 1. Command Syntax Issues
- **Problem**: The original plan used `export portable` with unsupported flags
- **Solution**: Use `export maven` with correct flag syntax
- **Flags that work**: `--group`, `--artifact`, `--version`, `--output`, `--force`
- **Flags that don't work**: `--output-dir`, `--deps` (with test dependencies)

### 2. Test Dependencies Cannot Be Added During Export
- **Problem**: JBang export failed when trying to add test dependencies without versions
- **Root Cause**: Test dependencies like `spring-boot-starter-test` need explicit versions, but JBang export doesn't resolve them properly
- **Solution**: Add test dependencies manually to pom.xml after export

### 3. Package Structure Issues
- **Problem**: JBang export created `com.github.issues` package instead of our desired `org.springaicommunity.github.ai.collection`
- **Root Cause**: JBang derives package structure from script content, not from Maven coordinates
- **Solution**: Manual package restructuring required

### 4. Maven Configuration Incompleteness
- **Problem**: Generated pom.xml lacked Spring Boot parent, proper dependency management, and Spring Boot plugin
- **Solution**: Extensive manual pom.xml editing required

## Recommended Approach for Future JBang to Maven Conversions

### Step 1: Basic JBang Export (Automated)
```bash
# Use correct syntax for Maven export
/home/mark/.sdkman/candidates/jbang/current/bin/jbang export maven \
  --force \
  --group=org.springaicommunity.github.ai \
  --artifact=collection \
  --version=1.0.0-SNAPSHOT \
  --output=project \
  CollectGithubIssues.java
```

### Step 2: Package Structure Fix (Manual)
```bash
# Create correct package directory
mkdir -p src/main/java/org/springaicommunity/github/ai/collection

# Move Java file to correct location
mv src/main/java/com/github/issues/CollectGithubIssues.java \
   src/main/java/org/springaicommunity/github/ai/collection/

# Clean up old directory structure
rm -rf src/main/java/com

# Update package declaration in Java file
sed -i 's/package com.github.issues;/package org.springaicommunity.github.ai.collection;/' \
  src/main/java/org/springaicommunity/github/ai/collection/CollectGithubIssues.java
```

### Step 3: Maven Configuration Enhancement (Manual)
Key changes needed in pom.xml:

1. **Add Spring Boot Parent**:
```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.0</version>
    <relativePath/>
</parent>
```

2. **Add Java Version Property**:
```xml
<properties>
    <java.version>17</java.version>
</properties>
```

3. **Remove Version Numbers from Spring Dependencies** (managed by parent)

4. **Add Test Dependencies**:
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.assertj</groupId>
    <artifactId>assertj-core</artifactId>
    <scope>test</scope>
</dependency>
```

5. **Add Spring Boot Maven Plugin**:
```xml
<plugin>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-maven-plugin</artifactId>
</plugin>
```

6. **Fix Main Class Reference** in maven-jar-plugin

### Step 4: Verification (Automated)
```bash
# Verify Maven coordinates
grep -A 3 -B 3 "groupId\|artifactId\|version" pom.xml | head -12

# Verify project structure
find src -name "*.java" -type f

# Verify package declarations
find src -name "*.java" -type f -exec grep "^package" {} \;

# Test compilation
mvnd clean compile -Dmaven.javadoc.skip=true -DskipTests

# Test execution
mvnd spring-boot:run -Dspring-boot.run.arguments="--help"
```

## Script Template for Future Use

Create `jbang_to_maven_converter.sh`:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_FILE="$1"
PROJECT_DIR="$2"
GROUP_ID="$3"
ARTIFACT_ID="$4"
VERSION="${5:-1.0.0-SNAPSHOT}"

echo "Converting $SCRIPT_FILE to Maven project in $PROJECT_DIR"

# Step 1: JBang export
/home/mark/.sdkman/candidates/jbang/current/bin/jbang export maven \
  --force \
  --group="$GROUP_ID" \
  --artifact="$ARTIFACT_ID" \
  --version="$VERSION" \
  --output="$PROJECT_DIR" \
  "$SCRIPT_FILE"

cd "$PROJECT_DIR"

# Step 2: Fix package structure
PACKAGE_PATH=$(echo "$GROUP_ID" | sed 's/\./\//g')
mkdir -p "src/main/java/$PACKAGE_PATH"

# Find and move Java file
JAVA_FILE=$(find src/main/java -name "*.java" -type f | head -1)
if [ -n "$JAVA_FILE" ]; then
    mv "$JAVA_FILE" "src/main/java/$PACKAGE_PATH/"
    # Update package declaration
    sed -i "s/package [^;]*;/package $GROUP_ID;/" "src/main/java/$PACKAGE_PATH/"*.java
fi

# Clean up old structure
find src/main/java -type d -empty -delete

# Step 3: Enhance pom.xml (would need a more sophisticated approach)
echo "Manual pom.xml editing required for:"
echo "- Spring Boot parent"
echo "- Test dependencies"
echo "- Spring Boot plugin"
echo "- Main class reference"

echo "Maven project created in $PROJECT_DIR"
echo "Manual pom.xml editing still required"
```

## Key Takeaways

1. **JBang Export is a Starting Point, Not a Complete Solution**: Always expect manual configuration
2. **Test Dependencies Must Be Added Manually**: JBang export cannot handle test dependencies with proper scoping
3. **Package Structure Requires Manual Fix**: JBang doesn't respect Maven coordinates for package naming
4. **Spring Boot Integration Needs Manual Setup**: Parent POM, plugins, and proper dependency management
5. **Verification is Critical**: Always test compilation and execution after conversion

## Impact on Implementation Plan

- **Phase 0 Duration**: Extended from "Very Low Risk" to requiring significant manual intervention
- **Automation Level**: Lower than expected; approximately 60% manual work required
- **Future Planning**: Account for 2-3 hours of manual Maven configuration in similar conversions

This experience shows that while JBang export provides a good foundation, achieving a production-ready Maven project requires substantial manual configuration work.