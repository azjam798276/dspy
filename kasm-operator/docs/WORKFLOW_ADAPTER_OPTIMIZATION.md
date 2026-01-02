# Adapter Pattern Optimization Workflow

This document outlines the standard operating procedure for optimizing agent skills in the `dspy` framework using the **Adapter Pattern**. This approach ensures that the base skill definition (`SKILL.md`) remains immutable, while optimization results and few-shot examples are saved to a dynamic `adapter.md` file.

## 1. Concept

The **Adapter Pattern** decouples the static "Persona" from the dynamic "Learnings".
- **`SKILL.md`**: The base persona, core principles, and immutable instructions. (Hand-written, version controlled).
- **`adapter.md`**: The optimized overlay. Contains:
  - Refined instructions or slight tweaks to the rules.
  - **Demonstrations**: A set of few-shot "Problem -> Solution" examples bootstrapped from successful runs.

When the agent runs, it loads `SKILL.md` + `adapter.md` (if present) to form its full system prompt.

## 2. Project Setup

When initializing a new project folder (e.g., `kasm-operator`, `toddlerbot`):

### 2.1 File Structure
Ensure the following structure exists:
```text
project-root/
├── scripts/
│   ├── optimize.py       # The optimization engine
│   └── retrospective.py  # Trend analysis & example generation
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md      # Base definition
│       └── adapter.md    # (Generated Output)
├── stories/              # User stories for training
└── golden-examples/      # (Optional) Seed examples
```

### 2.2 Script Dependencies
Ensure `scripts/optimize.py` is the version that supports the Adapter Pattern. Key features:
- Defaults to `adapter.md` output.
- Appends `## Demonstrations` to the output file.
- Loads `SKILL.md` as the baseline context.

## 3. Workflow Steps

### Step 1: Define the Base Skill
Create or verify `skills/<skill-name>/SKILL.md`. This should contain the "Identity", "Core Principles", and "Format" instructions.
**Do not** populate it with many examples manually; the optimizer will do that.

### Step 2: Generate Golden Examples (Retrospective)
If you have previous run logs or a few manually solved stories, use `retrospective.py` to harvest them into a dataset.

```bash
python3 scripts/retrospective.py \
  --skill <skill-name> \
  --input-dir .gemini/traces \
  --output-dir golden-examples/<skill-name>
```

### Step 3: Run Optimization
Execute `optimize.py`. This script will:
1. Load `SKILL.md` as the baseline.
2. Run the `BootstrapFewShot` optimizer against the `stories/`.
3. Select the best traces.
4. Generate `adapter.md` containing the optimized instructions and the top few-shot demonstrations.

**Command:**
```bash
python3 scripts/optimize.py \
  --trainset stories/*.story.md \
  --skill <skill-name> \
  --max-rollouts 10 \
  --bootstrap \
  --examples-dir golden-examples/<skill-name> \
  --repo-root .
```

### Step 4: Verify Output
Check `skills/<skill-name>/adapter.md`.
- It should start with any refined text/headers.
- It MUST end with a `## Demonstrations` section containing the bootstrapped examples.

## 4. Usage in Agent
The `GeminiSkillAdapter` (or execution agent) reads both files:
1. `SKILL.md` is read as the system instruction.
2. `adapter.md` is appended to the context, providing specific "How-To" patterns without overwriting the core persona.

## 5. Iteration
To improve the skill further:
1. keep `adapter.md` (the script prioritizes it as the new baseline if it exists).
2. Run `optimize.py` again.
3. The script will refine the content in `adapter.md` and potentially rotate the demonstrations based on new scoring.
