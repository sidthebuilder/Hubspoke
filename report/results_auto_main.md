# Results tables (main)

## Table 1 and the pre-registered tests

| condition | runs | price index, periods 26-40 (95% CI) | profit index | consumer surplus vs Nash | follows advice |
|---|---|---|---|---|---|
| solo | 12 | -0.04 (-0.13 to 0.06) | -0.07 | +2.3% |  |
| chat (+ctrl) | 12 | 0.35 (0.25 to 0.45) | 0.51 | -20.4% |  |
| isolated | 12 | 0.25 (0.14 to 0.39) | 0.34 | -14.1% | 99% |
| pooled | 12 | 0.16 (-0.00 to 0.34) | 0.20 | -8.8% | 100% |
| aged | 12 | 0.23 (0.13 to 0.35) | 0.34 | -13.4% | 98% |
| aged + shared notebook | 12 | 0.27 (0.14 to 0.41) | 0.37 | -15.3% | 99% |
| portfolio (+ctrl) | 12 | 0.20 (0.00 to 0.38) | 0.26 | -11.3% | 96% |

| test | difference | 95% CI | p | p (Holm) |
|---|---|---|---|---|
| H1 pooled > isolated | -0.10 | -0.30 to +0.12 | 0.801 | 1.000 |
| H2 aged < pooled | +0.08 | -0.12 to +0.27 | 0.761 | 1.000 |
| H3 aged_sharedmem > aged | +0.03 | -0.14 to +0.21 | 0.356 | 1.000 |
| H4 isolated vs solo | +0.29 | +0.14 to +0.45 | 0.002 | 0.006 |
| aged - isolated | -0.02 | -0.19 to +0.14 | | |

## Hub replay (change in recommended price index; 95% bootstrap CI over runs)

| condition | runs | data removed | notebook entries removed | mean abs change, data | mean abs change, notebook | noise floor (abs resample diff) |
|---|---|---|---|---|---|---|
| aged | 12 | +0.003 (-0.002 to +0.009) | +0.000 (-0.004 to +0.006) | 0.015 | 0.015 | 0.017 |
| aged + shared notebook | 12 | +0.001 (-0.001 to +0.003) | +0.000 (-0.004 to +0.004) | 0.005 | 0.010 | 0.005 |
| isolated | 12 | -0.002 (-0.004 to -0.000) | +0.001 (-0.001 to +0.004) | 0.003 | 0.003 | 0.002 |
| pooled | 12 | -0.000 (-0.002 to +0.001) | -0.001 (-0.004 to +0.001) | 0.004 | 0.005 | 0.005 |

## Canary test (share of trials, 95% Wilson CI)

| notebook | trials | written to notebook | reaches other client's session | told to other client | in other client's memo | advice shift (index) |
|---|---|---|---|---|---|---|
| private | 48 | 24/48 = 0.50 (0.36 to 0.64) | 0/48 = 0.00 (0.00 to 0.07) | 0/48 = 0.00 (0.00 to 0.07) | 0/48 = 0.00 (0.00 to 0.07) | +0.001 (-0.010 to +0.014) |
| shared | 48 | 24/48 = 0.50 (0.36 to 0.64) | 24/48 = 0.50 (0.36 to 0.64) | 5/48 = 0.10 (0.05 to 0.22) | 20/48 = 0.42 (0.29 to 0.56) | +0.091 (+0.031 to +0.166) |

- private, by fact: code: written 0/24, exposed 0/24, disclosed 0/24; price: written 24/24, exposed 0/24, disclosed 0/24
- shared, by fact: code: written 0/24, exposed 0/24, disclosed 0/24; price: written 24/24, exposed 24/24, disclosed 5/24

## Fork test (Firm A forced to its one-shot best response in period 26; means over runs, 95% CI)

| condition | runs | deviation size (index) | excess cut by B | B's reaction vs original | placebo reaction | A's net gain, 10 periods | placebo gain |
|---|---|---|---|---|---|---|---|
| chat (+ctrl) | 12 | +0.21 | +0.159 (+0.100 to +0.228) | -0.130 (-0.192 to -0.067) | +0.012 (-0.006 to +0.030) | -6.7% (-9.2 to -4.1) | +0.1% (-0.8 to +0.9) |
| isolated | 12 | +0.22 | +0.085 (+0.040 to +0.131) | -0.097 (-0.174 to -0.034) | +0.000 (+0.000 to +0.000) | -1.4% (-6.9 to +6.1) | +0.1% (-0.6 to +0.6) |
| pooled | 12 | +0.10 | +0.035 (-0.029 to +0.104) | -0.085 (-0.174 to -0.008) | +0.018 (-0.005 to +0.045) | -2.7% (-5.0 to -0.8) | -0.3% (-1.4 to +0.8) |
| portfolio (+ctrl) | 12 | +0.10 | +0.038 (-0.062 to +0.113) | -0.115 (-0.213 to -0.015) | -0.004 (-0.013 to +0.004) | -1.7% (-6.1 to +3.1) | -0.7% (-1.7 to -0.0) |

## Who can tell pooled from isolated? (AUROC, 95% bootstrap CI; 0.5 = chance)

| vantage point | AUROC | 95% CI | runs (pooled, isolated) |
|---|---|---|---|
| fork test | 0.64 | 0.39 to 0.86 | 12, 12 |
| hub replay | 0.58 | 0.36 to 0.81 | 12, 12 |
| hub logs (leak rule) | 0.50 | 0.50 to 0.50 | 12, 12 |
| one firm's records | 0.43 | 0.19 to 0.67 | 12, 12 |
| market prices | 0.33 | 0.11 to 0.58 | 12, 12 |

## Predictions

| prediction | value | holds |
|---|---|---|
| P1 pooled - isolated >= 0.15 | -0.10 | no |
| P2 aged removes >= half the gap | 0.80 | not scored |
| P3 shared notebook restores >= half | -0.45 | not scored |
| P5 isolated above solo | 0.29 | yes |
| P4 prices < 0.8 and replay >= 0.8 | 0.33, 0.58 | no |
