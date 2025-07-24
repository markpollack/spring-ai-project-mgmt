# Spring AI Design-Labeled Issues with Full Review Metadata

## 🧵 Issue Summary
**Issue**: [#3103 – Add Model Captability class](https://github.com/spring-projects/spring-ai/issues/3103)
**Category**: API Redesign, Configuration Model Evolution
**Impact**: High

### 💡 Proposed Change
**Current Design**: Capabilities handled ad hoc via prompt or logic
**Proposed Change**: Introduce centralized ModelCapability class
**Justification**: Avoid brittle logic, enable proactive client behavior

### 🔧 Implementation Considerations
**Complexity**: Medium
**Migration Path**: Additive at first
**Dependencies**: Prompt composition, tools

### ✅ Priority Recommendation
**High Priority**

---

## 🧵 Issue Summary
**Issue**: [#2104 – Add an opportunity to choose a model in vector store](https://github.com/spring-projects/spring-ai/issues/2104)
**Category**: Interface Segregation, Configuration Model Evolution
**Impact**: Medium

### 💡 Proposed Change
**Current Design**: No model override per operation
**Proposed Change**: Add overloads for model/EmbeddingOptions
**Justification**: Avoid decorator hacks

### 🔧 Implementation Considerations
**Complexity**: Low to Medium
**Migration Path**: Additive overloads
**Dependencies**: Vector store refactors

### ✅ Priority Recommendation
**Medium Priority**

---

## 🧵 Issue Summary
**Issue**: [#1838 – Are `Document` objects supposed to be immutable?](https://github.com/spring-projects/spring-ai/issues/1838)
**Category**: Stronger Type Safety, API Redesign
**Impact**: High

### 💡 Proposed Change
**Current Design**: `Document` is semi-immutable with mutable collections
**Proposed Change**: Make `Document` fully immutable
**Justification**: Safety and clarity, especially with concurrency

### 🔧 Implementation Considerations
**Complexity**: High
**Migration Path**: Breaking, requires adaptation
**Dependencies**: All vector store impls

### ✅ Priority Recommendation
**High Priority**

---

## 🧵 Issue Summary
**Issue**: [#1815 – About Chat Memory’s message management strategy](https://github.com/spring-projects/spring-ai/issues/1815)
**Category**: Configuration Model Evolution
**Impact**: Medium

### 💡 Proposed Change
**Current Design**: Limited storage and windowing strategy
**Proposed Change**: Add plug-in windowing/persistence strategy
**Justification**: Extensibility, production readiness

### 🔧 Implementation Considerations
**Complexity**: Medium
**Migration Path**: Additive
**Dependencies**: ChatMemory, MessageStore

### ✅ Priority Recommendation
**Medium Priority**

---

## 🧵 Issue Summary
**Issue**: [#1775 – Milvus vectorstore SearchRequest cannot specify DB](https://github.com/spring-projects/spring-ai/issues/1775)
**Category**: Configuration Model Evolution
**Impact**: Low

### 💡 Proposed Change
**Current Design**: No way to pass DB/collection in SearchRequest
**Proposed Change**: Add support to specify DB/collection
**Justification**: Improves multi-tenant support

### 🔧 Implementation Considerations
**Complexity**: Low
**Migration Path**: Non-breaking
**Dependencies**: Milvus module

### ✅ Priority Recommendation
**Low Priority**

---
