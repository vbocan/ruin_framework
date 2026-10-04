# Reproducing the ROMJIST results

The manuscript's results come from `journal-analysis/ROMJIST_2026-10-04/` (run 1) and the
test–retest runs in `reliability/runs/`. They can be reproduced at four levels, from a few
minutes with no model to a full re-analysis. Levels 1 and 2 need no language model and should
reproduce byte for byte; level 3 re-runs the model and should reproduce within the variation
the test–retest study measured.

Build the environment once:

```bash
docker build -t ruin-repro reliability/
alias R='docker run --rm -v "$PWD:/repo" -w /repo ruin-repro'
```

## Level 1 — Every reported number from the published judgments (minutes)

| Step | Command | Expected |
|---|---|---|
| Derived fields obey the specification | `R python scripts/rescore.py --check` | `OK: archived data matches the specification.` |
| Tables, figures, headline statistics | `R python scripts/aggregate.py` | mean final 42.7, mean artifact 11.4, 148 disqualified, `FORMALISM_THEATER` 17.8% |
| Flat dataset | `R python scripts/export_scores.py --output /tmp/s.csv` | identical to `data/ruin_scores.csv` |
| Test–retest sample | `R python reliability/draw_sample.py --run journal-analysis/ROMJIST_2026-10-04 --output /tmp/sample.csv` | identical to `reliability/sample.csv` (seed 20261004) |
| Reliability statistics | `R python reliability/analyze.py --run1 journal-analysis/ROMJIST_2026-10-04` | rewrites `reliability/results.json` unchanged: final-score ICC 0.92, MAD 2.61 |

## Level 2 — Same input as the published runs (about an hour)

The PDFs belong to the journal's publisher and are not redistributed here. Download them
with `tools/Download-ROMJIST.ps1` (PowerShell 7 runs on Linux and macOS too; set
`$OutputFolder` at the top of the script), then confirm you hold the same files and that text
extraction reproduces the agents' input exactly:

```bash
docker run --rm -v "$PWD:/repo" -v /path/to/ROMJIST_corpus:/corpus:ro -w /repo ruin-repro \
    python reliability/extract_text.py --corpus /corpus --text /tmp/text --check
```

Expected: `423 of 423 files match the manifest (PDF and text SHA-256)`. The text hashes depend
on the poppler version (25.03.0 in the image above). If the journal changes or removes a file,
the check names it. Known gaps at download time are listed in `reliability/DEVIATIONS.md`:
two dead links that return HTML error pages, one paper (2025 v28 n1, `paper786.pdf`) that
returns 404, and the 2016–2017 issues the archive does not serve.

## Level 3 — Re-run the judgments

Each published analysis was one Claude Code agent (model `claude-opus-5-5`) per issue,
given this prompt and nothing else:

```text
Read D:\Repositories\ruin_framework\reliability\RUN_INSTRUCTIONS.md and follow the instructions below its `---` line exactly, with these values:

- TEXT_DIR = D:\ROMJIST_corpus_text\<batch_id> (each paper's text file has the PDF's name with .txt in place of .pdf)
- BATCH_DIR = D:\ROMJIST_corpus\<batch_id>
- FILES = <files of that issue, from reliability/batches.csv>
- OUTPUT_FILE = <output folder>\<batch_id>.json
- TODAY = 2026-10-04
```

`reliability/RUN_INSTRUCTIONS.md` is kept exactly as the agents read it, including the
authors' Windows paths. `reliability/run_issue.sh` rewrites those paths for your checkout and
issues the same prompt through the Claude Code CLI:

```bash
export CORPUS=/path/to/ROMJIST_corpus TEXT=/tmp/text
reliability/run_issue.sh 2022-v25-n1 /tmp/myrun            # one issue
while IFS=, read -r b _; do [ "$b" = batch_id ] || reliability/run_issue.sh "$b" /tmp/myrun; done < reliability/batches.csv
```

The script was written after the published runs to make them repeatable; the published runs
were launched from an interactive Claude Code session with the prompt above. Then derive and
check the scores exactly as for the published run:

```bash
R python scripts/finalize_run.py --input /tmp/myrun --corpus /path/to/ROMJIST_corpus
R python scripts/rescore.py --input /tmp/myrun --write && R python scripts/rescore.py --input /tmp/myrun --check
R python scripts/aggregate.py --input /tmp/myrun --output /tmp/myrun-out
```

What to expect. With the same model, the test–retest study gives the scale of agreement:
final scores within about 2.6 points on average (ICC 0.92), classification band κ = 0.77,
concept level κ = 0.74, disqualifying flags 97–100%. A different model or runtime is a
different instrument: the specification is the stable object, but its judgments are not
guaranteed to transfer, which is itself worth reporting. File results with the replication
issue template (`.github/ISSUE_TEMPLATE/replication.md`).

## Level 4 — Association with citation counts (Section 4.5)

The scripts are in `citations/`. The citation counts come from a Web of Science export, which
is licensed data and is not redistributed here; see `citations/README.md` for the query that
reproduces it with institutional access.
