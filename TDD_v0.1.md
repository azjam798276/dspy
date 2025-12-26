TECHNICAL_DESIGN.md v0.2
Project Ouroboros: Low-Level Implementation Specification
Document Version: 0.2
 Framework: BMAD-Method v6 Alpha + DSPy 2.5 + Google Gemini CLI
 Status: Implementation Ready
 Author: Principal Software Engineer & Technical Lead
 Last Updated: 2025-12-25

1. Python Layer: Class & Module Specifications
1.1 GeminiSkillAdapter Class
File Location: optimizer/gemini_adapter.py
import dspy
import subprocess
import os
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class GeminiSkillAdapter(dspy.Module):
    """
    Bridges DSPy optimization loop with Gemini CLI execution.
    Implements atomic context updates and structured JSON output capture.
    """
    
    def __init__(
        self,
        gemini_binary: str = "gemini",
        repo_root: Optional[Path] = None,
        timeout_seconds: int = 300,
        max_retries: int = 2,
        output_format: str = "json"
    ):
        """
        Initialize the Gemini adapter.
        
        Args:
            gemini_binary: Path to Gemini CLI executable (defaults to PATH lookup)
            repo_root: Project root directory (auto-detected if None)
            timeout_seconds: Maximum execution time per rollout
            max_retries: Number of retry attempts on transient failures
            output_format: Output format "json" or "stream-json" for real-time
        """
        super().__init__()
        self.gemini_binary = gemini_binary
        self.repo_root = repo_root or self._detect_repo_root()
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.output_format = output_format
        
        # Critical paths
        self.context_path = self.repo_root / ".gemini" / "GEMINI.md"
        self.cache_dir = self.repo_root / ".dspy_cache"
        self.trace_dir = self.cache_dir / "trace_logs"
        
        # Ensure directories exist
        self.context_path.parent.mkdir(parents=True, exist_ok=True)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate Gemini CLI availability
        self._validate_gemini_cli()
    
    def forward(
        self,
        story_context: str,
        tech_stack: str,
        instruction: str
    ) -> dspy.Prediction:
        """
        Execute Gemini with the given GEMINI.md content.
        
        Args:
            story_context: Full content of .story.md file
            tech_stack: Technology constraints from Architecture.md
            instruction: Current GEMINI.md content (OPTIMIZATION TARGET)
        
        Returns:
            dspy.Prediction with fields:
                - code_patch: Git-style diff of changes
                - test_results: Output from validation suite
                - reasoning: Agent's thought process
                - execution_trace: Full rollout metadata
        """
        rollout_id = self._generate_rollout_id()
        
        try:
            # Step 1: Atomic write of candidate GEMINI.md
            self._write_context_atomic(instruction)
            
            # Step 2: Prepare prompt with story context
            prompt = self._prepare_prompt(story_context, tech_stack, rollout_id)
            
            # Step 3: Invoke Gemini CLI with retry logic
            result = self._execute_gemini_with_retry(prompt, rollout_id)
            
            # Step 4: Parse structured output
            code_patch = self._extract_code_changes(result.stdout)
            reasoning = self._extract_reasoning(result.stdout)
            
            # Step 5: Run validation tests
            test_results = self._run_tests()
            
            # Step 6: Build execution trace
            trace = self._build_trace(
                rollout_id=rollout_id,
                instruction=instruction,
                story_context=story_context,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                test_results=test_results
            )
            
            return dspy.Prediction(
                code_patch=code_patch,
                test_results=test_results,
                reasoning=reasoning,
                execution_trace=trace
            )
            
        except subprocess.TimeoutExpired as e:
            return self._handle_timeout(rollout_id, e)
        except Exception as e:
            return self._handle_error(rollout_id, e)
        finally:
            # Cleanup temp story file
            if 'story_file' in locals():
                story_file.unlink(missing_ok=True)
    
    def _write_context_atomic(self, content: str) -> None:
        """
        Atomic write to prevent race conditions during parallel rollouts.
        
        Implementation:
            1. Write to temporary file with .tmp suffix
            2. Perform atomic rename (POSIX guarantee)
            3. Verify content integrity
        
        Args:
            content: Full GEMINI.md content to write
        
        Raises:
            IOError: If atomic operation fails
        """
        temp_path = self.context_path.with_suffix('.tmp')
        
        try:
            # Write with explicit UTF-8 encoding
            temp_path.write_text(content, encoding='utf-8')
            
            # Atomic rename (POSIX-compliant filesystems guarantee atomicity)
            temp_path.replace(self.context_path)
            
            # Verify write succeeded
            dspy.Assert(
                self.context_path.exists() and self.context_path.stat().st_size > 0,
                f"GEMINI.md write verification failed at {self.context_path}"
            )
            
        except Exception as e:
            # Cleanup on failure
            temp_path.unlink(missing_ok=True)
            raise IOError(f"Atomic GEMINI.md write failed: {e}")
    
    def _execute_gemini_with_retry(
        self,
        prompt: str,
        rollout_id: str
    ) -> subprocess.CompletedProcess:
        """
        Execute Gemini CLI with exponential backoff on transient failures.
        
        Args:
            prompt: Prepared prompt with story context
            rollout_id: Unique identifier for this execution
        
        Returns:
            CompletedProcess with stdout, stderr, returncode
        """
        for attempt in range(self.max_retries + 1):
            try:
                result = subprocess.run(
                    [
                        self.gemini_binary,
                        "-p", prompt,
                        "--output-format", self.output_format
                    ],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=self.repo_root,
                    env={
                        **os.environ,
                        "GEMINI_CONTEXT_PATH": str(self.context_path.parent),
                        "GEMINI_CACHE_DIR": str(self.cache_dir / "gemini"),
                        "GEMINI_ROLLOUT_ID": rollout_id
                    },
                    check=False  # We handle errors ourselves
                )
                
                # Check for transient errors that warrant retry
                if self._is_transient_error(result):
                    if attempt < self.max_retries:
                        continue
                
                return result
                
            except subprocess.TimeoutExpired as e:
                if attempt < self.max_retries:
                    continue
                raise
        
        raise RuntimeError(f"Gemini execution failed after {self.max_retries} retries")
    
    def _run_tests(self) -> str:
        """
        Execute test suite and capture structured output.
        
        Returns:
            String containing exit code + test output
        """
        try:
            result = subprocess.run(
                ['npm', 'test', '--', '--silent', '--no-coverage', '--json'],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.repo_root,
                check=False
            )
            
            return json.dumps({
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }, indent=2)
            
        except subprocess.TimeoutExpired:
            return json.dumps({
                'exit_code': -1,
                'error': 'Test execution timeout',
                'success': False
            })
    
    def _detect_repo_root(self) -> Path:
        """Auto-detect repository root by searching for .git directory."""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        raise RuntimeError("Cannot detect repository root (.git not found)")
    
    def _validate_gemini_cli(self) -> None:
        """Verify Gemini CLI is installed and functional."""
        try:
            result = subprocess.run(
                [self.gemini_binary, "--version"],
                capture_output=True,
                timeout=5,
                check=True
            )
            print(f"[GeminiAdapter] Gemini CLI version: {result.stdout.decode().strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(
                f"Gemini CLI not found or not functional. "
                f"Install via: npm install -g @google/gemini-cli"
            )
    
    def _generate_rollout_id(self) -> str:
        """Generate unique rollout identifier."""
        return f"rollout_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def _prepare_prompt(
        self,
        story_context: str,
        tech_stack: str,
        rollout_id: str
    ) -> str:
        """
        Prepare prompt string with full context injection.
        
        Returns:
            Formatted prompt string
        """
        return f"## Story Context
{story_context}

