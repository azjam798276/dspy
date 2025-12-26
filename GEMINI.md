# Project Ouroboros Context

## 1. Project Overview
**Project Name:** Project Ouroboros (also known as Self-Healing Sheet Music)
**Goal:** To implement a "Reflective Optimization Loop" where an AI agent (Developer persona) autonomously refines its own governing instructions (`SKILL.md`) using the Genetic-Pareto (GEPA) algorithm from the DSPy framework.
**Core Innovation:** Treating the static `SKILL.md` definition of an agent as a mutable variable that evolves based on feedback from implementation failures (test logs, linter errors).

## 2. Current Workspace Status
**Type:** Design & Configuration Repository
**Status:** Design Phase / Solutioning
**Note:** This directory currently contains the **Design Documentation** and **Skill Definitions**. The implementation code (Python optimizer, Node.js BMAD scaffolding, adapters) described in the TDD is **not present** in this root directory.

## 3. Key Documentation Files
*   **`PRD.md` (Product Requirements Document):**
    *   Outlines the "Jazz Musician" problem: AI agents improvising instead of following strict constraints.
    *   Defines the PoC objective: Use GEPA to optimize `SKILL.md` to pass specific "User Stories".
    *   Target Metric: Pass Rate improvement >20%.
*   **`ADD_v0.1.md` (Architecture Design Document):**
    *   Describes the **Trinity Architecture**:
        1.  **BMAD Layer:** Node.js orchestration.
        2.  **Gemini Layer:** Execution agent (Direct CLI).
        3.  **DSPy Layer:** Python-based optimization engine.
    *   Defines the "Read-Execute-Reflect-Rewrite" cycle.
*   **`TDD_v0.1.md` (Technical Design Document):**
    *   Detailed specifications for:
        *   `GeminiSkillAdapter`: Python bridge to Gemini CLI.
        *   `BMadImplementationMetric`: Feedback extraction from `npm test` logs.
        *   Data Schemas: Trace logs, Pareto frontier JSON.

## 4. Directory Structure
```text
/
├── ADD_v0.1.md          # Architecture specs
├── PRD.md               # High-level requirements and goals
├── TDD_v0.1.md          # Technical implementation specs
└── skills/              # Agent Persona Definitions (SKILL.md registry)
    ├── architect/       # System Architect persona
    ├── backend-engineer/# Backend Developer persona
    ├── orchestrator/    # Workflow Orchestrator
    ├── qa1/             # QA Engineer
    └── ...              # Other personas
```

## 5. System Architecture (Current)
The system operates as follows:
1.  **Optimization Engine (DSPy):** Selects a `SKILL.md` candidate.
2.  **Adapter:** Writes the candidate skill to `.gemini/sessions/{skill}/GEMINI.md`.
3.  **Student (Gemini CLI):** Reads the skill and a Story file, then generates code changes.
4.  **Validator:** Runs `npm test`.
5.  **Metric:** capturing failure logs (e.g., "ReferenceError").
6.  **Reflector (Gemini CLI):** Analyzes *why* it failed and proposes a mutation to `SKILL.md` (e.g., adding a constraint "Always validate input").

## 6. Usage Guidelines
*   **For Context:** Refer to `PRD.md` for the "Why" and `ADD_v0.1.md` for the "How".
*   **For Implementation:** Use `TDD_v0.1.md` as the blueprint for writing the `optimizer/` Python module and adapters.
*   **For Skills:** The `skills/` directory acts as the seed/baseline for the agent personas. Future optimization runs will evolve these files.
