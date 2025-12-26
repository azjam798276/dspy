---
id: "20251225_metric_enhancement"
difficulty: "hard"
tags: ["python", "dspy", "testing", "metrics"]
tech_stack: "Python, DSPy, PyTest"
---

# User Story
As an Optimization Engineer, I want the `BMadImplementationMetric` to provide more granular scoring beyond binary pass/fail so that the GEPA optimizer can distinguish between partial successes and total failures.

# Context & Constraints
The current metric returns 1.0 for success and 0.0 for failure. We need a continuous or multi-step score.

**Requirements:**
- Implement a `_calculate_score(test_results)` method.
- Score should be:
    - 1.0: All tests pass.
    - 0.5: Tests run but some fail (partial success).
    - 0.1: Code compilation fails or syntax error.
    - 0.0: Execution timeout or system crash.
- Ensure the score is returned as part of `ScoreWithFeedback`.
- Feedback must include the specific reason for the score (e.g., "Partial success: 5/10 tests passed").

# Acceptance Criteria
- [ ] Refactor `BMadImplementationMetric.__call__` to use granular scoring.
- [ ] Extract the number of passed/failed tests from the JSON output of `npm test --json`.
- [ ] Handle cases where JSON output is missing or malformed.
- [ ] Verify that GEPA receives a `float`-compatible score.
- [ ] Pass unit tests for score calculation logic.
