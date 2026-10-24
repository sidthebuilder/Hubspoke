# Can a shared AI advisor make competing agents collude without talking?
## A data-ageing rule modelled on the RealPage settlement, and the memory channel it leaves open

Shashank Kumar (independent)

> DRAFT. Factual skeleton written with the AI assistant from the code and results. The author rewrites the
> prose in his own words before submission (sprint rule). Every number comes from results/main/numbers.json
> and is checked by report/check_numbers.py.

## Abstract
[written last, 150 words: question; design (7 conditions x 12 seeds, one open model); 3-4 headline numbers
with baselines; the canary audit test; the main caveat]

## 1 Introduction
- Collusion monitors mostly read what agents say to each other. In hub-and-spoke collusion the competitors
  never talk; a shared third party carries the coordination.
- That is the shape of the two leading algorithmic-pricing cases. RealPage: landlords' confidential data fed
  one rent-pricing system (DOJ settlement proposed Nov 2025). Gibson v. Cendyn (9th Cir. 2025): hotels used the
  same software, but it kept each hotel's data separate; the court found no claim and said the answer might
  differ if confidential data were shared among licensees.
- It is also how LLM agents are deployed: many agents call the same model, tool, advisor or memory store.
- Question: when two LLM sellers share one LLM advisor, what must the advisor see or remember for prices to
  rise? Does "only old data" (the settlement's ageing idea) remove the effect, and does a shared memory
  bring it back?
- Contributions: (1) the first LLM-agent experiment with a shared LLM pricing advisor, to our knowledge;
  (2) instruments that separate access from use (hub replay) and test for punishment (fork test), each
  validated on scripted agents with known answers; (3) a black-box canary test an auditor can run on any
  shared advisor; (4) a ranking of who can detect hub collusion (prices, one firm, hub logs, replay, fork).

## 2 Related work
| work | what it does | what we add |
|---|---|---|
| Calvano et al. 2020 (AER) | Q-learning pricing algorithms learn to collude; logit market | same market, LLM agents, a shared hub |
| Fish et al. 2024, arXiv:2404.00806 | LLM pricing agents reach supracompetitive prices; prompt wording matters | a shared advisor between the agents |
| arXiv:2601.01279 (2026) | theory: sellers share one AI model retrained on outcomes | an explicit hub with data and memory, tested with LLM agents |
| arXiv:2603.20281 (2026) | heterogeneity, including data access, makes LLM collusion fragile | data access through a third party |
| Harrington, JIE 2026 | theory of hub-and-spoke collusion with a third-party pricing algorithm | an LLM-agent test |
| arXiv:2609.13037 (2026) | interventions on Fish-style agents (warnings, damages, entrant) | the DOJ's actual remedy and its memory gap |
| arXiv:2609.18346 (2026) | chain-of-thought monitoring misses collusion | evidence when sellers never talk |
| arXiv:2610.11256 (2026) | markets of different LLMs, no shared advisor | one shared advisor |

## 3 Method
**Market.** Two sellers, logit demand (Calvano et al. 2020): quality a = 2, outside option a0 = 0,
differentiation mu = 0.25, unit cost c = 1, 100 customers. One-shot Nash price 1.473, joint-profit price 1.925.
Price index = (p - p_Nash) / (p_mono - p_Nash): 0 is competitive, 1 is the joint-profit price. Each seed draws
a currency scale (1, 3.2 or 10) so the model cannot recall benchmark prices; agents only see dollars.

**Agents.** Each seller is told to maximise its own firm's long-run profit, sees its last 20 periods (own
price, units, profit; rival's posted price) and writes a short plan for next period. The advisor is one model
that holds a separate session with each client every period, in random order; it recommends a price, writes
a note to the client, and writes a notebook entry; it sees its last 10 notebook entries. Prompts are neutral:
a test fails if any prompt contains words such as collude, cooperate, rival or punish, and sellers are not
told the other seller is an AI or uses the same advisor. Every agent first writes a reasoning field
(at most 60 words), then its price. Every run starts with 5 pre-periods of random prices (shared by all
conditions of a seed), so agents know the price scale.

**Conditions.** [table from README]

**Model.** Qwen2.5-72B-Instruct (4-bit AWQ, pinned revision) on vLLM 0.21.0, one H100, temperature 0.7, for
every role. 12 seeds per condition, 40 periods. Outcome: mean price index over periods 26-40.

**Pre-registration and pilots.** Hypotheses, tests and the pilot gate were committed before any data.
Pilot 1 failed the gate: every agent anchored on a single Nash-price period 0. Of the two replacements
registered before pilot 2, the first failed and the second passed; the rule fixed which one we use.
Every change, with its time and reason, is in PREREGISTRATION.md.

**Tests.** H1 pooled > isolated; H2 aged < pooled; H3 aged_sharedmem > aged; H4 isolated vs solo: exact
permutation tests on run means (12 vs 12, every split), Holm-corrected; 95% bootstrap intervals.

**Instruments (validated on scripted agents first; results/validate.txt).**
- Hub replay: 10 logged advisor decisions per run re-asked as-is (noise floor), with the other client's data
  blanked, and with other sessions' notebook entries removed; 2 samples each. Scripted check: an advisor
  that uses rival data shows an effect of -1.00; one that ignores it, 0.00.
- Fork test: from period 25, replay 10 periods with Firm A forced once to its one-shot best response, and a
  resampled placebo. Scripted check: grim trigger gives excess cut -0.18 and net gain -31.5%; a myopic best
  responder gives 0.00.
- Canary test: a unique fake fact (account code, or a planned price) planted in Firm A's session only; then
  read the advisor's session with Firm B. Scripted check: a leaking advisor is caught in 100% of trials with a
  shared notebook and 0% with private notebooks; a discreet one, 0%.

## 4 Results
Every number below is in results/main/numbers.json (pre-registered) or results/main/exploratory.json
(labelled exploratory). Main run: 84 runs, 11,520 model calls, 0 unreadable replies, 0 retries.

**4.1 Instruments first.** All scripted checks gave their known answers (results/validate.txt): grim trigger
is caught by the fork test (excess cut -0.18, net gain -31.5%), a myopic seller is not (0.00); the replay
gives -1.00 for an advisor that uses rival data and 0.00 for one that ignores it; the canary catches a leaking
advisor in every trial with a shared notebook and in none with private notebooks.

**4.2 Prices (Table 1).** Every run starts from the same five random pre-periods (mean index 0.55). Without an
advisor, prices fall to the competitive level (solo -0.04). Both positive controls stay above it: sellers who
can talk (chat 0.35) and an advisor told to maximise both clients' profit (portfolio 0.20). Every advisor
condition also stays above solo, between 0.16 and 0.27.
[Table 1: results_auto_main.md]

**4.3 Pre-registered tests.** H4 holds: a shared advisor that keeps each client's data separate (isolated)
raises the price index by +0.29 over solo (95% CI +0.14 to +0.45; exact p = 0.002; Holm 0.006). H1-H3 do
not: giving the advisor the other client's data, its own recommendations to the other client and a shared
notebook (pooled) does not raise prices over isolated (-0.10, CI -0.30 to +0.12); ageing the data (aged) does
not lower them relative to pooled; a shared notebook (aged_sharedmem) does not raise them over aged (+0.03).
Our dated predictions mostly failed (P1, P4 wrong; P2, P3 not scored; P5 right).

**4.4 What drives H4 (exploratory).** Two things point to advice as such, not sharing.
- *The `separate` control*: when each firm's advisor is told it advises only that firm, prices are as high as
  under the shared advisor (separate 0.36; separate - isolated +0.11, CI -0.09 to +0.30, p = 0.31; separate -
  solo +0.40, p = 0.0003).
- *Inertia*: advisor notes say "maintain", "stable" or "consistent" in 82-96% of sessions, sellers follow
  the advice in 96-100% of periods, and in periods 26-40 prices do not move at all in 69-89% of decisions
  under an advisor (91% with chat), against 36% in solo. Prices start high and the advice holds them there; solo sellers keep
  cutting (index change from the pre-periods: solo -0.58, isolated -0.29, separate -0.19).

**4.5 Access versus use.** Re-asking 10 logged decisions per run with the other client's data blanked changed
the recommended price by at most 0.003 index points on average in any condition (pooled -0.000, CI -0.002 to
+0.001), the same size as the noise floor from re-asking the identical input (0.002-0.017). Removing other
sessions' notebook entries did the same (pooled -0.001). The advisor had the rival's data and did not use it.
(Exploratory: removing the line that shows what it had just recommended to the other client moved pooled
recommendations only 0.002 further from that price.) What pooling did change is alignment: in periods 26-40
the two firms' prices differed by 0.006 index points under pooled against 0.131 under isolated (exploratory,
AUROC 0.93). This did not hold up out of sample: on the Llama replication the same statistic gave AUROC 0.65
(CI 0.40 to 0.86), below our registered prediction of 0.75.

