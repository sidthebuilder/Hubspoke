# Hubspoke

**Can a shared AI pricing advisor make competing agents collude without talking?**

Shashank Kumar. Produced during the Apart Research AI Collusion Research Sprint, 23-25 October 2026.

**Report (PDF): [Advice, Not Data](report/paper/main.pdf)**

This repository holds the code, the data and every model reply behind the sprint report. Every result can be
rebuilt from it offline, with no GPU and no API key; the one exception is the AI Village field check, whose
dataset is not re-hosted here.

## What the work is about

In hub-and-spoke collusion, competitors never talk to each other; a shared third party carries the coordination.
That is the shape of the leading algorithmic-pricing cases (RealPage; Gibson v. Cendyn), and of how LLM agents
are deployed: many agents call the same model, tool or memory store.

We test it with LLM agents. Two LLM sellers in a logit duopoly (Calvano et al. 2020) never message each other,
but both take advice from one LLM pricing advisor. We vary only what the advisor sees and remembers, in seven
pre-registered conditions:

| condition | what the advisor sees and remembers | role |
|---|---|---|
| solo | no advisor, no messages | baseline |
| chat | no advisor; the sellers can message each other | positive control |
| isolated | only the current client's data; one notebook per client | firewalled advisor (as in Gibson v. Cendyn) |
| pooled | both clients' data, its recommendations to the other client, one shared notebook | RealPage as alleged |
| aged | the other client's data only once 12 periods old; one notebook per client | an ageing rule modelled on the RealPage settlement |
| aged_sharedmem | as aged, but one notebook shared across clients | the memory channel an ageing rule leaves open |
| portfolio | as pooled, but told to maximise both clients' combined profit | positive control for the advisor |
| separate (exploratory) | as isolated, but each advisor is told it advises only one firm | added after the main analysis |

Each condition has 12 runs of 40 periods; the outcome is the mean price index over periods 26-40 (0 = one-shot
Nash price, 1 = joint-profit price). In every run, both sellers and the advisor are the same open-weight model.
The seven conditions were run on three models: Qwen2.5-72B-Instruct (the main model), Llama-3.1-70B-Instruct and
gpt-oss-120b. On Qwen, instruments separate what the advisor has from what it uses (hub replay), test for
punishment (fork test), and plant made-up confidential facts with one client to see whether they reach the other
(canary test). A second, pre-registered round added a start-low test (Qwen, Llama), a larger canary test with
four kinds of fact and four notebook setups (all three models), a disclosure judge checked against a blind human
rater, the gpt-oss replication, and a descriptive check of the AI Village dataset.

## Findings

1. **An advice layer kept prices higher on two of three models, and giving it the rival's data did not raise
   them further.**
   - Firewalled shared advisor (isolated) against no advisor (solo): +0.29 on Qwen (exact permutation test,
     p = 0.002), +0.44 on Llama (p = 0.009), +0.02 on gpt-oss-120b (p = 0.77).
   - The lift is not only prices staying where they start: from pre-periods below the Nash price, the advisor
     again priced above sellers without one (+0.18 on Qwen, p = 0.057; +0.18 on Llama, p = 0.050). By the
     registered decision rule, a difference of +0.15 or more means "the advisor raises prices". Prices still
     ended below Nash.
   - Pooling the rival's confidential data did not raise prices over the firewalled advisor on any model
     (pooled - isolated: Qwen -0.10, Llama -0.04, gpt-oss +0.02). On Qwen, re-asking logged sessions with the
     rival's data removed moved the recommended price by 0.003 index points or less on average (mean absolute
     change 0.003-0.015), about as much as re-asking the unchanged session (0.002-0.017): the advisor had the
     data and did not use it.
   - On Llama, the aged condition priced 0.23 below pooled (Holm p = 0.047), the lowest of its advisor
     conditions; gpt-oss went the same way without significance (-0.12, p = 0.066) and Qwen did not (+0.08).
     Since pooling had not raised prices, this is not an ageing rule removing a pooling effect.
   - The advisor positive control failed on every model: told to maximise both clients' combined profit, it did
     not price above the firewalled advisor (portfolio - isolated: Qwen -0.05, Llama +0.02, gpt-oss +0.07,
     against the +0.15 that the registered capability check requires). These results therefore say little
     about a more capable or more strategic advisor.

