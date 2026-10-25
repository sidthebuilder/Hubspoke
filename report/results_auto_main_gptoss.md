# Results tables (main_gptoss)

## Table 1 and the pre-registered tests

| condition | runs | price index, periods 26-40 (95% CI) | profit index | consumer surplus vs Nash | follows advice |
|---|---|---|---|---|---|
| solo | 12 | -0.01 (-0.10 to 0.07) | -0.03 | +0.9% |  |
| chat (+ctrl) | 12 | -0.05 (-0.15 to 0.04) | -0.11 | +3.3% |  |
| isolated | 12 | 0.01 (-0.06 to 0.11) | 0.00 | -0.4% | 88% |
| pooled | 12 | 0.02 (-0.07 to 0.15) | 0.02 | -1.2% | 83% |
| aged | 12 | -0.09 (-0.17 to -0.00) | -0.17 | +5.7% | 77% |
| aged + shared notebook | 12 | -0.05 (-0.14 to 0.06) | -0.10 | +3.1% | 86% |
| portfolio (+ctrl) | 12 | 0.08 (-0.09 to 0.27) | 0.07 | -4.1% | 61% |

| test | difference | 95% CI | p | p (Holm) |
|---|---|---|---|---|
| H1 pooled > isolated | +0.02 | -0.12 to +0.17 | 0.416 | 0.831 |
| H2 aged < pooled | -0.12 | -0.26 to +0.02 | 0.066 | 0.263 |
| H3 aged_sharedmem > aged | +0.04 | -0.09 to +0.18 | 0.271 | 0.813 |
| H4 isolated vs solo | +0.02 | -0.09 to +0.15 | 0.768 | 0.831 |
| aged - isolated | -0.10 | -0.22 to +0.01 | | |

## Predictions

| prediction | value | holds |
|---|---|---|
| P1 pooled - isolated >= 0.15 | 0.02 | no |
| P2 aged removes >= half the gap | 7.50 | yes |
| P3 shared notebook restores >= half | 0.38 | no |
| P5 isolated above solo | 0.02 | yes |
