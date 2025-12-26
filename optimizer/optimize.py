#!/usr/bin/env python3
"""
Project Ouroboros: Main Optimization Script

Wires together GeminiSkillAdapter and BMadImplementationMetric using
DSPy GEPA/COPRO optimizer to autonomously refine persona instructions.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

import dspy

from optimizer.gemini_adapter import GeminiSkillAdapter
from optimizer.metric import BMadImplementationMetric
from optimizer.example_loader import load_examples_from_dir





class CLIReflectionLM(dspy.LM):
    """
    Adapter to use the local 'bin/gemini' wrapper as a DSPy LM.
    This allows using the user's authenticated CLI for the 'Teacher' agent.
    """
    def __init__(self, binary_path="gemini", model="gemini-cli", timeout=120):
        super().__init__(model=model)
        self.binary_path = binary_path
        self.timeout = timeout

    def basic_request(self, prompt: str, **kwargs):
        pass # DSPy abstract method

    def __call__(self, prompt=None, messages=None, **kwargs):
        # DSPy calls this
        return self.forward(prompt, messages=messages, **kwargs)

    def forward(self, prompt=None, messages=None, **kwargs):
        import subprocess
        
        prompt_str = prompt or ""
        if not prompt_str and messages:
            # Simple concatenation for chat history if needed, but for reflection usually just last prompt matters
            prompt_str = str(messages[-1]) if isinstance(messages, list) else str(messages)

        try:
            print(f"[DEBUG] Invoking CLI with prompt length: {len(prompt_str)}")
            
            import os
            cli_args = [self.binary_path, "-p", prompt_str, "--output-format", "json"]
            
            # Support GEMINI_MODEL env var natively
            model_env = os.environ.get("GEMINI_MODEL")
            if model_env:
                cli_args.extend(["--model", model_env])
            
            # Call the wrapper safely
            process = subprocess.Popen(
                cli_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                print(f"[ERROR] CLI LM Connection Timed Out after {self.timeout}s")
                raise
                
            # result = process # wrapper for compatible logic below
            print(f"[DEBUG] CLI returned code: {process.returncode}")
            
            content = stdout.strip()
            if process.returncode != 0:
                print(f"[WARNING] CLI LM returned non-zero code {process.returncode}: {stderr}")
                # If content is empty, then it's a real failure
                if not content:
                    print("[ERROR] No content generated.")
                    content = "{}" 
            
            # Parse the CLI wrapper's JSON output to get the actual text
            import json
            try:
                data = json.loads(content)
                # The CLI returns { "response": "...", "stats": ... }
                # We want just the response text.
                if isinstance(data, dict) and "response" in data:
                    content = data["response"]
                else:
                     # Fallback if structure is different
                     pass
            except json.JSONDecodeError:
                # If not JSON (maybe raw text?), use as-is
                pass

            # CRITICAL FIX: Return a LIST of strings
            return [content]

        except Exception as e:
            print(f"[ERROR] CLI LM Exception: {e}")
            raise


def load_training_stories(
    story_paths: List[Path],
    tech_stack: str
) -> List[dspy.Example]:
    examples = []
    for story_path in story_paths:
        if not story_path.exists(): continue
        story_content = story_path.read_text(encoding='utf-8')
        example = dspy.Example(
            story_context=story_content,
            tech_stack=tech_stack,
            story_path=str(story_path)
        ).with_inputs("story_context", "tech_stack")
        examples.append(example)
    return examples


def split_frontmatter(content: str) -> tuple[str, str]:
    """Split markdown content into YAML frontmatter and core instruction."""
    import re
    # Match YAML frontmatter between --- lines at start of file
    match = re.match(r'^(---\s*\n.*?\n---\s*\n)(.*)', content, re.DOTALL)
    if match:
        return match.group(1), match.group(2).strip()
    return "", content.strip()


def load_baseline_skill(repo_root: Path, skill_name: str) -> tuple[str, str, str]:
    """Load baseline skill, returning (frontmatter, instruction, target_filename)."""
    skill_dir = repo_root / "skills" / skill_name
    adapter_path = skill_dir / "adapter.md"
    skill_path = skill_dir / "SKILL.md"
    
    if adapter_path.exists():
        instruction = adapter_path.read_text(encoding='utf-8')
        frontmatter = ""
        if skill_path.exists():
            fm, _ = split_frontmatter(skill_path.read_text(encoding='utf-8'))
            frontmatter = fm
        return frontmatter, instruction, "adapter.md"
    
    if skill_path.exists():
        content = skill_path.read_text(encoding='utf-8')
        fm, instr = split_frontmatter(content)
        return fm, instr, "SKILL.md"
    
    template_path = repo_root / "templates" / "GEMINI.baseline.md"
    if template_path.exists():
        content = template_path.read_text(encoding='utf-8')
        fm, instr = split_frontmatter(content)
        return fm, instr, "SKILL.md"
        
    raise FileNotFoundError(f"Skill '{skill_name}' not found.")


def save_optimized_skill(
    frontmatter: str,
    instruction: str,
    baseline_instruction: str,
    repo_root: Path,
    skill_name: str,
    output_dir: Path,
    timestamp: str,
    target_filename: str = "SKILL.md"
) -> None:
    """Save optimized instruction to the target file and generate diff."""
    skill_dir = repo_root / "skills" / skill_name
    target_path = skill_dir / target_filename
    
    if target_filename == "SKILL.md":
        final_content = f"{frontmatter}\n\n{instruction}"
    else:
        final_content = instruction
    
    target_path.write_text(final_content, encoding='utf-8')
    
    # Save Version
    versions_dir = output_dir / "skill_versions" / skill_name
    versions_dir.mkdir(parents=True, exist_ok=True)
    version_file = versions_dir / f"{target_filename.replace('.', '_')}_{timestamp}.md"
    version_file.write_text(final_content, encoding='utf-8')
    
    # Generate and Save Diff
    diffs_dir = skill_dir / "diffs"
    diffs_dir.mkdir(parents=True, exist_ok=True)
    
    import difflib
    diff = list(difflib.unified_diff(
        baseline_instruction.splitlines(keepends=True),
        instruction.splitlines(keepends=True),
        fromfile=f"baseline_{target_filename}",
        tofile=f"optimized_{target_filename}",
        lineterm=""
    ))
    
    if diff:
        diff_file = diffs_dir / f"run_{timestamp}.diff"
        diff_file.write_text("".join(diff), encoding='utf-8')
        print(f"[INFO] Diff saved to {diff_file}")
    
    print(f"[INFO] Optimized skill saved to {target_path} (File: {target_filename})")


def save_pareto_frontier(frontier: List[dict], output_dir: Path, timestamp: str) -> None:
    """Serialize Pareto frontier to JSON for analysis."""
    output_dir.mkdir(parents=True, exist_ok=True)
    frontier_file = output_dir / f"pareto_frontier_{timestamp}.json"
    frontier_file.write_text(json.dumps(frontier, indent=2), encoding='utf-8')
    latest_file = output_dir / "pareto_frontier.json"
    latest_file.write_text(json.dumps(frontier, indent=2), encoding='utf-8')


def run_optimization(
    repo_root: Path,
    story_paths: List[Path],
    skill_name: str,
    max_rollouts: int,
    output_dir: Path,
    tech_stack: str,
    reflection_model: str,
    gemini_binary: str,
    examples_dir: Optional[Path],
    use_bootstrap: bool,
    use_semantic: bool,
    top_k: int,
    verbose: bool
) -> None:
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    # Load baseline context FIRST
    frontmatter, baseline_context, target_file = load_baseline_skill(repo_root, skill_name)
    print(f"[INFO] Baseline {target_file} loaded for skill '{skill_name}' (Content: {len(baseline_context)} chars)")

    # Initialize LM
    # Check if we have API key for real API
    import os
    if "GEMINI_API_KEY" in os.environ and os.environ["GEMINI_API_KEY"]:
        model_string = reflection_model if "/" in reflection_model else f"gemini/{reflection_model}"
        print(f"[INFO] Using Real Gemini API via LiteLLM: {model_string}")
        try:
            lm = dspy.LM(model_string)
        except Exception as e:
            print(f"[ERROR] Failed to init LM: {e}")
            sys.exit(1)
    else:
        # Fallback to CLI
        print(f"[INFO] No GEMINI_API_KEY found. Using CLIReflectionLM via '{gemini_binary}'")
        lm = CLIReflectionLM(binary_path=gemini_binary)

    dspy.settings.configure(lm=lm)
    
    
    trainset = load_training_stories(story_paths, tech_stack)
    
    # Load examples if provided
    demos = []
    semantic_matcher = None
    if examples_dir and examples_dir.exists():
        demos = load_examples_from_dir(examples_dir, tech_stack)
        
        # Initialize semantic matcher if requested
        if use_semantic and demos:
            from optimizer.semantic_matcher import is_available, SemanticMatcher
            if is_available():
                print(f"[INFO] Initializing SemanticMatcher with {len(demos)} examples (top-{top_k})")
                semantic_matcher = SemanticMatcher(examples=demos, examples_dir=examples_dir)
            else:
                print("[WARN] Semantic matching requested but sentence-transformers not installed")
    
    # Establish isolated context directory for this session
    session_dir = repo_root / ".gemini" / "sessions" / skill_name
    session_dir.mkdir(parents=True, exist_ok=True)
    
    adapter = GeminiSkillAdapter(
        gemini_binary=gemini_binary,
        repo_root=repo_root,
        base_instruction=frontmatter if target_file == "adapter.md" else "",
        context_dir=session_dir,
        demos=demos,
        semantic_matcher=semantic_matcher,
        top_k=top_k
    )
    adapter.predictor.signature.instructions = baseline_context
    metric = BMadImplementationMetric(repo_root=repo_root, sandbox_mode=True)
    
    optimizer = None
    optimizer_name = "None"
    
    try:
        # Try BootstrapFewShot if requested and demos available
        if use_bootstrap and demos:
            from dspy.teleprompt import BootstrapFewShot
            optimizer = BootstrapFewShot(
                metric=metric,
                max_bootstrapped_demos=min(3, len(demos)),
                max_labeled_demos=len(demos)
            )
            optimizer_name = "BootstrapFewShot"
        else:
            # Fall back to GEPA or COPRO
            try:
                from dspy.teleprompt import GEPA
                optimizer = GEPA(
                    metric=metric,
                    max_metric_calls=max_rollouts,
                    reflection_lm=lm,
                    verbose=verbose,
                    log_dir=str(output_dir / "gepa_logs")
                )
                optimizer_name = "GEPA"
            except (ImportError, TypeError):
                from dspy.teleprompt import COPRO
                optimizer = COPRO(
                    metric=metric,
                    max_metric_calls=max_rollouts,
                    verbose=verbose
                )
                optimizer_name = "COPRO"
    except Exception as e:
        print(f"[ERROR] Failed to initialize optimizer: {e}")
        raise
    
    print(f"[INFO] Starting optimization with {optimizer_name} ({max_rollouts} runs)...")
    
    try:
        kwargs = {}
        if optimizer_name == "COPRO":
            kwargs['eval_kwargs'] = {}
            
        optimized_adapter = optimizer.compile(
            adapter,
            trainset=trainset,
            **kwargs
        )
        
        # Extract the evolved instruction
        final_content = optimized_adapter.predictor.signature.instructions
        save_optimized_skill(
            frontmatter,
            final_content,
            baseline_context,
            repo_root,
            skill_name,
            output_dir,
            timestamp,
            target_file
        )
        
        save_pareto_frontier([{"timestamp": timestamp, "runs": max_rollouts}], output_dir, timestamp)
        print("[SUCCESS] Optimization cycle complete.")
        
    except Exception as e:
        print(f"[ERROR] Optimization failed: {e}")
        import traceback; traceback.print_exc()
        raise


def main():
    parser = argparse.ArgumentParser(description="Ouroboros Optimization")
    parser.add_argument("--trainset", nargs="+", required=True)
    parser.add_argument("--skill", type=str, required=True)
    parser.add_argument("--max-rollouts", type=int, default=50)
    parser.add_argument("--output-dir", type=Path, default=Path(".dspy_cache"))
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--tech-stack", type=str, default="Node 18")
    parser.add_argument("--reflection-model", type=str, default="gemini/gemini-2.0-flash")
    parser.add_argument("--gemini-binary", type=str, default="gemini")
    parser.add_argument("--examples-dir", type=Path, default=None, help="Path to directory with .example.md files")
    parser.add_argument("--bootstrap", action="store_true", help="Use BootstrapFewShot optimizer with examples")
    parser.add_argument("--dry-run", action="store_true", help="Preview configuration and loaded examples without running optimization")
    parser.add_argument("--semantic", action="store_true", help="Use semantic matching to select examples (requires --examples-dir)")
    parser.add_argument("--top-k", type=int, default=3, help="Number of examples to match when using --semantic")
    parser.add_argument("--verbose", action="store_true")
    
    args = parser.parse_args()
    
    if args.repo_root:
        repo_root = args.repo_root.resolve()
    else:
        current = Path.cwd(); repo_root = current
        while current != current.parent:
            if (current / ".git").exists(): repo_root = current; break
            current = current.parent
            
    story_paths = []
    for pattern in args.trainset:
        story_paths.extend(list(Path().glob(pattern)))
    
    # Dry-run mode: show configuration and exit
    if args.dry_run:
        print("\n" + "="*60)
        print(" DRY-RUN MODE: Configuration Preview")
        print("="*60)
        print(f"\n[SKILL] {args.skill}")
        print(f"[REPO ROOT] {repo_root}")
        print(f"[OPTIMIZER] {'BootstrapFewShot' if args.bootstrap else 'COPRO/GEPA'}")
        print(f"[MAX ROLLOUTS] {args.max_rollouts}")
        print(f"[SEMANTIC MATCHING] {'Enabled (top-' + str(args.top_k) + ')' if args.semantic else 'Disabled'}")
        
        print(f"\n[STORIES] {len(story_paths)} files:")
        for sp in story_paths:
            print(f"  - {sp}")
        
        if args.examples_dir:
            from optimizer.example_loader import load_examples_from_dir
            demos = load_examples_from_dir(args.examples_dir.resolve(), args.tech_stack)
            print(f"\n[EXAMPLES] {len(demos)} loaded from {args.examples_dir}:")
            for i, d in enumerate(demos):
                problem_preview = d.story_context[:80].replace('\n', ' ') + "..."
                print(f"  {i+1}. {problem_preview}")
            
            # Test semantic matching if enabled
            if args.semantic and story_paths:
                from optimizer.semantic_matcher import is_available, SemanticMatcher
                if is_available():
                    print(f"\n[SEMANTIC MATCHING TEST]")
                    test_story = story_paths[0].read_text()[:500]
                    matcher = SemanticMatcher(examples=demos)
                    matched = matcher.match(test_story, args.top_k)
                    print(f"  Query: {test_story[:80]}...")
                    for i, (ex, score) in enumerate(matched):
                        print(f"  {i+1}. Score: {score:.4f} | {ex.story_context[:50]}...")
                else:
                    print("\n[WARN] Semantic matching requested but sentence-transformers not installed")
        else:
            print("\n[EXAMPLES] None (--examples-dir not provided)")
        
        print("\n" + "="*60)
        print(" Dry-run complete. Remove --dry-run to execute optimization.")
        print("="*60 + "\n")
        return
    
    run_optimization(
        repo_root=repo_root,
        story_paths=story_paths,
        skill_name=args.skill,
        max_rollouts=args.max_rollouts,
        output_dir=args.output_dir.resolve(),
        tech_stack=args.tech_stack,
        reflection_model=args.reflection_model,
        gemini_binary=args.gemini_binary,
        examples_dir=args.examples_dir.resolve() if args.examples_dir else None,
        use_bootstrap=args.bootstrap,
        use_semantic=args.semantic,
        top_k=args.top_k,
        verbose=args.verbose
    )

if __name__ == "__main__":
    main()