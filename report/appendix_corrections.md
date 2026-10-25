# Appendix E: Corrections log (what went wrong and what we changed)

Times IST, 24 Oct 2026. Full detail and the commits are in PREREGISTRATION.md and the git history.

1. **Opening prices (smoke test, 19:09).** With no history, the advisor opened at 10x unit cost and prices hit
   the $5 cap. We added a period 0 at the Nash price before the pilot.
2. **Anchoring (pilot 1, 19:21).** With that period 0, every agent in one seed stayed at the Nash price for all
   15 periods, the portfolio advisor included, so the positive control failed the gate. The registered rule
   said to switch model; we judged the cause to be our design, and registered two replacement designs and a
   selection rule before running them. This deviation is ours, and we report it.
3. **Selection (pilot 2, 19:34).** The first replacement (random pre-periods) failed the gate; the second
   (plus a reasoning field) passed, narrowly (portfolio +0.206 against a 0.2 bar; one seed +0.39, the other
   +0.02). We fixed the measurement window for the gate while the first design's runs were finishing and
   before any run of the second had finished.
4. **Power (19:40).** The pilots varied widely between seeds, so we doubled the main sample from 6 to 12
   seeds per condition before the main run, and ran it blind (the run log shows only reply health).
5. **Instrument bugs caught by the scripted checks.** The grim-trigger seller treated the pre-game period
   as a deviation (fixed: it ignores periods before 1). The myopic fork check gave an excess cut of 4e-5
   instead of 0, because prices are stored to 4 decimals (tolerance documented in the test).
6. **Dropped before data.** The advisor's forecast error (its reply has no forecast field) and a local 7B
   replication (no local model server).
7. **Operational, no effect on data.** A Windows text-encoding error in the deploy script; two pilot
   processes writing one log file (one pilot was restarted before it made any call).
[Add anything found during analysis or writing.]
8. **A race on one fork (21:01).** A stuck terminal released two queued fork jobs at once, so three processes
   computed the fork of pooled seed 2 at the same moment and could have stored different replies for the
   same cache key. We deleted that fork file and recomputed it from the cache alone; `verify` then checks
   every fork against the cache.
9. **Exploratory additions after seeing the main result** (each logged in PREREGISTRATION.md with its time):
   the `separate` control, descriptive measures (explore.py), the live-recommendation replay, and a hold-out
   test of the price-gap finding on the Llama replication, registered before looking at Llama outcomes.

Round 2 (25 Oct, IST):

10. **A registered statement we departed from.** The Llama registration said the replication would never be
    pooled with the main results. Two exploratory checks average over Qwen and Llama (robust.py); they are
    labelled as a departure, and every registered test is reported per model.
11. **An interrupted run (01:16-10:45).** The local machine that drives the runs went offline overnight during
    the gpt-oss main run (10 of 84 runs done). The run was resumed with the same command; interrupted games
    replayed their cached replies first, so nothing was re-sampled. The run was blind throughout.
12. **A dropped exploratory metric.** explore.py measured how often the advisor's private reasoning named the
    other firm (Qwen: isolated 0.81, pooled 0.43, aged 0.95, aged + shared notebook 0.71, portfolio 0.50,
    separate 0.87). Every advisor sees the rival's posted price, so naming the rival says nothing about the use
    of confidential data; we removed it rather than interpret it.
13. **The judge's false-alarm baseline was added after the judge was registered** (before any judge output):
    the judge also reads Firm B's control note from the same state, which cannot contain Firm A's fact. The
    registered measure and tests are unchanged.
14. **Our own predictions.** Kiro's start-low prediction (inertia, p = 0.65) was wrong on both models. Every
    prediction and its outcome, with a Brier score, is in Appendix D (report/appendix_predictions.md).
15. **A blinding slip (11:46).** With about 62 of 84 gpt-oss runs finished, an exploratory script computed paired
    tests on them and the AI assistant read the interim values (logged in PREREGISTRATION.md). No analysis choice
    changed afterwards; the scripts now refuse to read a run until it is complete.