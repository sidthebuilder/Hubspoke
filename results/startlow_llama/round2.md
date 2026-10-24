# Start-low run (startlow_llama), R2.3

Mean price index over periods 26-40 (0 = Nash, 1 = joint-profit price); 'start' = the 5 pre-periods.

| condition | runs | index 26-40 (95% CI) | start | change from start (95% CI) |
|---|---|---|---|---|
| isolated | 12 | -0.24 (-0.33 to -0.15) | -0.38 | +0.14 (+0.07 to +0.22) |
| pooled | 12 | -0.43 (-0.53 to -0.33) | -0.38 | -0.05 (-0.15 to +0.03) |
| portfolio | 12 | -0.37 (-0.47 to -0.27) | -0.38 | +0.01 (-0.08 to +0.10) |
| separate | 12 | -0.29 (-0.44 to -0.16) | -0.38 | +0.09 (-0.05 to +0.20) |
| solo | 12 | -0.42 (-0.56 to -0.29) | -0.38 | -0.04 (-0.18 to +0.09) |

H5 isolated - solo: +0.183 (CI +0.020 to +0.348), exact p (two-sided) 0.0500. Registered decision: the advisor raises prices.
H6 isolated change from its own pre-periods: +0.140 (CI +0.067 to +0.216), sign-flip p 0.0049; up 9/12, down 1/12.
Exploratory, paired by seed: +0.183, sign-flip p 0.0195 (n 12).
Exploratory, portfolio - isolated: -0.134 (CI -0.266 to -0.002), p 0.0723.

Exploratory: the same conditions from the main start (main_llama) and from the low start.

| condition | pre-periods high / low | index 26-40 high | index 26-40 low | high - low |
|---|---|---|---|---|
| isolated | +0.55 / -0.38 | +0.39 | -0.24 | +0.63 |
| pooled | +0.55 / -0.38 | +0.35 | -0.43 | +0.79 |
| portfolio | +0.55 / -0.38 | +0.41 | -0.37 | +0.78 |
| solo | +0.55 / -0.38 | -0.05 | -0.42 | +0.37 |
