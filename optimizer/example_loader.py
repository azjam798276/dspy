"""
Example Loader: Parses .example.md files into dspy.Example objects.
"""

import dspy
import re
from pathlib import Path
from typing import List, Optional


def parse_example_file(filepath: Path) -> Optional[dspy.Example]:
    """
    Parse a .example.md file into a dspy.Example.
    
    Expected format:
    ---
    id: "example_id"
    tags: ["tag1", "tag2"]
    ---
    ## Problem
    <problem description>
    
    ## Solution
    ```language
    <code solution>
    ```
    """
    content = filepath.read_text(encoding='utf-8')
    
    # Extract frontmatter
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not frontmatter_match:
        print(f"[WARNING] No frontmatter in {filepath}")
        return None
    
    body = content[frontmatter_match.end():]
    
    # Extract Problem section
    problem_match = re.search(r'##\s*Problem\s*\n(.*?)(?=##|\Z)', body, re.DOTALL | re.IGNORECASE)
    problem = problem_match.group(1).strip() if problem_match else ""
    
    # Extract Solution section (including code blocks)
    solution_match = re.search(r'##\s*Solution\s*\n(.*?)(?=##\s*Key|\Z)', body, re.DOTALL | re.IGNORECASE)
    solution = solution_match.group(1).strip() if solution_match else ""
    
    if not problem or not solution:
        print(f"[WARNING] Missing Problem or Solution in {filepath}")
        return None
    
    return dspy.Example(
        story_context=problem,
        code_patch=solution,
        source_file=str(filepath)
    ).with_inputs("story_context")


def load_examples_from_dir(examples_dir: Path, tech_stack: str = "") -> List[dspy.Example]:
    """
    Load all .example.md files from a directory.
    """
    examples = []
    if not examples_dir.exists():
        print(f"[INFO] Examples directory not found: {examples_dir}")
        return examples
    
    for example_file in examples_dir.glob("**/*.example.md"):
        example = parse_example_file(example_file)
        if example:
            # Add tech_stack if provided
            if tech_stack:
                example = dspy.Example(
                    story_context=example.story_context,
                    code_patch=example.code_patch,
                    tech_stack=tech_stack,
                    source_file=example.source_file
                ).with_inputs("story_context", "tech_stack")
            examples.append(example)
    
    print(f"[INFO] Loaded {len(examples)} examples from {examples_dir}")
    return examples
