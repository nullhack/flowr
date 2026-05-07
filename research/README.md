# Scientific Research — Index

Theoretical and empirical foundations for the decisions made in this template, organised by domain.

Each source is documented in its own file following the research source note template. Files are organised into topic subdirectories.

## Directory Structure

| Directory | Files | Domain |
|---|---|---|
| `architecture/` | 9 | Hexagonal Architecture, ADRs, 4+1 View Model, C4 model, information hiding, ATAM, Conway's Law, architect as decision-maker, team topologies |
| `ai-agents/` | 14 | Minimal-scope agent design, context isolation, on-demand skills, instruction conflict resolution, positional attention degradation, modular prompt de-duplication, three-file separation synthesis, actor model, CSP, session types, statecharts, design by contract, Petri nets |
| `cognitive-science/` | 10 | Pre-mortem, implementation intentions, commitment devices, System 2, adversarial collaboration, accountability, chunking, elaborative encoding, error feedback, prospective memory |
| `documentation/` | 7 | Developer information needs, docs-as-code, Diátaxis framework, blameless post-mortems, arc42 template, Google design docs, RFC/technical spec pattern |
| `domain-modeling/` | 8 | DDD bounded contexts, DDD Reference, ubiquitous language (Fowler), bounded context (Fowler), Vernon IDDD, Verraes UL-not-glossary, Whirlpool process, ISO 704 |
| `oop-design/` | 5 | Object Calisthenics, Refactoring (Fowler), GoF Design Patterns, SOLID, refactoring.guru |
| `refactoring-empirical/` | 6 | QDIR smell prioritization, smells + architectural refactoring, SPIRIT tool, bad OOP engineering properties, CWC complexity metric, metric threshold unreliability |
| `requirements-elicitation/` | 16 | INVEST, Example Mapping, declarative Gherkin, MoSCoW, active listening, active listening synthesis, Kipling 5Ws, BA framework, FDD, affinity mapping, Event Storming, CIT, cognitive interview, laddering, funnel technique, RE issues |
| `software-economics/` | 1 | Cost of change curve (shift left) |
| `testing/` | 9 | Observable behaviour testing, test-behaviour alignment, first-class tests, property-based testing, mutation testing, Canon TDD, GOOS outer/inner loop, Is TDD Dead, BDD origin |
| `version-control/` | 5 | Pro Git, git-flow model, Git cheat sheet, Git anti-patterns, merge vs. rebase |

## File Naming Convention

- `author_year.md` — single or two authors (e.g., `cockburn_2005.md`, `skelton_pais_2019.md`)
- `firstauthor_et_al_year.md` — three or more authors (e.g., `geng_et_al_2025.md`)
- `org_year.md` — organizations (e.g., `openai_2024.md`)
- `topic_synthesis.md` — synthesized from multiple sources (e.g., `agent_architecture_synthesis.md`)

## Confidence Levels

| Level | Meaning |
|---|---|
| High | Confirmed by peer-reviewed research or widely adopted industry practice |
| Moderate | Partially confirmed or confirmed with caveats |
| Low | Practitioner synthesis or single-source evidence |
| Very low | Inferred or not directly verified |

## Method Categories

| Method | Meaning |
|---|---|
| Meta-analysis | Systematic review of multiple studies |
| Experiment | Controlled or quasi-experimental study |
| Observational | Industry report or field study |
| Theoretical | Conceptual framework or formal model |
| Practitioner | Industry blog, book, or practitioner experience |
| Synthesized | Convergence of multiple sources |