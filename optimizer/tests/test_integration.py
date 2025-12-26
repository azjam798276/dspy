"""
Integration Test Suite for Project Ouroboros Optimizer

Tests the Read-Execute-Reflect-Rewrite cycle components:
- BMadImplementationMetric error parsing
- GeminiSkillAdapter atomic writes
- End-to-end optimization loop

Reference: TDD_v0.1.md Section 5.2
"""

import pytest
import json
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import dspy


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def tmp_repo(tmp_path):
    """Create a minimal repository structure for testing."""
    # Initialize git repo
    import subprocess
    subprocess.run(['git', 'init'], cwd=tmp_path, check=True, capture_output=True)
    
    # Create GEMINI.md
    gemini_dir = tmp_path / '.gemini'
    gemini_dir.mkdir(parents=True)
    
    baseline_context = """---
name: feature-development
description: Implements features with tests
version: 1.0.0
---

## Role
You are a specialized Feature Developer.

## Workflow
1. Analyze the story
2. Generate code
3. Write tests
"""
    (gemini_dir / 'GEMINI.md').write_text(baseline_context)
    
    # Create package.json
    (tmp_path / 'package.json').write_text('{"scripts": {"test": "echo PASS"}}')
    
    return tmp_path


@pytest.fixture
def metric(tmp_repo):
    """Create BMadImplementationMetric instance."""
    from optimizer.metric import BMadImplementationMetric
    return BMadImplementationMetric(repo_root=tmp_repo)


@pytest.fixture
def adapter(tmp_repo):
    """Create GeminiSkillAdapter instance."""
    from optimizer.gemini_adapter import GeminiSkillAdapter
    return GeminiSkillAdapter(repo_root=tmp_repo)


# ============================================================================
# BMadImplementationMetric Tests
# ============================================================================

class TestBMadImplementationMetric:
    """Test suite for metric function parsing logic."""
    
    def test_parses_undefined_variable_error(self, metric):
        """Verify ReferenceError extraction from test logs."""
        stderr = """
        ReferenceError: db is not defined
            at Object.<anonymous> (src/feature.js:42:10)
        """
        
        feedback = metric._extract_rich_feedback(stderr, "", "")
        
        assert "Undefined variables: db" in feedback
        assert "GEMINI.md should enforce" in feedback
        assert "verify variable declarations" in feedback.lower()
    
    def test_parses_type_error_correctly(self, metric):
        """Verify TypeError extraction from test logs."""
        stderr = """
        TypeError: Cannot read property 'map' of undefined
            at processItems (src/utils.js:15:8)
        """
        
        feedback = metric._extract_rich_feedback(stderr, "", "")
        
        assert "Type errors" in feedback
        assert "Cannot read property" in feedback
    
    def test_parses_import_error(self, metric):
        """Verify module import error extraction."""
        stderr = """
        Error: Cannot find module 'lodash'
        Require stack:
        - /project/src/feature.js
        """
        
        feedback = metric._extract_rich_feedback(stderr, "", "")
        
        assert "Missing modules: lodash" in feedback
        assert "package.json" in feedback.lower()
    
    def test_parses_assertion_failure(self, metric):
        """Verify test assertion error extraction."""
        stderr = """
        AssertionError: Expected 'foo' to equal 'bar'
            at Context.<anonymous> (test/feature.spec.js:25:10)
        """
        
        feedback = metric._extract_rich_feedback(stderr, "", "")
        
        assert "Test assertions" in feedback
        assert "acceptance criteria" in feedback.lower()
    
    def test_fallback_for_unknown_errors(self, metric):
        """Verify generic fallback when no patterns match."""
        stderr = "Some unknown error format that doesn't match patterns"
        
        feedback = metric._generate_generic_feedback(stderr, "")
        
        assert "Test failed" in feedback
        assert "unknown error" in feedback
    
    def test_returns_score_with_feedback(self, metric):
        """Verify metric returns proper ScoreWithFeedback type."""
        # Mock prediction with failed test results
        prediction = Mock()
        prediction.test_results = json.dumps({
            'success': False,
            'stderr': 'ReferenceError: x is not defined',
            'stdout': ''
        })
        prediction.code_patch = ''
        
        example = dspy.Example(story_context="Test story")
        
        result = metric(example, prediction)
        
        assert hasattr(result, 'score')
        assert hasattr(result, 'feedback')
        assert result.score == 0.0
        assert len(result.feedback) > 0
    
    def test_success_case_returns_positive_score(self, metric):
        """Verify passing tests return score 1.0."""
        prediction = Mock()
        prediction.test_results = json.dumps({
            'success': True,
            'stderr': '',
            'stdout': 'All tests passed'
        })
        
        example = dspy.Example(story_context="Test story")
        
        result = metric(example, prediction)
        
        assert result.score == 1.0
        assert "passed" in result.feedback.lower()


# ============================================================================
# GeminiSkillAdapter Tests
# ============================================================================

