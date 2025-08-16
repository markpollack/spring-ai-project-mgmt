# Multi-Label Classification Results - Full Test Set

## Summary Statistics

- **Total Issues Evaluated**: 111
- **Perfect Predictions**: 4 (3.6%)
- **Total Predictions Made**: 1256
- **Total Ground Truth Labels**: 203
- **Average Predictions per Issue**: 11.3
- **Average Ground Truth per Issue**: 1.8

## Overall Performance Metrics

### Micro-Averaged Metrics
- **Precision**: 0.095
- **Recall**: 0.586
- **F1 Score**: 0.164

### Macro-Averaged Metrics
- **Precision**: 0.069
- **Recall**: 0.271
- **F1 Score**: 0.097

## Per-Label Performance

| Label | Precision | Recall | F1 Score | Support |
|-------|-----------|---------|----------|---------|
| bug | 0.255 | 0.667 | 0.369 | 18 |
| type: backport | 0.923 | 1.000 | 0.960 | 12 |
| enhancement | 0.237 | 0.750 | 0.360 | 12 |
| vector store | 0.429 | 0.750 | 0.545 | 12 |
| tool/function calling | 0.324 | 1.000 | 0.489 | 11 |
| documentation | 0.217 | 0.500 | 0.303 | 10 |
| design | 0.250 | 0.125 | 0.167 | 8 |
| model client | 0.129 | 0.667 | 0.216 | 6 |
| MCP | 0.375 | 0.500 | 0.429 | 6 |
| code cleanup | 0.000 | 0.000 | 0.000 | 5 |
| Bedrock | 0.286 | 0.800 | 0.421 | 5 |
| openai | 0.125 | 0.600 | 0.207 | 5 |
| azure | 0.333 | 0.800 | 0.471 | 5 |
| configuration | 0.133 | 0.800 | 0.229 | 5 |
| help wanted | 0.000 | 0.000 | 0.000 | 4 |
| status: to-discuss | 0.000 | 0.000 | 0.000 | 4 |
| follow up | 0.000 | 0.000 | 0.000 | 4 |
| ollama | 0.143 | 1.000 | 0.250 | 4 |
| status: backported | 0.000 | 0.000 | 0.000 | 4 |
| Observability | 0.222 | 0.500 | 0.308 | 4 |

## Top 10 Most Frequent Labels (Ground Truth)

1. **bug**: 18 occurrences (P: 0.255, R: 0.667, F1: 0.369)
2. **type: backport**: 12 occurrences (P: 0.923, R: 1.000, F1: 0.960)
3. **enhancement**: 12 occurrences (P: 0.237, R: 0.750, F1: 0.360)
4. **vector store**: 12 occurrences (P: 0.429, R: 0.750, F1: 0.545)
5. **tool/function calling**: 11 occurrences (P: 0.324, R: 1.000, F1: 0.489)
6. **documentation**: 10 occurrences (P: 0.217, R: 0.500, F1: 0.303)
7. **design**: 8 occurrences (P: 0.250, R: 0.125, F1: 0.167)
8. **model client**: 6 occurrences (P: 0.129, R: 0.667, F1: 0.216)
9. **MCP**: 6 occurrences (P: 0.375, R: 0.500, F1: 0.429)
10. **code cleanup**: 5 occurrences (P: 0.000, R: 0.000, F1: 0.000)

## Classification Analysis

### Strong Performers (F1 > 0.8)
- **type: backport**: F1 = 0.960 (P: 0.923, R: 1.000, Support: 12)

