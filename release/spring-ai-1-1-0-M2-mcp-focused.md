---
title: "Spring AI 1.1.0-M2 Available Now: Enhanced Model Context Protocol Support"
category: Releases
publishedAt: 2025-09-19
author: markpollack
---

On behalf of the Spring AI engineering team and everyone who has contributed, I'm happy to announce that Spring AI `1.1.0-M2` has been released and is now available from Maven Central.

This milestone release focuses primarily on **enhanced Model Context Protocol (MCP) support**, incorporating critical fixes and improvements from the [MCP Java SDK v0.13.0 release](https://github.com/modelcontextprotocol/java-sdk/releases/tag/v0.13.0), along with significant updates across the Spring AI ecosystem.

## Release Summary

This release includes [44 improvements, bug fixes, and documentation updates](https://github.com/spring-projects/spring-ai/releases/tag/v1.1.0-M2). The primary focus areas include:

- **Model Context Protocol Enhancements**: Updated to MCP Java SDK v0.13.0 with protocol version 2025-06-18 support
- **MCP Integration Fixes**: Resolved critical stateless server registration issues
- **Developer Experience**: 19 improvements across the framework
- **Stability & Security**: 3 bug fixes and 3 dependency upgrades

## 🔧 Model Context Protocol Improvements

This release brings **production-ready MCP integration** to Spring AI, motivated by significant improvements in the MCP Java SDK v0.13.0:

### **Core MCP Enhancements**
- **Updated MCP Java SDK**: Upgraded from v0.12.1 to v0.13.0, incorporating protocol version 2025-06-18 support
- **Stateless Server Registration**: Fixed critical issues with MCP server connection handling for reliable production deployments
- **Enhanced Tool Management**: Improved tool name prefix generation with automatic duplicate handling
- **Configuration Polish**: Streamlined MCP configuration properties for better Spring Boot integration

### **Enterprise Integration**
- **Docker Compose Support**: Native service connection support for MCP Gateway in containerized environments
- **Testcontainers Integration**: Seamless testing capabilities for Docker-based MCP gateway deployments
- **Dependency Management**: Leverages the new `mcp-core` module with reduced Jackson dependencies

### **Breaking Changes & Migration**
The MCP Java SDK v0.13.0 includes breaking changes that Spring AI now handles:
- Updated `CallToolResult.structuredContent()` API for better array-type content support
- Module restructuring for improved dependency management
- Enhanced error recovery in `LifecycleInitializer`

For developers using MCP in Spring AI applications, this release provides a more stable and feature-rich foundation for tool integration workflows.

**Special thanks to the [MCP Java SDK v0.13.0](https://github.com/modelcontextprotocol/java-sdk/releases/tag/v0.13.0) community** for their exceptional work on the underlying SDK improvements that made this Spring AI release possible:

**Broadcom**: [Christian Tzolov (@tzolov)](https://github.com/tzolov), [Daniel Garnier-Moiroux (@Kehrlann)](https://github.com/Kehrlann)  
**Oracle**: [Graeme Rocher (@graemerocher)](https://github.com/graemerocher), [Sergio del Amo (@sdelamo)](https://github.com/sdelamo)  
**Google**: [Yanming Zhou (@quaff)](https://github.com/quaff)  
**Open Source Community**: [@He-Pin](https://github.com/He-Pin) - key developer in the Java and Scala open-source communities, serving as a Project Management Committee (PMC) member for the prominent Apache Pekko project and actively contributing to the ReactivePlatform organization

## Additional Functional Areas Enhanced

Beyond MCP improvements, this release includes:

- **Structured Output Revolution**: VertexAI Gemini response schema validation for guaranteed JSON/XML generation
- **Chinese AI Model Expansion**: ZhipuAI integration with GLM-4.5, GLM-Z1, and GLM-4.1v-thinking-flash models
- **Multimodal Intelligence**: Mistral AI OCR API for document and image text extraction
- **Ollama Enterprise Features**: Comprehensive hardware, memory, and performance configuration options
- **API Consistency**: Unified builder patterns across EmbeddingOptions, ChatOptions, and AssistantMessage

## Community

The Spring AI community continues to grow and contribute in meaningful ways. This release includes contributions from community members who reported issues, submitted fixes, and provided valuable feedback.

🙏 **Contributors**

Thanks to all contributors who made this release possible:

- [Alexandros Pappas (@apappascs)](https://github.com/apappascs)
- [Andrei Sumin (@andrei.sumin)](https://github.com/andrei.sumin)
- [Christian Tzolov (@tzolov)](https://github.com/tzolov)
- [Dan Dobrin (@ddobrin)](https://github.com/ddobrin)
- [Daniel Garnier-Moiroux (@git)](https://github.com/git)
- [Eddú Meléndez (@eddu.melendez)](https://github.com/eddu.melendez)
- [Gareth Evans (@gareth)](https://github.com/gareth)
- [Ilayaperumal Gopinathan (@ilayaperumalg)](https://github.com/ilayaperumalg)
- [Josh Long (@joshlong)](https://github.com/joshlong)
- [leeyazhou (@bytesgo)](https://github.com/bytesgo)
- [Li Huagang-简放视野 (@bert825_work)](https://github.com/bert825_work)
- [Nicolas Krier (@nicolaskrier)](https://github.com/nicolaskrier)
- [Oleksandr Klymenko (@alexanderklmn)](https://github.com/alexanderklmn)
- [SiBo Ai (@ai-afk)](https://github.com/ai-afk)
- [Stuart Loxton (@stuart.loxton)](https://github.com/stuart.loxton)
- [Sun Yuhan (@sunyuhan1998)](https://github.com/sunyuhan1998)
- [Thomas Vitale (@ThomasVitale)](https://github.com/ThomasVitale)
- [Toshiaki Maki (@makingx)](https://github.com/makingx)
- [Waldemar Panas (@waldemar.panas)](https://github.com/waldemar.panas)
- [xfl12345 (@xfl12345)](https://github.com/xfl12345)
- [Yanming Zhou (@zhouyanming)](https://github.com/zhouyanming)
- [YuJie Wan (@eeaters)](https://github.com/eeaters)
- [YunKui Lu (@luyunkui95)](https://github.com/luyunkui95)

### How can you help?

If you're interested in contributing, check out the ["ideal for contribution" tag](https://github.com/spring-projects/spring-ai/labels/ideal-for-contribution) in our issue repository. For MCP-specific questions, please ask on [Stack Overflow](https://stackoverflow.com) using the [`spring-ai`](https://stackoverflow.com/tags/spring-ai) and [`model-context-protocol`](https://stackoverflow.com/tags/model-context-protocol) tags.

## What's Next

With robust MCP foundation in place, upcoming Spring AI releases will focus on:
- Advanced MCP tool composition patterns
- Enhanced protocol version support
- Expanded containerization features
- Improved developer tooling for MCP integration

For the latest updates and to contribute to the project, visit our [GitHub repository](https://github.com/spring-projects/spring-ai) or join the discussion in our community channels.

## Resources

[Project Page](https://spring.io/projects/spring-ai/) | [GitHub](https://github.com/spring-projects/spring-ai) | [Issues](https://github.com/spring-projects/spring-ai/issues) | [Documentation](https://docs.spring.io/spring-ai/docs/1.1.0-M2/reference/html) | [MCP Java SDK](https://github.com/modelcontextprotocol/java-sdk) | [Stack Overflow](https://stackoverflow.com/questions/tagged/spring-ai)