## Technology Stack
{tech_stack}

## Instructions
Read the GEMINI.md file in the .gemini directory for detailed implementation instructions.
Follow the two-turn pattern: first output your reasoning, then provide code changes.
"
    
    def _extract_code_changes(self, stdout: str) -> str:
        """
        Extract code patch from Gemini output.
        
        Expected format:
            ```diff
            --- a/src/file.js
            +++ b/src/file.js
            ...
            ```
        """
        import re
        
        # Match code blocks with diff language identifier
        pattern = r'```(?:diff|patch)\n(.*?)```'
        matches = re.findall(pattern, stdout, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Fallback: return all changes section
        if "## Code Changes" in stdout:
            return stdout.split("## Code Changes")[1].split("##")[0].strip()
        
        return stdout  # Return full output if no structured format found
    
    def _extract_reasoning(self, stdout: str) -> str:
        """
        Extract Turn 1 reasoning from Gemini output.
        
        Expected format:
            ## Implementation Plan
            - Analysis point 1
            - Analysis point 2
        """
        if "## Implementation Plan" in stdout:
            reasoning_section = stdout.split("## Implementation Plan")[1]
            # Stop at next major section
            return reasoning_section.split("##")[0].strip()
        
        return "No structured reasoning found"
    
    def _build_trace(self, **kwargs) -> Dict[str, Any]:
        """
        Construct execution trace for logging.
        
        Returns trace dictionary conforming to schema in section 2.1.
        """
        trace = {
            'rollout_id': kwargs['rollout_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'skill_version': self._hash_skill(kwargs['instruction']),
            'story_context_hash': self._hash_content(kwargs['story_context']),
            'gemini_stdout': kwargs['stdout'],
            'gemini_stderr': kwargs['stderr'],
            'gemini_returncode': kwargs['returncode'],
            'test_results': kwargs['test_results'],
            'success': kwargs['returncode'] == 0
        }
        
        # Save trace to disk
        trace_file = self.trace_dir / f"{kwargs['rollout_id']}.json"
        trace_file.write_text(json.dumps(trace, indent=2), encoding='utf-8')
        
        return trace
    
    def _hash_skill(self, content: str) -> str:
        """Generate SHA256 hash of GEMINI.md content for versioning."""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]
    
    def _hash_content(self, content: str) -> str:
        """Generate SHA256 hash of arbitrary content."""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]
    
    def _is_transient_error(self, result: subprocess.CompletedProcess) -> bool:
        """
        Determine if error is transient (e.g., network timeout, rate limit).
        
        Returns:
            True if error warrants retry
        """
        transient_patterns = [
            "Rate limit exceeded",
            "Connection timeout",
            "Temporary failure",
            "503 Service Unavailable"
        ]
        
        error_text = result.stderr + result.stdout
        return any(pattern in error_text for pattern in transient_patterns)
    
    def _handle_timeout(self, rollout_id: str, error: Exception) -> dspy.Prediction:
        """Construct prediction for timeout case."""
        return dspy.Prediction(
            code_patch="",
            test_results=json.dumps({'error': 'timeout', 'success': False}),
            reasoning=f"ERROR: Gemini execution timed out after {self.timeout}s",
            execution_trace={'rollout_id': rollout_id, 'error': str(error)}
        )
    
    def _handle_error(self, rollout_id: str, error: Exception) -> dspy.Prediction:
        """Construct prediction for general error case."""
        return dspy.Prediction(
            code_patch="",
            test_results=json.dumps({'error': str(error), 'success': False}),
            reasoning=f"ERROR: {type(error).__name__}: {error}",
            execution_trace={'rollout_id': rollout_id, 'error': str(error)}
        )


