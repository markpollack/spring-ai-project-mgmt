---
title: "Spring AI 1.1.0-M2 Available Now"
category: Releases
publishedAt: 2025-09-19
author: markpollack
---

On behalf of the Spring AI engineering team and everyone who has contributed, I'm happy to announce that Spring AI `1.1.0-M2` has been released and is now available from Maven Central.

This patch release delivers important stability improvements and bug fixes.

## Release Summary

This release includes [44 improvements, bug fixes, and documentation updates](https://github.com/spring-projects/spring-ai/releases/tag/v1.1.0-M2). The focus of this patch release is on:

- **Improvements**: 19 enhancements to expand capabilities and functionality
- **Stability**: 3 bug fixes addressing community-reported issues
- **Documentation**: 19 improvements to help developers
- **Security**: 3 dependency upgrades for enhanced security

Thanks to all those who have contributed with issue reports and pull requests.

## Key Highlights

- Enhanced functionality with 19 improvements
- Updated dependencies for better security and performance

These improvements ensure that Spring AI continues to provide a robust and reliable foundation for building production-ready AI applications.
## Key Functional Areas Enhanced

This release brings significant improvements across major functional areas of Spring AI:

- **Advanced Model Context Protocol Infrastructure** - stateless MCP server registration fixes, enhanced tool name prefix generation with automatic duplicate handling, Docker Compose and Testcontainers service connections for mcp-gateway enabling seamless containerized tool execution
- **Structured Output Revolution with VertexAI Gemini** - response schema validation support for guaranteed JSON/XML structured generation, eliminating parsing errors and ensuring reliable data extraction workflows
- **Next-Generation Chinese AI Model Arsenal** - native ZhipuAI integration with GLM-4.5, GLM-Z1, and GLM-4.1v-thinking-flash models, featuring advanced thinking parameters and response formatting capabilities
- **Multimodal Document Intelligence Breakthrough** - Mistral AI OCR API integration for extracting text from documents and images, transforming visual content into actionable data streams
- **Enterprise-Grade Ollama Embedding Control** - comprehensive hardware, memory, performance and execution configuration options, plus proper system role handling for optimized local model deployments
- **Developer Experience API Consistency** - unified builder patterns across EmbeddingOptions, ChatOptions, and AssistantMessage creation, delivering consistent API design throughout the framework

These enhancements strengthen Spring AI's capabilities across the entire AI application development lifecycle.

## Community

The Spring AI community continues to grow and contribute in meaningful ways. This release includes contributions from community members who reported issues, submitted fixes, and provided valuable feedback. Special thanks to our contributors: - [Alexandros Pappas (@apappascs)](https://github.com/apappascs), - [Andrei Sumin (@andrei.sumin)](https://github.com/andrei.sumin), - [Christian Tzolov (@tzolov)](https://github.com/tzolov), - [Dan Dobrin (@ddobrin)](https://github.com/ddobrin), - [Daniel Garnier-Moiroux (@git)](https://github.com/git), - [Eddú Meléndez (@eddu.melendez)](https://github.com/eddu.melendez), - [Gareth Evans (@gareth)](https://github.com/gareth), - [Ilayaperumal Gopinathan (@ilayaperumalg)](https://github.com/ilayaperumalg), - [Josh Long (@joshlong)](https://github.com/joshlong), - [leeyazhou (@bytesgo)](https://github.com/bytesgo) and 13 others.

Thanks to all those who have contributed with issue reports and pull requests.

### How can you help?

If you're interested in contributing, check out the ["ideal for contribution" tag](https://github.com/spring-projects/spring-ai/labels/ideal-for-contribution) in our issue repository. For general questions, please ask on [Stack Overflow](https://stackoverflow.com) using the [`spring-ai` tag](https://stackoverflow.com/tags/spring-ai).

## What's Next

The Spring AI team continues to focus on improving AI application development with Spring Boot. Based on the momentum from 1.1.0-M2, upcoming releases will build on these foundations with enhanced capabilities and developer experience improvements.

For the latest updates and to contribute to the project, visit our [GitHub repository](https://github.com/spring-projects/spring-ai) or join the discussion in our community channels.

## Resources

[Project Page](https://spring.io/projects/spring-ai/) | [GitHub](https://github.com/spring-projects/spring-ai) | [Issues](https://github.com/spring-projects/spring-ai/issues) | [Documentation](https://docs.spring.io/spring-ai/docs/1.1.0-M2/reference/html) | [Stack Overflow](https://stackoverflow.com/questions/tagged/spring-ai)
🙏 Contributors
Thanks to all contributors who made this release possible:

[- [Alexandros Pappas (@apappascs)](https://github.com/apappascs)](https://github.com/https://github.com/apappascs)
[- [Andrei Sumin (@andrei.sumin)](https://github.com/andrei.sumin)](https://github.com/https://github.com/andrei.sumin)
[- [Christian Tzolov (@tzolov)](https://github.com/tzolov)](https://github.com/https://github.com/tzolov)
[- [Dan Dobrin (@ddobrin)](https://github.com/ddobrin)](https://github.com/https://github.com/ddobrin)
[- [Daniel Garnier-Moiroux (@git)](https://github.com/git)](https://github.com/https://github.com/git)
[- [Eddú Meléndez (@eddu.melendez)](https://github.com/eddu.melendez)](https://github.com/https://github.com/eddu.melendez)
[- [Gareth Evans (@gareth)](https://github.com/gareth)](https://github.com/https://github.com/gareth)
[- [Ilayaperumal Gopinathan (@ilayaperumalg)](https://github.com/ilayaperumalg)](https://github.com/https://github.com/ilayaperumalg)
[- [Josh Long (@joshlong)](https://github.com/joshlong)](https://github.com/https://github.com/joshlong)
[- [leeyazhou (@bytesgo)](https://github.com/bytesgo)](https://github.com/https://github.com/bytesgo)
[- [Li Huagang-简放视野 (@bert825_work)](https://github.com/bert825_work)](https://github.com/https://github.com/bert825_work)
[- [Nicolas Krier (@nicolaskrier)](https://github.com/nicolaskrier)](https://github.com/https://github.com/nicolaskrier)
[- [Oleksandr Klymenko (@alexanderklmn)](https://github.com/alexanderklmn)](https://github.com/https://github.com/alexanderklmn)
[- [SiBo Ai (@ai-afk)](https://github.com/ai-afk)](https://github.com/https://github.com/ai-afk)
[- [Stuart Loxton (@stuart.loxton)](https://github.com/stuart.loxton)](https://github.com/https://github.com/stuart.loxton)
[- [Sun Yuhan (@sunyuhan1998)](https://github.com/sunyuhan1998)](https://github.com/https://github.com/sunyuhan1998)
[- [Thomas Vitale (@ThomasVitale)](https://github.com/ThomasVitale)](https://github.com/https://github.com/ThomasVitale)
[- [Toshiaki Maki (@makingx)](https://github.com/makingx)](https://github.com/https://github.com/makingx)
[- [Waldemar Panas (@waldemar.panas)](https://github.com/waldemar.panas)](https://github.com/https://github.com/waldemar.panas)
[- [xfl12345 (@xfl12345)](https://github.com/xfl12345)](https://github.com/https://github.com/xfl12345)
[- [Yanming Zhou (@zhouyanming)](https://github.com/zhouyanming)](https://github.com/https://github.com/zhouyanming)
[- [YuJie Wan (@eeaters)](https://github.com/eeaters)](https://github.com/https://github.com/eeaters)
[- [YunKui Lu (@luyunkui95)](https://github.com/luyunkui95)](https://github.com/https://github.com/luyunkui95)