# Notes for writing the report (facts only; every one checked on 24 Oct 2026)

These are raw facts and sources for the author to write from. The final text must be the author's own words
(sprint rule: "The report itself has to be your team's own writing about your team's own work").

## Sources opened and what each one says (paraphrased)
- Fish, Gonczarowski, Shorrer, "Algorithmic Collusion by Large Language Models", arXiv:2404.00806.
  LLM pricing agents in oligopoly settings reach supracompetitive prices and profits quickly and without
  being told to; small wording changes in the prompt change how high prices go.
- Calvano, Calzolari, Denicolò, Pastorello (2020), "Artificial Intelligence, Algorithmic Pricing, and
  Collusion", AER 110(10). The logit-demand environment we use (a = 2, a0 = 0, mu = 0.25, c = 1); our code
  reproduces its benchmarks: Nash price 1.473, joint-profit price 1.925 (tests/test_core.py).
- "Supracompetitive Pricing Under AI Monoculture", arXiv:2601.01279 (submitted by Shengyu Cao, v3 June 2026).
  Theory: two sellers take recommendations from one shared AI that is retrained on outcomes; above a
  fidelity threshold, supracompetitive pricing becomes a stable outcome. No LLM-agent experiment.
- "On the Fragility of AI Agent Collusion", arXiv:2603.20281 (2026; submitted by Gerry Tsoukalas).
  Heterogeneity between LLM agents (patience, data access) weakens collusion: price lift falls from 22% to
  10% (patience) and to 7% (asymmetric data access).
- "Mitigating Emergent Collusion in LLM Pricing Agents", arXiv:2609.13037 (Sept 2026). Reproduces Fish et al.'s
  prompt effect with DeepSeek-V3.1; tests a prompt warning, a Harrington-style damages regulator and a random
  entrant.
- "Faithful yet Collusive", arXiv:2609.18346 (Findings of EMNLP 2026). Across nine LLMs, how collusive a model
  is and how faithful its chain of thought is come apart; CoT monitoring alone is not a safeguard.
- "Who Leads and Who Collects: Algorithmic Collusion in Markets of Heterogeneous Language Models",
  arXiv:2610.11256 (8 Oct 2026). Four providers' models in a four-firm logit market; collusion depends on the
  model. No shared advisor.
- Harrington, "Hub-and-Spoke Collusion with a Third-Party Pricing Algorithm", J. Industrial Economics (2026),
  pdf at joeharrington5201922.github.io/pdf/jie26.pdf. Theory of a third party coordinating competitors'
  prices through its algorithm. (Open and read the PDF before citing specifics.)
- DOJ press release, 24 Nov 2025, "Justice Department Requires RealPage to End the Sharing of Competitively
  Sensitive Information and Alignment of Pricing Among Competitors" (justice.gov/opa/pr/...). The proposed
  consent judgment would (among other things) stop the software using competitors' nonpublic data to set
  prices *in runtime operation*; limit *model training* to nonpublic data aged at least 12 months; and remove
  or redesign features that aligned pricing between competing users.
  -> Careful framing for our `aged` condition: the 12-month ageing rule in the settlement is about training
  data; runtime use of competitors' nonpublic data is banned outright. For an LLM advisor, data in the prompt
  is the runtime input, so `aged` is our analogue of "only old data", not a literal copy of the decree.
- Gibson v. Cendyn Group, No. 24-3576 (9th Cir. 15 Aug 2025). Competing Las Vegas hotels independently
  licensed the same revenue-management software; the court affirmed dismissal. Per the Axinn summary, the
  software used only public data and each hotel's own data, and the court said its analysis might differ if
  the software had shared competitors' confidential information among licensees. -> our `isolated` condition.

## Facts about our own runs (fill the numbers from numbers.json, never by hand)
- Model: Qwen/Qwen2.5-72B-Instruct-AWQ, revision 698703eae6604af048a3d2f509995dc302088217; vLLM 0.21.0; one
  H100 on Modal; temperature 0.7; JSON mode; every agent and the advisor use the same model.
- Main: 7 conditions x 12 seeds x 40 periods, design D2 (5 random pre-periods, reasoning field).
- Pilots: pilot 1 (period-0 Nash start) failed G1; pilot 2 D1 failed, D2 passed (portfolio +0.206).
- Instrument checks with scripted agents: results/validate.txt.

## What judges asked for (from the rubric and the September winner's reviews)
- A baseline beside every headline number.
- Rank the detection vantage points by how well they work (AUROC), do not just list them.
- A second rater on any judged label, with kappa (the hand check: results/handcheck.csv).
- One usable artifact (the canary audit test).
- Corrections logged; honest AI-use statement; preexisting code marked.
