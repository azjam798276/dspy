#!/usr/bin/env python3
"""
Retrospective Generator: Auto-generate Golden Examples from Successful Traces

Reads trace logs from .dspy_cache/trace_logs/ and generates .example.md files
for successful rollouts that can be used for future Few-Shot optimization.
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict


def extract_key_techniques(code_patch: str) -> List[str]:
    """
    Extract key coding patterns from a code patch.
    """
    techniques = []
    
    # Pattern detection
    patterns = {
        "async/await": r'\basync\b.*\bawait\b',
        "try/catch error handling": r'\btry\s*{.*}\s*catch\b',
        "Lua script atomicity": r'lua[Ss]cript|redis\.call',
        "JWT token handling": r'jwt\.|jsonwebtoken|token',
        "Transaction management": r'transaction|BEGIN|COMMIT|ROLLBACK',
        "Input validation": r'validate|Joi\.|Zod\.|schema',
        "Middleware pattern": r'middleware|next\(\)',
        "Queue/Job processing": r'bull|queue|job\.data',
        "REST API design": r'router\.(get|post|put|delete)',
        "Database operations": r'findOne|findMany|create\(|update\(|delete\(',
    }
    
    for technique, pattern in patterns.items():
        if re.search(pattern, code_patch, re.IGNORECASE | re.DOTALL):
            techniques.append(technique)
    
    return techniques[:5]  # Limit to top 5


def generate_example_content(
    rollout_id: str,
    story_context: str,
    code_patch: str,
    techniques: List[str],
    tags: List[str]
) -> str:
    """Generate .example.md content from trace data."""
    
    # Truncate story to problem description (first 500 chars or first section)
    problem = story_context[:800] if len(story_context) > 800 else story_context
    
    # Clean up code patch - extract main code block
    solution = code_patch[:3000] if len(code_patch) > 3000 else code_patch
    
    techniques_list = "\n".join([f"- {t}" for t in techniques]) if techniques else "- Production-ready implementation"
    tags_str = ", ".join([f'"{t}"' for t in tags])
    
    return f'''---
id: "{rollout_id}_golden"
generated_at: "{datetime.utcnow().isoformat()}"
tags: [{tags_str}]
---

## Problem
{problem}

## Solution
{solution}

## Key Techniques
{techniques_list}
'''


def process_trace_file(
    trace_path: Path,
    domain: str,
    min_score: float,
    output_dir: Path
) -> Optional[str]:
    """
    Process a single trace file and generate example if successful.
    Returns the output path if generated, None otherwise.
    """
    try:
        with open(trace_path, 'r', encoding='utf-8') as f:
            trace = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[WARN] Failed to read {trace_path}: {e}")
        return None
    
    # Check success criteria
    if not trace.get('success', False):
        return None
    
    # Parse test results if available
    test_results = trace.get('test_results', '{}')
    if isinstance(test_results, str):
        try:
            test_results = json.loads(test_results)
        except:
            test_results = {}
    
    pass_rate = 1.0 if test_results.get('success', False) else 0.0
    if pass_rate < min_score:
        return None
    
    # Extract required fields
    rollout_id = trace.get('rollout_id', trace_path.stem)
    instruction = trace.get('instruction', '')
    
    # We need story context - check if it's in the trace
    story_context = trace.get('story_context', instruction)
    if not story_context:
        print(f"[WARN] No story context in {trace_path}")
        return None
    
    # Get code patch from the trace (might need to be extracted differently)
    code_patch = trace.get('code_patch', '')
    if not code_patch:
        print(f"[WARN] No code patch in {trace_path}")
        return None
    
    # Extract techniques and generate
    techniques = extract_key_techniques(code_patch)
    tags = [domain, "auto-generated"]
    
    content = generate_example_content(
        rollout_id=rollout_id,
        story_context=story_context,
        code_patch=code_patch,
        techniques=techniques,
        tags=tags
    )
    
    # Write to output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{rollout_id}_golden.example.md"
    output_path.write_text(content, encoding='utf-8')
    
    return str(output_path)


def run_retrospective(
    trace_dir: Path,
    domain: str,
    output_dir: Path,
    min_score: float = 0.9,
    limit: int = 10
) -> List[str]:
    """
    Scan trace directory and generate Golden Examples from successful traces.
    """
    generated = []
    
    if not trace_dir.exists():
        print(f"[ERROR] Trace directory not found: {trace_dir}")
        return generated
    
    trace_files = list(trace_dir.glob("*.json"))
    print(f"[INFO] Found {len(trace_files)} trace files in {trace_dir}")
    
    for trace_path in trace_files[:limit]:
        result = process_trace_file(trace_path, domain, min_score, output_dir)
        if result:
            print(f"[SUCCESS] Generated: {result}")
            generated.append(result)
    
    print(f"\n[SUMMARY] Generated {len(generated)} Golden Examples from {len(trace_files)} traces")
    return generated


def main():
    parser = argparse.ArgumentParser(description="Generate Golden Examples from successful traces")
    parser.add_argument("--trace-dir", type=Path, default=Path(".dspy_cache/trace_logs"),
                        help="Directory containing trace JSON files")
    parser.add_argument("--domain", type=str, required=True,
                        help="Domain for generated examples (e.g., 'backend', 'algorithms')")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Output directory (default: examples/{domain})")
    parser.add_argument("--min-score", type=float, default=0.9,
                        help="Minimum pass rate to consider successful (default: 0.9)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Maximum number of examples to generate")
    parser.add_argument("--auto-pr", action="store_true",
                        help="Automatically register and create PRs for generated examples")
    
    args = parser.parse_args()
    
    output_dir = args.output_dir or Path(f"examples/{args.domain}")
    
    print(f"\n{'='*60}")
    print(f" Retrospective Generator")
    print(f"{'='*60}")
    print(f"[CONFIG] Trace Dir: {args.trace_dir}")
    print(f"[CONFIG] Domain: {args.domain}")
    print(f"[CONFIG] Output: {output_dir}")
    print(f"[CONFIG] Min Score: {args.min_score}")
    print(f"[CONFIG] Auto-PR: {'Enabled' if args.auto_pr else 'Disabled'}")
    print(f"{'='*60}\n")
    
    generated = run_retrospective(
        trace_dir=args.trace_dir,
        domain=args.domain,
        output_dir=output_dir,
        min_score=args.min_score,
        limit=args.limit
    )
    
    # Auto-PR workflow
    if args.auto_pr and generated:
        print(f"\n[AUTO-PR] Registering {len(generated)} examples...")
        from optimizer.registry import register_example, create_pr
        
        # Detect repo root
        repo_root = Path.cwd()
        while repo_root != repo_root.parent:
            if (repo_root / ".git").exists():
                break
            repo_root = repo_root.parent
        
        for example_path in generated:
            path = Path(example_path)
            register_example(path, repo_root, args.domain)
            # Optionally create PR (can be done in batch later)
            # create_pr(path, repo_root)


if __name__ == "__main__":
    main()
