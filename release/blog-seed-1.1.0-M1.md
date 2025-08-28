
**Current Focus Areas for Spring AI 1.1**

For 1.1, we’re concentrating on a mix of high-impact enhancements and targeted foundational work, with a clear focus on what can realistically land before code freeze.
It is still an rather agressive list.  We will be reviewing compared against GitHub issues and PRs and look for feedback on what to prioritze.

---

### **1. Model Context Protocol (MCP) Support**
Deep integration with the latest MCP Java SDK releases, aligning Spring AI with the most up-to-date protocol and transport capabilities:
- **Multi-protocol version negotiation** (2024-11-05 and 2025-03-26).
- **OAuth2-secured MCP server connections** via new transport customizers.
- **Streamable HTTP and WebMVC/HttpServlet server transports** for reactive and servlet deployments.
- **Structured output validation** with JSON Schema enforcement.
- **Pagination, keep-alive pings, URI template support** for richer resource interactions.
- **Improved error handling, logging, and initialization flows**.
- Migration to **builder-based APIs** for tools and transport providers.

---

### **2. Core Responses API Enhancements**
Expanding the Responses API to close feature gaps, improve provider parity, and bring in the latest SDK capabilities:
- **Prompt caching** to cut latency and cost.
- **“Thinking” model support** for enhanced reasoning.
- **Message batching** for higher throughput.
- **Native JSON mode** and stronger structured output handling across providers.
- Hooks for **provider-specific extensions** while keeping a unified API.
- **Google Vertex AI SDK update** – upgrade to the latest SDK to:
  - Unlock newly released endpoints (including non-chat APIs).
  - Ensure compatibility with enhanced Responses API features.
  - Bring security fixes and long-term support.
  - Refresh and expand Vertex AI integration tests.

Special thanks to [Dan Dobrin](https://github.com/ddobrin) for contributing this work.

---

### **3. Chat Memory Improvements**
Advancing Spring AI’s memory handling for production scenarios:
- **Memory compaction** to manage token budgets.
- Configurable retention policies for long-running conversations.
- Improved integration points for custom memory stores.

---

### **4. Observability & Multi-Client Configuration**
- **Simplified observability setup**, including easier integration with tools like Langfuse.
- **Multi-client configuration improvements** to streamline working with multiple providers in the same application.

---

### **5. Net new areas**  
These are mostly net-new implementations and may extend beyond 1.1 if timing is tight, but early groundwork may begin:
- **Azure OpenAI** – new SDK support.
- **Vector store improvements**, including hybrid search.
- **Reranking** – first-class support for re-ranker models.
- **Enterprise guardrails** – security and compliance features.

---