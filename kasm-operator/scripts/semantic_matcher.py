#!/usr/bin/env python3
"""
Semantic Skill Matcher: Dynamic example selection using text embeddings.

Uses sentence-transformers to embed Golden Examples and stories,
then selects the most similar examples via cosine similarity.
"""

import json
from pathlib import Path
from typing import List, Optional, Tuple
import dspy

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("[WARN] sentence-transformers or scikit-learn not installed. Semantic matching disabled.")


class SemanticMatcher:
    """
    Matches stories to Golden Examples using embedding similarity.
    
    Usage:
        matcher = SemanticMatcher(examples_dir=Path("examples/backend"))
        matched_demos = matcher.match(story_context="Implement JWT auth...", top_k=3)
    """
    
    def __init__(
        self,
        examples: List[dspy.Example] = None,
        examples_dir: Optional[Path] = None,
        model_name: str = "all-MiniLM-L6-v2",
        cache_embeddings: bool = True
    ):
        if not EMBEDDINGS_AVAILABLE:
            raise RuntimeError("sentence-transformers not installed. Run: pip install sentence-transformers scikit-learn")
        
        self.model_name = model_name
        self.encoder = SentenceTransformer(model_name)
        self.cache_embeddings = cache_embeddings
        self.examples_dir = examples_dir
        
        # Load examples
        if examples:
            self.examples = examples
        elif examples_dir:
            from example_loader import load_examples_from_dir
            self.examples = load_examples_from_dir(examples_dir)
        else:
            self.examples = []
        
        # Compute or load embeddings
        self.embeddings = self._get_embeddings()
    
    def _get_embeddings(self) -> Optional[np.ndarray]:
        """Get embeddings for all examples, using cache if available."""
        if not self.examples:
            return None
        
        cache_file = None
        if self.cache_embeddings and self.examples_dir:
            cache_file = self.examples_dir / f".embeddings_{self.model_name.replace('/', '_')}.npy"
            if cache_file.exists():
                try:
                    cached = np.load(cache_file)
                    if len(cached) == len(self.examples):
                        print(f"[INFO] Loaded cached embeddings from {cache_file}")
                        return cached
                except Exception as e:
                    print(f"[WARN] Failed to load cache: {e}")
        
        # Compute embeddings
        texts = [self._get_example_text(ex) for ex in self.examples]
        print(f"[INFO] Computing embeddings for {len(texts)} examples...")
        embeddings = self.encoder.encode(texts, show_progress_bar=True)
        
        # Cache if enabled
        if cache_file:
            try:
                np.save(cache_file, embeddings)
                print(f"[INFO] Cached embeddings to {cache_file}")
            except Exception as e:
                print(f"[WARN] Failed to cache embeddings: {e}")
        
        return embeddings
    
    def _get_example_text(self, example: dspy.Example) -> str:
        """Extract text from example for embedding."""
        return getattr(example, 'story_context', str(example))
    
    def match(self, story_context: str, top_k: int = 3) -> List[Tuple[dspy.Example, float]]:
        """
        Find the top-k most similar examples to the given story.
        
        Returns:
            List of (example, similarity_score) tuples, sorted by similarity
        """
        if not self.examples or self.embeddings is None:
            return []
        
        story_embedding = self.encoder.encode([story_context])
        similarities = cosine_similarity(story_embedding, self.embeddings)[0]
        
        top_k = min(top_k, len(self.examples))
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [(self.examples[i], float(similarities[i])) for i in top_indices]
    
    def match_examples_only(self, story_context: str, top_k: int = 3) -> List[dspy.Example]:
        """Convenience method returning just examples without scores."""
        return [ex for ex, _ in self.match(story_context, top_k)]


def is_available() -> bool:
    """Check if semantic matching is available."""
    return EMBEDDINGS_AVAILABLE


def create_matcher(examples_dir: Path, examples: List[dspy.Example] = None) -> Optional[SemanticMatcher]:
    """Factory function to create a SemanticMatcher if dependencies are available."""
    if not EMBEDDINGS_AVAILABLE:
        return None
    try:
        return SemanticMatcher(examples=examples, examples_dir=examples_dir)
    except Exception as e:
        print(f"[ERROR] Failed to create SemanticMatcher: {e}")
        return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test semantic matching")
    parser.add_argument("--examples-dir", type=Path, required=True)
    parser.add_argument("--query", type=str, default="Implement JWT authentication with refresh tokens")
    parser.add_argument("--top-k", type=int, default=3)
    
    args = parser.parse_args()
    
    matcher = SemanticMatcher(examples_dir=args.examples_dir)
    results = matcher.match(args.query, args.top_k)
    
    print(f"\n{'='*60}")
    print(f"Query: {args.query[:80]}...")
    print(f"{'='*60}")
    for i, (ex, score) in enumerate(results):
        preview = ex.story_context[:100].replace('\n', ' ')
        print(f"\n{i+1}. [Score: {score:.4f}]")
        print(f"   {preview}...")
