# Round-2 facts for writing (25 Oct 2026; facts and sources only, the author writes the prose)

Registered in PREREGISTRATION.md (R2.1-R2.5, commit d2dbc03, 25 Oct 00:10 IST) before any round-2 run.
Every number below is in the file named next to it. "Exploratory" = not registered.

## Canary v2 (R2.1): what a shared notebook carries, and whether a rule or owner tags stop it
Files: results/canary2/round2.md (Qwen), results/canary2_llama/round2.md (Llama), figures fig2_notebook.png,
fig3_checks.png. 384 trials per model: 4 facts x 4 notebook setups x 24 states (12 runs x periods 30 and 36).

**Written into Firm A's notebook entry (exact text, all four setups, 96 trials per fact):**
- Qwen: account code 0%, warehouse town 0%, cost cut 6%, price plan 100% (96/96).
- Llama: account code 4%, town 32%, cost cut 6%, price plan 61%.
- P6 (written >= 0.8 for price and cost, <= 0.2 for code and town) fails on both models, because cost cuts are
  almost never written with their number. Qwen's gate is "price plans only", not "anything price-relevant".
- Caveat: "written" is exact text. Llama often paraphrases (e.g. a memo mentioning "Firm A's 5-period price
  commitment" without the number), so the exact count is a lower bound.

**Advice to Firm B judged to reveal or rely on A's price plan (24 trials per cell):**
| | private | shared | shared + rule | shared + owner tags |
|---|---|---|---|---|
| Qwen, judged | 0/24 | 18/24 (75%) | 16/24 (67%) | 15/24 (62%) |
| Qwen, judge on control notes (false alarms) | 1/24 | 0/24 | 1/24 | 2/24 |
| Qwen, exact number | 0/24 | 5/24 | 7/24 | 5/24 |
| Llama, judged | 4/24 (17%) | 8/24 (33%) | 13/24 (54%) | 11/24 (46%) |
| Llama, judge on control notes | 5/24 | 5/24 | 4/24 | 7/24 |
| Llama, exact number | 0/24 | 1/24 | 0/24 | 0/24 |

- Registered tests (Fisher, Holm over three): Qwen shared vs private p = 3.7e-08 (Holm 1.1e-07); rule vs
  shared p = 0.75; tags vs shared p = 0.53 (both Holm 1.0). Llama: shared vs private p = 0.32; rule vs shared p = 0.24; tags vs
  shared p = 0.56 (all Holm 0.73).
- Predictions: P7 (private 0, shared >= 0.5) holds on Qwen, fails on Llama (private 4/24 judged, shared 8/24).
  P8 (rule cuts it by less than half) and P9 (tags cut it by less than half) hold on both models.
- The judge's false-alarm rate is low on Qwen's notes (0-8%) and high on Llama's (17-29%): Llama's notes often
  say "match Firm A's price", which the judge sometimes reads as relying on the plan.
- Codes and towns: never told to B by exact text on either model (0/96 each per model).

**B's recommended price, probe minus control (index units; 95% bootstrap CI):**
- Qwen: private -0.001; shared +0.126 (+0.029 to +0.257); rule +0.074 (+0.022 to +0.143); tags +0.088
  (+0.007 to +0.202).
- Llama: private -0.013; shared +0.060 (+0.002 to +0.132); rule +0.087 (+0.027 to +0.153); tags +0.017
  (-0.025 to +0.082).
- Exploratory: the shift comes with the reveal. Qwen shared: +0.146 when the judge says the note reveals the
  plan (n 18) vs +0.066 when not (n 6). Llama shared: +0.146 (n 8) vs +0.017 (n 16).
- Exploratory, share of trials where B's advice rose by more than 0.02 index: Qwen shared 9/24 vs private
  noise floor (identical inputs, fresh sample) 1/24; Llama 12/24 vs 5/24.

**Exploratory "excess raise" (results/robust.md).** A one-shot best response to A's planned price, instead of
A's last price, would raise B's price by +0.33 to +0.36 index. The advice moved by +0.06 to +0.13 (25-35% of
that on Qwen, 18-26% on Llama). The leak pulls B's price up, by less than a best response would.

## Judge validation (R2.2)
File: results/judge_validation.md. Judge: Qwen2.5-72B, temperature 0, fixed prompt (hubspoke/judge.py).
- On the 48 canary-v1 notes: judge says reveal in 16/24 shared-arm notes and 1/24 private-arm notes; exact
  rule 5/24 and 0/24. Judge vs exact: agree 36/48, kappa 0.35 (every disagreement is judge 1 / exact 0).
- [PENDING: the author's blind labels in results/handcheck_canary.csv -> judge-human kappa; if < 0.6 the judged
  measure is reported as secondary only (registered).]

## Start-low (R2.3): does advice raise prices, or only stop them falling?
Files: results/startlow/round2.md (Qwen), results/startlow_llama/round2.md (Llama), figure fig1_starts.png.
Pre-periods at index -0.38 on average (below Nash), the same for every condition of a seed.

| periods 26-40 | solo | isolated | pooled | portfolio | separate |
|---|---|---|---|---|---|
| Qwen | -0.42 | -0.25 | -0.36 | -0.22 | +0.00 |
| Llama | -0.42 | -0.24 | -0.43 | -0.37 | -0.29 |

- H5 isolated - solo: Qwen +0.178 (CI +0.010 to +0.339), exact p = 0.057; Llama +0.183 (CI +0.020 to +0.348),
  p = 0.050 (two-sided). Registered rule: >= +0.15 means "the advisor raises prices", so that is the registered
  conclusion on both models. Kiro's prediction (inertia, p = 0.65) was wrong.
- H6 isolated's change from its own pre-periods: Qwen +0.132 (CI +0.023 to +0.240), sign-flip p = 0.054, 8 of 12
  up; Llama +0.140 (CI +0.067 to +0.216), p = 0.005, 9 of 12 up.
- Exploratory: paired by seed, p = 0.036 (Qwen) and 0.020 (Llama); averaged over both models +0.180 (CI +0.063
  to +0.296), stratified permutation p = 0.006 (results/robust.md; added after seeing the results).
- Careful reading: from below Nash, prices that rise are moving towards the competitive level, not above it;
  every condition except Qwen's `separate` (+0.00) ended below Nash. Solo sellers barely moved from their start
  (-0.05 and -0.04): without an advisor, LLM sellers stay where they start, high or low (start-high minus
  start-low: +0.39 Qwen, +0.37 Llama for solo). The advisor adds about +0.18 to +0.44 index on top of that, from
  either start: +0.29 / +0.18 (Qwen, high / low start), +0.44 / +0.18 (Llama).
- Exploratory: portfolio - isolated: Qwen +0.025 (p 0.84), Llama -0.134 (CI -0.266 to -0.002). The joint-profit
  advisor again did not raise prices above the firewalled one.
- Exploratory: Qwen's `separate` advisor (told it serves only one firm) priced highest from both starts (+0.36
  high, +0.00 low), above the shared isolated advisor (+0.25, -0.25).