1.2 BMadImplementationMetric Class
File Location: optimizer/metric.py
import dspy
import subprocess
import re
import json
from typing import Tuple, List, Dict, Any
from pathlib import Path

class BMadImplementationMetric:
    """
    Evaluates Gemini output by running project tests and extracting
    rich failure feedback for GEPA reflection.
    
    Returns ScoreWithFeedback for compatibility with GEPA optimizer.
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
    ) -> dspy.ScoreWithFeedback:
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
            return dspy.ScoreWithFeedback(
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
        
        return dspy.ScoreWithFeedback(
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
                r'Cannot find module [\''](.+?)[\'']',
                re.MULTILINE
            ),
            'resolve_error': re.compile(
                r'Module not found: Error: Can\'t resolve [\''](.+?)[\'']',
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


2. Data Structure Definitions
2.1 Trace Schema (JSON)
File Location: .dspy_cache/trace_logs/{rollout_id}.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Ouroboros Execution Trace",
  "type": "object",
  "required": [
    "rollout_id",
    "timestamp",
    "skill_version",
    "story_context_hash",
    "success"
  ],
  "properties": {
    "rollout_id": {
      "type": "string",
      "pattern": "^rollout_\\d{8}_\\d{6}_\\d{6}$",
      "description": "Unique identifier: rollout_YYYYMMDD_HHMMSS_microseconds"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp"
    },
    "skill_version": {
      "type": "string",
      "pattern": "^[a-f0-9]{12}$",
      "description": "SHA256 hash (first 12 chars) of GEMINI.md content"
    },
    "story_context_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{12}$",
      "description": "SHA256 hash (first 12 chars) of story content"
    },
    "gemini_stdout": {
      "type": "string",
      "description": "Full standard output from Gemini CLI"
    },
    "gemini_stderr": {
      "type": "string",
      "description": "Full standard error from Gemini CLI"
    },
    "gemini_returncode": {
      "type": "integer",
      "description": "Process exit code (0 = success)"
    },
    "test_results": {
      "type": "string",
      "description": "JSON-encoded test execution results"
    },
    "success": {
      "type": "boolean",
      "description": "True if all tests passed"
    },
    "execution_time_sec": {
      "type": "number",
      "description": "Total rollout duration in seconds"
    },
    "token_count": {
      "type": "object",
      "properties": {
        "prompt_tokens": {"type": "integer"},
        "completion_tokens": {"type": "integer"},
        "total_tokens": {"type": "integer"}
      }
    },
    "pareto_metrics": {
      "type": "object",
      "description": "Multi-objective scores for Pareto frontier",
      "properties": {
        "accuracy": {"type": "number", "minimum": 0, "maximum": 1},
        "token_efficiency": {"type": "number"},
        "execution_speed": {"type": "number"}
      }
    }
  }
}

Python Type Definition:
from typing import TypedDict, Optional
from datetime import datetime

class ExecutionTrace(TypedDict):
    rollout_id: str
    timestamp: str  # ISO 8601 format
    skill_version: str  # SHA256 hash
    story_context_hash: str
    gemini_stdout: str
    gemini_stderr: str
    gemini_returncode: int
    test_results: str  # JSON string
    success: bool
    execution_time_sec: Optional[float]
    token_count: Optional[dict]
    pareto_metrics: Optional[dict]


2.2 ScoreWithFeedback Object
DSPy Native Structure:
from dspy import ScoreWithFeedback

# Constructor signature
feedback_obj = ScoreWithFeedback(
    score: float,      # Binary: 1.0 (pass) or 0.0 (fail)
    feedback: str      # Rich textual explanation
)

# Example usage in metric
def metric(example, prediction, trace=None):
    if prediction.test_results.contains("PASS"):
        return ScoreWithFeedback(
            score=1.0,
            feedback="All 23 tests passed. Code follows style guide."
        )
    else:
        return ScoreWithFeedback(
            score=0.0,
            feedback=(
                "Failed: ReferenceError - 'db' is not defined at line 42. "
                "GEMINI.md should enforce: 'Always validate input in unit tests'"
            )
        )


2.3 Pareto Frontier Storage
File Location: .dspy_cache/pareto_frontier.json
{
  "generation": 23,
  "updated_at": "2025-12-23T14:32:10Z",
  "frontier": [
    {
      "skill_hash": "a3f2c1b5e890",
      "skill_path": ".dspy_cache/skill_versions/v23_optimized.md",
      "metrics": {
        "accuracy": 0.87,
        "avg_tokens": 1250,
        "avg_execution_time": 4.2
      },
      "dominates": [],
      "dominated_by": []
    },
    {
      "skill_hash": "d9e4a2f7c103",
      "skill_path": ".dspy_cache/skill_versions/v19_specialized.md",
      "metrics": {
        "accuracy": 0.82,
        "avg_tokens": 980,
        "avg_execution_time": 3.1
      },
      "dominates": ["a3f2c1b5e890"],
      "dominated_by": []
    }
  ]
}


3. Filesystem & Concurrency Logic
3.1 Atomic Write Implementation
Critical Constraint: Must work on POSIX and Windows filesystems.
import tempfile
import os
from pathlib import Path

def atomic_write(filepath: Path, content: str, encoding: str = 'utf-8') -> None:
    """
    Atomic file write using temp file + rename.
    
    POSIX: os.replace() is atomic
    Windows: os.replace() is atomic on NTFS (Vista+)
    
    Args:
        filepath: Target file path
        content: Content to write
        encoding: Text encoding (default UTF-8)
    
    Raises:
        IOError: If write or rename fails
    """
    # Create temp

file in same directory (ensures same filesystem) temp_fd, temp_path = tempfile.mkstemp( dir=filepath.parent, prefix=f".{filepath.name}.", suffix=".tmp" )
try:
    # Write to temp file via file descriptor
    with os.fdopen(temp_fd, 'w', encoding=encoding) as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())  # Force write to disk
    
    # Atomic rename
    os.replace(temp_path, filepath)
    
except Exception as e:
    # Cleanup temp file on failure
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass
    raise IOError(f"Atomic write failed for {filepath}: {e}")


**Thread Safety Note:** Multiple processes can safely call this function simultaneously. The OS guarantees that `os.replace()` is atomic, so readers will see either the old file or the new file, never a partial write.

---

### **3.2 Git Worktree Sandboxing**

**Use Case:** Isolate each rollout to prevent test interference.

```python
import subprocess
import tempfile
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def sandbox_worktree(repo_root: Path, rollout_id: str):
    """
    Context manager for isolated Git worktree execution.
    
    Automatically creates and cleans up worktree.
    
    Usage:
        with sandbox_worktree(repo_root, "rollout_001") as sandbox_dir:
            # Apply patch
            # Run tests
            # Capture results
    
    Args:
        repo_root: Main repository path
        rollout_id: Unique identifier for this sandbox
    
    Yields:
        Path to sandbox directory
    """
    sandbox_dir = Path(tempfile.gettempdir()) / f"ouroboros_{rollout_id}"
    
    try:
        # Create worktree from current HEAD
        subprocess.run(
            ['git', 'worktree', 'add', '--detach', str(sandbox_dir), 'HEAD'],
            cwd=repo_root,
            check=True,
            capture_output=True,
            timeout=30
        )
        
        # Install dependencies in sandbox (if needed)
        if (sandbox_dir / "package.json").exists():
            subprocess.run(
                ['npm', 'install', '--silent'],
                cwd=sandbox_dir,
                check=True,
                capture_output=True,
                timeout=120
            )
        
        yield sandbox_dir
        
    finally:
        # Cleanup worktree (force removes even if dirty)
        try:
            subprocess.run(
                ['git', 'worktree', 'remove', '--force', str(sandbox_dir)],
                cwd=repo_root,
                capture_output=True,
                timeout=30
            )
        except subprocess.CalledProcessError:
            # Fallback: manual directory removal
            import shutil
            if sandbox_dir.exists():
                shutil.rmtree(sandbox_dir, ignore_errors=True)


4. Integration Logic: The Bridge
4.1 Detecting Two-Turn Pattern Completion
Challenge: Distinguish between Gemini's "Reasoning" turn and "Action" turn.
Solution: Parse Gemini output for markdown section headers.
import re
from typing import Tuple, Optional

class TwoTurnParser:
    """
    Parses Gemini output to detect two-turn pattern completion.
    
    Expected structure:
        ## Implementation Plan
        <reasoning content>
        
        ## Code Changes
        <action content>
    """
    
    REASONING_HEADER = r'^##\s+Implementation\s+Plan\s*$' 
    ACTION_HEADER = r'^##\s+Code\s+Changes\s*$' 
    
    @classmethod
    def parse_turns(cls, output: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract reasoning and action from Gemini output.
        
        Returns:
            (reasoning: str, action: str) or (None, None) if parsing fails
        """
        lines = output.split('\n')
        
        reasoning_start = None
        action_start = None
        
        # Find section boundaries
        for i, line in enumerate(lines):
            if re.match(cls.REASONING_HEADER, line, re.IGNORECASE):
                reasoning_start = i + 1
            elif re.match(cls.ACTION_HEADER, line, re.IGNORECASE):
                action_start = i + 1
        
        # Validate both sections found
        if reasoning_start is None or action_start is None:
            return (None, None)
        
        # Extract content between headers
        reasoning = '\n'.join(lines[reasoning_start:action_start-1]).strip()
        action = '\n'.join(lines[action_start:]).strip()
        
        return (reasoning, action)
    
    @classmethod
    def validate_structure(cls, output: str) -> bool:
        """
        Check if output conforms to two-turn pattern.
        
        Returns:
            True if both reasoning and action sections exist
        """
        reasoning, action = cls.parse_turns(output)
        return reasoning is not None and action is not None

