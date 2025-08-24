---
title: "Spring AI 1.0.1 Released"
category: Releases
publishedAt: 2025-08-08
author: markpollack
---

On behalf of the Spring AI engineering team and everyone who has contributed, I'm happy to announce that Spring AI `1.0.1` has been released and is now available from Maven Central.

This patch release delivers important stability improvements and bug fixes.

## Release Summary

This release includes [151 improvements, bug fixes, and documentation updates](https://github.com/spring-projects/spring-ai/releases/tag/v1.0.1). The focus of this patch release is on:

- **Improvements**: 56 enhancements to expand capabilities and functionality
- **Stability**: 50 bug fixes addressing community-reported issues
- **Documentation**: 45 improvements to help developers


## Community

The Spring AI community continues to grow and contribute in meaningful ways. This release includes contributions from community members who reported issues, submitted fixes, and provided valuable feedback.

Thanks to all those who have contributed with issue reports and pull requests.


## Looking Ahead: Spring AI 1.1 and Beyond

While version 1.0.1 focused on stability and bug fixes, the Spring AI team is working on new capabilities for version 1.1. However, with a rapidly evolving AI landscape and over 150 open pull requests to manage, we're being thoughtful about prioritization and would value community input on what matters most.

Our [2025 roadmap diagram](https://claude.ai/public/artifacts/e211dc9e-249d-425d-abd6-9425b8a2bf16) provides key dates and shows our planning focus on Spring AI 2.0 with new Spring Boot 4 foundations. The roadmap is primarily date-driven to help the community understand timing, while indicating the major architectural changes we're preparing for the next generation of Spring AI.

**Current Focus Areas for Spring AI 1.1:**

Our roadmap includes a broad range of potential feature areas. Rather than overpromise, we want to share the full "menu" of what we're considering so the community can help us prioritize:

**Core Infrastructure & Maintenance:**
- Spring Boot 4 support and compatibility
- CI/CD improvements (Google Vertex, Amazon testing gaps)
- Issue triage and community PR integration
- Kotlin null-safety improvements

**AI Model Provider Enhancements:**
- Chat vendor SDK updates (Azure OpenAI, Google Vertex migrations)
- Enhanced chat vendor features (prompt caching, message batching, "thinking" models)
- Non-chat API breadth (Responses API, Image API, Text-to-Speech, Realtime API)
- Native JSON mode and structured output improvements

**Advanced Capabilities:**
- Model Context Protocol (MCP) integration and streaming support
- Vector store improvements and hybrid search (beyond similarity search)
- Enterprise guardrails and security features
- Enhanced observability and monitoring
- Chat memory enhancements and MemGPT-style implementations

**Developer Experience:**
- Evaluators and testing frameworks for AI applications
- Agent frameworks and workflow helpers
- Multi-client configuration improvements
- API key rotation and supplier patterns

**Emerging Areas:**
- Agent-to-agent protocols and communication
- Commercial MCP proxy solutions
- GraphRAG and advanced retrieval patterns

**Community Guidance Needed:**

We can't tackle everything simultaneously, so community feedback on prioritization is invaluable. If any of these areas are critical to your use cases, please engage with us on [GitHub Issues](https://github.com/spring-projects/spring-ai/issues) or contribute pull requests.

The team is also investing in AI-powered tooling to help manage our growing backlog more efficiently, but your input remains essential for steering the project's direction.

## 🙏 Contributors

Thanks to all contributors who made this release possible:

- [Ahmed Maruf (@ohMaruf)](https://github.com/ohMaruf)
- [Ahoo Wang (@ahoowang)](https://github.com/ahoowang)
- [Alexandros Pappas (@apappascs)](https://github.com/apappascs)
- [Andrea Vacondio (@andrea.vacondio)](https://github.com/andrea.vacondio)
- [azurelee (@aliqingdong)](https://github.com/aliqingdong)
- [chainHo (@chainhou)](https://github.com/chainhou)
- [chen.xue (@huihaoweishui)](https://github.com/huihaoweishui)
- [Cho-Hyun-Seung (@Cho-Hyun-Seung)](https://github.com/Cho-Hyun-Seung)
- [Christian Tzolov (@christian.tzolov)](https://github.com/christian.tzolov)
- [Dan Sarlo (@dsarlo-viso)](https://github.com/dsarlo-viso)
- [Daniel Garnier-Moiroux (@git)](https://github.com/git)
- [Eddú Meléndez (@eddu.melendez)](https://github.com/eddu.melendez)
- [Eddú Meléndez Gonzales (@eddu.melendez)](https://github.com/eddu.melendez)
- [Emmanuel Essien-nta (@colourfulemmanuel)](https://github.com/colourfulemmanuel)
- [Filip Hrisafov (@filip.hrisafov)](https://github.com/filip.hrisafov)
- [finyuq (@finyuq)](https://github.com/finyuq)
- [Gareth Evans (@gareth)](https://github.com/gareth)
- [Gerrit Meier (@meistermeier)](https://github.com/meistermeier)
- [Giorgos Gaganis (@gaganis)](https://github.com/gaganis)
- [Guan Huo (@9uanhuo)](https://github.com/9uanhuo)
- [Guo (@ggndnn)](https://github.com/ggndnn)
- [han (@TheEterna)](https://github.com/TheEterna)
- [Henning Pöttker (@hpoettker)](https://github.com/hpoettker)
- [Hudson Luiz Sales Schumaker (@hudson.schumaker)](https://github.com/hudson.schumaker)
- [Hyunsik Aeom (@aeomhs)](https://github.com/aeomhs)
- [Ilayaperumal Gopinathan (@ilayaperumalg)](https://github.com/ilayaperumalg)
- [ingbyr (@zwk)](https://github.com/zwk)
- [Jan-Eric Harnack (@janericharnack)](https://github.com/janericharnack)
- [jay (@rlaakswo0687)](https://github.com/rlaakswo0687)
- [Jemin Huh (@hjm1980)](https://github.com/hjm1980)
- [jonghoonpark (@dev)](https://github.com/dev)
- [lambochen (@lambochen)](https://github.com/lambochen)
- [loong-coder (@garen.mao)](https://github.com/garen.mao)
- [Lpepsi (@846179345)](https://github.com/846179345)
- [Mark Pollack (@mark.pollack)](https://github.com/mark.pollack)
- [Mingyuan Wu (@my.wu)](https://github.com/my.wu)
- [Nirsa (@KoreaNirsa)](https://github.com/KoreaNirsa)
- [NOUNI El bachir (@enimiste)](https://github.com/enimiste)
- [pavan kumar punna (@punnapavankumar9)](https://github.com/punnapavankumar9)
- [Philipp Krenn (@xeraa)](https://github.com/xeraa)
- [Piotr Kubowicz (@piotr.kubowicz)](https://github.com/piotr.kubowicz)
- [qwp_p (@RobinElysia)](https://github.com/RobinElysia)
- [Sebastian Espei (@seblsebastian)](https://github.com/seblsebastian)
- [Seokjae Lee (@seok9211)](https://github.com/seok9211)
- [SexyProgrammer (@SexyProgrammer)](https://github.com/SexyProgrammer)
- [shown (@yuluo08290126)](https://github.com/yuluo08290126)
- [SiBo Ai (@ai-afk)](https://github.com/ai-afk)
- [Sizhe Fan (@paoxiaomooo)](https://github.com/paoxiaomooo)
- [Soby Chacko (@soby.chacko)](https://github.com/soby.chacko)
- [Solomon Hsu (@solnone)](https://github.com/solnone)
- [spud (@jamespud)](https://github.com/jamespud)
- [Sun Yuhan (@sunyuhan1998)](https://github.com/sunyuhan1998)
- [Tran Ngoc Nhan (@ngocnhan.tran1996)](https://github.com/ngocnhan.tran1996)
- [WOONBE (@kepull2918)](https://github.com/kepull2918)
- [Yang Buyi (@yangbuyiya)](https://github.com/yangbuyiya)
- [Yanming Zhou (@zhouyanming)](https://github.com/zhouyanming)
- [yiangjm (@yangjm-41)](https://github.com/yangjm-41)
- [YunKui Lu (@luyunkui95)](https://github.com/luyunkui95)
- [徐功明 (@XuGongming)](https://github.com/XuGongming)
- [老虎是条大狼狗 (@494509580)](https://github.com/494509580)
- [난기수 (@nankisu0301)](https://github.com/nankisu0301)



## Resources

[Project Page](https://spring.io/projects/spring-ai/) | [GitHub](https://github.com/spring-projects/spring-ai) | [Issues](https://github.com/spring-projects/spring-ai/issues) | [Documentation](https://docs.spring.io/spring-ai/docs/1.0.1/reference/html) | [Stack Overflow](https://stackoverflow.com/questions/tagged/spring-ai)