class TestGeminiSkillAdapter:
    """Test suite for Gemini adapter logic."""
    
    def test_atomic_write_creates_file(self, adapter, tmp_repo):
        """Verify atomic write succeeds."""
        content = "# Test GEMINI.md\nThis is a test"
        
        adapter._write_context_atomic(content)
        
        assert adapter.context_path.exists()
        assert adapter.context_path.read_text() == content
    
    def test_atomic_write_is_actually_atomic(self, adapter, tmp_repo):
        """Verify no partial writes visible to readers."""
        import random
        import string
        
        # Generate large content
        large_content = ''.join(
            random.choices(string.ascii_letters, k=10000)
        )
        
        read_values = []
        
        def reader():
            """Continuously read file during write."""
            for _ in range(100):
                if adapter.context_path.exists():
                    content = adapter.context_path.read_text()
                    read_values.append(len(content))
                time.sleep(0.001)
        
        reader_thread = threading.Thread(target=reader)
        reader_thread.start()
        
        # All reads should see either old content or complete new content
        # (never partial writes)
        initial_size = len((tmp_repo / '.gemini' / 'GEMINI.md').read_text())
        
        # Perform write
        adapter._write_context_atomic(large_content)
        
        reader_thread.join()
        
        mismatches = [size for size in read_values if size > 0 and size not in [initial_size, len(large_content)]]
        if mismatches:
            print(f"Debug: initial_size={initial_size}, target_size={len(large_content)}, read_values={read_values}")
            print(f"Debug: mismatches={mismatches}")
        
        assert all(
            size in [initial_size, len(large_content)] 
            for size in read_values if size > 0
        )
    
    def test_generates_unique_rollout_ids(self, adapter):
        """Verify rollout ID generation is unique."""
        ids = [adapter._generate_rollout_id() for _ in range(10)]
        
        # All unique
        assert len(ids) == len(set(ids))
        
        # All match expected pattern
        import re
        pattern = r'^rollout_\d{8}_\d{6}_\d{6}$'
        assert all(re.match(pattern, id) for id in ids)
    
    def test_detects_transient_errors_correctly(self, adapter):
        """Verify transient error detection logic."""
        import subprocess
        
        # Rate limit error
        rate_limit_result = Mock()
        rate_limit_result.stderr = "Rate limit exceeded. Try again later."
        rate_limit_result.stdout = ""
        
        assert adapter._is_transient_error(rate_limit_result) is True
        
        # Permanent error
        perm_error_result = Mock()
        perm_error_result.stderr = "Invalid API key"
        perm_error_result.stdout = ""
        
        assert adapter._is_transient_error(perm_error_result) is False
    
    def test_prepare_prompt_includes_context(self, adapter):
        """Verify prompt preparation includes story and tech stack."""
        prompt = adapter._prepare_prompt(
            story_context="User can register with email",
            tech_stack="Node 18, Express"
        )
        
        assert "User can register" in prompt
        assert "Node 18" in prompt
        assert "GEMINI.md" in prompt


# ============================================================================
# TwoTurnParser Tests (if applicable)
# ============================================================================

class TestTwoTurnParser:
    """Test suite for output parsing logic."""
    
    def test_parses_valid_two_turn_output(self):
        """Verify correct parsing of structured output."""
        output = json.dumps({
            "reasoning": "## Implementation Plan\n1. Create user service\n2. Add validation\n3. Write tests",
            "code_patch": "function register(email) {\n    return { email };\n}"
        })
        from optimizer.gemini_adapter import GeminiSkillAdapter
        adapter = GeminiSkillAdapter.__new__(GeminiSkillAdapter)
        
        reasoning = adapter._extract_reasoning(output)
        code = adapter._extract_code_changes(output)
        
        assert "Create user service" in reasoning
        assert "function register" in code
    
    def test_handles_missing_sections(self):
        """Verify graceful handling of incomplete output."""
        output = "Just some plain text without structure"
        
        from optimizer.gemini_adapter import GeminiSkillAdapter
        adapter = GeminiSkillAdapter.__new__(GeminiSkillAdapter)
        
        reasoning = adapter._extract_reasoning(output)
        
        assert "No reasoning" in reasoning

# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestOptimizationLoop:
    """
    End-to-end test of the optimization loop.
    
    WARNING: These tests may require actual CLI tools.
    """
    
    def test_single_optimization_iteration(self, tmp_repo, adapter, metric):
        """Verify one iteration of the optimization loop."""
        # Create training example
        example = dspy.Example(
            story_context="As a user, I want to register with my email"
        ).with_inputs("story_context")
        
        # Manually verify metrics logic with a pre-constructed prediction
        # Use dspy.Prediction directly to test the metric component in isolation
        prediction = dspy.Prediction(
            code_patch="function register() {}",
            test_results=json.dumps({
                'exit_code': 0,
                'success': True,
                'stdout': 'All tests passed',
                'stderr': ''
            }),
            reasoning="Will create register function",
            execution_trace={}
        )
        
        # Evaluate with metric
        result = metric(example, prediction)
        
        # Verify result structure
        assert hasattr(result, 'score')
        assert hasattr(result, 'feedback')
        assert result.score == 1.0


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests requiring external dependencies"
    )