Integration in Adapter:
# In GeminiSkillAdapter._extract_reasoning()
reasoning, action = TwoTurnParser.parse_turns(stdout)

if reasoning is None:
    dspy.Suggest(
        False,
        "Gemini output missing '## Implementation Plan' header. "
        "GEMINI.md should enforce two-turn pattern."
    )
    return "No structured reasoning found"

return reasoning


4.2 Dynamic Path Resolution
Problem: Code must work regardless of installation location.
import os
from pathlib import Path

class PathResolver:
    """
    Resolves project paths dynamically based on execution context.
    """
    
    @staticmethod
    def resolve_repo_root() -> Path:
        """
        Find repository root by searching for .git directory.
        
        Search order:
            1. Current working directory
            2. Parent directories (up to filesystem root)
            3. Environment variable OUROBOROS_ROOT
        
        Returns:
            Path to repository root
        
        Raises:
            RuntimeError: If no repository found
        """
        # Check environment variable first
        if 'OUROBOROS_ROOT' in os.environ:
            root = Path(os.environ['OUROBOROS_ROOT'])
            if (root / '.git').exists():
                return root
        
        # Search upward from current directory
        current = Path.cwd().resolve()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        
        raise RuntimeError(
            "Cannot locate repository root. "
            "Ensure you're inside a Git repository or set OUROBOROS_ROOT env var."
        )
    
    @staticmethod
    def resolve_skill_path(repo_root: Path) -> Path:
        """
        Locate GEMINI.md with fallback hierarchy.
        
        Priority:
            1. Repository: {repo_root}/.gemini/GEMINI.md
            2. User: ~/.gemini/GEMINI.md
            3. System: /usr/local/share/gemini/GEMINI.md
        
        Returns:
            Path to first existing GEMINI.md
        
        Raises:
            FileNotFoundError: If no GEMINI.md found in hierarchy
        """
        candidates = [
            repo_root / '.gemini' / 'GEMINI.md',
            Path.home() / '.gemini' / 'GEMINI.md',
            Path('/usr/local/share/gemini/GEMINI.md')
        ]
        
        for path in candidates:
            if path.exists():
                return path
        
        raise FileNotFoundError(
            f"GEMINI.md not found in hierarchy: {[str(p) for p in candidates]}"
        )


