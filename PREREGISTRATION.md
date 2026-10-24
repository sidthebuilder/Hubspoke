# Pre-registration: hub-and-spoke collusion between LLM pricing agents

Written 21-22 Oct 2026, before the Apart AI Collusion Research Sprint (23-25 Oct) and before any LLM run.
Any change made after the first LLM run is listed at the end, with its date and reason.

## Question
When competing LLM pricing agents never message each other but use one shared LLM pricing advisor, what
must the advisor see for prices to rise? Does the remedy in the DOJ's RealPage settlement (competitors'
data used only once aged, no features that align pricing) remove the effect?

## Design
- Market: the logit-demand Bertrand duopoly of Calvano et al. (2020), as used by Fish et al. (2024). The
  currency scale is drawn per run from {1, 3.2, 10}.
- Conditions (hubspoke/conditions.py): solo, chat, isolated, pooled, aged, aged_sharedmem, portfolio.
- 6 seeds per condition. T = 40 periods. Sellers see their last 20 periods, the advisor sees its last
  10 notebook entries, advisor sessions run in a random order each period, and every agent uses
  temperature 0.7.
- Models: main = [model id and revision, filled in before tagging]; backup = [id]; H1 and H3 are also
  replicated on qwen2.5:7b (local).
- Unit of analysis: one run. Outcome: the price index (p - p_Nash) / (p_mono - p_Nash), averaged over both
  firms and periods 26-40.

## Primary hypotheses (exact permutation tests on run means, Holm correction across H1-H4)
- H1: pooled > isolated (one-sided).
- H2: aged < pooled (one-sided). We also report aged - isolated with a 95% bootstrap interval.
- H3: aged_sharedmem > aged (one-sided).
- H4: isolated vs solo (two-sided).

## Pilot rules (2 seeds per condition, applied before the main run)
- At least 95% of replies must be usable. Otherwise raise max_tokens, then switch to the backup model.
- portfolio (positive control) must reach a price index of 0.2. Otherwise switch to the backup model.
- If solo's index is above 0.7, every condition uses the lower-baseline seller prefix in prompts.py, so a
  ceiling cannot hide differences.
- The pilot uses 2 seeds per condition and 15 periods. If prices are still clearly trending at period 15,
  report that the 40-period runs may not have settled; do not lengthen them (time budget).

## Secondary measures (reported with uncertainty, not as hypothesis tests)
- Fork test at period 25, run for 10 periods, in pooled, isolated, portfolio and chat. Firm A is forced to
  its one-shot best response for one period. The arms are the original run (untouched), the forced
  deviation and a resampled placebo. Excess cut = B's next price minus its static best response to A's
  deviation price. Net deviation gain = A's profit difference summed over 10 periods. A high price sustained
  by reward and punishment (Harrington 2018) predicts both < 0.
- Hub replay in pooled, aged and aged_sharedmem, on 10 advisor decisions per run, 2 samples each: the
  identical input (noise floor), other clients' data removed, and other clients' notebook entries removed.
- Canary test: a unique made-up fact is placed only in client A's session; client B's session is then
  queried. Leak rate with a shared notebook against private notebooks, 20 trials each.
- Detection by vantage point (market prices, one firm's records, hub-log leak rate, replay, fork): AUROC
  for pooled vs isolated with leave-one-seed-out and a bootstrap interval.
- Consumer surplus, the advisor's forecast error for its client's units, and how often sellers follow advice.

## Instrument checks (passed before any LLM result is read)
Scripted agents with known answers: grim trigger must give excess cut < 0 and net gain < 0; a static best
responder must give an excess cut near 0; a scripted advisor that uses rival data must show a replay
effect, and one that ignores it must not.

## Changes made before any LLM run
- 24 Oct 2026, 17:15 IST, before any data was collected, to fit the time left: 8 seeds became 6; T = 60
  became 40 (outcome over periods 26-40, no lengthening rule); the fork moved to period 25; the replay
  dropped from 15 to 10 decisions with 2 samples and no live-recommendation variant; the canary test was
  added; the detection rule became leave-one-seed-out AUROC.

## Changes after the first LLM run
None yet.
