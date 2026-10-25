# hubspoke: can a shared AI advisor make competing agents collude without talking?

Two LLM pricing agents sell competing products. They never message each other, but both use the same LLM
pricing advisor (the hub). We vary only what the advisor can see and remember, and measure prices, whether
the advisor *uses* what it sees (hub replay), whether a planted secret travels between clients (canary test),
and whether high prices are held up by punishment (fork test).

Submission to the Apart Research AI Collusion Research Sprint (23-25 Oct 2026). Author: Shashank Kumar.
The report is in `report/`. Pre-registration and every change to it, with times: `PREREGISTRATION.md`.

## Conditions
| condition | what the advisor sees and remembers | role |
|---|---|---|
| solo | no advisor, no messages | baseline |
| chat | no advisor; sellers message each other | positive control |
| isolated | only the current client's data; one notebook per client | firewall (Gibson v. Cendyn) |
| pooled | every client's data up to last period, its own recommendations to the others this period, one shared notebook | RealPage as alleged |
| aged | other clients' data only once 12 periods old; one notebook per client | an ageing rule modelled on the RealPage settlement |
| aged_sharedmem | as aged, but one shared notebook | the memory gap |
| portfolio | as pooled, but told to maximise all clients' combined profit | positive control for the hub |
| separate (exploratory) | as isolated, but each advisor is told it advises only one firm | added after the main analysis |

Market: logit-demand Bertrand duopoly of Calvano et al. (2020), as used by Fish et al. (2024); price index
0 = one-shot Nash price, 1 = joint-profit price. 12 seeds per condition, 40 periods, outcome = mean price index
over periods 26-40. Every role in a run (both sellers and the advisor) uses the same model, temperature 0.7, on
vLLM 0.21.0 and one H100 on Modal. The disclosure judge (round 2) is Qwen2.5-72B at temperature 0 for every
model's notes.

| model (pinned Hugging Face revision) | results |
|---|---|
| Qwen/Qwen2.5-72B-Instruct-AWQ (698703eae6604af048a3d2f509995dc302088217), main model | `results/main` and every instrument |
| hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4 (2123003760781134cfc31124aa6560a45b491fdf) | `results/main_llama`, `startlow_llama`, `canary2_llama` |
| openai/gpt-oss-120b (b5c939de8f754692c1647ca79fbf85e8c1e70f8a), default reasoning effort | `results/main_gptoss`, `canary2_gptoss` |

