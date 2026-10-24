# Results tables (main_llama)

## Table 1 and the pre-registered tests

| condition | runs | price index, periods 26-40 (95% CI) | profit index | consumer surplus vs Nash | follows advice |
|---|---|---|---|---|---|
| solo | 12 | -0.05 (-0.26 to 0.19) | -0.16 | +3.8% |  |
| chat (+ctrl) | 12 | 0.35 (0.14 to 0.56) | 0.44 | -19.8% |  |
| isolated | 12 | 0.39 (0.23 to 0.59) | 0.49 | -22.0% | 94% |
| pooled | 12 | 0.35 (0.20 to 0.53) | 0.46 | -20.1% | 94% |
| aged | 12 | 0.12 (0.02 to 0.22) | 0.17 | -6.9% | 88% |
| aged + shared notebook | 12 | 0.33 (0.16 to 0.51) | 0.42 | -18.5% | 89% |
| portfolio (+ctrl) | 12 | 0.41 (0.25 to 0.56) | 0.55 | -23.3% | 97% |

| test | difference | 95% CI | p | p (Holm) |
|---|---|---|---|---|
| H1 pooled > isolated | -0.04 | -0.29 to +0.20 | 0.610 | 0.610 |
| H2 aged < pooled | -0.23 | -0.44 to -0.05 | 0.016 | 0.047 |
| H3 aged_sharedmem > aged | +0.21 | +0.01 to +0.42 | 0.036 | 0.072 |
| H4 isolated vs solo | +0.44 | +0.15 to +0.73 | 0.009 | 0.034 |
| aged - isolated | -0.27 | -0.49 to -0.08 | | |

## Predictions

| prediction | value | holds |
|---|---|---|
| P1 pooled - isolated >= 0.15 | -0.04 | no |
| P2 aged removes >= half the gap | -6.32 | not scored |
| P3 shared notebook restores >= half | 0.88 | yes |
| P5 isolated above solo | 0.44 | yes |
