"""
BMadImplementationMetric: DSPy Metric Function for Project Ouroboros

This module implements the feedback mechanism for the optimization loop.
It executes project tests (npm test) and extracts rich textual feedback
from failure logs (stdout/stderr) to guide the GEPA optimizer.
"""

import dspy
import subprocess
import re
import json
from typing import Tuple, List, Dict, Any
from pathlib import Path

class ScoreWithFeedback:
    """Helper class to return score and feedback."""
    def __init__(self, score: float, feedback: str):
        self.score = float(score)
        self.feedback = feedback

    def __float__(self):
        return self.score

    def __add__(self, other):
        return self.score + float(other)

    def __radd__(self, other):
        return self.score + float(other)

    def __lt__(self, other):
        return self.score < float(other)

    def __gt__(self, other):
        return self.score > float(other)

    def __le__(self, other):
        return self.score <= float(other)

    def __ge__(self, other):
        return self.score >= float(other)

    def __repr__(self):
        return f"ScoreWithFeedback(score={self.score}, feedback='{self.feedback[:50]}...')"

class BMadImplementationMetric:
    """
    Evaluates Gemini output by running project tests and extracting
    rich failure feedback for GEPA reflection.
    
    Returns ScoreWithFeedback compatibility object.
    """
    
    def __init__(
        self,
        repo_root: Path,
        sandbox_mode: bool = True,
        failure_weight: float = 1.0
    ):
        """
        Initialize metric function.
        
        Args:
            repo_root: Project root directory
            sandbox_mode: If True, execute tests in isolated worktree
            failure_weight: Penalty multiplier for failed tests
        """
        self.repo_root = repo_root
        self.sandbox_mode = sandbox_mode
        self.failure_weight = failure_weight
        
        # Compile regex patterns for error extraction
        self._compile_error_patterns()
    
    def __call__(
        self,
        example: dspy.Example,
        prediction: dspy.Prediction,
        trace: Any = None
    ) -> ScoreWithFeedback:
        """
        Evaluate code implementation quality.
        
        Args:
            example: Training instance (story + expected behavior)
            prediction: Gemini-generated code changes
            trace: Full execution trace (optional)
        
        Returns:
            ScoreWithFeedback: Binary score + rich textual feedback
        """
        # Parse test results from prediction
        try:
            test_data = json.loads(prediction.test_results)
        except json.JSONDecodeError:
            return ScoreWithFeedback(
                score=0.0,
                feedback="ERROR: Cannot parse test results JSON"
            )
        
        # Calculate binary score
        score = 1.0 if test_data.get('success', False) else 0.0
        
        # Extract rich feedback if failed
        if score == 0.0:
            feedback = self._extract_rich_feedback(
                test_data.get('stderr', ''),
                test_data.get('stdout', ''),
                prediction.code_patch
            )
        else:
            feedback = "All tests passed successfully"
        
        return ScoreWithFeedback(
            score=score,
            feedback=feedback
        )
    
    def _compile_error_patterns(self) -> None:
        """
        Compile regex patterns for common JavaScript/TypeScript errors.
        
        Patterns are prioritized by severity and actionability.
        """
        self.error_patterns = {
            # Critical runtime errors
            'undefined_variable': re.compile(
                r'ReferenceError: (\w+) is not defined',
                re.MULTILINE
            ),
            'type_error': re.compile(
                r'TypeError: (.+?)(?:\n|$)',
                re.MULTILINE
            ),
            'syntax_error': re.compile(
                r'SyntaxError: (.+?)(?:\n|$)',
                re.MULTILINE
            ),
            
            # Test assertion failures
            'assertion_error': re.compile(
                r'AssertionError: (.+?)(?:\n|$)',
                re.MULTILINE
            ),
            'expect_failure': re.compile(
                r'Expected (.+?) to (.+?) but got (.+?)(?:\n|$)',
                re.MULTILINE
            ),
            
            # Module/import errors
            'import_fail': re.compile(
                r"Cannot find module ['\"](.+?)['\"]",
                re.MULTILINE
            ),
            'resolve_error': re.compile(
                r"Module not found: Error: Can't resolve ['\"](.+?)['\"]",
                re.MULTILINE
            ),
            
            # Async/Promise errors
            'unhandled_promise': re.compile(
                r'UnhandledPromiseRejectionWarning: (.+?)(?:\n|$)',
                re.MULTILINE
            ),
            'timeout_error': re.compile(
                r'Timeout of (\d+)ms exceeded',
                re.MULTILINE
            ),
            
            # ESLint/Linter errors
            'eslint_error': re.compile(
                r'(\d+:\d+)\s+error\s+(.+?)\s+(\w+)$',
                re.MULTILINE
            ),
            
            # Build/compilation errors
            'webpack_error': re.compile(
                r'Module build failed.*?Error: (.+?)(?:\n|$)',
                re.DOTALL
            )
        }
    
    def _extract_rich_feedback(
        self,
        stderr: str,
        stdout: str,
        code_patch: str
    ) -> str:
        """
        Extract actionable error patterns from test logs.
        
        Priority:
            1. Runtime errors (ReferenceError, TypeError)
            2. Import/module errors
            3. Assertion failures
            4. Syntax/linting errors
        
        Args:
            stderr: Standard error from test execution
            stdout: Standard output from test execution
            code_patch: Generated code changes
        
        Returns:
            Human-readable feedback string for GEPA reflection
        """
        combined_log = stderr + "\n" + stdout
        
        # Extract all matching errors by category
        errors_by_category = {}
        for category, pattern in self.error_patterns.items():
            matches = pattern.findall(combined_log)
            if matches:
                errors_by_category[category] = matches
        
        # No errors found in logs
        if not errors_by_category:
            return self._generate_generic_feedback(stderr, stdout)
        
        # Build structured feedback
        feedback_parts = ["Test execution failed with the following issues:"]
        
        # Priority 1: Runtime errors
        if 'undefined_variable' in errors_by_category:
            vars_undefined = errors_by_category['undefined_variable']
            feedback_parts.append(
                f"\n[CRITICAL] Undefined variables: {', '.join(vars_undefined)}"
            )
            feedback_parts.append(
                "→ GEMINI.md should enforce: 'Always verify variable declarations "
                "before use. Import all dependencies at file top.'"
            )
        
        if 'type_error' in errors_by_category:
            type_errors = errors_by_category['type_error'][:3]  # Limit to 3
            feedback_parts.append(
                f"\n[CRITICAL] Type errors:\n  - " + "\n  - ".join(type_errors)
            )
            feedback_parts.append(
                "→ GEMINI.md should enforce: 'Add JSDoc type annotations for "
                "function parameters. Use TypeScript strict mode.'"
            )
        
        # Priority 2: Import errors
        if 'import_fail' in errors_by_category:
            missing_modules = errors_by_category['import_fail']
            feedback_parts.append(
                f"\n[ERROR] Missing modules: {', '.join(missing_modules)}"
            )
            feedback_parts.append(
                "→ GEMINI.md should enforce: 'Cross-reference package.json before "
                "importing. Use relative paths for local modules.'"
            )
        
        # Priority 3: Assertion failures
        if 'assertion_error' in errors_by_category:
            assertions = errors_by_category['assertion_error'][:2]
            feedback_parts.append(
                f"\n[FAILURE] Test assertions:\n  - " + "\n  - ".join(assertions)
            )
            feedback_parts.append(
                "→ GEMINI.md should enforce: 'Read acceptance criteria from story "
                "file. Validate edge cases before implementation.'"
            )
        
        # Priority 4: Syntax/linting
        if 'syntax_error' in errors_by_category:
            syntax_errors = errors_by_category['syntax_error'][:2]
            feedback_parts.append(
                f"\n[SYNTAX] Parse errors:\n  - " + "\n  - ".join(syntax_errors)
            )
        
        # Add code context if patch is small enough
        if len(code_patch) < 500:
            feedback_parts.append(f"\n\nCode generated:\n```\n{code_patch}\n```")
        
        return "\n".join(feedback_parts)
    
    def _generate_generic_feedback(self, stderr: str, stdout: str) -> str:
        """
        Fallback feedback when no specific patterns match.
        
        Returns last 500 characters of error logs.
        """
        combined = stderr + stdout
        if len(combined) > 500:
            return f"Test failed. Last 500 chars of log:\n{combined[-500:]}"
        return f"Test failed. Full log:\n{combined}"
    
    def execute_in_sandbox(self, code_patch: str, rollout_id: str) -> Tuple[bool, str]:
        """
        Execute code changes in isolated Git worktree.
        
        Args:
            code_patch: Git diff to apply
            rollout_id: Unique identifier for sandbox
        
        Returns:
            (success: bool, log: str)
        """
        import tempfile
        import uuid
        
        sandbox_dir = Path(tempfile.gettempdir()) / f"ouroboros_{rollout_id}"
        
        try:
            # Create worktree
            subprocess.run(
                ['git', 'worktree', 'add', str(sandbox_dir), 'HEAD'],
                check=True,
                cwd=self.repo_root,
                capture_output=True
            )
            
            # Apply patch
            patch_file = sandbox_dir / "changes.patch"
            patch_file.write_text(code_patch, encoding='utf-8')
            
            subprocess.run(
                ['git', 'apply', 'changes.patch'],
                check=True,
                cwd=sandbox_dir,
                capture_output=True
            )
            
            # Run tests in sandbox
            result = subprocess.run(
                ['npm', 'test', '--', '--silent'],
                cwd=sandbox_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return (result.returncode == 0, result.stderr)
            
        except Exception as e:
            return (False, f"Sandbox execution failed: {e}")
        
        finally:
            # Cleanup worktree
            if sandbox_dir.exists():
                subprocess.run(
                    ['git', 'worktree', 'remove', str(sandbox_dir), '--force'],
                    cwd=self.repo_root,
                    capture_output=True
                )