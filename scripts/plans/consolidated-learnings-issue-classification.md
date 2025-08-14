# Consolidated Learnings for Issue Classification Module Implementation

## Executive Summary

This document consolidates critical learnings from Phases 1-5 of the GitHub Issues Collection module refactoring and the JBang export experience to guide the implementation of the new Issue Classification module. These learnings provide essential safety protocols, testing strategies, and architectural patterns that must be followed to avoid production data operations and ensure successful module creation.

## 🚨 CRITICAL SAFETY PROTOCOLS

### The CommandLineRunner Danger

**CRITICAL UNDERSTANDING**: The existing application implements `CommandLineRunner`, which means ANY use of `@SpringBootTest` in tests will automatically trigger the main application's `run()` method, causing:
- Real GitHub API calls
- Production data collection 
- Generation of hundreds/thousands of files
- API rate limit consumption

**MANDATORY RULE**: NEVER use `@SpringBootTest` in any test class for the classification module.

### Safe Testing Hierarchy

```java
// ✅ SAFE: Plain JUnit for pure Java classes
@DisplayName("Classification Tests - Plain JUnit Only")
class ClassificationTest {
    // No Spring context, no production risk
}

// ✅ SAFE: Minimal Spring context for configuration
@SpringJUnitConfig
@Import({TestConfig.class})
class ConfigurationTest {
    @TestConfiguration
    static class TestConfig {
        // Only required beans, NO CommandLineRunner
    }
}

// ❌ DANGEROUS: Full Spring context
@SpringBootTest  // NEVER USE THIS
class DangerousTest {
    // Will trigger CommandLineRunner and production operations
}
```

## 📋 Module Implementation Strategy

### Phase-Based Approach (Proven Successful)

Based on the successful 5-phase extraction, follow this pattern for the classification module:

#### Task 1: Module Setup (Apply Phase 0 & 1 Learnings)
**Critical Learnings to Apply:**
- Maven module creation requires manual configuration beyond basic generation
- Spring Boot parent POM essential for dependency management
- Package structure must be correctly established from the start
- Test dependencies need explicit configuration with proper scoping

**Implementation Checklist:**
```bash
# 1. Create module directory structure
mkdir -p classification-engine/src/main/java/org/springaicommunity/github/ai/classification/{domain,service,config,util,evaluation}
mkdir -p classification-engine/src/test/java/org/springaicommunity/github/ai/classification
mkdir -p classification-engine/src/test/resources

# 2. Create pom.xml with Spring Boot parent
# 3. Add to parent POM modules section
# 4. Configure dependencies including Claude Code SDK
```

#### Task 2: Domain Models (Apply Phase 1 Learnings)
**Critical Learnings:**
- Java records provide structural immutability, not deep immutability
- Use `List.of()` for immutable collections in records
- Plain JUnit tests are sufficient for data models
- No Spring context needed for record testing

**Safe Testing Pattern:**
```java
@DisplayName("ClassificationResult Tests - Plain JUnit")
class ClassificationResultTest {
    @Test
    void shouldCreateRecordWithImmutableCollections() {
        var result = new ClassificationResult(
            1234,
            List.of(new LabelPrediction("vector store", 0.9)),
            "Explicitly mentions vector database"
        );
        // Test record behavior without Spring
    }
}
```

#### Task 3-5: Service Implementation (Apply Phase 2-4 Learnings)
**Critical Learnings:**
- Constructor-based dependency injection for all services
- Mock all external dependencies in tests
- Services should be pure Java where possible
- Spring's component scanning eliminates explicit imports

**Service Design Pattern:**
```java
@Service
public class LabelNormalizationService {
    private final CollectionProperties properties;
    
    // Constructor injection
    public LabelNormalizationService(CollectionProperties properties) {
        this.properties = properties;
    }
    
    // Pure Java implementation
}
```

**Safe Testing Pattern:**
```java
class LabelNormalizationServiceTest {
    @Mock
    private CollectionProperties mockProperties;
    
    private LabelNormalizationService service;
    
    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        service = new LabelNormalizationService(mockProperties);
    }
    
    // Test with mocked dependencies
}
```

#### Task 6-10: LLM Integration (Apply Phase 5 Learnings - Highest Risk)
**Critical Learnings from Phase 5 (780+ lines extraction):**
- This is the HIGHEST RISK phase - contains LLM integration
- Use @TempDir for ALL file operations
- Mock Claude Code SDK completely in tests
- NEVER allow real LLM calls during testing