## Robustness (exploratory; results/robust.md)
- Paired by seed (sign-flip tests): Qwen H4 +0.288, p = 0.001; Llama H2 -0.235, p = 0.004; Llama H3 +0.208,
  p = 0.030; Llama H4 +0.444, p = 0.002; H1 null on both (p 0.84, 0.58).
- H1 averaged over Qwen and Llama: pooled - isolated -0.067 (CI -0.227 to +0.093); one-sided 95% upper bound
  +0.066. Pooling the rival's data raised prices by at most about 0.07 index points in our runs.

## What an auditor needs (exploratory; results/robust.md, "audit power")
- A random account code or an irrelevant plan never reached B on either model: the usual canary gives a false
  all-clear. Plant a price plan instead.
- Qwen: with the judged reading against control sessions, 6 planted price plans (and 6 controls) give 80% power
  in the shared setup (9 with the rule, 11 with tags). Exact-number matching needs 13 trials for a 95% chance of
  one hit.
- Llama: the judge's false alarms are high, so judged reading needs 24 trials (rule setup) to > 60 (others);
  the "advice raised vs control" check separates better (12/24 vs 5/24).

## AI Village field check (R2.5; results/village/summary.json, merch_cases.json; aggregate only)
- Data: AI Digest, "AI Village dataset", 2026, https://theaidigest.org/village (research terms: analysis only).
- 2026 "Merch baron" pair (Claude Fable 5, Gemini 3.5 Flash, from 6 Jul 2026): 2,305 messages, 282 addressed
  to the other agent. Coded: own sales or profit 11, prices 18, cross-promotion 30, product allocation 3,
  declines joint action 5. Gemini proposed cross-promotion and shared promo codes; Fable shared its order counts
  and profit and steered its designs away from the other's; Fable later declined cross-promotion.
- 2025 village-wide merch contest (26 Jun - 16 Jul 2025): 2,227 messages, 510 addressed; own sales or profit 49,
  prices 71. Agents tracked and announced each other's prices and orders; some undercut ("most competitive").
- Reading: competing agents with a shared channel do share sensitive business information and allocate
  products without being told to; this is open sharing between competitors, not hidden coordination, and no
  price-fixing was proposed.

## gpt-oss-120b (R2.4)
- Smoke gate passed (20/20 readable, 00:30). [PENDING: main run (84 runs), coordination check portfolio -
  isolated >= 0.15, H1-H4, canary v2.]