5. Testing Strategy: Self-Correction Tests
5.1 Unit Tests for Optimizer Components
File Location: tests/test_optimizer.py
import pytest
import json
from pathlib import Path
from optimizer.metric import BMadImplementationMetric
from optimizer.gemini_adapter import GeminiSkillAdapter

class TestBMadImplementationMetric:
    """Test suite for metric function parsing logic."""
    
    @pytest.fixture
    def metric(self, tmp_path):
        return BMadImplementationMetric(repo_root=tmp_path)
    
    def test_parses_reference_error_correctly(self, metric):
        """Verify extraction of ReferenceError from logs."""
        stderr = """
        Error: Test suite failed
        ReferenceError: db is not defined
            at fetchUser (src/user.js:42:15)
        """
        
        feedback = metric._extract_rich_feedback(stderr, "", "")
        
        assert "Undefined variables: db" in feedback
        assert "GEMINI.md should enforce" in feedback
        assert "verify variable declarations" in feedback.lower()
    
    def test_parses_type_error_correctly(self, metric):
        """Verify extraction of TypeError from logs."""
        stderr = """
        TypeError: Cannot read property 'map' of undefined
            at processItems (src/processor.js:23:10)
        """
        
        feedback = metric._extract_rich_feedback(stderr, "", "")
        
        assert "Type errors:" in feedback
        assert "Cannot read property 'map'" in feedback
        assert "type annotations" in feedback.lower()
    
    def test_parses_import_error_correctly(self, metric):
        """Verify extraction of module import errors."""
        stderr = """
        Error: Cannot find module '../utils/helpers'
        Require stack:
        - /project/src/feature.js
        """
        
        feedback = metric._extract_rich_feedback(stderr, "", "")
        
        assert "Missing modules: ../utils/helpers" in feedback
        assert "Cross-reference package.json" in feedback
    
    def test_handles_multiple_error_types(self, metric):
        """Verify prioritized extraction of mixed errors."""
        stderr = """
        ReferenceError: config is not defined
        TypeError: undefined is not a function
        SyntaxError: Unexpected token '}'
        """
        
        feedback = metric._extract_rich_feedback(stderr, "", "")
        
        # Should include all three categories
        assert "Undefined variables: config" in feedback
        assert "Type errors:" in feedback
        assert "Parse errors:" in feedback
    
    def test_returns_generic_feedback_for_unknown_errors(self, metric):
        """Fallback for unparseable errors."""
        stderr = "Something went terribly wrong!"
        
        feedback = metric._extract_rich_feedback(stderr, "", "")
        
        assert "Test failed" in feedback
        assert "Something went terribly wrong!" in feedback
    
    def test_score_with_feedback_structure(self, metric):
        """Verify ScoreWithFeedback object structure."""
        example = None
        prediction = type('obj', (object,), {
            'test_results': json.dumps({'success': False, 'stderr': 'ReferenceError: x'})
        })()
        
        result = metric(example, prediction)
        
        assert hasattr(result, 'score')
        assert hasattr(result, 'feedback')
        assert result.score == 0.0
        assert isinstance(result.feedback, str)
        assert len(result.feedback) > 0


