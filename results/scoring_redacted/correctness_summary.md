# Correctness (predicted label vs frozen Commission ground truth)

Positive class = high-risk. Accuracy plus per-class precision/recall/F1 because the set is imbalanced (frozen). Parse failures counted as incorrect and also shown separately.

| Config | n | Accuracy | HR precision | HR recall | HR F1 | Macro F1 | Parse fails |
|---|---|---|---|---|---|---|---|
| agent_structured | 215 | 0.856 | 0.722 | 0.864 | 0.786 | 0.839 | 0 |
| baseline1_plain_llm | 215 | 0.688 | 0.496 | 0.894 | 0.638 | 0.682 | 0 |
| baseline2_standard_rag | 215 | 0.879 | 0.770 | 0.864 | 0.814 | 0.862 | 0 |

## agent_structured

Confusion (high-risk positive): tp=57 fp=22 fn=9 tn=127

By edge-case type: article-6-3-filter n=41 acc=0.780, none n=174 acc=0.874

By area: biometrics 0.812, critical-infrastructure 0.556, education 0.893, employment 1.000, essential-services 0.837, justice-democracy 0.750, law-enforcement 0.870, migration 1.000

## baseline1_plain_llm

Confusion (high-risk positive): tp=59 fp=60 fn=7 tn=89

By edge-case type: article-6-3-filter n=41 acc=0.780, none n=174 acc=0.667

By area: biometrics 0.531, critical-infrastructure 0.556, education 0.929, employment 0.906, essential-services 0.698, justice-democracy 0.688, law-enforcement 0.261, migration 0.826

## baseline2_standard_rag

Confusion (high-risk positive): tp=57 fp=17 fn=9 tn=132

By edge-case type: article-6-3-filter n=41 acc=0.878, none n=174 acc=0.879

By area: biometrics 0.812, critical-infrastructure 0.611, education 0.929, employment 0.969, essential-services 0.837, justice-democracy 0.875, law-enforcement 0.957, migration 1.000
