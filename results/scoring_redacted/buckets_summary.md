# Four-bucket outcome matrix (correctness x faithfulness)

Faithful threshold = 0.5 (a reporting choice; sweep and continuous stats below so nothing rests on it). Off-diagonal buckets are the findings: **wrong + faithful** is the headline 'faithful but wrong'.

## agent_structured

Joined & scored rows: 215  (unscored, no faithfulness: 0)

| | faithful | unfaithful |
|---|---|---|
| **label right** | 91 | 93 |
| **label wrong** | 17 | 14 |

Mean faithfulness when label right: 0.450
Mean faithfulness when label wrong: 0.487
Point-biserial corr(correct, faithfulness): -0.043

Bucket counts across faithful thresholds:

| threshold | right+faithful | right+unfaithful | wrong+faithful | wrong+unfaithful |
|---|---|---|---|---|
| 0.3 | 112 | 72 | 22 | 9 |
| 0.5 | 91 | 93 | 17 | 14 |
| 0.7 | 51 | 133 | 7 | 24 |
| 0.9 | 7 | 177 | 1 | 30 |
| 1.0 | 6 | 178 | 1 | 30 |

## baseline2_standard_rag

Joined & scored rows: 215  (unscored, no faithfulness: 0)

| | faithful | unfaithful |
|---|---|---|
| **label right** | 110 | 79 |
| **label wrong** | 14 | 12 |

Mean faithfulness when label right: 0.561
Mean faithfulness when label wrong: 0.451
Point-biserial corr(correct, faithfulness): 0.142

Bucket counts across faithful thresholds:

| threshold | right+faithful | right+unfaithful | wrong+faithful | wrong+unfaithful |
|---|---|---|---|---|
| 0.3 | 155 | 34 | 21 | 5 |
| 0.5 | 110 | 79 | 14 | 12 |
| 0.7 | 58 | 131 | 1 | 25 |
| 0.9 | 25 | 164 | 0 | 26 |
| 1.0 | 25 | 164 | 0 | 26 |