2. **A shared notebook carries one client's price plans into its competitor's advice, and a confidentiality
   rule or owner tags did not stop it (Qwen).**
   - Over 384 canary trials on Qwen, the advisor wrote every planted price plan into its notebook (96 of 96), and
     few of the other planted facts (a supplier account code 0 of 96, a warehouse move 0 of 96, a cut in unit
     cost 6 of 96; counted by exact text).
   - With one shared notebook, the advice to the competitor revealed or relied on the plan in 18 of 24 trials,
     against 0 of 24 with private notebooks (Fisher p = 3.7e-8). A system-prompt rule not to use other clients'
     entries left 16 of 24; marking each entry with its owner left 15 of 24.
   - The competitor's recommended price rose after the plant (+0.13 index points, 95% CI +0.03 to +0.26), and
     not with private notebooks (-0.001).
   - These counts come from an LLM judge (Qwen2.5-72B, temperature 0). On 48 notes from the first canary test,
     it agreed with a blind human rating at Cohen's kappa 0.87. Matching the exact planted number agreed with the
     human at kappa 0.32: it missed 13 of the 18 notes the human counted.
   - The channel was weaker on Llama (shared 8 of 24, private 4 of 24, Fisher p = 0.32) and not detectable on
     gpt-oss-120b (5 of 24 against 3 of 24, p = 0.70). On these two models the judge also flagged 4 to 9 of 24
     control notes, from sessions where the plan could not appear.

3. **The usual canary would have passed the leaking advisor.** A planted random code never appeared in the
   advice to the competitor on any model (0 of 96 on each), while price plans did on Qwen. An audit should plant
   facts the advisor has a reason to keep, such as a planned price, and compare the competitor's advice with
   matched sessions without the plant. `hubspoke/audit.py` scores such an audit; at the rates observed on Qwen,
   6 planted price plans and 6 control sessions give 80% power with the judged reading (an exploratory
   calculation).

4. **Field check (descriptive).** In the AI Village dataset, two agents were given the same competitive goal
   ("Maximize profit from your own merch store"). In the open group chat, one shared its order counts and profit
   and steered its product designs away from the other's; the other proposed cross-promotion and shared promo
   codes. We found no proposal to align prices.

## What this does not show

- Three open-weight models, two sellers, one market, 40 periods. Frontier models were not tested.
- The canary facts were planted in logged states. The tests show the channel exists and what moves through it,
  not how often a deployed advisor would leak.
- The judge was checked against one human rater (the author), who saw neither the notebook setup nor any label,
  but knew the hypotheses. The judge is the same model as the Qwen advisor whose notes it reads.
- Several analyses were added after seeing results. They are labelled exploratory here, in the report and in
  `PREREGISTRATION.md`.

## Repository map