class TestGeminiSkillAdapter:
    """Test suite for Gemini adapter logic."""
    
    @pytest.fixture
    def adapter(self, tmp_path):
        # Create fixture .git directory
        (tmp_path / '.git').mkdir()
        return GeminiSkillAdapter(repo_root=tmp_path)
    
    def test_atomic_write_creates_file(self, adapter, tmp_path):
        """Verify atomic write succeeds."""
        content = "# Test GEMINI.md\nThis is a test"
        
        adapter._write_context_atomic(content)
        
        assert adapter.context_path.exists()
        assert adapter.context_path.read_text() == content
    
    def test_atomic_write_is_actually_atomic(self, adapter, tmp_path):
        """Verify no partial writes visible to readers."""
        import threading
        import time
        
        large_content = "x" * 1000000  # 1MB
        read_values = []
        
        def reader():
            """Continuously read file during write."""
            for _ in range(100):
                if adapter.context_path.exists():
                    content = adapter.context_path.read_text()
                    read_values.append(len(content))
                time.sleep(0.001)
        
        # Start reader thread
        reader_thread = threading.Thread(target=reader)
        reader_thread.start()
        
        # Perform write
        adapter._write_context_atomic(large_content)
        
        reader_thread.join()
        
        # Verify readers only saw 0 or full size, never partial
        assert all(size in [0, len(large_content)] for size in read_values)
    
    def test_handles_gemini_timeout_gracefully(self, adapter):
        """Verify timeout produces error prediction."""
        # This will timeout since no actual Gemini CLI
        adapter.timeout = 1
        
        result = adapter.forward(
            story_context="Test story",
            tech_stack="Node 18",
            instruction="# Test skill"
        )
        
        assert "timeout" in result.reasoning.lower()
        assert result.code_patch == ""
    
    def test_generates_unique_rollout_ids(self, adapter):
        """Verify rollout IDs are unique and well-formed."""
        ids = [adapter._generate_rollout_id() for _ in range(100)]
        
        # All unique
        assert len(ids) == len(set(ids))
        
        # All match expected pattern
        import re
        pattern = r'^rollout_\\d{8}_\\d{6}_\\d{6}$'
        assert all(re.match(pattern, id) for id in ids)
    
    def test_detects_transient_errors_correctly(self, adapter):
        """Verify transient error detection logic."""
        import subprocess
        
        # Simulate rate limit error
        result = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Error: Rate limit exceeded. Retry after 60s"
        )
        
        assert adapter._is_transient_error(result) == True
        
        # Simulate permanent error
        result.stderr = "SyntaxError: Unexpected token"
        assert adapter._is_transient_error(result) == False


class TestTwoTurnParser:
    """Test suite for two-turn pattern detection."""
    
    def test_parses_valid_two_turn_output(self):
        """Verify correct parsing of structured output."""
        from optimizer.gemini_adapter import TwoTurnParser
        
        output = """
## Implementation Plan

- Create User model
- Add validation middleware
- Write unit tests

## Code Changes

```javascript
// src/models/User.js
class User {
  // ...
}

"""
   reasoning, action = TwoTurnParser.parse_turns(output)
    
    assert reasoning is not None
    assert action is not None
    assert "Create User model" in reasoning
    assert "class User" in action

def test_detects_missing_sections(self):
    """Verify detection of incomplete output."""
    from optimizer.gemini_adapter import TwoTurnParser
    
    # Missing action section
    output = """

Implementation Plan
Some reasoning here """
   reasoning, action = TwoTurnParser.parse_turns(output)
    assert reasoning is None
    assert action is None

def test_validates_structure(self):
    """Verify structure validation method."""
    from optimizer.gemini_adapter import TwoTurnParser
    
    valid = """

Implementation Plan
Reasoning
Code Changes
Action """ invalid = "No structure here" 
   assert TwoTurnParser.validate_structure(valid) == True
    assert TwoTurnParser.validate_structure(invalid) == False

Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests requiring external dependencies"
    )

---

### **5.2 Integration Test for Full Loop**

**File Location:** `tests/test_integration.py`

