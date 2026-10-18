# Run 5: the stated Necessity Test rule (specification 1.2.1)

Fixed on 2026-10-18, before any analysis in this protocol was run. Results are
reported against this document; any deviation is recorded at the end of it.

## Why this run exists

Runs 1–4 used specification 1.2.0, which listed the three Necessity Test
questions without stating how their answers combine, and recorded verdicts as
narrative. Specification 1.2.1 states the rule (an element is unnecessary only
when it performs none of the three functions: Q1 yes, Q2 no, Q3 no) and asks
for the answer to each question, element by element. Run 5 measures whether the
stated rule changes the formalism-theater flags, and whether the recorded
answers are consistent with the flags the agents raise.

The run was designed after the corpus results and after run 4 were known. It is
a supplementary study and is reported as such.

## Sample

[`draw_sample.py`](draw_sample.py), output [`sample.csv`](sample.csv):

- every research paper that run 1 flagged `FORMALISM_THEATER` (72);
- the 40 uncapped Level 1–2 controls of run 4.

Run 4 analysed the same 112 papers under specification 1.2.0 on the same day;
comparing run 5 with run 4 on the same papers separates the effect of the rule
from run-to-run variation.

## Run 5

- Model: **Claude Opus 5.5** (`claude-opus-5-5`), as Claude Code subagents
  launched from an interactive session, with the runtime's default sampling
  settings, as in runs 1–4.
- Specification: the four files in `framework/` as of commit `c1bb0fb`
  (version 1.2.1; they differ from tag `spec-1.2.1` only in the wording of
  two example captions, "validation corpus" becoming "ROMJIST corpus").
- Instructions: [`RUN_INSTRUCTIONS.md`](RUN_INSTRUCTIONS.md), the text of
  `../RUN_INSTRUCTIONS.md` with the analysis version set to 1.2.1.
- One agent per issue, `FILES` limited to the sampled papers of that issue,
  `OUTPUT_FILE` = `reliability/runs/run5/{batch_id}.json`, `TODAY` = the date of
  the run. Input: the same pre-extracted text, hash-checked against
  `../pdf_manifest.csv`.
- `scripts/finalize_run.py`, then `scripts/rescore.py --write`; `--check` must pass.

## Metrics ([`analyze.py`](analyze.py), written before the run)

1. Share of the 72 papers flagged `FORMALISM_THEATER` again: run 4 (1.2.0)
   against run 5 (1.2.1).
2. Share of the 40 controls that acquire the flag: run 4 against run 5.
3. Discordant pairs between run 4 and run 5 on all 112 papers.
4. Concept level identical to run 1: run 4 against run 5.
5. Per-question records: the share of papers whose provenance has a Necessity
   Test section, the number of elements recorded and recorded as unnecessary,
   and the share of papers whose flag agrees with the recorded answers
   (flag present exactly when the paper is at Level 1–2 and at least one
   element is recorded as Q1 yes, Q2 no, Q3 no).
6. Disqualified papers among the 112 in runs 1, 4 and 5.

Nothing here is a pass/fail criterion. Output: [`results.json`](results.json).

## Deviations

None so far.
