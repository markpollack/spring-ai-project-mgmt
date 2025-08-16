# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Build and Test
- `./mvnw clean package` - Build with unit tests
- `./mvnw clean verify -Pintegration-tests` - Build with integration tests (requires API keys)
- `./mvnw clean install -DskipTests -Dmaven.javadoc.skip=true` - Quick compile and install without tests
- `./mvnw verify -Pintegration-tests -pl <module>` - Run integration tests for specific module
- `./mvnw -Pci-fast-integration-tests` - Run quick integration tests (OpenAI, PGVector, Chroma)

### Code Quality
- `./mvnw spring-javaformat:apply` - Format code using Spring Java Format
- `./mvnw clean package -DskipTests -Ddisable.checks=false` - Enable checkstyle validation
- `./mvnw license:update-file-header -Plicense` - Update license headers
- `./mvnw javadoc:javadoc -Pjavadoc` - Generate Javadocs

### Documentation
- `./mvnw -pl spring-ai-docs antora` - Build documentation (output in `spring-ai-docs/target/antora/site/index.html`)

### Module-Specific Testing
- `./mvnw -pl vector-stores/spring-ai-pgvector-store -Pintegration-tests -Dfailsafe.rerunFailingTestsCount=2 -Dit.test=PgVectorStoreIT verify` - Run specific integration test with retries

## Project Architecture

### Core Module Structure
- **spring-ai-model**: Core AI model abstractions and interfaces (ChatModel, EmbeddingModel, ImageModel, etc.)
- **spring-ai-commons**: Common utilities, document processing, tokenization, and observation support
- **spring-ai-client-chat**: ChatClient fluent API and advisor framework
- **spring-ai-vector-store**: Vector store abstractions and implementations
- **spring-ai-rag**: RAG (Retrieval Augmented Generation) support

### Model Providers
Located in `models/` directory:
- spring-ai-openai, spring-ai-anthropic, spring-ai-azure-openai
- spring-ai-bedrock, spring-ai-vertex-ai-gemini, spring-ai-ollama
- spring-ai-mistral-ai, spring-ai-huggingface, spring-ai-deepseek

### Vector Stores
Located in `vector-stores/` directory:
- spring-ai-pgvector-store, spring-ai-chroma-store, spring-ai-pinecone-store
- spring-ai-elasticsearch-store, spring-ai-redis-store, spring-ai-weaviate-store

### Auto-Configuration
Located in `auto-configurations/` directory:
- Model auto-configurations in `models/`
- Vector store auto-configurations in `vector-stores/`
- MCP (Model Control Protocol) auto-configurations in `mcp/`

### Spring Boot Starters
Located in `spring-ai-spring-boot-starters/` directory - provides starter dependencies for each model and vector store.

## Key Design Patterns

### Portable APIs
Spring AI provides portable APIs across different AI providers. Core interfaces like `ChatModel`, `EmbeddingModel`, and `VectorStore` abstract provider-specific implementations.

### Observation and Metrics
Comprehensive observability support through Micrometer with conventions defined in `spring-ai-commons/src/main/java/org/springframework/ai/observation/conventions/`.

### ChatClient and Advisors
- **ChatClient**: Fluent API similar to WebClient/RestClient for AI interactions
- **Advisors**: Encapsulate recurring patterns like memory management, content filtering, and RAG

### Tool/Function Calling
Support for AI model tool calling with Spring beans automatically registered as callable functions via `@Tool` annotation.

## Notable Architectural Patterns

### Consistent Module Structure
All Spring AI components follow predictable naming and organization patterns:

**Vector Stores:**
- Core module: `spring-ai-{name}-store` (e.g., `spring-ai-pinecone-store`)
- Package: `org.springframework.ai.vectorstore.{name}` (e.g., `org.springframework.ai.vectorstore.pinecone`)
- Main class: `{Name}VectorStore` (e.g., `PineconeVectorStore`)
- Auto-configuration: `spring-ai-autoconfigure-vector-store-{name}`
- Properties class: `{Name}VectorStoreProperties`
- Configuration prefix: `spring.ai.vectorstore.{name}`

**Model Providers:**
- Core module: `spring-ai-{provider}` (e.g., `spring-ai-openai`)
- Package: `org.springframework.ai.{provider}` (e.g., `org.springframework.ai.openai`)
- Main classes: `{Provider}ChatModel`, `{Provider}EmbeddingModel`, etc.
- Auto-configuration: `spring-ai-autoconfigure-model-{provider}`
- Properties class: `{Provider}Properties`
- Configuration prefix: `spring.ai.{provider}`

**Spring Boot Integration:**
- Auto-configuration modules: `auto-configurations/{category}/spring-ai-autoconfigure-{component}`
- Starter modules: `spring-ai-spring-boot-starters/spring-ai-starter-{component}`
- All components follow Spring Boot configuration property conventions

### Three-Layer Architecture
1. **Core Implementation**: Business logic and provider-specific code
2. **Auto-Configuration**: Spring Boot integration with properties and beans
3. **Starter**: Dependency aggregation for easy consumption

### GitHub Issue Classification Patterns
Common issue types by component:
- **Vector Stores**: configuration, connection, performance
- **Model Providers**: configuration, connection, timeout, runtime
- **Core Features**: integration, runtime, configuration
- **Testing**: test, integration, configuration
- **Documentation**: documentation, missing feature, clarification

### Configuration Hierarchy
- Global: `spring.ai.*`
- Component type: `spring.ai.{component-type}.*` (e.g., `spring.ai.vectorstore.*`)
- Provider-specific: `spring.ai.{provider}.*` (e.g., `spring.ai.openai.*`)
- Feature-specific: `spring.ai.{provider}.{feature}.*` (e.g., `spring.ai.openai.chat.*`)

## Testing Notes

### Integration Tests
- Require API keys for respective providers (OpenAI, Anthropic, etc.)
- Tests are skipped if API keys are not set
- Use `-Dfailsafe.rerunFailingTestsCount=2` for unreliable hosted services
- Full integration tests run in separate repository: spring-ai-integration-tests

### Test Utilities
- `spring-ai-test` module provides evaluation utilities for generated content
- Support for testing hallucination prevention and content quality

## Development Setup

### Git LFS
This repository contains large model files. Either:
- Clone with `GIT_LFS_SKIP_SMUDGE=1 git clone ...` to skip large files
- Install Git LFS before cloning

### Code Style
- Follows Spring Framework code style conventions
- Uses spring-javaformat-maven-plugin for consistent formatting
- Checkstyle configured but currently disabled by default