ARCHITECTURE.md v0.1
Project Ouroboros: Autonomous Reflective Optimization System
Document Version: 0.2
 Framework: BMAD-Method v6 Alpha + DSPy 2.5 + Google Gemini CLI
 Status: Design Phase (Solutioning)
 Author: System Architecture Team
 Last Updated: 2025-12-25

1. Executive Summary
Project Ouroboros implements a Trinity Architecture that enables autonomous refinement of AI agent instructions through mathematical optimization. The system combines three distinct layers:
BMAD Layer (Orchestration): Node.js-based framework managing the agile workflow, story files, and agent coordination
Gemini Layer (Execution): Google Gemini CLI agent performing actual code implementation using dynamically loaded context (GEMINI.md)
DSPy Layer (Optimization): Python-based reflective optimization engine using GEPA to evolve skill definitions
The core innovation is treating the GEMINI.md context file as a mutable instruction variable within a DSPy program. Implementation failures (test logs, linter errors) serve as negative reward signals, driving evolutionary convergence toward domain-specific precision. This architecture solves the interoperability challenge through a subprocess-based adapter pattern that bridges Python's optimization loop with the Gemini CLI's execution environment.
Key Architectural Principle: The system implements a "read-execute-reflect-rewrite" cycle where the Python optimizer modifies the context file, the Gemini agent executes using those instructions, and the metric function analyzes failures to guide the next mutation.

2. Technology Stack
2.1 Python Environment (Optimization Engine)
Component
Version
Purpose
Python
3.10+
Runtime environment
DSPy
2.5.0+
Prompt optimization framework
GEPA
(bundled with DSPy 2.5)
Genetic-Pareto optimizer
PyYAML
6.0+
SKILL.md frontmatter parsing
pytest
7.4+
Test harness for validation
subprocess32
Latest
Reliable process invocation

Installation:
pip install dspy-ai>=2.5.0 pyyaml pytest

2.2 Node.js Environment (BMAD Scaffolding)
Component
Version
Purpose
Node.js
18.x LTS
Runtime environment
BMAD-Method
v6.0.0-alpha
Agile workflow framework
TypeScript
5.x
Type-safe orchestration
Gemini CLI
Latest
Agent execution wrapper (1M token context, 60 req/min free tier)

Installation:
npx bmad-method@alpha install
npm install -g @anthropic/gemini-cli  # Or: npx @anthropic/gemini-cli