**Claude Code SDK Integration Pattern:**
```java
@Service
public class LLMClassificationService {
    private static final String CLASSIFICATION_PROMPT_PATH = "/prompts/classification.md";
    
    public ClassificationResult classifyWithLLM(List<Issue> batch) {
        // Load prompt from resources
        String systemPrompt = loadPromptFromResources(CLASSIFICATION_PROMPT_PATH);
        
        // Prepare batch JSON
        String batchJson = prepareBatchJson(batch);
        
        // Call Claude Code SDK (MUST BE MOCKED IN TESTS)
        QueryResult result = Query.execute(batchJson, CLIOptions.builder()
            .model("claude-3-sonnet-20240229")
            .systemPrompt(systemPrompt)
            .maxTokens(2000)
            .timeout(Duration.ofSeconds(30))
            .build());
        
        // Parse and return results
        return parseClassificationResult(result);
    }
}
```

**MANDATORY Testing Approach:**
```java
class LLMClassificationServiceTest {
    @TempDir
    Path tempDir;  // File operations ONLY in temp directory
    
    @Mock
    private Query mockQuery;  // NEVER real LLM calls
    
    @Test
    void shouldClassifyBatchWithMockedLLM() {
        // Mock the Query.execute static method
        try (MockedStatic<Query> mockedQuery = mockStatic(Query.class)) {
            QueryResult mockResult = createMockQueryResult();
            mockedQuery.when(() -> Query.execute(any(), any()))
                      .thenReturn(mockResult);
            
            // Test classification without real LLM calls
        }
    }
}
```

## 🔐 Safety Verification Checklist

### Before EVERY Test Run

1. **Verify Test Annotations:**
   ```bash
   # Check for dangerous annotations
   grep -r "@SpringBootTest" classification-engine/src/test/
   # Should return NOTHING
   ```

2. **Verify No Main Class Imports:**
   ```bash
   # Check for main application imports
   grep -r "import.*CollectGithubIssues" classification-engine/src/test/
   # Should return NOTHING
   ```

3. **Check Working Directory:**
   ```bash
   # Ensure no production files exist
   ls -la issues/ 2>/dev/null && echo "WARNING: issues/ exists!"
   ls -la batch_* 2>/dev/null && echo "WARNING: batch files exist!"
   ```

### Emergency Response Protocol

**If Production Operations Start During Testing:**
1. **IMMEDIATELY** press Ctrl+C
2. Run cleanup:
   ```bash
   rm -rf issues/ logs/ batch_*
   git status  # Verify no production files staged
   ```
3. Fix test configuration before retrying
4. Document the issue in learnings

## 🏗️ Architectural Patterns

### Clean Migration Approach (Proven in All Phases)

**Two-Step Process:**
1. **Create New**: Build complete new module/class with tests
2. **Remove Old**: Only after new is working, remove old code

**Benefits:**
- No namespace conflicts
- No compilation errors
- Safe rollback if needed
- Clear validation point

### Dependency Injection Pattern

```java
// ✅ CORRECT: Constructor injection
@Service
public class ClassificationService {
    private final LabelNormalizationService labelService;
    private final LLMClassificationService llmService;
    
    public ClassificationService(
            LabelNormalizationService labelService,
            LLMClassificationService llmService) {
        this.labelService = labelService;
        this.llmService = llmService;
    }
}

// ❌ WRONG: Field injection (harder to test)
@Service
public class BadService {
    @Autowired
    private SomeService service;  // Avoid this
}
```

### Error Handling Pattern

```java
// Use exceptions instead of System.exit()
public ParsedConfiguration parse(String[] args) {
    try {
        // Parsing logic
        validateConfiguration(config);
        return config;
    } catch (IllegalArgumentException e) {
        throw new ClassificationException("Invalid configuration: " + e.getMessage(), e);
    }
}
```

## 📊 Performance and Quality Metrics

### Test Execution Standards
- **Unit Tests**: < 5 seconds for entire test suite
- **Integration Tests**: < 10 seconds with mocked dependencies
- **No Network Calls**: All external APIs must be mocked
- **No File I/O**: Outside of @TempDir in tests

### Code Organization Standards
- **Service Size**: Aim for < 500 lines per service (Phase 5 was exceptional at 780 lines)
- **Method Size**: Keep methods under 50 lines
- **Test Coverage**: Minimum 80% for business logic
- **Mocking Coverage**: 100% for external dependencies

## 🎯 Specific Guidance for Classification Module

