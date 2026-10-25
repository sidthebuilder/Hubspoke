# Appendix A: Limitations and dual-use / ethical considerations

(Facts for the author to write from; updated 25 Oct after round 2. Numbers: report/table_models.md and
report/notes_round2.md.)

## What this does and does not establish
- Three open-weight models, one at a time. In every run, both sellers and the advisor are the same model (Qwen2.5-72B
  4-bit, Llama-3.1-70B 4-bit, or gpt-oss-120b). The advice-layer price lift appeared on Qwen and Llama and not on
  gpt-oss-120b, so it is model-dependent. Frontier API models were not tested.
- The hub positive control failed on all three models. Told to maximise both clients' combined profit, with both
  clients' live data, the advisor did not price above the firewalled advisor (portfolio - isolated: Qwen -0.05,
  Llama +0.02, gpt-oss +0.07; registered bar for a capable hub: +0.15). Our nulls for data pooling (H1) therefore say
  little about a more capable or more strategic advisor.
- Short horizon. 40 periods, outcome over 26-40. Some runs may still be moving at period 40.
- Duopoly, one market, one demand model, two clients per advisor. Real hubs serve hundreds of clients.
- Our "aged" condition borrows the idea of the RealPage settlement (only old competitor data), not its exact
  terms: the proposed decree bans competitors' nonpublic data in runtime pricing and allows only data aged
  12+ months for model training. For an LLM advisor, data in the prompt is the runtime input.
- Design choices shaped the baseline. Pilot 1 showed agents anchor on a Nash-price status quo; the final design
  starts every run from 5 random pre-periods. Every condition of a seed shares the same pre-periods, so comparisons
  between conditions are fair, but levels are not universal: LLM sellers stay near where they start (start-high minus
  start-low, solo: +0.39 Qwen, +0.37 Llama). The start-low test shows the advisor's lift is not only inertia.
- The reasoning field (agents write before pricing) was added after pilot 2's first design failed the gate.
  It changes behaviour; we report it as part of the design, not as a neutral measurement.
- Leak measurement. The exact-number rule misses paraphrased leaks (human 17 of 24 reveals vs rule 5 of 24 in the
  shared arm of canary v1). The judged measure is validated against one blind human rater, the author, who knew the
  hypotheses (judge vs human kappa 0.87 on 48 notes); a second, independent human rater would be stronger. The judge
  is Qwen2.5-72B, the same model as the Qwen advisor whose notes it reads. Its false-alarm rate on control notes was
  low on Qwen's notes (0-8%) and high on Llama's (17-29%).
- The canary facts are our own plants in logged states (counterfactual sessions), not leaks that arose in the main
  runs; they show the channel exists and what moves through it, not how often a real hub would leak.
- 12 runs per condition gives exact tests, but the 95% intervals for H1-H3 still allow differences of about
  0.2 index points either way; "no effect" here means "no effect we could detect". Averaged over Qwen and Llama
  (exploratory), the one-sided 95% upper bound for pooled - isolated is +0.07.
- The fork test's net gain mixes two things: the rival's reaction and the deviator's own later choices (its
  agent keeps the lower price). The excess-cut measure isolates the rival's reaction.
- Exploratory additions (the `separate` control, descriptive measures, the live-recommendation replay, the
  price-gap statistic, the round-2 robustness checks, cross-model averages, the audit tool) were added after we saw
  results; they are labelled exploratory. The price-gap statistic failed both of its out-of-sample checks (Llama
  AUROC 0.65 vs a registered 0.75; gpt-oss 0.39).
- One interim look at a blind run (11:46, 25 Oct; logged in PREREGISTRATION.md) and one overnight interruption of a
  run, resumed from the cache.
- The AI Village field check is descriptive: keyword rules plus reading, one reader, no test, two cases.

## Dual use
- What could help a colluder: the finding that a shared notebook carries a client's plans to its competitor, and
  that a prompt rule or owner tags do not stop it. Hub vendors already know their architectures; regulators and
  auditors mostly do not, so the balance favours publishing.
- What we withhold: nothing that is not already in the code. We do not tune prompts to maximise collusion,
  and we release no optimised "collusive" advisor prompt. The portfolio positive control states its goal
  openly (maximise combined profit), which is the conduct antitrust law already prohibits.
- How the work could make collusion harder to detect: a vendor could learn from the audit test to avoid repeating
  planted facts while still using them. Our influence measure (does the advice move, even without quoting, against
  a control session) is designed to catch that; the replay needs vendor cooperation.
- No real firms, prices or personal data are involved. The AI Village data are used under AI Digest's research
  terms: only aggregate counts and paraphrases are reported, and no message text is in the repository.
