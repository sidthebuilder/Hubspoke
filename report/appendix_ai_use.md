# Appendix F: AI use and preexisting work

**AI use.** [Author: edit so it is accurate, in your own words.] I used an AI coding assistant (Kiro) throughout.
It wrote the code, the tests and the analysis scripts under my direction, ran the experiments, and drafted notes
and parts of the text; the dated predictions in the pre-registration were made by the assistant and are labelled
as its own. I chose the question, the conditions and the decisions recorded in PREREGISTRATION.md, checked the
results against the run files, and wrote the final text. The disclosure judge was validated against my own blind
rating of 48 notes (I saw each note, Firm A's plan and Firm A's last public price, but not the notebook setup, the
judge's label or the exact-number rule's label); the assistant entered my labels into the sheet. The optional
second sheet (20 notes, for the round-1 exact-number leak rule) was not rated. The language models in the
experiment (Qwen2.5-72B, Llama-3.1-70B, gpt-oss-120b) are the subjects of the study, and Qwen2.5-72B is also the
disclosure judge.

**Preexisting work.** Before the sprint (19-22 Oct 2026) I wrote the market model, the conditions, the reply
parser, parts of the prompts, the client cache and the observation classes, plus the first pre-registration
and plan. Everything else, including every LLM run, was done during the sprint (23-25 Oct). The repository
README lists the split file by file. The git history starts on 24 Oct, so it does not itself show the split.