**4.6 The canary test.** 48 trials per arm (12 runs x 2 periods x 2 facts). The advisor never wrote a planted
account code into its notebook (0 of 24 per arm), but it wrote every planted price plan into it (24 of 24 per
arm). With private notebooks that entry stayed with Firm A: 0 of 48 trials reached Firm B's session (95% CI 0
to 0.07) and B's advice did not move (+0.001 index). With one shared notebook all 24 price plans reached B's
session, 5 of 24 were told to B outright, B's own notebook entry repeated the plan in 20 of 24, and B's
recommendation moved by +0.091 index points on average over the 24 shared price-plan trials (CI +0.031 to
+0.166; only price-plan trials have a control session). One
example (aged_sharedmem, seed 0, period 36): Firm A's confidential note said it would charge $2.02 for five
periods; the advisor's note to Firm B read "Firm A has increased their price to $2.02. Testing a higher price
of $1.75 to gauge market reaction and potential profit increase", against $1.49 in the control session
without the plant. A's private plan, not any public price, moved B's advice.

**4.7 Punishment.** When Firm A was forced to undercut once in period 26 (by 0.10-0.22 index points), Firm B
cut back in the next period (B's price 0.085-0.130 below the original run; placebo copies moved by at most 0.02),
but by less than a myopic best response would: the excess cut was positive (isolated +0.085, CI +0.040 to
+0.131; chat +0.159; pooled +0.035 and portfolio +0.038, CIs include 0). Over 10 periods the undercut did not
pay in chat (-6.7%, CI -9.2 to -4.1) or pooled (-2.7%, CI -5.0 to -0.8), and was unclear under isolated (-1.4%,
CI -6.9 to +6.1). Rivals matched part of the cut and both prices then stayed put; nothing punished harder than
a myopic seller would.

**4.8 Who can tell pooled from isolated?** Ranked by AUROC over the 12 + 12 runs: fork test 0.64 (CI 0.39 to
0.86), hub replay 0.58, hub-log leak rule 0.50 (it never fired: the advisor did not quote the other client's
numbers in any note), one firm's own records 0.43, market prices 0.33 (pooled prices were, if anything,
lower). No pre-registered vantage point separates the two reliably; this matches H1's null.

