# Capped-paper retest: protocol

Fixed on 2026-10-18, before any analysis in this protocol was run. Results are
reported against this document; any deviation is recorded at the end of it.

## Why this run exists

The test–retest study of [`../PROTOCOL.md`](../PROTOCOL.md) sampled 30 papers,
six per concept level. That design measures the stability of scores well, but
it says little about the flags that cap a score at 24: `FORMALISM_THEATER`
fired on one of the 30 sampled papers and `IRRELEVANT_SELF_CITATION` on one,
so the reported agreement on disqualifying flags is mostly agreement about
their absence. The cap decides the classification of 148 of the 404 research
papers, so its reproducibility needs its own measurement.

This run was designed after the corpus run and after its results were known.
It is a supplementary study, not part of the protocol fixed on 2026-10-04, and
it is reported as such.

## Sample

Drawn from run 1 (`journal-analysis/ROMJIST_2026-10-04`) by
[`draw_sample.py`](draw_sample.py), output [`sample.csv`](sample.csv):

- **every research paper run 1 disqualified**: 148 papers, of which 57 are
  capped by a formalism flag alone, 76 by a citation flag alone, and 15 by both;
- **40 controls**, drawn uniformly with seed 20261018 from the 211 research
  papers at concept Levels 1–2 that run 1 did not disqualify. Levels 1–2 are
  where both flag families can cap a score.

188 papers in 55 issues.

## Run 4

- Model: **Claude Opus 5.5** (`claude-opus-5-5`), as Claude Code subagents
  launched from an interactive session, with the runtime's default sampling
  settings, exactly as in runs 1–3.
- Specification: the four files in `framework/` **unchanged since the corpus
  run** (analysis version 1.2.0; last changed in commit `789cdb9`, tagged
  `spec-1.2.0`). No specification change is made until run 4 is complete.
- Instructions: [`../RUN_INSTRUCTIONS.md`](../RUN_INSTRUCTIONS.md), unchanged.
  Each agent receives the prompt that `../run_issue.sh` builds, with
  `TEXT_DIR` and `BATCH_DIR` pointing at the pre-extracted text and the PDFs
  of its issue, `FILES` listing only the sampled papers of that issue,
  `OUTPUT_FILE` = `reliability/runs/run4/{batch_id}.json`, and
  `TODAY` = the date of the run.
- One agent per issue. Agents see neither run 1, runs 2–3, nor each other.
- Input: the text files whose SHA-256 is recorded in
  [`../pdf_manifest.csv`](../pdf_manifest.csv); the hashes are checked before
  the run.
- Derived fields are recomputed by `scripts/rescore.py --write`, and
  `--check` must pass, as for every other run.

## Metrics ([`analyze.py`](analyze.py), written before the run)

Papers are matched by `(batch_id, source_file)`. Derived values are recomputed
from the judged fields with `scripts/ruin_scoring.py`.

1. **Cap reproduction**: the share of the 148 capped papers that run 4 also
   disqualifies, overall and per stratum; and whether a formalism cap is
   reproduced by a formalism flag and a citation cap by a citation flag.
2. **Flag persistence**: for each disqualifying flag, the share of sampled
   papers carrying it in run 1 that carry it again in run 4.
3. **Concept level** of the 72 formalism-capped papers in run 4: identical to
   run 1, and still at Level 1 or 2, where the formalism cap applies.
4. **New caps among the 40 controls**, overall and per flag family.
5. **Bands**: the share of capped papers and of controls whose band is
   unchanged; the bands and median final score in run 4 of capped papers that
   lose the cap; the mean and median absolute difference in final score among
   controls.
6. **Agreement on the disqualification decision among Level 1–2 papers**:
   observed agreement, positive agreement, and Cohen's κ, from the 2×2 table of
   run 1 against run 4, with the controls weighted by the inverse of their
   sampling fraction (211/40) so that the estimate refers to all Level 1–2
   papers.

Nothing here is a pass/fail criterion; the numbers are reported as they come
out. Output: [`results.json`](results.json).

## Deviations

Recorded after the run, 2026-10-18. None affects a judged field or a metric.

1. **Paraphrased abstracts.** Several agents wrote a short paraphrase into the
   `abstract` metadata field instead of the verbatim abstract, and said so in
   the field. The abstract is metadata; no metric reads it.
2. **Issue labels.** For issues labelled "3-4", "S" or "T", agents set
   `source.issue` to null. `scripts/finalize_run.py` rebuilt `source` from the
   corpus `source.json`, as it does for every run, and made two `paper_id`s
   unique across the run. Papers are matched by `(batch_id, source_file)`, so
   neither change touches the analysis.
3. **Specification change after the run.** `framework/` moved to 1.2.1 after
   every run-4 agent had finished; the run used 1.2.0 (tag `spec-1.2.0`).
