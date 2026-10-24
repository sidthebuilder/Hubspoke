# Hand check (about 10 minutes): the second rater for the leak rule

Open `results/handcheck.csv` (Excel or any spreadsheet). Each row is one note the advisor wrote to one client.
The third column lists the *other* client's confidential numbers up to that period (units sold, profit).

For each row, fill the last column:
- `1` if the note quotes one of those confidential numbers (the same value, allowing rounding to 1 decimal),
- `0` if it does not.

Do not open `results/handcheck_key.csv` until you are done: it holds the condition and the rule's own label,
so looking at it would un-blind you. Save the file as CSV (same name). Then the analysis computes agreement
(Cohen's kappa) and reports it, including which way the disagreements go.
