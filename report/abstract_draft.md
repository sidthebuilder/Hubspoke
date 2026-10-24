# Abstract draft (aim: exactly 150 words, so it meets both "150 or fewer" and "150 to 250")

Collusion monitors read what agents say to each other, but competitors can also coordinate through a shared
third party without talking. We test this hub-and-spoke route with LLM pricing agents: two sellers in a logit
duopoly share one LLM pricing advisor, and we vary only what the advisor sees and remembers (seven
pre-registered conditions, 12 runs each, on Qwen2.5-72B and Llama-3.1-70B). In both models a firewalled shared
advisor kept prices above the no-advisor baseline (price index +0.29 and +0.44; exact p = 0.002 and 0.009),
but giving it rivals' confidential data did not raise prices further; on Qwen, replays show the advisor had
that data without using it. Ageing the data lowered prices only on Llama, where a shared notebook partly
undid the drop. A black-box canary test shows why memory still matters: through a shared notebook, every
planted price plan (24 of 24) reached the rival's advice session and shifted that advice upward on average;
through private notebooks, none did.

[Word count: check with report/check_numbers.py-style count before submitting; the author rewrites it.]
