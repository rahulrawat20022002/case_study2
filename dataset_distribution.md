# Test set distribution — Case Study 2 (215 cases, frozen)

The evaluation set is 215 labelled cases drawn from the worked examples in the EU Commission's May 2026 draft guidelines on Annex III high-risk classification, each carrying an authoritative label (high-risk / not-high-risk), its Annex III area, and a source reference to the exact guideline passage.

## Distribution across the eight Annex III areas

| Annex III area | High-risk | Not-high-risk | Art 6(3) filter cases | Total |
|---|---:|---:|---:|---:|
| biometrics | 14 | 18 | 0 | 32 |
| critical-infrastructure | 8 | 10 | 0 | 18 |
| education | 9 | 19 | 10 | 28 |
| employment | 14 | 18 | 7 | 32 |
| essential-services | 21 | 22 | 5 | 43 |
| law-enforcement | 0 | 23 | 4 | 23 |
| migration | 0 | 23 | 10 | 23 |
| justice-democracy | 0 | 16 | 5 | 16 |
| **Total** | **66** | **149** | **41** | **215** |

All eight Annex III areas are represented.

## Class balance

66 high-risk (30.7%) and 149 not-high-risk (69.3%). The set is deliberately imbalanced because it uses every case that survived automated cleanup, with no downsampling. Reported per-class precision, recall and F1 alongside accuracy so the minority high-risk class is not masked, and this imbalance is noted as a study limitation.

## Article 6(3) filter edge cases

41 of the 215 cases are Article 6(3) "filter" edge cases, marked with `edge_case_type = article-6-3-filter`. These are the deliberately hard cases where a system falls within an Annex III area but may be exempted, and they are analysed as a separate group against the normal cases.

## Source asymmetry (disclose in the method section)

Three areas contain no high-risk cases: law-enforcement, migration, and justice-democracy are all not-high-risk. This is a property of the source, not a sampling choice: the Commission guidelines provide no high-risk worked examples in those three areas, only filter cases or out-of-scope not-high-risk examples. The consequence is that the study tests high-risk *detection* in five areas (biometrics, critical-infrastructure, education, employment, essential-services) and correct *rejection* across all eight.
