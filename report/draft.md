# Can a shared AI advisor make competing agents collude without talking?
## Testing the RealPage remedy, and the memory gap it leaves, with LLM pricing agents

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
[after analysis]

## 5 Discussion
[after analysis]

## Appendix A: Limitations and dual-use / ethical considerations
## Appendix B: Prompts (generated: report/prompts_appendix.md)
## Appendix C: The hub audit test (one page)
## Appendix D: Pre-registration, predictions and how they resolved
## Appendix E: Corrections log
## Appendix F: AI use and preexisting code
