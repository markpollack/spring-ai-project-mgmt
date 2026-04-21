# PR Review Pipeline

## Project
Python-based PR review/merge pipeline for spring-projects/spring-ai. Being rewritten in Java using AgentWorks stack.

## Tracking
- `plans/ROADMAP.md` is the source of truth for implementation progress
- Execute steps individually, capture learnings after each step
- Read prior step learnings before starting the next step

## Build (Python — current)
```bash
python3 pr_workflow.py <PR_NUMBER> --batch-mode
```

## Build (Java — planned)
```bash
./mvnw compile    # compile
./mvnw test       # unit tests
./mvnw verify     # full build with quality checks
```

## Key AgentWorks Dependencies (all released, no SNAPSHOTs)
- `agentworks-bom` 1.0.4 (`io.github.markpollack`)
- `workflow-core` 0.3.0 (`io.github.markpollack`) — Step<I,O>, Workflow DSL
- `journal-core` 0.9.0 (`io.github.markpollack`) — Run tracking, events
- `agent-judge-core` 0.9.1 (`org.springaicommunity`) — Judge framework
- `agent-client-core` 0.11.0 (`org.springaicommunity.agents`) — AgentClient for Claude Code

## AgentWorks Source
- Local source: `~/projects/agentworks/`
- Prefer reading source over decompiling from ~/.m2
