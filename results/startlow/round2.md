# Start-low run (startlow), R2.3

Mean price index over periods 26-40 (0 = Nash, 1 = joint-profit price); 'start' = the 5 pre-periods.

| condition | runs | index 26-40 (95% CI) | start | change from start (95% CI) |
|---|---|---|---|---|
| isolated | 12 | -0.25 (-0.37 to -0.12) | -0.38 | +0.13 (+0.03 to +0.24) |
| pooled | 12 | -0.36 (-0.52 to -0.19) | -0.38 | +0.02 (-0.13 to +0.17) |
| portfolio | 12 | -0.22 (-0.39 to -0.02) | -0.38 | +0.16 (-0.00 to +0.34) |
| separate | 12 | +0.00 (-0.18 to +0.20) | -0.38 | +0.38 (+0.20 to +0.57) |
| solo | 12 | -0.42 (-0.53 to -0.30) | -0.38 | -0.05 (-0.15 to +0.06) |

H5 isolated - solo: +0.178 (CI +0.010 to +0.339), exact p (two-sided) 0.0574. Registered decision: the advisor raises prices.
H6 isolated change from its own pre-periods: +0.132 (CI +0.023 to +0.240), sign-flip p 0.0542; up 8/12, down 2/12.
Exploratory, paired by seed: +0.178, sign-flip p 0.0356 (n 12).
Exploratory, portfolio - isolated: +0.025 (CI -0.183 to +0.250), p 0.8355.

Exploratory: the same conditions from the main start (main) and from the low start.

| condition | pre-periods high / low | index 26-40 high | index 26-40 low | high - low |
|---|---|---|---|---|
| isolated | +0.55 / -0.38 | +0.25 | -0.25 | +0.50 |
| pooled | +0.55 / -0.38 | +0.16 | -0.36 | +0.52 |
| portfolio | +0.55 / -0.38 | +0.20 | -0.22 | +0.42 |
| separate | +0.55 / -0.38 | +0.36 | +0.00 | +0.36 |
| solo | +0.55 / -0.38 | -0.04 | -0.42 | +0.39 |
