# hubspoke: can a shared AI advisor make competing agents collude without talking?

Two LLM pricing agents sell competing products. They never message each other, but both use the same LLM
pricing advisor (the hub). We vary only what the advisor can see and remember, and measure prices, whether
the advisor *uses* what it sees (hub replay), whether a planted secret travels between clients (canary test),
and whether high prices are held up by punishment (fork test).

Submission to the Apart Research AI Collusion Research Sprint (23-25 Oct 2026). Author: Shashank Kumar.
The report is in `report/`. Pre-registration and every change to it: `PREREGISTRATION.md`.

## Conditions
| condition | what the advisor sees and remembers | role |
|---|---|---|
| solo | no advisor, no messages | baseline |
| chat | no advisor; sellers message each other | positive control |
| isolated | only the current client's data; one notebook per client | firewall (Gibson v. Cendyn) |
| pooled | every client's data up to last period, its own recommendations to the others this period, one shared notebook | RealPage as alleged |
| aged | other clients' data only once 12 periods old; one notebook per client | the RealPage settlement's ageing rule |
| aged_sharedmem | as aged, but one shared notebook | the memory gap |
| portfolio | as pooled, but told to maximise all clients' combined profit | positive control for the hub |
| separate (exploratory) | as isolated, but each advisor is told it advises only one firm | added after the main analysis |

Market: logit-demand Bertrand duopoly of Calvano et al. (2020), as used by Fish et al. (2024); price index
0 = one-shot Nash price, 1 = joint-profit price. Model: Qwen/Qwen2.5-72B-Instruct-AWQ (revision
698703eae6604af048a3d2f509995dc302088217) on vLLM 0.21.0, one H100 on Modal, temperature 0.7, every role.
12 seeds per condition, 40 periods, outcome = mean price index over periods 26-40.

## Rebuild every number without a GPU or API key
Every model reply is stored in `results/cache.jsonl.gz` (rebuilt into `results/cache.sqlite` by
`cache_io.py import`), keyed by a hash of the model, the full prompt, the sampling settings and a sample key.
Replaying from the cache reproduces every run exactly.
```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt     (Linux/macOS: .venv/bin/python)
.venv\Scripts\python cache_io.py import                      restores results/cache.sqlite from the export
.venv\Scripts\python -m pytest -q tests                      instrument checks with scripted agents
.venv\Scripts\python -m hubspoke validate                    writes results/validate.txt
.venv\Scripts\python -m hubspoke analyse                     tables, tests, figures, results/main/numbers.json
.venv\Scripts\python -m hubspoke verify                      replays every run from the cache (offline) and
                                                             recomputes the headline numbers with numpy/scipy
```
`verify` sets `HUBSPOKE_OFFLINE=1`: any reply missing from the cache is an error, so it proves the run files
follow from the stored replies. It writes `results/verify_main.txt`.

## Run it again from scratch (needs Modal)
```
python -m modal setup
python modal_secret.py        creates the endpoint key, stores it in .env and in the Modal secret (never printed)
python modal_deploy.py        deploys modal_serve.py and writes the URL to .env
python -m hubspoke smoke
python -m hubspoke run --T 40 --out main --start history --reasoning --blind
python -m hubspoke forks ; python -m hubspoke replay ; python -m hubspoke canary
python -m hubspoke analyse ; python -m hubspoke verify
```
New runs draw new samples only if the cache file is removed or renamed.

## Files
- `hubspoke/market.py` demand, benchmarks; `conditions.py` the seven conditions; `prompts.py` every prompt;
  `agents.py` observations and LLM policies; `game.py` the repeated game; `llm.py` client and cache;
  `scripted.py` scripted agents with known answers; `forks.py`, `replay.py`, `canary.py` the instruments;
  `stats.py` exact permutation tests, Holm, bootstrap, AUROC, Wilson; `analysis.py`; `verify.py`; `cli.py`.
- `results/pilot*`: the three pilots (see PREREGISTRATION.md for what each one decided).
- `results/main_llama`: the pre-registered replication on Llama 3.1 70B (4-bit). `results/livereplay` and
  `results/main/exploratory.*`: exploratory measures added after the main analysis (`hubspoke/explore.py`).
- `finalize.ps1`: rebuilds every table, figure and check in order (Windows; the commands inside run anywhere).
- `results/main`, `results/forks`, `results/replay`, `results/canary`: one JSON file per run, with every
  prompt input and raw reply. `results/figures`: the report's figures. `results/handcheck.csv`: the sample
  for the second rater.
- Round 2 (registered in PREREGISTRATION.md, R2.1-R2.5, before any of its runs): `canary2.py` (four kinds of
  planted fact x four notebook setups) -> `results/canary2*`; `judge.py` (disclosure judge and the blind human
  sheet `results/handcheck_canary.csv`) -> `results/judged.json`, `results/judge_validation.*`; start-low runs
  -> `results/startlow*`; the gpt-oss-120b replication -> `results/main_gptoss`; `village.py` (aggregate counts
  from the AI Village dataset; raw text is never written to the repository). `round2.py` runs the registered
  round-2 analyses; `robust.py` (exploratory: paired tests, a cross-model bound, excess raise, audit power) ->
  `results/robust.*`; `figs2.py` -> `results/figures/fig2_notebook.png`, `fig3_checks.png`.

## Preexisting code (written 19-22 Oct 2026, before the sprint began on 23 Oct)
The git history starts on 24 Oct, so it cannot show this split; it is declared here and in the report.
- Complete before the sprint: `market.py`, `conditions.py`, `parsing.py`, `__init__.py`, `__main__.py`.
- Partly before the sprint: in `prompts.py`, the seller prompts and `advisor_system`; in `llm.py`, the
  `Cache` class and `_seed`; in `agents.py`, the observation and action dataclasses.
- Also before the sprint: the first version of `PREREGISTRATION.md` and the project plan.
Everything else was written during the sprint: the advisor's user prompt, the LLM client, the LLM policies,
the game engine, scripted agents, every instrument, the statistics, the analysis, the tests, the Modal
server and every LLM run. Sprint edits to the preexisting files (for example the pre-periods and the
reasoning field) are in the git history.

## AI use
The code, analysis and first drafts of the text were written with an AI coding assistant (Kiro) working under
the author's direction; the author chose the research question and design, made the decisions recorded in
PREREGISTRATION.md, and checked the results and the final text. The dated predictions in PREREGISTRATION.md
were made by the assistant and are labelled as such.

## Safety
The endpoint key lives in `.env` (git-ignored) and in a Modal secret; it is never printed or logged.