### Label Normalization (From Python Analysis)
```java
// Port from Python stratified_split.py
Map<String, String> LABEL_GROUPS = Map.of(
    "pgvector", "vector store",
    "azure-openai-embedding-store", "vector store",
    "chroma", "vector store",
    "milvus", "vector store",
    "opensearch", "vector store",
    "pinecone", "vector store",
    "qdrant", "vector store",
    "redis", "vector store",
    "weaviate", "vector store"
);

Set<String> IGNORED_LABELS = Set.of(
    "triage", "duplicate", "invalid", "wontfix",
    "bug", "enhancement"  // Excluded due to poor performance
);
```

### Batch Processing Strategy (From Python batch_processor.py)
```java
public class BatchProcessor {
    private static final int DEFAULT_BATCH_SIZE = 25;  // Optimal for LLM
    private static final int MAX_RETRIES = 3;
    private static final Duration BACKOFF_DURATION = Duration.ofSeconds(5);
    
    public List<ClassificationResult> processBatches(List<Issue> issues) {
        // Process in batches of 25 for LLM efficiency
        // Include retry logic with exponential backoff
        // Track progress for resume capability
    }
}
```

### Classification Prompt Management
```java
@Component
public class PromptManager {
    private static final String PROMPT_RESOURCE_PATH = "/prompts/";
    
    public String loadClassificationPrompt() {
        // Load from src/main/resources/prompts/improved_classification_prompt.md
        // This is the proven prompt achieving 82.1% F1 score
        try (InputStream is = getClass().getResourceAsStream(
                PROMPT_RESOURCE_PATH + "improved_classification_prompt.md")) {
            return new String(is.readAllBytes(), StandardCharsets.UTF_8);
        }
    }
}
```

## 📝 Task-Specific Safety Requirements

### Task 1-2: Module Setup & Domain Models
- **Risk Level**: LOW
- **Testing**: Plain JUnit only
- **External Dependencies**: None
- **File Operations**: None

### Task 3-4: Label Services
- **Risk Level**: LOW-MEDIUM  
- **Testing**: Plain JUnit with mocked properties
- **External Dependencies**: Configuration only
- **File Operations**: None

### Task 5-6: Classification Core & Batch Processing
- **Risk Level**: MEDIUM
- **Testing**: Plain JUnit with mocked services
- **External Dependencies**: Mocked GitHub services
- **File Operations**: @TempDir only

### Task 7-10: LLM Integration & Evaluation
- **Risk Level**: HIGHEST
- **Testing**: Plain JUnit with fully mocked Claude Code SDK
- **External Dependencies**: ALL must be mocked
- **File Operations**: @TempDir only
- **Special Requirements**: 
  - NEVER allow real LLM calls
  - Mock Query.execute() static method
  - Use test classification responses
  - Verify no network activity

## 🚀 Success Criteria

### Functional Success
- [ ] Achieve F1 score within 2% of Python baseline (82.1%)
- [ ] Process 100 issues in < 10 seconds (excluding LLM calls)
- [ ] Support all high-performing labels from Python
- [ ] Integrate seamlessly with collection-library

### Safety Success  
- [ ] Zero production operations during development
- [ ] No real LLM calls during testing
- [ ] No files created outside target/ and @TempDir
- [ ] All tests complete in < 10 seconds

### Quality Success
- [ ] Clean modular architecture
- [ ] Comprehensive test coverage
- [ ] Clear documentation
- [ ] Consistent error handling

## 🔄 Continuous Improvement

### After Each Task Completion
1. Create learnings document: `task-N-[name]-learnings.md`
2. Update this consolidated guide if new patterns emerge
3. Commit with descriptive message
4. Verify no production artifacts in git status

### Red Flags Requiring Immediate Action
- Test execution > 30 seconds
- Network activity during tests
- Files appearing in issues/ or logs/
- GitHub API rate limit warnings
- LLM response delays during tests

## Conclusion

These consolidated learnings from 5 successful phases and the JBang export experience provide a comprehensive safety framework for implementing the issue classification module. The key to success is:

1. **NEVER use @SpringBootTest** - This is the golden rule
2. **Mock all external dependencies** - Especially Claude Code SDK
3. **Use @TempDir for file operations** - Never write to working directory
4. **Apply clean migration approach** - Create new, then remove old
5. **Document learnings continuously** - Each task should update knowledge base

Following these patterns will ensure safe, efficient development of the classification module while maintaining the 82.1% F1 score benchmark established by the Python implementation.