## Rebuild every number without a GPU or API key
Every model reply is stored in `results/cache.jsonl.gz` (rebuilt into `results/cache.sqlite` by
`cache_io.py import`), keyed by a hash of the model, the full prompt, the sampling settings and a sample key.
Replaying from the cache reproduces every run exactly.
```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt     (Linux/macOS: .venv/bin/python)
.venv\Scripts\python cache_io.py import                      restores results/cache.sqlite from the export
.venv\Scripts\python cache_io.py check                       confirms the database matches the export exactly
powershell -File finalize.ps1                                every step below, in order (log: finalize_log.txt)
```
The steps, one python command each (set `HUBSPOKE_OFFLINE=1` first so no model is ever called):
```
python -m pytest -q tests                          instrument checks with scripted agents (known answers)
python -m hubspoke validate                        results/validate.txt
python -m hubspoke analyse --src main              registered H1-H4: results/main/numbers.json, table1.md
python -m hubspoke.explore main                    exploratory descriptives (also main_llama, main_gptoss)
python -m hubspoke.round2 startlow startlow main   start-low test R2.3 (also startlow_llama main_llama)
python -m hubspoke.round2 canary2 canary2          canary v2, R2.1 (also canary2_llama, canary2_gptoss)
python -m hubspoke.round2 judge                    judge vs blind human rater, R2.2
python -m hubspoke.round2 hub main_gptoss          coordination check, R2.4
python -m hubspoke.robust                          exploratory robustness checks: results/robust.md
python -m hubspoke.figs2                           round-2 figures
python -m hubspoke.audit --demo                    the audit tool, run on our own canary trials (results/audit_demo)
python report/table_models.py                      the main tables, every model side by side
python report/predictions_table.py                 every dated prediction and how it resolved
python -m hubspoke verify --src main               replays every run from the cache and recomputes the numbers
```
`verify` (any result folder, or `--src judge`) refuses to call a model: a reply missing from the cache is an
error, so it shows the result files follow from the stored replies. It then recomputes the registered numbers
independently (numpy, scipy's exact permutation and Fisher tests) and writes `results/verify_<folder>.txt`.

## Run it again from scratch (needs Modal)
```
python -m modal setup
python modal_secret.py        creates the endpoint key, stores it in .env and in the Modal secret (never printed)
python modal_deploy.py        deploys modal_serve.py and writes the URL to .env (deploy_llama.ps1, deploy_gptoss.ps1
                              set the model variables for the other two models)
python -m hubspoke smoke
python -m hubspoke run --T 40 --out main --start history --reasoning --blind
python -m hubspoke forks ; python -m hubspoke replay ; python -m hubspoke canary ; python -m hubspoke canary2
python -m hubspoke run --conditions solo isolated pooled portfolio separate --out startlow --start history_low --reasoning --blind
python -m hubspoke judge --v1 --folders canary2
```
Add `--config configs/modal_llama70b.json` (or `modal_gptoss120b.json`) and a different `--out` for the other
models. New runs draw new samples only if the cache file is removed or renamed.

## Files
- `hubspoke/market.py` demand, benchmarks; `conditions.py` the conditions; `prompts.py` every prompt;
  `agents.py` observations and LLM policies; `game.py` the repeated game; `llm.py` client and cache;
  `scripted.py` scripted agents with known answers; `forks.py`, `replay.py`, `canary.py` the instruments;
  `stats.py` exact permutation, sign-flip and Fisher tests, Holm, bootstrap, AUROC, Wilson; `analysis.py`;
  `explore.py`; `verify.py`; `cli.py`.
- Round 2 (registered in PREREGISTRATION.md, R2.1-R2.5, before any of its runs): `canary2.py` (four kinds of
  planted fact x four notebook setups); `judge.py` (the disclosure judge and the blind human sheet
  `results/handcheck_canary.csv`); `round2.py` (the registered round-2 analyses); `robust.py` (exploratory
  checks); `figs2.py` (figures); `village.py` (aggregate counts from the AI Village dataset).
- `hubspoke/audit.py`: the hub audit test (report/audit_test.md) as a tool. An auditor collects client B's
  advice after a planted fact and from a matched session without it, in a CSV; the tool scores exact matches,
  judged reveals (Fisher test against the controls), the price shift, and the trials needed.
  `python -m hubspoke.audit sessions.csv [--judge configs/modal_qwen72b.json]`.
- `results/pilot*`: the three pilots (see PREREGISTRATION.md for what each one decided).
- `results/main`, `results/forks`, `results/replay`, `results/canary`, `results/livereplay`: one JSON file per
  run, with every prompt input and raw reply. `results/figures`: the report's figures.
- `results/handcheck.csv`, `results/handcheck_canary.csv`: the sheets for the blind human rater (the keys are
  in the matching `_key.csv` files; instructions in `report/HANDCHECK_INSTRUCTIONS.md`).
- `results/village/*.json`: aggregate counts only. The AI Village data (AI Digest, "AI Village dataset", 2026,
  https://theaidigest.org/village) are used under their research terms; no message text is in this repository.
- `report/`: drafts, the prompt appendix (generated), the predictions appendix (generated), `check_numbers.py`
  (traces every number in a text file to a result file).
- Dev helpers (not needed to rebuild): `status.py`, `cache_count.py`, `cache_by_model.py`, `peek.py`,
  `secret_scan.py` (checks that no key from `.env` is in any tracked file), `git_*.ps1`, `run_*.ps1`.

## Preexisting code (written 19-22 Oct 2026, before the sprint began on 23 Oct)
The git history starts on 24 Oct, so it cannot show this split; it is declared here and in the report.
- Complete before the sprint: `market.py`, `conditions.py`, `parsing.py`, `__init__.py`, `__main__.py`.
- Partly before the sprint: in `prompts.py`, the seller prompts and `advisor_system`; in `llm.py`, the
  `Cache` class and `_seed`; in `agents.py`, the observation and action dataclasses.
- Also before the sprint: the first version of `PREREGISTRATION.md` and the project plan.
Everything else was written during the sprint: the advisor's user prompt, the LLM client, the LLM policies,
the game engine, scripted agents, every instrument, the statistics, the analysis, the tests, the Modal
server and every LLM run. Sprint edits to the preexisting files (for example the pre-periods, the reasoning
field, the `separate` condition and the round-2 notebook setups) are in the git history.

## AI use
The code, analysis and first drafts of the text were written with an AI coding assistant (Kiro) working under
the author's direction; the author chose the research question and design, made the decisions recorded in
PREREGISTRATION.md, and checked the results and the final text. The dated
predictions in PREREGISTRATION.md were made by the assistant and are labelled as such.

## Safety
The endpoint key lives in `.env` (git-ignored) and in a Modal secret; it is never printed or logged.
`secret_scan.py` checks every tracked file for it before a commit.
