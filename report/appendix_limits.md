# Appendix A: Limitations and dual-use / ethical considerations

## What this does and does not establish
- One model family. Every agent and the advisor are the same open model (Qwen2.5-72B, 4-bit). Results may
  differ for other models, especially frontier API models. [If the replication runs: second model results.]
- Short horizon. 40 periods, outcome over 26-40. Some runs may still be moving at period 40.
- Duopoly, one market, one demand model, two clients per advisor. Real hubs serve hundreds of clients.
- Our "aged" condition borrows the idea of the RealPage settlement (only old competitor data), not its exact
  terms: the proposed decree bans competitors' nonpublic data in runtime pricing and allows only data aged
  12+ months for model training. For an LLM advisor, data in the prompt is the runtime input.
- Design choices shaped the baseline. Pilot 1 showed agents anchor on a Nash-price status quo; the final
  design starts every run from 5 random pre-periods, which is itself a choice. Every condition of a seed
  shares the same pre-periods, so comparisons between conditions are fair, but levels are not universal.
- The reasoning field (agents write before pricing) was added after pilot 2's first design failed the gate.
  It changes behaviour; we report it as part of the design, not as a neutral measurement.
- Leak detection in the hub's notes is rule-based (exact numbers). A paraphrased leak ("your competitor is
  selling a lot") is missed; the blind hand check of 20 notes measures how often the rule is wrong.
- 12 runs per condition gives exact tests, but the 95% intervals for H1-H3 still allow differences of about
  0.2 index points either way; "no effect" here means "no effect we could detect", not "no effect".
- The hub positive control was weak. Told to maximise both clients' combined profit, with both clients' live
  data, the advisor reached only 0.20 (below the firewalled advisor's 0.25). This model either cannot or will not
  steer two clients to the joint-profit price, so our nulls for data pooling say little about a more capable
  or more strategic advisor. A stronger model is the first thing to test next.
- The fork test's net gain mixes two things: the rival's reaction and the deviator's own later choices (its
  agent keeps the lower price). The excess-cut measure isolates the rival's reaction.
- The `separate` control, the descriptive measures, the live-recommendation replay and the price-gap statistic
  were added after we saw the main result; they are exploratory, and only the price-gap statistic was tested on
  held-out data (the Llama replication).

## Dual use
- What could help a colluder: the finding that a shared notebook carries information between clients, and
  the conditions under which prices rise. Hub vendors already know their architectures; regulators and
  auditors mostly do not, so the balance favours publishing.
- What we withhold: nothing that is not already in the code. We do not tune prompts to maximise collusion,
  and we release no optimised "collusive" advisor prompt. The portfolio positive control states its goal
  openly (maximise combined profit), which is the conduct antitrust law already prohibits.
- How the work could make collusion harder to detect: an advisor designer could use the canary test to
  learn to avoid quoting planted facts while still using them. Our influence measure (does the advice move,
  even without quoting) is designed to catch that; the replay requires vendor cooperation.
- No real firms, prices or personal data are involved. All runs used an open model on rented compute.
