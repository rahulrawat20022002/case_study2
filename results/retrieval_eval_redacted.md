# Retrieval quality evaluation

Retriever: hybrid BM25 + `BAAI/bge-base-en-v1.5` dense, alpha=0.5, over 400 chunks. Gold = section-level from label_source. Primary metric: **Hit@5**. 215 test inputs.

Gold match kinds: {'exact': 215}

## Overall

| Metric | Value |
|---|---|
| **Hit@5 (primary)** | **0.795** |
| Hit@10 | 0.856 |
| Recall@5 | 0.251 |
| Recall@10 | 0.357 |
| MRR | 0.651 |

## By Annex III area

| Group | n | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR |
|---|---|---|---|---|---|---|
| biometrics | 32 | 0.875 | 0.875 | 0.116 | 0.188 | 0.757 |
| critical-infrastructure | 18 | 0.833 | 0.944 | 0.500 | 0.653 | 0.573 |
| education | 28 | 0.786 | 0.857 | 0.423 | 0.528 | 0.730 |
| employment | 32 | 0.938 | 0.938 | 0.169 | 0.287 | 0.838 |
| essential-services | 43 | 0.791 | 0.860 | 0.223 | 0.350 | 0.587 |
| justice-democracy | 16 | 0.875 | 0.938 | 0.149 | 0.248 | 0.888 |
| law-enforcement | 23 | 0.565 | 0.739 | 0.297 | 0.391 | 0.412 |
| migration | 23 | 0.652 | 0.696 | 0.224 | 0.301 | 0.401 |

## By edge-case type (filter rows are the Article 6(3) cases)

| Group | n | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR |
|---|---|---|---|---|---|---|
| article-6-3-filter | 41 | 0.732 | 0.780 | 0.226 | 0.292 | 0.581 |
| none | 174 | 0.810 | 0.874 | 0.257 | 0.372 | 0.667 |
