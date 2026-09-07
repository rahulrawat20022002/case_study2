"""
Encoder factory. Real runs use BAAI/bge-base-en-v1.5 (frozen). A deterministic
hashing fallback exists ONLY for offline plumbing tests where the model cannot
be downloaded (set CS2_FAKE_EMBED=1). The fallback is not semantic and must
never be used for eval results; it exists to prove the retrieval fusion code
runs end to end.
"""
import os
import numpy as np


class _HashingEncoder:
    """Bag-of-hashed-words -> L2-normalised vector. Test-only stand-in."""
    def __init__(self, dim=768):
        self.dim = dim

    def _vec(self, text):
        v = np.zeros(self.dim, dtype=np.float32)
        for tok in text.lower().split():
            v[hash(tok) % self.dim] += 1.0
        n = np.linalg.norm(v)
        return v / n if n else v

    def encode(self, texts, normalize_embeddings=True, **kw):
        single = isinstance(texts, str)
        arr = np.vstack([self._vec(t) for t in ([texts] if single else texts)])
        return arr[0] if single else arr


def get_encoder(model_name="BAAI/bge-base-en-v1.5"):
    if os.environ.get("CS2_FAKE_EMBED") == "1":
        print("[encoder] WARNING: CS2_FAKE_EMBED=1 -> hashing stand-in, not for eval")
        return _HashingEncoder()
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)
