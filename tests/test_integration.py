"""
Integration Tests for Ouroboros Optimization Loop

These tests verify that the GeminiSkillAdapter and BMadImplementationMetric
work together correctly within the DSPy framework.
"""

import pytest
import dspy
from pathlib import Path
from optimizer.gemini_adapter import GeminiSkillAdapter
from optimizer.metric import BMadImplementationMetric
from datetime import datetime

@pytest.mark.integration
class TestOptimizationLoop:
    
    @pytest.fixture
    def test_repo(self, tmp_path):
        """Create minimal test repository structure."""
        repo = tmp_path / "test_project"
        repo.mkdir()
        
        # Initialize git
        import subprocess
        subprocess.run(['git', 'init'], cwd=repo, check=True)
        
        # Create .gemini structure
        gemini_dir = repo / '.gemini'
        gemini_dir.mkdir(parents=True)
        (gemini_dir / 'GEMINI.md').write_text("# Test Context")
        
        return repo

    def test_adapter_initialization(self, test_repo):
        """Verify adapter initializes with correct paths."""
        adapter = GeminiSkillAdapter(repo_root=test_repo)
        assert adapter.context_path == test_repo / ".gemini" / "GEMINI.md"
    
    def test_metric_initialization(self, test_repo):
        """Verify metric initializes correctly."""
        metric = BMadImplementationMetric(repo_root=test_repo)
        assert metric.repo_root == test_repo

    def test_trace_logging(self, test_repo):
        """Verify execution traces are saved."""
        adapter = GeminiSkillAdapter(repo_root=test_repo) 
        
        # Manually build trace since we are actively avoiding external process execution in this unit test
        rollout_id = "test_rollout_001"
        trace = adapter._build_trace(
            rollout_id=rollout_id,
            instruction="Test Instruction",
            story_context="Test Story",
            stdout="Mock Output",
            stderr="",
            returncode=0,
            test_results="{}",
            start_time=datetime.utcnow()
        )
        
        trace_file = test_repo / ".dspy_cache" / "trace_logs" / f"{rollout_id}.json"
        assert trace_file.exists()
        import json
        saved_trace = json.loads(trace_file.read_text())
        assert saved_trace['rollout_id'] == rollout_id
