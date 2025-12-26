"""
GeminiSkillAdapter: DSPy Module for Gemini CLI Integration

This module bridges DSPy's optimization loop with the Google Gemini CLI.
It uses a Signature to store the instructions, allowing DSPy optimizers
to natively refine the prompt text.
"""

import dspy
import subprocess
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class GeminiSignature(dspy.Signature):
    """
    Signature for agent execution. 
    The 'instructions' field of this signature is what GEPA/COPRO will optimize.
    """
    story_context = dspy.InputField(desc="The implementation task/story context")
    tech_stack = dspy.InputField(desc="Technology constraints")
    code_patch = dspy.OutputField(desc="Extracted git patch with changes")
    reasoning = dspy.OutputField(desc="Agent's thought process")


class GeminiSkillAdapter(dspy.Module):
    """
    Bridges DSPy optimization loop with Gemini CLI execution.
    
    Optimizers (GEPA, COPRO) will mutate self.predictor.signature.instructions.
    """
    
    def __init__(
        self,
        gemini_binary: str = "gemini",
        repo_root: Optional[Path] = None,
        timeout_seconds: int = 300,
        max_retries: int = 2,
        output_format: str = "json",
        base_instruction: str = "",
        context_dir: Optional[Path] = None,
        demos: List = None
    ):
        super().__init__()
        self.gemini_binary = gemini_binary
        self.repo_root = repo_root or self._detect_repo_root()
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.output_format = output_format
        self.base_instruction = base_instruction
        self.demos = demos or []
        
        # Define the predictor. Its instructions are the optimization target.
        self.predictor = dspy.Predict(GeminiSignature)
        
        # Critical paths
        if context_dir:
            self.context_path = context_dir / "GEMINI.md"
        else:
            self.context_path = self.repo_root / ".gemini" / "GEMINI.md"
            
        self.cache_dir = self.repo_root / ".dspy_cache"
        self.trace_dir = self.cache_dir / "trace_logs"
        
        # Ensure directories exist
        self.context_path.parent.mkdir(parents=True, exist_ok=True)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        
        self._validate_gemini_cli()
    
    def forward(
        self,
        story_context: str,
        tech_stack: str
    ) -> dspy.Prediction:
        """
        Execute Gemini with the instructions currently in the signature.
        """
        rollout_id = self._generate_rollout_id()
        start_time = datetime.utcnow()
        
        # Get the current optimized instructions from the predictor's signature
        instruction = self.predictor.signature.instructions
        
        try:
            # Step 1: Atomic write of candidate instruction (combined with base)
            full_context = f"{self.base_instruction}\n\n{instruction}" if self.base_instruction else instruction
            self._write_context_atomic(full_context)
            
            # Step 2: Prepare prompt with demos
            prompt = self._prepare_prompt(story_context, tech_stack, self.demos)
            
            # Step 3: Invoke Gemini CLI
            result = self._execute_gemini_with_retry(prompt, rollout_id)
            
            # Step 4: Parse structured output
            code_patch = self._extract_code_changes(result.stdout)
            reasoning = self._extract_reasoning(result.stdout)
            
            # Step 5: Run validation tests
            test_results = self._run_tests()
            
            # Step 6: Build execution trace (includes code_patch for retrospective)
            trace = self._build_trace(
                rollout_id=rollout_id,
                instruction=instruction,
                story_context=story_context,
                code_patch=code_patch,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                test_results=test_results,
                start_time=start_time
            )
            
            print(f"[DEBUG] Rollout {rollout_id} - Code Patch length: {len(code_patch)}")
            print(f"[DEBUG] Rollout {rollout_id} - Reasoning length: {len(reasoning)}")

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
    
    def _write_context_atomic(self, content: str) -> None:
        temp_path = self.context_path.with_suffix('.tmp')
        try:
            temp_path.write_text(content, encoding='utf-8')
            temp_path.replace(self.context_path)
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            raise IOError(f"Atomic GEMINI.md write failed: {e}")
    
    def _prepare_prompt(self, story_context: str, tech_stack: str, demos: List = None) -> str:
        demo_section = ""
        if demos:
            demo_parts = []
            for i, d in enumerate(demos[:3]):  # Max 3 demos to avoid context overflow
                problem = getattr(d, 'story_context', str(d))
                solution = getattr(d, 'code_patch', '')
                demo_parts.append(f"### Example {i+1}\n**Problem:**\n{problem}\n\n**Solution:**\n{solution}")
            demo_section = "\n\n---\n\n".join(demo_parts)
        
        demos_header = f"## Demonstrations\n{demo_section}\n\n" if demo_section else ""
        
        return f"""{demos_header}## Current Task\n{story_context}

## Technology Stack
{tech_stack}

## Instructions
Read context from .gemini/GEMINI.md. Output reasoning then code changes as JSON.
"""
    
    def _execute_gemini_with_retry(
        self,
        prompt: str,
        rollout_id: str
    ) -> subprocess.CompletedProcess:
        import time
        
        gemini_args = [
            self.gemini_binary,
            "-p", prompt,
            "--output-format", self.output_format
        ]
        
        # Support GEMINI_MODEL env var natively
        model_env = os.environ.get("GEMINI_MODEL")
        if model_env:
            gemini_args.extend(["--model", model_env])

        for attempt in range(self.max_retries + 1):
            try:
                process = subprocess.Popen(
                    gemini_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    cwd=self.repo_root,
                    env={
                        **os.environ,
                        "GEMINI_CONTEXT_PATH": str(self.context_path.parent),
                        "GEMINI_ROLLOUT_ID": rollout_id
                    }
                )
                stdout, stderr = process.communicate(timeout=self.timeout)
                result = subprocess.CompletedProcess(gemini_args, process.returncode, stdout, stderr)
                if self._is_transient_error(result):
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)
                        continue
                return result
            except subprocess.TimeoutExpired:
                if attempt < self.max_retries:
                    continue
                raise
        raise RuntimeError(f"Gemini execution failed after {self.max_retries} retries")

    def _run_tests(self) -> str:
        try:
            result = subprocess.run(
                ['npm', 'test', '--', '--silent', '--json'],
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
            })
        except subprocess.TimeoutExpired:
            return json.dumps({'error': 'timeout', 'success': False})

    def _detect_repo_root(self) -> Path:
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        raise RuntimeError("Cannot detect repository root")

    def _validate_gemini_cli(self) -> None:
        try:
            subprocess.run([self.gemini_binary, "--version"], capture_output=True, timeout=5, check=True)
        except:
            raise RuntimeError("Gemini CLI not found")

    def _generate_rollout_id(self) -> str:
        return f"rollout_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

    def _extract_code_changes(self, stdout: str) -> str:
        try:
            # Handle potential markdown wrapping
            clean_stdout = stdout.strip()
            if clean_stdout.startswith("```json"):
                import re
                match = re.search(r'```json\s*(.*?)\s*```', clean_stdout, re.DOTALL)
                if match:
                    clean_stdout = match.group(1)
            
            data = json.loads(clean_stdout)
            return data.get('code_patch', stdout)
        except Exception as e:
            print(f"[WARNING] Failed to parse code_patch JSON: {e}")
            return stdout

    def _extract_reasoning(self, stdout: str) -> str:
        try:
            clean_stdout = stdout.strip()
            if clean_stdout.startswith("```json"):
                import re
                match = re.search(r'```json\s*(.*?)\s*```', clean_stdout, re.DOTALL)
                if match:
                    clean_stdout = match.group(1)
            
            data = json.loads(clean_stdout)
            return data.get('reasoning', "No reasoning")
        except Exception as e:
            print(f"[WARNING] Failed to parse reasoning JSON: {e}")
            return "No reasoning"

    def _build_trace(self, **kwargs) -> Dict[str, Any]:
        trace = {
            'rollout_id': kwargs['rollout_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'instruction': kwargs['instruction'],
            'story_context': kwargs.get('story_context', ''),
            'code_patch': kwargs.get('code_patch', ''),
            'success': kwargs['returncode'] == 0,
            'test_results': kwargs['test_results']
        }
        trace_file = self.trace_dir / f"{kwargs['rollout_id']}.json"
        trace_file.write_text(json.dumps(trace, indent=2), encoding='utf-8')
        return trace

    def _is_transient_error(self, result: subprocess.CompletedProcess) -> bool:
        error_text = result.stderr + result.stdout
        return any(p in error_text for p in ["429", "Rate limit", "RESOURCE_EXHAUSTED"])

    def _handle_timeout(self, rollout_id: str, error: Exception) -> dspy.Prediction:
        return dspy.Prediction(code_patch="", test_results="{}", reasoning="timeout", execution_trace={})

    def _handle_error(self, rollout_id: str, error: Exception) -> dspy.Prediction:
        return dspy.Prediction(code_patch="", test_results="{}", reasoning=str(error), execution_trace={})
