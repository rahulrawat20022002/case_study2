# Retrieval quality evaluation

Retriever: hybrid BM25 + `BAAI/bge-base-en-v1.5` dense, alpha=0.5, over 400 chunks. Gold = section-level from label_source. Primary metric: **Hit@5**. 215 test inputs.

Gold match kinds: {'exact': 215}

## Overall

| Metric | Value |
|---|---|
| **Hit@5 (primary)** | **0.833** |
| Hit@10 | 0.898 |
| Recall@5 | 0.246 |
| Recall@10 | 0.374 |
| MRR | 0.633 |

## By Annex III area

| Group | n | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR |
|---|---|---|---|---|---|---|
| biometrics | 32 | 0.969 | 0.969 | 0.133 | 0.210 | 0.789 |
| critical-infrastructure | 18 | 0.722 | 0.944 | 0.347 | 0.597 | 0.522 |
| education | 28 | 0.821 | 0.857 | 0.382 | 0.524 | 0.655 |
| employment | 32 | 0.969 | 1.000 | 0.188 | 0.335 | 0.790 |
| essential-services | 43 | 0.837 | 0.907 | 0.231 | 0.346 | 0.577 |
| justice-democracy | 16 | 0.938 | 0.938 | 0.173 | 0.304 | 0.859 |
| law-enforcement | 23 | 0.652 | 0.826 | 0.312 | 0.424 | 0.391 |
| migration | 23 | 0.652 | 0.696 | 0.251 | 0.351 | 0.443 |

## By edge-case type (filter rows are the Article 6(3) cases)

| Group | n | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR |
|---|---|---|---|---|---|---|
| article-6-3-filter | 41 | 0.707 | 0.780 | 0.188 | 0.275 | 0.437 |
| none | 174 | 0.862 | 0.925 | 0.259 | 0.397 | 0.679 |
