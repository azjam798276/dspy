# DSPy Project Optimization Workflow

This guide explains how to onboard and optimize new agentic projects using the **Adapter Pattern** within the `dspy` workspace.

**Source of Truth:** The optimization logic resides in `optimizer/`.
**Target:** Projects are loaded as subdirectories (e.g., `kasm-operator/`, `my-new-project/`).

## 1. The Adapter Pattern

We do `not` modify the handwritten `SKILL.md`. Instead, we generate an `adapter.md` overlay.
- **`SKILL.md`**: The immutable "Persona" (handwritten).
- **`adapter.md`**: The dynamic "Learnings" (machine-generated instructions + few-shot demos).

## 2. Onboarding a New Project

To add a new project (e.g., `@my-project`) to the workspace:

### Step 1: Create Directory Structure
Create a folder `my-project/` in the `dspy` root with this structure:
```text
my-project/
├── skills/
│   └── <skill-name>/
│       └── SKILL.md      # Define your agent's persona here
├── stories/              # Create .story.md files for training
└── golden-examples/      # (Optional) Seed examples
```

### Step 2: Define the Base Skill
Write your `SKILL.md`. Include the core identity and rules.
*Example: `my-project/skills/developer/SKILL.md`*

## 3. Running Optimization

Run the central optimizer against your project folder.

### A. Generate Golden Examples (Retrospective)
If you have trace logs from previous runs, harvest them:
```bash
python3 optimizer/retrospective.py \
  --repo-root my-project \
  --skill <skill-name> \
  --input-dir .gemini/traces \
  --output-dir my-project/golden-examples/<skill-name>
```

### B. Run COPRO Optimization
This will train the agent and generate the `adapter.md`.

```bash
python3 optimizer/optimize.py \
  --repo-root my-project \
  --trainset my-project/stories/*.story.md \
  --skill <skill-name> \
  --max-rollouts 10 \
  --bootstrap \
  --examples-dir my-project/golden-examples/<skill-name>
```

## 4. Result
The optimizer will create:
`my-project/skills/<skill-name>/adapter.md`

This file contains:
1. Optimized Instructions (evolved nuances).
2. `## Demonstrations`: A curated list of few-shot examples that guide the agent.

## 5. Execution
Your agent runtime (`GeminiSkillAdapter`) should load:
`SKILL.md` + `adapter.md` (if exists).
