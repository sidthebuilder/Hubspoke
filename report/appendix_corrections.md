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