| path | what it is |
|---|---|
| `PREREGISTRATION.md` | hypotheses, tests, decision rules and dated predictions, written before the data; every later change, deviation and slip, with its time |
| `hubspoke/` | the package: market, conditions, prompts, agents, game, LLM client and reply cache, instruments (`forks`, `replay`, `canary`, `canary2`, `judge`), statistics, analysis (`analysis`, `explore`, `round2`, `robust`), figures, `verify`, `audit`, `village` |
| `tests/` | tests, most of them with scripted agents whose right answers are known |
| `configs/` | the three model configurations, with pinned Hugging Face revisions |
| `results/main`, `main_llama`, `main_gptoss` | one JSON file per run, with every prompt input and raw reply; `numbers.json`, `table1.md`, `exploratory.*` |
| `results/forks`, `replay`, `canary`, `livereplay` | the instruments, on the Qwen runs |
| `results/startlow`, `startlow_llama` | the start-low test |
| `results/canary2`, `canary2_llama`, `canary2_gptoss` | canary v2, one file per run, and `round2.md` |
| `results/judged.json`, `judge_validation.*` | the judge's labels and its agreement with the blind human rating |
| `results/handcheck_canary.csv`, `handcheck_canary_key.csv` | the blind rating sheet with the human labels, and its key |
| `results/robust.*`, `audit_demo/`, `village/` | exploratory checks; the audit tool run on our own trials; AI Village counts |
| `results/cache.jsonl.gz` | every model reply, keyed by a hash of the model, the prompt, the sampling settings and a sample key |
| `results/verify_*.txt` | output of the offline rebuild check, one file per result folder |
| `results/figures/` | figures |
| `results/pilot*` | the pilots that fixed the design (see `PREREGISTRATION.md`) |
| `report/paper/` | the report: `main.pdf`, its LaTeX source `main.tex`, `make_figures.py` (figures from `results/`), `check_text.py` (traces every number in the text to a result file) and `build.ps1` |
| `report/` | generated tables and appendices (`table_models.md`, `prompts_appendix.md`, `appendix_predictions.md`), the audit test, the corrections log, the hand-check instructions, and the scripts that generate the tables |
| `modal_serve.py`, `modal_deploy.py`, `modal_secret.py` | the vLLM server on Modal |
| `finalize.ps1`, `cache_io.py` | the full offline rebuild; moving the reply cache in and out of git |
| `scripts/` | the commands used to run, deploy and analyse |
| `dev/` | helpers used while running (progress, git, secret scan); not needed to rebuild |

## Reproduce the numbers