### Challenging Labels (F1 < 0.5)
- **bug**: F1 = 0.369 (P: 0.255, R: 0.667, Support: 18)
- **enhancement**: F1 = 0.360 (P: 0.237, R: 0.750, Support: 12)
- **tool/function calling**: F1 = 0.489 (P: 0.324, R: 1.000, Support: 11)
- **documentation**: F1 = 0.303 (P: 0.217, R: 0.500, Support: 10)
- **design**: F1 = 0.167 (P: 0.250, R: 0.125, Support: 8)
- **model client**: F1 = 0.216 (P: 0.129, R: 0.667, Support: 6)
- **MCP**: F1 = 0.429 (P: 0.375, R: 0.500, Support: 6)
- **code cleanup**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 5)
- **Bedrock**: F1 = 0.421 (P: 0.286, R: 0.800, Support: 5)
- **openai**: F1 = 0.207 (P: 0.125, R: 0.600, Support: 5)
- **azure**: F1 = 0.471 (P: 0.333, R: 0.800, Support: 5)
- **configuration**: F1 = 0.229 (P: 0.133, R: 0.800, Support: 5)
- **help wanted**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 4)
- **status: to-discuss**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 4)
- **follow up**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 4)
- **ollama**: F1 = 0.250 (P: 0.143, R: 1.000, Support: 4)
- **status: backported**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 4)
- **Observability**: F1 = 0.308 (P: 0.222, R: 0.500, Support: 4)
- **chat client**: F1 = 0.174 (P: 0.100, R: 0.667, Support: 3)
- **question**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 3)
- **anthropic**: F1 = 0.200 (P: 0.111, R: 1.000, Support: 3)
- **Chat Memory**: F1 = 0.308 (P: 0.200, R: 0.667, Support: 3)
- **chromadb**: F1 = 0.118 (P: 0.071, R: 0.333, Support: 3)
- **vertex**: F1 = 0.133 (P: 0.083, R: 0.333, Support: 3)
- **gcp**: F1 = 0.182 (P: 0.125, R: 0.333, Support: 3)
- **advisors**: F1 = 0.174 (P: 0.095, R: 1.000, Support: 2)
- **prompt management**: F1 = 0.133 (P: 0.071, R: 1.000, Support: 2)
- **embedding**: F1 = 0.160 (P: 0.087, R: 1.000, Support: 2)
- **structured output**: F1 = 0.200 (P: 0.111, R: 1.000, Support: 2)
- **ETL**: F1 = 0.400 (P: 0.333, R: 0.500, Support: 2)
- **redis**: F1 = 0.211 (P: 0.118, R: 1.000, Support: 2)
- **status: waiting-for-feedback**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 2)
- **opensearch**: F1 = 0.125 (P: 0.067, R: 1.000, Support: 1)
- **elastic search**: F1 = 0.125 (P: 0.067, R: 1.000, Support: 1)
- **metadata filters**: F1 = 0.077 (P: 0.040, R: 1.000, Support: 1)
- **kotlin**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **cassandra**: F1 = 0.182 (P: 0.100, R: 1.000, Support: 1)
- **for: backport-to-1.0.x**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **retry**: F1 = 0.250 (P: 0.143, R: 1.000, Support: 1)
- **invalid**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **client timeouts**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **duplicate**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **chat options**: F1 = 0.100 (P: 0.053, R: 1.000, Support: 1)
- **deepseek**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **testing**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **watson**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **milvus**: F1 = 0.200 (P: 0.111, R: 1.000, Support: 1)
- **streaming**: F1 = 0.077 (P: 0.040, R: 1.000, Support: 1)
- **good first issue**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **epic**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **mariadb**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **next priorities**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **deprecation**: F1 = 0.400 (P: 0.250, R: 1.000, Support: 1)
- **dependencies**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 1)
- **typesense**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **qdrant**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **mongo**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **improvement**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **multiple models**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **CI/CD**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **moderation**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **security**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **model-option-utils**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **ZhiPu**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **weaviate**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **gemfire**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **hybrid search**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **templating**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **cross platform**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **multimodality**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **Getting Started Experience**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **moonshot**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **document-reader**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **messages**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **speech**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **audio**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **stabilityai**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **docker-compose**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **status: waiting-for-triage**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **neo4j**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **integration testing**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **image models**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **guardrails**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **mistral**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **testcontainers**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **pgvector**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **minimax**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **Malicious/Attack**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **wontfix**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **qianfan**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **couchbase**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **refactoring**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **Evaluation**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **onxx**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **pinecone**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **huggingface**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **postgresml**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **i18n**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **gemini**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **AOT/Native**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **coherence**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **oracle**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **transcription models**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **claude**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)
- **breaking**: F1 = 0.000 (P: 0.000, R: 0.000, Support: 0)

## Sample Predictions

### Perfect Predictions (showing first 5)

**Issue #3578**
- Predicted: ['bug', 'type: backport']
- Actual: ['bug', 'type: backport']
- Match: ✅ Perfect

**Issue #2337**
- Predicted: ['tool/function calling']
- Actual: ['tool/function calling']
- Match: ✅ Perfect

**Issue #2983**
- Predicted: ['Bedrock', 'embedding']
- Actual: ['Bedrock', 'embedding']
- Match: ✅ Perfect

**Issue #992**
- Predicted: ['ollama', 'tool/function calling']
- Actual: ['ollama', 'tool/function calling']
- Match: ✅ Perfect

### Challenging Predictions (showing first 5)

