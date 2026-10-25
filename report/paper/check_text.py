"""Checks on report/paper/main.tex: abstract word count, and every number in the prose traced to a result file
(via report/check_numbers.py). Written during the sprint.

    python report/paper/check_text.py      -> report/paper/check_text_out.txt
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
tex = (HERE / "main.tex").read_text(encoding="utf-8")
body = tex.split(r"\begin{document}", 1)[1]
body = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", " ", body, flags=re.S)
body = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}", " ", body, flags=re.S)
body = re.sub(r"(?m)%.*$", " ", body)
body = re.sub(r"\\includegraphics(\[[^\]]*\])?\{[^}]*\}", " ", body)
body = re.sub(r"\\(begin|end)\{[a-zA-Z*]+\}(\[[^\]]*\])?(\{[^}]*\})*", " ", body)
body = re.sub(r"\\(url|href|label|ref|cite|texttt|code)\{[^}]*\}", " ", body)
body = re.sub(r"\\rule\{[^}]*\}\{[^}]*\}|\\\\\[[^\]]*\]|\\vspace\{[^}]*\}|\\setlength\{[^}]*\}\{[^}]*\}", " ", body)
body = re.sub(r"\[(enhanced|@)[^\]]*\]", " ", body)
body = re.sub(r"\\begin\{tcolorbox\}\[.*?\]", " ", body, flags=re.S)
body = body.replace("$", "").replace("\\%", "%").replace("--", "-")
body = re.sub(r"\\[a-zA-Z]+\*?", " ", body)
body = re.sub(r"[{}~]", " ", body)
body = re.sub(r"p\{[\d.]+cm\}", " ", body)
plain = HERE / "main_plain.txt"
plain.write_text(body, encoding="utf-8")

abstract = re.search(r"\\begin\{minipage\}\{[^}]*\}(.*?)\\end\{minipage\}", tex, flags=re.S).group(1)
abstract = re.sub(r"\\setlength\{[^}]*\}\{[^}]*\}|\\itshape|\\small", " ", abstract)
words = len(re.findall(r"\S+", abstract.strip()))
r = subprocess.run([sys.executable, str(ROOT / "report" / "check_numbers.py"), str(plain), "--where"],
                   capture_output=True, text=True, encoding="utf-8")
(HERE / "check_text_out.txt").write_text(f"abstract words: {words}\n\n{r.stdout}\n{r.stderr}", encoding="utf-8")