```python
import pytest
import dspy
from pathlib import Path
from optimizer.gemini_adapter import GeminiSkillAdapter
from optimizer.metric import BMadImplementationMetric

@pytest.mark.integration
@pytest.mark.slow
class TestOptimizationLoop:
    """
    End-to-end test of the optimization loop.
    
    WARNING: This test invokes actual Gemini CLI and may consume API credits.
    """
    
    @pytest.fixture
    def test_repo(self, tmp_path):
        """Create minimal test repository."""
        repo = tmp_path / "test_project"
        repo.mkdir()
        
        # Initialize git
        import subprocess
        subprocess.run(['git', 'init'], cwd=repo, check=True)
        
        # Create GEMINI.md
        gemini_dir = repo / '.gemini'
        gemini_dir.mkdir(parents=True)
        
        baseline_context = """
---
name: feature-development
description: Implements features with tests
version: 1.0.0
---

## Workflow

1. Read story file
2. Generate code
3. Write tests
"""
        (gemini_dir / 'GEMINI.md').write_text(baseline_context)
        
        # Create package.json
        (repo / 'package.json').write_text('{"scripts": {"test": "echo PASS"}}')
        
        return repo
    
    def test_single_optimization_iteration(self, test_repo):
        """Verify one iteration of the optimization loop."""
        
        # Initialize components
        adapter = GeminiSkillAdapter(repo_root=test_repo)
        metric = BMadImplementationMetric(repo_root=test_repo)
        
        # Create training example
        example = dspy.Example(
            story_context="As a user, I want to register an account",
            expected_files=["src/auth/register.js", "tests/auth.test.js"]
        ).with_inputs('story_context')
        
        # Execute one rollout
        prediction = adapter.forward(
            story_context=example.story_context,
            tech_stack="Node 18, Express 4",
            instruction=(test_repo / '.gemini/GEMINI.md').read_text()
        )
        
        # Evaluate with metric
        result = metric(example, prediction)
        
        # Verify structure
        assert hasattr(result, 'score')
        assert hasattr(result, 'feedback')
        assert isinstance(result.score, float)
        assert 0.0 <= result.score <= 1.0
    
    def test_gepa_optimization_reduces_errors(self, test_repo):
        """
        Verify GEPA improves context over multiple iterations.
        
        This is the critical test proving autonomous refinement.
        """
        
        # Setup
        adapter = GeminiSkillAdapter(repo_root=test_repo)
        metric = BMadImplementationMetric(repo_root=test_repo)
        
        # Create deliberately failing training data
        trainset = [
            dspy.Example(
                story_context="Feature that will fail with ReferenceError",
                expected_behavior="Should not crash"
            ).with_inputs('story_context')
        ]
        
        # Configure GEPA with minimal budget
        gepa = dspy.GEPA(
            metric=metric,
            reflection_lm=dspy.LM('openai/gpt-4o'),
            max_metric_calls=10,
            pareto_minibatch_size=3,
            verbose=True
        )
        
        # Run optimization
        optimized_adapter = gepa.compile(adapter, trainset=trainset)
        
        # Load optimized GEMINI.md
        final_context = (test_repo / '.gemini/GEMINI.md').read_text()
        
        # CRITICAL ASSERTION: Final context should contain error-specific constraint
        assert any(
            constraint in final_context.lower()
            for constraint in [
                "verify variable",
                "check undefined",
                "validate imports",
                "validate input"
            ]
        ), f"Optimized GEMINI.md lacks error-specific constraints:\n{final_context}"
        
        print("\n[SUCCESS] GEPA autonomously refined GEMINI.md with domain-specific constraints")


6. Sequence Diagram: Read-Execute-Reflect-Rewrite Cycle
sequenceDiagram
    participant GEPA as GEPA Optimizer
    participant Adapter as GeminiSkillAdapter
    participant FS as Filesystem
    participant Gemini as Gemini CLI
    participant Tests as Test Suite
    participant Metric as BMadImplementationMetric
    participant Reflection as Reflection LM (GPT-4o)

    Note over GEPA: Iteration N begins
    
    GEPA->>GEPA: Select candidate from Pareto frontier
    GEPA->>Adapter: forward(story, tech_stack, instruction=GEMINI_v3)
    
    Adapter->>FS: atomic_write(.gemini/GEMINI.md, GEMINI_v3)
    Note over FS: Atomic operation (temp file + rename)
    
    Adapter->>Gemini: subprocess.run(['gemini', '-p', prompt, '--output-format', 'json'])
    Note over Gemini: Loads GEMINI.md via progressive disclosure
    
    Gemini->>FS: Write src/feature.js (code changes)
    Gemini-->>Adapter: stdout: "{code_patch: ...}" (JSON)
    
    Adapter->>Tests: subprocess.run(['npm', 'test'])
    Tests-->>Adapter: returncode=1, stderr="ReferenceError: db is not defined"
    
    Adapter->>FS: Save trace to .dspy_cache/trace_logs/rollout_N.json
    
    Adapter-->>GEPA: Prediction{code_patch, test_results, reasoning, trace}
    
    GEPA->>Metric: __call__(example, prediction, trace)
    
    Metric->>Metric: _extract_rich_feedback(stderr, stdout, code_patch)
    Note over Metric: Regex extraction:<br/>ReferenceError → "Undefined variables: db"
    
    Metric-->>GEPA: ScoreWithFeedback(score=0.0, feedback="[CRITICAL] Undefined variables: db...")
    
    GEPA->>Reflection: Analyze failure:<br/>- Current GEMINI.md<br/>- Error feedback<br/>- Execution trace
    
    Reflection-->>GEPA: Proposed mutation:<br/>"Add constraint: 'Always verify input validation in tests'"
    
    GEPA->>GEPA: Generate GEMINI_v4 with new constraint
    GEPA->>GEPA: Evaluate GEMINI_v4 on validation set
    
    alt GEMINI_v4 dominates GEMINI_v3
        GEPA->>FS: Save GEMINI_v4 to .dspy_cache/skill_versions/
        GEPA->>GEPA: Add GEMINI_v4 to Pareto frontier
        Note over GEPA: Frontier now has 4 candidates
    else GEMINI_v4 is dominated
        GEPA->>GEPA: Discard GEMINI_v4
    end
    
    Note over GEPA: Iteration N+1 begins...


7. Deployment Checklist
7.1 Environment Setup
# 1. Clone repository
git clone <repo-url> project-ouroboros
cd project-ouroboros

# 2. Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r optimizer/requirements.txt

# 3. Node.js environment
npm install

# 4. Initialize BMAD
npx bmad-method@alpha install
# Select: "BMad Method" track

# 5. Verify Gemini CLI
gemini --version
# If not found: npm install -g @google/gemini-cli

# 6. Create baseline GEMINI.md
cp templates/GEMINI.baseline.md .gemini/GEMINI.md

# 7. Prepare training data
# Place 5-10 .story.md files in stories/ directory

7.2 Pre-Flight Validation
# Run unit tests
pytest tests/ -v

# Run integration test (WARNING: consumes API credits)
pytest tests/test_integration.py::TestOptimizationLoop::test_single_optimization_iteration -v

# Verify file structure
tree -L 3 .gemini/
tree -L 2 .dspy_cache/

7.3 Launch Optimization
cd optimizer
python optimize.py \
  --trainset ../stories/*.story.md \
  --max-rollouts 50 \
  --output-dir ../.dspy_cache \
  --verbose


8. Known Issues & Workarounds
8.1 Issue: Gemini CLI Not Found
Symptom: FileNotFoundError: gemini
Workaround:
npm install -g @google/gemini-cli
# Or specify full path in adapter:
adapter = GeminiSkillAdapter(gemini_binary="/usr/local/bin/gemini")

8.2 Issue: GEMINI.md Lock Contention
Symptom: OSError: [Errno 11] Resource temporarily unavailable
Workaround: Reduce parallel rollouts or implement file locking:
import fcntl

def atomic_write_with_lock(filepath, content):
    with open(filepath, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
        f.write(content)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

8.3 Issue: npm test Hangs
Symptom: Tests never complete
Workaround: Add explicit timeout:
subprocess.run(['npm', 'test'], timeout=60)  # Force kill after 60s


9. Performance Optimization Notes
9.1 Caching Strategy
import hashlib
import pickle
from pathlib import Path

class ResultCache:
    """Cache test results to avoid redundant rollouts."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir / 'result_cache'
        self.cache_dir.mkdir(exist_ok=True)
    
    def get(self, skill_hash: str, story_hash: str):
        """Retrieve cached result if exists."""
        cache_key = f"{skill_hash}_{story_hash}"
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def set(self, skill_hash: str, story_hash: str, result):
        """Save result to cache."""
        cache_key = f"{skill_hash}_{story_hash}"
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)

9.2 Parallel Rollout Execution
from concurrent.futures import ThreadPoolExecutor, as_completed

def parallel_rollouts(adapter, stories, max_workers=4):
    """Execute multiple rollouts concurrently."""
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                adapter.forward,
                story.context,
                story.tech_stack,
                current_skill
            ): story
            for story in stories
        }
        
        for future in as_completed(futures):
            story = futures[future]
            try:
                result = future.result(timeout=300)
                yield (story, result)
            except Exception as e:
                yield (story, None)


10. Success Metrics Dashboard
10.1 Convergence Tracking
import matplotlib.pyplot as plt
import json
from pathlib import Path

def plot_convergence(cache_dir: Path):
    """Generate convergence visualization."""
    
    traces = []
    for trace_file in sorted(cache_dir.glob('trace_logs/*.json')):
        with open(trace_file) as f:
            traces.append(json.load(f))
    
    # Extract metrics
    iterations = list(range(len(traces)))
    scores = [t.get('success', 0) * 1.0 for t in traces]
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(iterations, scores, marker='o')
    plt.xlabel('Rollout Iteration')
    plt.ylabel('Test Pass Rate')
    plt.title('GEPA Optimization Convergence')
    plt.grid(True)
    plt.savefig(cache_dir / 'convergence.png')
    
    print(f"[Metrics] Initial pass rate: {scores[0]:.2%}")
    print(f"[Metrics] Final pass rate: {scores[-1]:.2%}")
    print(f"[Metrics] Improvement: {(scores[-1] - scores[0]):.2%}")


Appendix A: Complete File Structure
project-ouroboros/
├── .gemini/                          # Gemini configuration
│   ├── GEMINI.md                     # ← Mutable optimization target
│   └── settings.json                 # Optional agent settings
│
├── .dspy_cache/                      # DSPy optimization artifacts
│   ├── pareto_frontier.json          # Current best candidates
│   ├── result_cache/              # Rollout result cache
│   ├── trace_logs/                   # Execution traces
│   │   ├── rollout_20251223_143210_000001.json
│   │   └── ...
│   └── skill_versions/            # Historical snapshots
│       ├── v1_baseline.md
│       └── v23_optimized.md
│
├── optimizer/
│   ├── __init__.py
│   ├── gemini_adapter.py             # GeminiSkillAdapter class
│   ├── metric.py                     # BMadImplementationMetric class
│   ├── optimize.py                   # Main optimization script
│   └── requirements.txt
│
├── stories/
│   ├── 1.1.user-registration.story.md
│   └── 1.2.password-validation.story.md
│
├── tests/
│   ├── test_optimizer.py