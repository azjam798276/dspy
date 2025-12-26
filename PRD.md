PRD: Autonomous Reflective Optimization of Codex Skills via GEPA
Project Codenames: Project Ouroboros / Self-Healing Sheet Music Version: 1.0 (PoC Candidate) Author: Prof. [Your Name] Framework Base: BMAD-Method v6 Alpha + DSPy 2.5 + OpenAI Codex
1. Executive Summary
This project seeks to validate a Reflective Optimization Loop where an agentic software engineer autonomously refines its own governing instructions. By treating the static SKILL.md definition of a Codex agent as a mutable variable within a DSPy program, we will employ the Genetic-Pareto (GEPA) algorithm to mathematically converge on an optimal prompt signature. The system will utilize implementation-phase failure logs (e.g., test failures, linter errors) as negative reward signals to evolve the agent's skills from stochastic improvisation to domain-specific precision.
2. Problem Statement
• The "Jazz Musician" Problem: Current AI coding agents (like Codex) are talented improvisers but prone to "hallucinations" and context drift when given static instructions.
• Static Competence: SKILL.md files provide context and capabilities, but they are currently static text written by humans. If an agent repeatedly fails a specific task (e.g., "always validate the database input in tests"), the human must manually update the skill.
• Inefficient Optimization: Traditional Reinforcement Learning (GRPO) requires thousands of rollouts to correct behavior. We need a method that learns from rich textual feedback in fewer than 600 rollouts.
3. PoC Objectives
1. Implement the Loop: Successfully wrap a BMAD "Developer" Agent (Codex-based) within a dspy.Module.
2. Enable Mutation: Configure dspy.GEPA to treat the text content of SKILL.md as the "Instruction" variable to be optimized.
3. Close the Feedback Cycle: Automate the extraction of failure logs (from npm test or build logs) and feed them into the GEPA metric function as "Reflective Feedback".
4. Measure Convergence: Demonstrate that the agent's pass rate on a specific set of "User Stories" increases over iterations without human intervention.
4. Technical Architecture
4.1 The Subject: Codex Agent with Dynamic Skills
We will utilize the BMAD v6 structure, specifically the Developer persona.
• Skill Location: $REPO_ROOT/.codex/skills/feature-dev/SKILL.md.
• Skill Structure: Standard Codex YAML frontmatter + Markdown body.
• Mutability: The Markdown body (Instructions) is the optimization target.
4.2 The Optimizer: DSPy & GEPA
We will use GEPA (Genetic-Pareto) because it supports "Rich Textual Feedback" rather than just scalar scores.
• Candidate Selection: Pareto-based. We want to find prompts that balance speed (token usage) with accuracy (test pass rate).
• Reflection LM: A strong model (GPT-4o) that analyzes why the code failed and rewrites the SKILL.md to prevent that specific error type.
4.3 The Environment: BMAD Workflow
• Trigger: The Scrum Master (SM) creates a Story file (1.1.user-registration.story.md).
• Action: The Codex Agent reads the story and the SKILL.md, then generates code.
• Validation: The QA Agent (Quinn) runs the test suite. The output of this validation is the "Ground Truth" for the optimizer.
5. Implementation Specifications
5.1 Step 1: Project Initialization (BMAD)
• Action: Initialize a BMAD v6 project using the npx bmad-method@alpha install command.
• Configuration: Select "BMad Method" track (standard product) to ensure we have PRD and Architecture documents.
• Customization: Use the BMad Builder to scaffold a custom module named SelfHealingDev.
5.2 Step 2: The Adapter (Codex_DSPy)
We must bridge the gap between DSPy's Python environment and Codex's CLI.
• Reference Repo: darinkishore/codex_dspy.
• Adapter Logic: Create a class CodexSkillAdapter that inherits from dspy.Module.
    ◦ Input: story_context (The content of the .story.md file).
    ◦ Instruction: The content of SKILL.md (This is what GEPA optimizes).
    ◦ Output: code_diff (The actual code changes).
    ◦ Mechanism: The adapter writes the current "Instruction" candidate to .codex/skills/feature-dev/SKILL.md before invoking the Codex CLI.
5.3 Step 3: The Metric Function (The Critic)
We define a custom GEPAFeedbackMetric.
def bmad_implementation_metric(gold, pred, trace):
    # 1. Run the BMAD validation script (e.g., npm test)
    result = subprocess.run(['npm', 'test'], capture_output=True, text=True)
    
    # 2. Score Calculation
    score = 1.0 if result.returncode == 0 else 0.0
    
    # 3. Rich Feedback Extraction
    # If failed, extract the error message (e.g., "ReferenceError: db is not defined")
    feedback = f"Tests passed: {score}. Log: {result.stderr[-500:]}"
    
    return dspy.ScoreWithFeedback(score=score, feedback=feedback)

Citation:
5.4 Step 4: The Optimization Loop
Run the optimization using a "Trainset" of 5-10 failed implementation stories from a previous project.
optimizer = dspy.GEPA(
    metric=bmad_implementation_metric,
    reflection_lm=dspy.LM('gpt-4o'),
    max_metric_calls=50  # Limit budget for PoC
)
# The "student" is our CodexSkillAdapter with the initial SKILL.md
optimized_program = optimizer.compile(student=codex_adapter, trainset=story_dataset)

Citation:
6. Expected Outcomes & Success Metrics
• Convergence: The optimizer should produce a SKILL.md that explicitly forbids the errors encountered in the first few runs (e.g., "Always import utils.js relative to src/").
• Metric: A "Pass Rate" improvement of >20% on the validation set compared to the generic Codex system prompt.
• Artifact: A highly specialized SKILL.md file that serves as a "Golden Instruction Set" for this specific codebase.
7. Risks and Mitigations
• Context Poisoning: If SKILL.md becomes too long, performance degrades.
    ◦ Mitigation: GEPA naturally penalizes verbosity if it leads to confusion/errors, but we can add a length penalty to the metric.
• Loop Latency: Running npm test inside an optimization loop is slow.
    ◦ Mitigation: Use small, isolated unit tests for the PoC rather than full integration suites.
• Cost: GPT-4o calls for reflection can be expensive.
    ◦ Mitigation: Use dspy.Assert to fail fast before calling the LLM if the syntax is obviously broken.
8. Professor's "Go/No-Go" Criterion
The PoC is considered a success if and only if the system autonomously modifies the SKILL.md file to include a specific technical constraint (e.g., "Use await on database calls") that was not in the original prompt, solely derived from analyzing a runtime error log. This proves the transition from "Vibe Coding" to "Reflective Engineering".

