"""
Embed the corpus chunks with bge-base-en-v1.5 and persist them to a Chroma
collection. Passages are embedded WITHOUT the bge query prefix (that prefix is
for queries only). Run once; the retriever reads the persisted store.

Usage:
    python embed_and_index.py [config/pipeline.yaml]
"""
import sys
import json
import yaml
import numpy as np
from pathlib import Path
from encoder import get_encoder


def main(cfg_path="config/pipeline.yaml"):
    cfg = yaml.safe_load(open(cfg_path))
    chunks = [json.loads(l) for l in open(cfg["corpus"]["chunks_file"], encoding="utf-8")]
    print(f"loaded {len(chunks)} chunks")

    enc = get_encoder(cfg["embedding"]["model"])
    texts = [c["text"] for c in chunks]
    vecs = enc.encode(texts, normalize_embeddings=cfg["embedding"]["normalize"],
                      show_progress_bar=True, batch_size=32)
    vecs = np.asarray(vecs, dtype=np.float32)
    print(f"embedded -> {vecs.shape}")

    import chromadb
    store_path = cfg["vector_store"]["path"]
    Path(store_path).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=store_path)
    coll_name = cfg["vector_store"]["collection"]
    try:
        client.delete_collection(coll_name)
    except Exception:
        pass
    coll = client.create_collection(coll_name, metadata={"hnsw:space": "cosine"})

    ids = [c["id"] for c in chunks]
    metas = [{
        "section": c.get("section"),
        "area": c.get("annex_iii_area") or "",
        "para_num": c.get("para_num") or "",
        "heading_path": c.get("heading_path") or "",
    } for c in chunks]
    B = 256
    for i in range(0, len(ids), B):
        coll.add(ids=ids[i:i+B], embeddings=vecs[i:i+B].tolist(),
                 documents=texts[i:i+B], metadatas=metas[i:i+B])
    print(f"persisted {coll.count()} vectors -> {store_path}/{coll_name}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "config/pipeline.yaml")
