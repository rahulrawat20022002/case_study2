"""
Hybrid retriever: BM25 (sparse) + bge dense over Chroma, fused with fixed
alpha=0.5 (frozen). Both score vectors are min-max normalised before fusion so
the weighting is meaningful. Returns top_k for the generator and logs top_log_k
for post-hoc analysis without re-running.

    r = HybridRetriever("config/pipeline.yaml")
    hits = r.search("credit scoring of a natural person")   # -> list of dicts
"""
import json
import re
import yaml
import numpy as np
from rank_bm25 import BM25Okapi
from encoder import get_encoder

_TOK = re.compile(r"[A-Za-z0-9]+")
def _tok(s):
    return _TOK.findall(s.lower())


def _minmax(x):
    x = np.asarray(x, dtype=np.float32)
    lo, hi = float(x.min()), float(x.max())
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


class HybridRetriever:
    def __init__(self, cfg_path="config/pipeline.yaml"):
        self.cfg = yaml.safe_load(open(cfg_path))
        self.chunks = [json.loads(l) for l in
                       open(self.cfg["corpus"]["chunks_file"], encoding="utf-8")]
        self.ids = [c["id"] for c in self.chunks]
        self.pos = {c["id"]: i for i, c in enumerate(self.chunks)}
        self.alpha = self.cfg["retrieval"]["hybrid_alpha"]
        self.top_k = self.cfg["retrieval"]["top_k"]
        self.log_k = self.cfg["retrieval"]["log_top_k"]

        self.bm25 = BM25Okapi([_tok(c["text"]) for c in self.chunks])
        self.enc = get_encoder(self.cfg["embedding"]["model"])
        self.qprefix = self.cfg["embedding"].get("query_prefix", "")

        import chromadb
        client = chromadb.PersistentClient(path=self.cfg["vector_store"]["path"])
        self.coll = client.get_collection(self.cfg["vector_store"]["collection"])

    def search(self, query, top_k=None, log_k=None):
        top_k = top_k or self.top_k
        log_k = log_k or self.log_k

        # dense: query gets the bge prefix; over-fetch for the fusion pool
        qv = self.enc.encode(self.qprefix + query,
                             normalize_embeddings=self.cfg["embedding"]["normalize"])
        qv = np.asarray(qv, dtype=np.float32).tolist()
        n_fetch = min(len(self.ids), max(log_k * 6, 50))
        res = self.coll.query(query_embeddings=[qv], n_results=n_fetch,
                              include=["distances"])
        dense = {cid: 1.0 - dist                      # cosine distance -> similarity
                 for cid, dist in zip(res["ids"][0], res["distances"][0])}

        # sparse: BM25 over the whole corpus
        bm = self.bm25.get_scores(_tok(query))
        bm_norm = _minmax(bm)
        dvals = _minmax([dense.get(cid, 0.0) for cid in self.ids])

        fused = self.alpha * dvals + (1.0 - self.alpha) * bm_norm
        order = np.argsort(-fused)[:log_k]

        hits = []
        for rank, idx in enumerate(order):
            c = self.chunks[idx]
            hits.append({
                "id": c["id"], "rank": rank + 1,
                "score": float(fused[idx]),
                "dense": float(dvals[idx]), "sparse": float(bm_norm[idx]),
                "section": c.get("section"), "area": c.get("annex_iii_area"),
                "heading_path": c.get("heading_path"), "text": c["text"],
            })
        return hits[:top_k], hits[:log_k]


if __name__ == "__main__":
    import sys
    r = HybridRetriever(sys.argv[1] if len(sys.argv) > 1 else "config/pipeline.yaml")
    q = "AI system to evaluate the creditworthiness of a natural person"
    top, _ = r.search(q)
    print(f"query: {q}\n")
    for h in top:
        print(f"  #{h['rank']} {h['id']} score={h['score']:.3f} "
              f"(d={h['dense']:.2f} s={h['sparse']:.2f}) {h['heading_path']}")
        print(f"     {h['text'][:130]}...")