Python 3.11. From the repository root:

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt     (Linux/macOS: .venv/bin/python)
.venv\Scripts\python cache_io.py import                      rebuilds results/cache.sqlite from the export
.venv\Scripts\python cache_io.py check                       confirms the two hold the same replies
powershell -ExecutionPolicy Bypass -File finalize.ps1        Windows: every step below, in order (log: finalize_log.txt)
```

The steps, one command each, on any OS (set `HUBSPOKE_OFFLINE=1` first, so no model is ever called):

```
python -m pytest -q tests                            instrument checks with scripted agents
python -m hubspoke validate                          results/validate.txt
python -m hubspoke analyse --src main                registered tests H1-H4 (also main_llama, main_gptoss)
python -m hubspoke.explore main                      exploratory descriptives (also main_llama, main_gptoss)
python -m hubspoke.round2 startlow startlow main     start-low test (also startlow_llama main_llama)
python -m hubspoke.round2 canary2 canary2            canary v2 (also canary2_llama, canary2_gptoss)
python -m hubspoke.round2 judge                      judge against the blind human rating
python -m hubspoke.round2 hub main_gptoss            the advisor capability check
python -m hubspoke.robust                            exploratory robustness checks
python -m hubspoke.figs2                             figures
python report/table_models.py                        the main tables, all models side by side
python report/predictions_table.py                   every dated prediction and how it resolved
python -m hubspoke verify --src main                 replay from the cache and recompute (every folder; also --src judge)
```

The report PDF is rebuilt with `powershell -File report/paper/build.ps1` (needs a LaTeX install with pdflatex);
`python report/paper/check_text.py` lists any number in its text that no result file contains.

`verify` refuses to call a model: a reply missing from the cache is an error. It replays every run and
instrument from the stored replies, checks that the result files follow from them, and recomputes the
registered numbers independently (numpy, and scipy's exact permutation and Fisher tests). Pilot 1 used the first
design (one period 0 at the Nash price), whose prompts the final code no longer renders; `scripts/replay_pilot1.ps1`
replays it with the code of commit 5e15448, the version it ran with.

To run everything again from scratch, a Modal account is needed: `modal_secret.py` creates the endpoint key
(stored in `.env` and a Modal secret, never printed), `modal_deploy.py` deploys the server (`scripts/deploy_*.ps1`
set the model for each), and the `python -m hubspoke` commands `smoke`, `run`, `forks`, `replay`, `canary`,
`canary2` and `judge` produce the result folders (the exact options are in `PREREGISTRATION.md` and `scripts/`).
New samples are drawn only if the cache file is removed or renamed.

## Pre-registration and changes

`PREREGISTRATION.md` was committed before the first model call (commit 724bfec, 24 Oct 18:26 IST); round 2 was
added before its first run (d2dbc03, 25 Oct 00:06 IST). Every later change is listed there with its time,
including the deviations: the pilot design switch, two cross-model averages that the registration had ruled out,
an interrupted run resumed from the cache, and one interim look at an unfinished blind run.
`report/appendix_corrections.md` lists them with the bugs fixed along the way. Dated predictions with
probabilities are in `PREREGISTRATION.md`; `report/appendix_predictions.md` scores them against the results.

## Data provenance

- Models: Qwen/Qwen2.5-72B-Instruct-AWQ (revision 698703eae6604af048a3d2f509995dc302088217),
  hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4 (2123003760781134cfc31124aa6560a45b491fdf) and
  openai/gpt-oss-120b (b5c939de8f754692c1647ca79fbf85e8c1e70f8a), served with vLLM 0.21.0 on one H100 on Modal,
  temperature 0.7 for the agents and 0 for the judge.
- AI Digest, "AI Village dataset", 2026, https://theaidigest.org/village. It is used under AI Digest's research
  terms (analysis only, no training, no redistribution). Only aggregate counts are in `results/village/`; the
  dataset and its messages are not in this repository. To rerun `hubspoke/village.py`, request the data from
  AI Digest and set `HUBSPOKE_VILLAGE_DATA` to its folder.
- No real firms, prices or personal data are used.

## Responsible disclosure and dual use

The results show how a shared advisory memory can move one client's plans to a competitor, and that two
prompt-level fixes did not stop it. Vendors of such systems already know their own designs; auditors and
regulators mostly do not, so we publish the test and the tool. We release no prompt tuned to raise prices; the
one advisor told to maximise joint profit (portfolio) states that goal openly, which is conduct antitrust law
already prohibits. The endpoint key is never in the repository (`.env` is git-ignored, and `dev/secret_scan.py`
checks every committed file for it).

## Preexisting code

Written 19-22 Oct 2026, before the sprint began on 23 Oct. The git history starts on 24 Oct, so it cannot show
this split; it is declared here and in the report.
- Complete before the sprint: `market.py`, `conditions.py`, `parsing.py`, `__init__.py`, `__main__.py`.
- Partly before the sprint: in `prompts.py`, the seller prompts and `advisor_system`; in `llm.py`, the
  `Cache` class and `_seed`; in `agents.py`, the observation and action dataclasses.
- Also before the sprint: the first version of `PREREGISTRATION.md` and the project plan.

Everything else was written during the sprint: the advisor's user prompt, the LLM client, the LLM policies, the
game engine, the scripted agents, every instrument, the statistics, the analysis, the tests, the Modal server and
every model run. Sprint edits to the preexisting files (for example the pre-periods, the reasoning field, the
`separate` condition and the round-2 notebook setups) are in the git history.

## Citation

Shashank Kumar. Hubspoke: can a shared AI pricing advisor make competing agents collude without talking?
Apart Research AI Collusion Research Sprint, October 2026. https://github.com/sidthebuilder/Hubspoke

## License

Code (the `.py` and `.ps1` files): MIT, see `LICENSE`. Data and documents (the result files, the reply export,
the figures and the write-ups): CC BY 4.0, see `LICENSE-DATA.md`. Model outputs remain subject to each model's
license, and the AI Village counts to AI Digest's terms.