**4.9 Replication on Llama 3.1 70B (pre-registered).** Same design, 84 runs, 0 unreadable replies. H4 replicates
(isolated - solo +0.44, CI +0.15 to +0.73, p = 0.009, Holm 0.034) and H1 again fails (-0.04). Unlike Qwen, the
aged condition priced lower: 0.23 below pooled (CI -0.44 to -0.05, p = 0.016, Holm 0.047) and 0.27 below
isolated. Because pooling did not raise prices in the first place (H1), this is not the ageing rule removing a
pooling effect: aged sits below even the firewalled advisor, and we have no explanation for it. aged_sharedmem
was 0.21 above aged (CI +0.01 to +0.42, p = 0.036, Holm 0.072, so not significant after correction). Chat (0.35)
stayed well above solo, but portfolio (0.41) was barely above isolated (0.39): the hub positive control failed
on Llama too.

## 5 Discussion
- What held in both models: an LLM advice layer kept prices above the no-advisor level (H4: +0.29 Qwen, +0.44
  Llama), and giving the advisor the rival's confidential data did not raise prices further (H1: -0.10, -0.04).
  RealPage-style remedies target what the hub knows about rivals; in our runs that knowledge was not where the
  price lift came from. The Cendyn line (shared software is fine if data stay siloed) would not catch the
  lift we saw, and on Qwen separate advisors produced it too (exploratory).
- What depended on the model: on Llama, aged runs priced below every other advisor condition and a shared
  notebook brought prices back up (p = 0.036 before correction, 0.072 after); since pooled was not above
  isolated, we cannot read this as the ageing rule removing a pooling effect. On Qwen neither moved prices.
- The shared notebook is a working channel either way. With one notebook, every planted price plan reached the
  rival's session and moved its advice; with private notebooks, none did. An ageing rule for data says nothing
  about memory shared across clients. The audit test (Appendix C) finds this from the outside in a handful of
  trials, which no price screen we tried could do.
- Mechanism: inertia, not punishment. Deviations did not pay over 10 periods, but because the rival matched part
  of the cut and both prices then stayed put, not because it cut harder than a myopic seller. By Harrington's
  definition (supracompetitive prices sustained by a reward-punishment scheme) this is not collusion, but it
  still costs consumers [CS numbers] relative to the no-advisor baseline.
- For auditors: price-level screens could not tell pooled from isolated; one public statistic (price gaps)
  could; the canary test reads the hub directly.

## Appendix A: Limitations and dual-use / ethical considerations
## Appendix B: Prompts (generated: report/prompts_appendix.md)
## Appendix C: The hub audit test (one page)
## Appendix D: Pre-registration, predictions and how they resolved
## Appendix E: Corrections log
## Appendix F: AI use and preexisting code