**Issue #1776**
- Predicted: ['RAG', 'advisors', 'chat client', 'elastic search', 'embedding', 'enhancement', 'metadata filters', 'model client', 'mongo', 'opensearch', 'prompt management', 'qdrant', 'typesense', 'vector store']
- Actual: ['RAG', 'enhancement', 'metadata filters']
- Metrics: P=0.214, R=1.000, F1=0.353
- TP: 3, FP: 11, FN: 0

**Issue #953**
- Predicted: ['AOT/Native', 'Bedrock', 'CI/CD', 'Chat Memory', 'ETL', 'Evaluation', 'Getting Started Experience', 'MCP', 'Malicious/Attack', 'Observability', 'RAG', 'ZhiPu', 'advisors', 'anthropic', 'audio', 'azure', 'breaking', 'bug', 'cassandra', 'chat client', 'chat options', 'chromadb', 'claude', 'client timeouts', 'code cleanup', 'coherence', 'configuration', 'couchbase', 'cross platform', 'deepseek', 'deprecation', 'design', 'docker-compose', 'document-reader', 'documentation', 'duplicate', 'elastic search', 'embedding', 'enhancement', 'epic', 'follow up', 'for: backport-to-1.0.x', 'gcp', 'gemfire', 'gemini', 'good first issue', 'guardrails', 'help wanted', 'huggingface', 'hybrid search', 'i18n', 'image models', 'improvement', 'integration testing', 'invalid', 'kotlin', 'mariadb', 'messages', 'metadata filters', 'milvus', 'minimax', 'mistral', 'model client', 'model-option-utils', 'moderation', 'mongo', 'moonshot', 'multimodality', 'multiple models', 'neo4j', 'next priorities', 'ollama', 'onxx', 'openai', 'opensearch', 'oracle', 'pgvector', 'pinecone', 'postgresml', 'prompt management', 'qdrant', 'qianfan', 'question', 'redis', 'refactoring', 'retry', 'security', 'speech', 'stabilityai', 'status: backported', 'status: to-discuss', 'status: waiting-for-feedback', 'status: waiting-for-triage', 'streaming', 'structured output', 'templating', 'testcontainers', 'testing', 'tool/function calling', 'transcription models', 'type: backport', 'typesense', 'vector store', 'vertex', 'watson', 'weaviate', 'wontfix']
- Actual: ['Observability']
- Metrics: P=0.009, R=1.000, F1=0.019
- TP: 1, FP: 106, FN: 0

**Issue #1878**
- Predicted: ['Bedrock', 'ZhiPu', 'advisors', 'anthropic', 'bug', 'chat client', 'claude', 'client timeouts', 'configuration', 'docker-compose', 'duplicate', 'embedding', 'enhancement', 'gemini', 'i18n', 'image models', 'invalid', 'messages', 'mistral', 'model client', 'multiple models', 'ollama', 'onxx', 'openai', 'postgresml', 'prompt management', 'qdrant', 'speech', 'stabilityai', 'streaming', 'structured output', 'tool/function calling']
- Actual: ['Bedrock', 'status: backported', 'tool/function calling']
- Metrics: P=0.062, R=0.667, F1=0.114
- TP: 2, FP: 30, FN: 1

**Issue #1707**
- Predicted: ['streaming', 'testing']
- Actual: ['Observability', 'streaming']
- Metrics: P=0.500, R=0.500, F1=0.500
- TP: 1, FP: 1, FN: 1

**Issue #3110**
- Predicted: ['bug', 'client timeouts', 'messages', 'ollama']
- Actual: ['MCP']
- Metrics: P=0.000, R=0.000, F1=0.000
- TP: 0, FP: 4, FN: 1

## Methodology

This multi-label classification was performed using Claude AI with the following approach:

1. **Feature Engineering**: Combined issue title and body text
2. **Label Matching**: Used enhanced label mappings with:
   - Direct keyword matching
   - Description word matching
   - Example problem phrase matching
   - Module/package/class name matching
   - Configuration key matching
3. **Confidence Scoring**: Weighted scoring system with threshold of 0.6
4. **Fallback Strategy**: Issues with all confidence scores < 0.6 assigned "needs more info"

## Data Sources

- **Test Set**: `issues/stratified_split/test_set.json` (111 issues)
- **Label Mapping**: `github-labels-mapping-enhanced.json` (enhanced with training data insights)
- **Valid Labels**: `labels.json` (official GitHub labels)

## Files Generated

- `results/classified_full_test_set.json`: Complete predictions for all test issues
- `results/evaluation_results.md`: This comprehensive report