2.3 Bridge Mechanism: GeminiAgent Adapter
The interoperability challenge is solved via the GeminiAgent Adapter Pattern. This adapter:
Writes the current context candidate to .gemini/GEMINI.md (Gemini's native context file)
Invokes the Gemini CLI via subprocess.run() with non-interactive mode (-p flag)
Captures structured JSON output (--output-format json)
Returns structured output to DSPy's evaluation pipeline
Critical Design Decision: We use Gemini CLI's native GEMINI.md context loading rather than API calls. This maintains zero impedance mismatch with Gemini's expected environment while leveraging its built-in file operations and shell command tools.

3. System Component Design
3.1 The Subject: Gemini Developer Agent
Component: GeminiExecutor
Type: Subprocess-wrapped CLI Agent
Location: $REPO_ROOT/.gemini/
Responsibility: Execute implementation tasks using dynamically loaded GEMINI.md context

Configuration:
Context loading: GEMINI.md file at repository root or .gemini/ directory
Context window: 1M tokens (Gemini 2.5 Pro)
Output format: JSON (--output-format json) or stream-json for real-time
Interface with DSPy:
class GeminiExecutor:
    def execute_story(self, skill_content: str, story_path: str) -> dict:
        # 1. Write context to .gemini/GEMINI.md
        # 2. Invoke: gemini -p "$(cat {story_path})" --output-format json
        # 3. Capture: code changes, test results, error logs
        # 4. Return: structured execution trace

3.2 The Critic: GEPAFeedbackMetric
Component: BMadImplementationMetric
Type: DSPy Metric Function
Responsibility: Evaluate code quality and extract failure feedback

Implementation Specification:
from dspy import ScoreWithFeedback
import subprocess
import re

class BMadImplementationMetric:
    def __call__(self, example, prediction, trace=None):
        """
        Evaluates Codex output by running project tests.
        
        Args:
            example: Training instance (story + expected behavior)
            prediction: Codex-generated code changes
            trace: Full execution trace (optional)
            
        Returns:
            ScoreWithFeedback: Binary score + rich textual feedback
        """
        # Apply the code changes to a sandbox branch
        apply_code_changes(prediction.code_patch)
        
        # Execute test suite
        test_result = subprocess.run(
            ['npm', 'test', '--', '--silent'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Calculate binary score
        score = 1.0 if test_result.returncode == 0 else 0.0
        
        # Extract rich feedback
        feedback = self._parse_failure_log(test_result.stderr)
        
        # Rollback sandbox
        rollback_changes()
        
        return ScoreWithFeedback(
            score=score,
            feedback=feedback
        )
    
    def _parse_failure_log(self, stderr: str) -> str:
        """
        Extracts actionable error patterns from test logs.
        
        Priority patterns:
        1. ReferenceError: Variable not defined
        2. TypeError: Incorrect function signature
        3. AssertionError: Test expectation violated
        """
        patterns = {
            'undefined_var': r'ReferenceError: (\w+) is not defined',
            'type_error': r'TypeError: (.+)',
            'assertion': r'AssertionError: (.+)',
            'import_fail': r'Cannot find module [\'"](.+)[\'"]'
        }
        
        errors = []
        for category, pattern in patterns.items():
            matches = re.findall(pattern, stderr)
            if matches:
                errors.append(f"{category}: {matches[0]}")
        
        return f"Test failure. Errors: {'; '.join(errors)}"

Critical Feature: The metric returns ScoreWithFeedback, not just a float. This enables GEPA's reflection model to understand why the code failed, not just that it failed.
3.3 The Optimizer: GEPA Engine
Component: ReflectiveSkillOptimizer
Type: DSPy GEPA Compiler
Responsibility: Evolve SKILL.md through Pareto-based selection

Configuration:
from dspy import GEPA, LM

optimizer = GEPA(
    metric=BMadImplementationMetric(),
    reflection_lm=LM('openai/gpt-4o'),  # Strong model for analysis
    max_metric_calls=50,  # Budget for PoC
    pareto_minibatch_size=10,  # Balance exploration/exploitation
    verbose=True
)

Optimization Loop:
graph TD
    A[Initialize Population] --> B[Select from Pareto Frontier]
    B --> C[Execute Rollout on Story]
    C --> D[Run Tests & Capture Logs]
    D --> E[Metric: Score + Feedback]
    E --> F[Reflection LM Analyzes Failure]
    F --> G[Propose SKILL.md Mutation]
    G --> H[Evaluate on Validation Set]
    H --> I{Dominates Existing?}
    I -->|Yes| J[Add to Frontier]
    I -->|No| K[Discard]
    J --> L{Budget Remaining?}
    K --> L
    L -->|Yes| B
    L -->|No| M[Return Best Candidate]

Pareto Frontier Logic: A candidate SKILL.md is non-dominated if:
No other skill scores higher on ALL validation stories
It introduces a unique trade-off (e.g., faster execution but slightly lower accuracy)
This multi-objective approach prevents premature convergence and maintains diversity in the skill population.

4. Data Flow & Directory Structure
4.1 Source Tree Layout
project-ouroboros/
├── .gemini/                          # Gemini configuration
│   ├── GEMINI.md                     # ← Mutable optimization target (context file)
│   └── settings.json                 # Optional agent settings
│
├── .dspy_cache/                      # DSPy optimization artifacts
│   ├── pareto_frontier.json          # Current best candidates
│   ├── trace_logs/                   # Rollout execution traces
│   │   ├── rollout_001.json
│   │   └── rollout_002.json
│   └── skill_versions/               # Historical GEMINI.md snapshots
│       ├── v1_baseline.md
│       └── v2_optimized.md
│
├── stories/                          # BMAD story files (training data)
│   ├── 1.1.user-registration.story.md
│   └── 1.2.password-validation.story.md
│
├── src/                              # Implementation (Gemini output)
│   ├── features/
│   └── utils/
│
├── tests/                            # Validation suite
│   └── integration/
│
├── optimizer/                        # Python DSPy module
│   ├── __init__.py
│   ├── gemini_adapter.py             # Bridge to Gemini CLI
│   ├── metric.py                     # BMadImplementationMetric
│   └── optimize.py                   # Main optimization script
│
└── package.json                      # Node.js dependencies

4.2 Data Flow Diagram
sequenceDiagram
    participant DSPy as DSPy Optimizer
    participant Adapter as GeminiAgent Adapter
    participant FS as Filesystem
    participant Gemini as Gemini CLI
    participant Tests as Test Suite
    
    DSPy->>Adapter: execute_with_skill(candidate_skill, story)
    Adapter->>FS: Write to .gemini/GEMINI.md
    Adapter->>Gemini: subprocess.run(['gemini', '-p', story_content, '--output-format', 'json'])
    Gemini->>FS: Load GEMINI.md as project context
    Gemini->>FS: Write code changes to src/
    Gemini-->>Adapter: Return JSON execution trace
    Adapter->>Tests: subprocess.run(['npm', 'test'])
    Tests-->>Adapter: Exit code + stderr log
    Adapter->>FS: Save trace to .dspy_cache/trace_logs/
    Adapter-->>DSPy: Return {code_patch, test_result, error_log}
    DSPy->>DSPy: Metric evaluates: score + feedback
    DSPy->>DSPy: Reflection LM proposes mutation
    DSPy->>FS: Update Pareto frontier JSON

Critical Path:
DSPy writes candidate → Filesystem
Gemini reads from Filesystem → Executes
Tests validate → Logs captured
Logs analyzed → Next candidate generated
Rationale for Filesystem Coupling: Gemini CLI's GEMINI.md context loading is filesystem-native. This ensures zero impedance mismatch with Gemini's expected environment while leveraging its 1M token context window.

5. Interface Definitions
5.1 DSPy Signature for GeminiSkillAdapter
from dspy import Signature, InputField, OutputField

class GeminiImplementationSignature(Signature):
    """
    Signature for Gemini-based feature implementation.
    The 'instruction' field is the mutable GEMINI.md content.
    """
    
    # Inputs
    story_context: str = InputField(
        desc="Full content of the .story.md file including acceptance criteria"
    )
    
    tech_stack: str = InputField(
        desc="Technology constraints from Architecture.md (e.g., 'React 18, Node 18')"
    )
    
    instruction: str = InputField(
        desc="Current GEMINI.md content - THIS IS THE OPTIMIZATION TARGET",
        prefix="You are a specialized Developer agent. Follow these instructions:\n"
    )
    
    # Outputs
    code_patch: str = OutputField(
        desc="Git-style diff of all file changes"
    )
    
    test_results: str = OutputField(
        desc="Output of 'npm test' command"
    )
    
    reasoning: str = OutputField(
        desc="Two-turn pattern: Thought process before action"
    )

Key Design Decision: The instruction field maps directly to GEMINI.md content. GEPA will mutate this field while holding story_context and tech_stack constant.
5.2 GeminiAgent Adapter Implementation
import dspy
import subprocess
import os
from pathlib import Path

class GeminiSkillAdapter(dspy.Module):
    """
    Bridges DSPy optimization loop with Gemini CLI execution.
    Uses non-interactive mode (-p) with JSON output format.
    """
    
    def __init__(self, gemini_binary: str = "gemini"):
        super().__init__()
        self.gemini_binary = gemini_binary
        self.context_path = Path(".gemini/GEMINI.md")
        
    def forward(self, story_context: str, tech_stack: str, instruction: str):
        """
        Execute Gemini with the given GEMINI.md content.
        
        Returns:
            dspy.Prediction with code_patch, test_results, reasoning
        """
        # Step 1: Write the candidate GEMINI.md atomically
        self._write_context_atomic(instruction)
        
        # Step 2: Prepare prompt with story context
        prompt = self._prepare_prompt(story_context, tech_stack)
        
        # Step 3: Invoke Gemini CLI with non-interactive mode
        try:
            result = subprocess.run(
                [self.gemini_binary, "-p", prompt, "--output-format", "json"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
                check=False
            )
            
            code_patch = self._extract_code_changes(result.stdout)
            reasoning = self._extract_reasoning(result.stdout)
            
        except subprocess.TimeoutExpired:
            code_patch = ""
            reasoning = "ERROR: Gemini execution timed out"
        
        # Step 4: Run tests to validate
        test_results = self._run_tests()
        
        return dspy.Prediction(
            code_patch=code_patch,
            test_results=test_results,
            reasoning=reasoning
        )
    
    def _write_context_atomic(self, content: str):
        """Atomic write to prevent race conditions."""
        self.context_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.context_path.with_suffix('.tmp')
        temp_path.write_text(content, encoding='utf-8')
        temp_path.replace(self.context_path)  # Atomic on POSIX
    
    def _run_tests(self) -> str:
        """Execute test suite and capture output."""
        result = subprocess.run(
            ['npm', 'test', '--', '--silent', '--no-coverage'],
            capture_output=True,
            text=True,
            timeout=120
        )
        return f"Exit code: {result.returncode}\n{result.stderr}"

Two-Turn Pattern Enforcement: The adapter expects Gemini to output:
Turn 1 (Reasoning): Markdown section explaining the implementation plan
Turn 2 (Action): Actual code changes
This is enforced via the GEMINI.md template structure.

6. Coding Standards
6.1 GEMINI.md Structure Requirements
All GEMINI.md files MUST follow this structure:
---
name: feature-development
description: Implements user stories with full test coverage
version: 1.0.0
---

## Role
You are a specialized Feature Developer in the BMAD framework.

## Workflow

### Phase 1: Analysis
1. Read the story file completely
2. Extract acceptance criteria
3. Identify technical constraints from tech_stack

### Phase 2: Reasoning (Turn 1)
Output a markdown section:

Implementation Plan
File changes needed: [list]
Edge cases: [list]
Test strategy: [description]

### Phase 3: Implementation (Turn 2)
Generate code following these rules:
- Rule 1: [Specific constraint]
- Rule 2: [Specific constraint]
...

Mutation Target: Rules in Phase 3 are the primary optimization target. GEPA will add/remove/modify these rules based on failure patterns.
6.2 Atomic GEMINI.md Updates
Requirement: All writes to GEMINI.md MUST be atomic to prevent race conditions during parallel rollouts.
Implementation:
# Correct: Atomic write via temp file
temp_path = context_path.with_suffix('.tmp')
temp_path.write_text(new_content)
temp_path.replace(context_path)  # Atomic on POSIX systems

# Incorrect: Direct write (not atomic)
context_path.write_text(new_content)  # FORBIDDEN

6.3 Error Handling Standards
Principle: Fail fast with actionable errors.
# DSPy programs should use assertions for invariants
import dspy

class GeminiAdapter(dspy.Module):
    def forward(self, story_context, ...):
        dspy.Assert(
            len(story_context) > 0,
            "Story context cannot be empty"
        )
        
        # If Gemini produces syntactically invalid output
        if not self._validate_code_patch(code):
            dspy.Suggest(
                False,
                "Code patch failed syntax validation. Retry with stricter formatting rules."
            )

Rationale: dspy.Assert prevents wasted LLM calls on obviously invalid inputs. dspy.Suggest allows the optimizer to learn from validation failures.
6.4 Logging & Traceability
Requirement: Every rollout MUST produce a trace log for post-hoc analysis.
import json
from datetime import datetime

def save_trace(rollout_id: int, trace_data: dict):
    trace_file = Path(f".dspy_cache/trace_logs/rollout_{rollout_id:03d}.json")
    trace_file.parent.mkdir(parents=True, exist_ok=True)
    
    with trace_file.open('w') as f:
        json.dump({
            'timestamp': datetime.utcnow().isoformat(),
            'rollout_id': rollout_id,
            'skill_version': trace_data['skill_version'],
            'story': trace_data['story'],
            'score': trace_data['score'],
            'feedback': trace_data['feedback'],
            'execution_time_sec': trace_data['execution_time']
        }, f, indent=2)

Trace Schema:
skill_version: Hash of the SKILL.md content
story: Which training instance was executed
score: Binary pass/fail (1.0 or 0.0)
feedback: Rich textual explanation of failure
execution_time_sec: Performance metric for Pareto trade-offs

7. Deployment & Execution
7.1 Initialization Sequence
# 1. Initialize BMAD project
npx bmad-method@alpha install
# Select: "BMad Method" track

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r optimizer/requirements.txt

# 3. Initialize baseline GEMINI.md
mkdir -p .gemini
cp templates/GEMINI.baseline.md .gemini/GEMINI.md

# 4. Prepare training data (story files)
# Ensure stories/ contains at least 5 failed implementation attempts

7.2 Running the Optimization Loop
cd optimizer
python optimize.py \
  --trainset ../stories/*.story.md \
  --max-rollouts 50 \
  --output-dir ../.dspy_cache

Expected Output:
[GEPA] Iteration 1/50: Baseline skill (score=0.2)
[GEPA] Iteration 5/50: Candidate #3 on frontier (score=0.4)
[GEPA] Iteration 23/50: New Pareto leader (score=0.7, -12% tokens)
[GEPA] Iteration 50/50: Converged. Best score=0.8
[GEPA] Optimized GEMINI.md saved to .gemini/GEMINI.md

7.3 Validation Protocol
Post-Optimization Checklist:
Run full test suite: npm test
Compare token usage: DSPy metrics
Manual review of GEMINI.md mutations
Rollback if score < baseline

8. Security & Sandboxing
8.1 Code Execution Isolation
Requirement: Gemini-generated code MUST execute in an isolated environment.
Implementation Options:
Docker container per rollout (Recommended for PoC)
Git worktree (Lightweight alternative)
def execute_in_sandbox(code_patch: str):
    # Create temporary worktree
    sandbox_dir = Path(f"/tmp/ouroboros_sandbox_{uuid.uuid4()}")
    subprocess.run(['git', 'worktree', 'add', sandbox_dir, 'HEAD'])
    
    try:
        # Apply patch
        (sandbox_dir / 'changes.patch').write_text(code_patch)
        subprocess.run(['git', 'apply', 'changes.patch'], cwd=sandbox_dir)
        
        # Run tests
        result = subprocess.run(['npm', 'test'], cwd=sandbox_dir, ...)
        
    finally:
        # Cleanup
        subprocess.run(['git', 'worktree', 'remove', sandbox_dir])

8.2 GEMINI.md Validation
Requirement: Prevent injection of malicious instructions.
def validate_context_content(gemini_md: str) -> bool:
    """Ensure GEMINI.md doesn't contain dangerous patterns."""
    forbidden_patterns = [
        r'rm\s+-rf',  # Destructive commands
        r'eval\(',    # Code injection
        r'__import__' # Python import hacks
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, gemini_md):
            raise SecurityError(f"Forbidden pattern detected: {pattern}")
    
    return True


9. Success Criteria & Metrics
9.1 PoC Success Definition
The architecture is validated if:
Autonomous Mutation: The system modifies GEMINI.md without human intervention
Error-Specific Learning: The final context includes constraints NOT in the baseline (e.g., "Always validate input in unit tests")
Convergence: Pass rate improves by ≥20% over 50 rollouts
Sample Efficiency: Achieves convergence in <600 rollouts (vs. 24,000 for GRPO)
9.2 Evaluation Metrics
Metric
Target
Measurement
Pass Rate
≥80%
Tests passed / Total tests
Token Efficiency
+15%
Avg tokens per successful implementation
Rollouts to Convergence
<600
Iterations until no improvement
Skill Verbosity
<2KB
Size of optimized SKILL.md


10. Known Limitations & Future Work
10.1 Current Constraints
Single-Agent Focus: PoC optimizes only the Developer agent, not the full BMAD team
Serial Execution: No parallel rollout support (impacts optimization speed)
Local Scope: Skills are repository-specific, not synced via Federated Knowledge Architecture
Test-Driven Only: Assumes existence of comprehensive test suite
10.2 Roadmap to v1.0
Phase 2: Extend to QA Engineer (Quinn) persona
Phase 3: Implement parallel rollout execution (5x speedup)
Phase 4: Integrate with BMAD's Federated Knowledge sync
Phase 5: Add multi-objective metrics (speed + accuracy + maintainability)

Appendix A: Glossary
Term
Definition
Pareto Frontier
Set of non-dominated solutions in multi-objective optimization
Progressive Disclosure
Loading context incrementally to maximize token efficiency
Two-Turn Pattern
Agent outputs reasoning first, then action (enforces structured thinking)
Atomic Write
Filesystem operation that completes entirely or not at all
Reflective Feedback
Rich textual error analysis, not just scalar scores


Document Control:
Approval Required From: Lead Architect, DSPy Integration Lead, BMAD Framework Owner
Next Review Date: Post-PoC completion
Change Log: Track all architectural decisions in .dspy_cache/architecture_decisions.md

ARCHITECTURE.md v0.2
Project Ouroboros: Autonomous Reflective Optimization System
Document Version: 0.2
 Framework: BMAD-Method v6 Alpha + DSPy 2.5 + Google Gemini CLI
 Status: Design Phase (Solutioning)
 Author: System Architecture Team
 Last Updated: 2025-12-25

1. Executive Summary
Project Ouroboros implements a Trinity Architecture that enables autonomous refinement of AI agent instructions through mathematical optimization. The system combines three distinct layers:
BMAD Layer (Orchestration): Node.js-based framework managing the agile workflow, story files, and agent coordination
Gemini Layer (Execution): Google Gemini CLI agent performing actual code implementation using dynamically loaded context (GEMINI.md)
DSPy Layer (Optimization): Python-based reflective optimization engine using GEPA to evolve skill definitions
The core innovation is treating the GEMINI.md context file as a mutable instruction variable within a DSPy program. Implementation failures (test logs, linter errors) serve as negative reward signals, driving evolutionary convergence toward domain-specific precision. This architecture solves the interoperability challenge through a subprocess-based adapter pattern that bridges Python's optimization loop with the Gemini CLI's execution environment.
Key Architectural Principle: The system implements a "read-execute-reflect-rewrite" cycle where the Python optimizer modifies the context file, the Gemini agent executes using those instructions, and the metric function analyzes failures to guide the next mutation.

2. Technology Stack
2.1 Python Environment (Optimization Engine)
Component
Version
Purpose
Python
3.10+
Runtime environment
DSPy
2.5.0+
Prompt optimization framework
GEPA
(bundled with DSPy 2.5)
Genetic-Pareto optimizer
PyYAML
6.0+
SKILL.md frontmatter parsing
pytest
7.4+
Test harness for validation
subprocess32
Latest
Reliable process invocation

Installation:
pip install dspy-ai>=2.5.0 pyyaml pytest

2.2 Node.js Environment (BMAD Scaffolding)
Component
Version
Purpose
Node.js
18.x LTS
Runtime environment
BMAD-Method
v6.0.0-alpha
Agile workflow framework
TypeScript
5.x
Type-safe orchestration
Gemini CLI
Latest
Agent execution wrapper

Installation:
npx bmad-method@alpha install
npm install -g @google/gemini-cli

2.3 Bridge Mechanism: GeminiAgent Adapter
The interoperability challenge is solved via the GeminiAgent Adapter Pattern. This adapter:
Writes the current context candidate to .gemini/GEMINI.md (Gemini's native context file)
Invokes the Gemini CLI via subprocess.run() with non-interactive mode (-p flag)
Captures structured JSON output (--output-format json)
Returns structured output to DSPy's evaluation pipeline
Critical Design Decision: We use Gemini CLI's native GEMINI.md context loading rather than API calls. This maintains zero impedance mismatch with Gemini's expected environment while leveraging its built-in file operations and shell command tools.

3. System Component Design
3.1 The Subject: Gemini Developer Agent
Component: GeminiExecutor
Type: Subprocess-wrapped CLI Agent
Location: $REPO_ROOT/.gemini/
Responsibility: Execute implementation tasks using dynamically loaded GEMINI.md context

Configuration:
Context loading: GEMINI.md file at repository root or .gemini/ directory
Context window: 1M tokens (Gemini 2.5 Pro)
Output format: JSON (--output-format json) or stream-json for real-time
Interface with DSPy:
class GeminiExecutor:
    def execute_story(self, skill_content: str, story_path: str) -> dict:
        # 1. Write context to .gemini/GEMINI.md
        # 2. Invoke: gemini -p "$(cat {story_path})" --output-format json
        # 3. Capture: code changes, test results, error logs
        # 4. Return: structured execution trace

3.2 The Critic: GEPAFeedbackMetric
Component: BMadImplementationMetric
Type: DSPy Metric Function
Responsibility: Evaluate code quality and extract failure feedback

Implementation Specification:
from dspy import ScoreWithFeedback
import subprocess
import re

class BMadImplementationMetric:
    def __call__(self, example, prediction, trace=None):
        """
        Evaluates Gemini output by running project tests.
        
        Args:
            example: Training instance (story + expected behavior)
            prediction: Gemini-generated code changes
            trace: Full execution trace (optional)
            
        Returns:
            ScoreWithFeedback: Binary score + rich textual feedback
        """
        # Apply the code changes to a sandbox branch
        apply_code_changes(prediction.code_patch)
        
        # Execute test suite
        test_result = subprocess.run(
            ['npm', 'test', '--', '--silent'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Calculate binary score
        score = 1.0 if test_result.returncode == 0 else 0.0
        
        # Extract rich feedback
        feedback = self._parse_failure_log(test_result.stderr)
        
        # Rollback sandbox
        rollback_changes()
        
        return ScoreWithFeedback(
            score=score,
            feedback=feedback
        )
    
    def _parse_failure_log(self, stderr: str) -> str:
        """
        Extracts actionable error patterns from test logs.
        
        Priority patterns:
        1. ReferenceError: Variable not defined
        2. TypeError: Incorrect function signature
        3. AssertionError: Test expectation violated
        """
        patterns = {
            'undefined_var': r'ReferenceError: (\w+) is not defined',
            'type_error': r'TypeError: (.+)',
            'assertion': r'AssertionError: (.+)',
            'import_fail': r'Cannot find module [\'"](.+)[\'"]'
        }
        
        errors = []
        for category, pattern in patterns.items():
            matches = re.findall(pattern, stderr)
            if matches:
                errors.append(f"{category}: {matches[0]}")
        
        return f"Test failure. Errors: {'; '.join(errors)}"

Critical Feature: The metric returns ScoreWithFeedback, not just a float. This enables GEPA's reflection model to understand why the code failed, not just that it failed.
3.3 The Optimizer: GEPA Engine
Component: ReflectiveSkillOptimizer
Type: DSPy GEPA Compiler
Responsibility: Evolve GEMINI.md through Pareto-based selection

Configuration:
from dspy import GEPA, LM

optimizer = GEPA(
    metric=BMadImplementationMetric(),
    reflection_lm=LM('openai/gpt-4o'),  # Strong model for analysis
    max_metric_calls=50,  # Budget for PoC
    pareto_minibatch_size=10,  # Balance exploration/exploitation
    verbose=True
)

Optimization Loop:
graph TD
    A[Initialize Population] --> B[Select from Pareto Frontier]
    B --> C[Execute Rollout on Story]
    C --> D[Run Tests & Capture Logs]
    D --> E[Metric: Score + Feedback]
    E --> F[Reflection LM Analyzes Failure]
    F --> G[Propose GEMINI.md Mutation]
    G --> H[Evaluate on Validation Set]
    H --> I{Dominates Existing?}
    I -->|Yes| J[Add to Frontier]
    I -->|No| K[Discard]
    J --> L{Budget Remaining?}
    K --> L
    L -->|Yes| B
    L -->|No| M[Return Best Candidate]

Pareto Frontier Logic: A candidate GEMINI.md is non-dominated if:
No other skill scores higher on ALL validation stories
It introduces a unique trade-off (e.g., faster execution but slightly lower accuracy)
This multi-objective approach prevents premature convergence and maintains diversity in the skill population.

4. Data Flow & Directory Structure
4.1 Source Tree Layout
project-ouroboros/
├── .gemini/                          # Gemini configuration
│   ├── GEMINI.md                     # ← Mutable optimization target (context file)
│   └── settings.json                 # Optional agent settings
│
├── .dspy_cache/                      # DSPy optimization artifacts
│   ├── pareto_frontier.json          # Current best candidates
│   ├── trace_logs/                   # Rollout execution traces
│   │   ├── rollout_001.json
│   │   └── rollout_002.json
│   └── skill_versions/               # Historical GEMINI.md snapshots
│       ├── v1_baseline.md
│       └── v2_optimized.md
│
├── stories/                          # BMAD story files (training data)
│   ├── 1.1.user-registration.story.md
│   └── 1.2.password-validation.story.md
│
├── src/                              # Implementation (Gemini output)
│   ├── features/
│   └── utils/
│
├── tests/                            # Validation suite
│   └── integration/
│
├── optimizer/                        # Python DSPy module
│   ├── __init__.py
│   ├── gemini_adapter.py             # Bridge to Gemini CLI
│   ├── metric.py                     # BMadImplementationMetric
│   └── optimize.py                   # Main optimization script
│
└── package.json                      # Node.js dependencies

4.2 Data Flow Diagram
sequenceDiagram
    participant DSPy as DSPy Optimizer
    participant Adapter as GeminiAgent Adapter
    participant FS as Filesystem
    participant Gemini as Gemini CLI
    participant Tests as Test Suite
    
    DSPy->>Adapter: execute_with_skill(candidate_skill, story)
    Adapter->>FS: Write to .gemini/GEMINI.md
    Adapter->>Gemini: subprocess.run(['gemini', '-p', story_content, '--output-format', 'json'])
    Gemini->>FS: Load GEMINI.md as project context
    Gemini->>FS: Write code changes to src/
    Gemini-->>Adapter: Return JSON execution trace
    Adapter->>Tests: subprocess.run(['npm', 'test'])
    Tests-->>Adapter: Exit code + stderr log
    Adapter->>FS: Save trace to .dspy_cache/trace_logs/
    Adapter-->>DSPy: Return {code_patch, test_result, error_log}
    DSPy->>DSPy: Metric evaluates: score + feedback
    DSPy->>DSPy: Reflection LM proposes mutation
    DSPy->>FS: Update Pareto frontier JSON

Critical Path:
DSPy writes candidate → Filesystem
Gemini reads from Filesystem → Executes
Tests validate → Logs captured
Logs analyzed → Next candidate generated
Rationale for Filesystem Coupling: Gemini CLI's GEMINI.md context loading is filesystem-native. This ensures zero impedance mismatch with Gemini's expected environment while leveraging its 1M token context window.

5. Interface Definitions
5.1 DSPy Signature for GeminiSkillAdapter
from dspy import Signature, InputField, OutputField

class GeminiImplementationSignature(Signature):
    """
    Signature for Gemini-based feature implementation.
    The 'instruction' field is the mutable GEMINI.md content.
    """
    
    # Inputs
    story_context: str = InputField(
        desc="Full content of the .story.md file including acceptance criteria"
    )
    
    tech_stack: str = InputField(
        desc="Technology constraints from Architecture.md (e.g., 'React 18, Node 18')"
    )
    
    instruction: str = InputField(
        desc="Current GEMINI.md content - THIS IS THE OPTIMIZATION TARGET",
        prefix="You are a specialized Developer agent. Follow these instructions:\n"
    )
    
    # Outputs
    code_patch: str = OutputField(
        desc="Git-style diff of all file changes"
    )
    
    test_results: str = OutputField(
        desc="Output of 'npm test' command"
    )
    
    reasoning: str = OutputField(
        desc="Two-turn pattern: Thought process before action"
    )

Key Design Decision: The instruction field maps directly to GEMINI.md content. GEPA will mutate this field while holding story_context and tech_stack constant.
5.2 GeminiAgent Adapter Implementation
import dspy
import subprocess
import os
from pathlib import Path

class GeminiSkillAdapter(dspy.Module):
    """
    Bridges DSPy optimization loop with Gemini CLI execution.
    Uses non-interactive mode (-p) with JSON output format.
    """
    
    def __init__(self, gemini_binary: str = "gemini"):
        super().__init__()
        self.gemini_binary = gemini_binary
        self.context_path = Path(".gemini/GEMINI.md")
        
    def forward(self, story_context: str, tech_stack: str, instruction: str):
        """
        Execute Gemini with the given GEMINI.md content.
        
        Returns:
            dspy.Prediction with code_patch, test_results, reasoning
        """
        # Step 1: Write the candidate GEMINI.md atomically
        self._write_context_atomic(instruction)
        
        # Step 2: Prepare prompt with story context
        prompt = self._prepare_prompt(story_context, tech_stack)
        
        # Step 3: Invoke Gemini CLI with non-interactive mode
        try:
            result = subprocess.run(
                [self.gemini_binary, "-p", prompt, "--output-format", "json"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
                check=False
            )
            
            code_patch = self._extract_code_changes(result.stdout)
            reasoning = self._extract_reasoning(result.stdout)
            
        except subprocess.TimeoutExpired:
            code_patch = ""
            reasoning = "ERROR: Gemini execution timed out"
        
        # Step 4: Run tests to validate
        test_results = self._run_tests()
        
        return dspy.Prediction(
            code_patch=code_patch,
            test_results=test_results,
            reasoning=reasoning
        )
    
    def _write_context_atomic(self, content: str):
        """Atomic write to prevent race conditions."""
        self.context_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.context_path.with_suffix('.tmp')
        temp_path.write_text(content, encoding='utf-8')
        temp_path.replace(self.context_path)  # Atomic on POSIX
    
    def _run_tests(self) -> str:
        """Execute test suite and capture output."""
        result = subprocess.run(
            ['npm', 'test', '--', '--silent', '--no-coverage'],
            capture_output=True,
            text=True,
            timeout=120
        )
        return f"Exit code: {result.returncode}\n{result.stderr}"

Two-Turn Pattern Enforcement: The adapter expects Gemini to output:
Turn 1 (Reasoning): Markdown section explaining the implementation plan
Turn 2 (Action): Actual code changes
This is enforced via the GEMINI.md template structure.

6. Coding Standards
6.1 GEMINI.md Structure Requirements
All GEMINI.md files MUST follow this structure:
---
name: feature-development
description: Implements user stories with full test coverage
version: 1.0.0
---

## Role
You are a specialized Feature Developer in the BMAD framework.

## Workflow

### Phase 1: Analysis
1. Read the story file completely
2. Extract acceptance criteria
3. Identify technical constraints from tech_stack

### Phase 2: Reasoning (Turn 1)
Output a markdown section:

Implementation Plan
File changes needed: [list]
Edge cases: [list]
Test strategy: [description]

### Phase 3: Implementation (Turn 2)
Generate code following these rules:
- Rule 1: [Specific constraint]
- Rule 2: [Specific constraint]
...

Mutation Target: Rules in Phase 3 are the primary optimization target. GEPA will add/remove/modify these rules based on failure patterns.
6.2 Atomic GEMINI.md Updates
Requirement: All writes to GEMINI.md MUST be atomic to prevent race conditions during parallel rollouts.
Implementation:
# Correct: Atomic write via temp file
temp_path = context_path.with_suffix('.tmp')
temp_path.write_text(new_content)
temp_path.replace(context_path)  # Atomic on POSIX systems

# Incorrect: Direct write (not atomic)
context_path.write_text(new_content)  # FORBIDDEN

6.3 Error Handling Standards
Principle: Fail fast with actionable errors.
# DSPy programs should use assertions for invariants
import dspy

class GeminiAdapter(dspy.Module):
    def forward(self, story_context, ...):
        dspy.Assert(
            len(story_context) > 0,
            "Story context cannot be empty"
        )
        
        # If Gemini produces syntactically invalid output
        if not self._validate_code_patch(code):
            dspy.Suggest(
                False,
                "Code patch failed syntax validation. Retry with stricter formatting rules."
            )

Rationale: dspy.Assert prevents wasted LLM calls on obviously invalid inputs. dspy.Suggest allows the optimizer to learn from validation failures.
6.4 Logging & Traceability
Requirement: Every rollout MUST produce a trace log for post-hoc analysis.
import json
from datetime import datetime

def save_trace(rollout_id: int, trace_data: dict):
    trace_file = Path(f".dspy_cache/trace_logs/rollout_{rollout_id:03d}.json")
    trace_file.parent.mkdir(parents=True, exist_ok=True)
    
    with trace_file.open('w') as f:
        json.dump({
            'timestamp': datetime.utcnow().isoformat(),
            'rollout_id': rollout_id,
            'skill_version': trace_data['skill_version'],
            'story': trace_data['story'],
            'score': trace_data['score'],
            'feedback': trace_data['feedback'],
            'execution_time_sec': trace_data['execution_time']
        }, f, indent=2)

Trace Schema:
skill_version: Hash of the GEMINI.md content
story: Which training instance was executed
score: Binary pass/fail (1.0 or 0.0)
feedback: Rich textual explanation of failure
execution_time_sec: Performance metric for Pareto trade-offs

7. Deployment & Execution
7.1 Initialization Sequence
# 1. Initialize BMAD project
npx bmad-method@alpha install
# Select: "BMad Method" track

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r optimizer/requirements.txt

# 3. Initialize baseline GEMINI.md
mkdir -p .gemini
cp templates/GEMINI.baseline.md .gemini/GEMINI.md

# 4. Prepare training data (story files)
# Ensure stories/ contains at least 5 failed implementation attempts

7.2 Running the Optimization Loop
cd optimizer
python optimize.py \
  --trainset ../stories/*.story.md \
  --max-rollouts 50 \
  --output-dir ../.dspy_cache

Expected Output:
[GEPA] Iteration 1/50: Baseline skill (score=0.2)
[GEPA] Iteration 5/50: Candidate #3 on frontier (score=0.4)
[GEPA] Iteration 23/50: New Pareto leader (score=0.7, -12% tokens)
[GEPA] Iteration 50/50: Converged. Best score=0.8
[GEPA] Optimized GEMINI.md saved to .gemini/GEMINI.md

7.3 Validation Protocol
Post-Optimization Checklist:
Run full test suite: npm test
Compare token usage: DSPy metrics
Manual review of GEMINI.md mutations
Rollback if score < baseline

8. Security & Sandboxing
8.1 Code Execution Isolation
Requirement: Gemini-generated code MUST execute in an isolated environment.
Implementation Options:
Docker container per rollout (Recommended for PoC)
Git worktree (Lightweight alternative)
def execute_in_sandbox(code_patch: str):
    # Create temporary worktree
    sandbox_dir = Path(f"/tmp/ouroboros_sandbox_{uuid.uuid4()}")
    subprocess.run(['git', 'worktree', 'add', sandbox_dir, 'HEAD'])
    
    try:
        # Apply patch
        (sandbox_dir / 'changes.patch').write_text(code_patch)
        subprocess.run(['git', 'apply', 'changes.patch'], cwd=sandbox_dir)
        
        # Run tests
        result = subprocess.run(['npm', 'test'], cwd=sandbox_dir, ...)
        
    finally:
        # Cleanup
        subprocess.run(['git', 'worktree', 'remove', sandbox_dir])

8.2 GEMINI.md Validation
Requirement: Prevent injection of malicious instructions.
def validate_context_content(gemini_md: str) -> bool:
    """Ensure GEMINI.md doesn't contain dangerous patterns."""
    forbidden_patterns = [
        r'rm\s+-rf',  # Destructive commands
        r'eval\(',    # Code injection
        r'__import__' # Python import hacks
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, gemini_md):
            raise SecurityError(f"Forbidden pattern detected: {pattern}")
    
    return True


9. Success Criteria & Metrics
9.1 PoC Success Definition
The architecture is validated if:
Autonomous Mutation: The system modifies GEMINI.md without human intervention
Error-Specific Learning: The final context includes constraints NOT in the baseline (e.g., "Always validate input in unit tests")
Convergence: Pass rate improves by ≥20% over 50 rollouts
Sample Efficiency: Achieves convergence in <600 rollouts (vs. 24,000 for GRPO)
9.2 Evaluation Metrics
Metric
Target
Measurement
Pass Rate
≥80%
Tests passed / Total tests
Token Efficiency
+15%
Avg tokens per successful implementation
Rollouts to Convergence
<600
Iterations until no improvement
Skill Verbosity
<2KB
Size of optimized GEMINI.md


10. Known Limitations & Future Work
10.1 Current Constraints
Single-Agent Focus: PoC optimizes only the Developer agent, not the full BMAD team
Serial Execution: No parallel rollout support (impacts optimization speed)
Local Scope: Skills are repository-specific, not synced via Federated Knowledge Architecture
Test-Driven Only: Assumes existence of comprehensive test suite
10.2 Roadmap to v1.0
Phase 2: Extend to QA Engineer (Quinn) persona
Phase 3: Implement parallel rollout execution (5x speedup)
Phase 4: Integrate with BMAD's Federated Knowledge sync
Phase 5: Add multi-objective metrics (speed + accuracy + maintainability)

Appendix A: Glossary
Term
Definition
Pareto Frontier
Set of non-dominated solutions in multi-objective optimization
Progressive Disclosure
Loading context incrementally to maximize token efficiency
Two-Turn Pattern
Agent outputs reasoning first, then action (enforces structured thinking)
Atomic Write
Filesystem operation that completes entirely or not at all
Reflective Feedback
Rich textual error analysis, not just scalar scores


Document Control:
Approval Required From: Lead Architect, DSPy Integration Lead, BMAD Framework Owner
Next Review Date: Post-PoC completion
Change Log: Track all architectural decisions in .dspy_cache/architecture_decisions.md

