# ROMJIST re-run and test–retest protocol

Fixed on 2026-10-04, before any analysis in this protocol was run. Results are
reported against this document; any deviation is recorded in `DEVIATIONS.md`.

## Purpose

1. Re-analyse the ROMJIST 2010–2025 corpus with a single, logged model under the
   current specification (framework v1.2.0), so that every reported number
   comes from one documented run.
2. Measure the run's test–retest reliability, with every raw output published.

## Model and runtime

- Model: **Claude Opus 5.5** (`claude-opus-5-5`), via Claude Code subagents, with
  the runtime's default sampling settings (Claude Code does not expose them).
- Every analysing agent receives the same instruction text,
  [`RUN_INSTRUCTIONS.md`](RUN_INSTRUCTIONS.md), and the four specification files
  in `framework/`. It has no access to earlier runs, to `data/`, or to other
  agents' outputs.
- Each batch file records `models.analysis`, `analysis_version`, the analysis
  timestamp, and per paper the source PDF file name.

## Corpus

- Source: `tools/Download-ROMJIST.ps1`, run 2026-10-04: 56 issues with PDFs,
  423 PDFs. One indexed paper (2025 v28 n1, `paper786.pdf`) returns 404 at the
  publisher and cannot be analysed.
- The PDFs are the journal's content and are **not** redistributed here.
  `reliability/pdf_manifest.csv` lists the SHA-256 of every PDF analysed so that
  anyone re-downloading the corpus can confirm they hold the same files.
- Every PDF is analysed. Front matter, editorials and section introductions are
  flagged `EDITORIAL`; unreadable files `PDF_CORRUPTED`. Neither enters any
  statistic.

## Run 1: the corpus run

One analysis of every PDF, one agent per issue, written to
`journal-analysis/ROMJIST_2026-10-04/{batch_id}.json`. Derived fields are then
computed by `scripts/rescore.py --write`, and `--check` must pass.

## Runs 2 and 3: test–retest

- **Sample**, drawn from run 1 by `reliability/draw_sample.py` (seed 20261004):
  30 research papers, 6 per concept level as classified in run 1, chosen
  uniformly at random within level. If a level has fewer than 6 papers, all are
  taken and the shortfall is filled from the adjacent level with more papers.
- Each sampled paper is analysed twice more, independently, by agents that
  receive the same instructions and see neither run 1 nor each other. Outputs:
  `reliability/runs/run2/`, `reliability/runs/run3/`. Run 1's records for the
  sample are the third observation.

## Metrics (`reliability/analyze.py`, written before the runs)

For the 30 papers × 3 runs:

- Mean absolute pairwise difference (MAD), per component and for the final
  score, with the standard deviation across papers.
- ICC(2,1), two-way random, absolute agreement, single rater, per component and
  final score.
- Fleiss κ for classification band, concept level, and artifact category, with
  exact three-way agreement; the number of sampled papers whose run-1 final score
  lies within 3 points of a band boundary is reported beside the band κ.
- Per flag: the share of papers on which all three runs agree about its presence.

Nothing here is a pass/fail criterion; the numbers are reported as they come out.

## What is published

All batch JSONs of all three runs, with full provenance; the sample and the
script that drew it; the PDF manifest; the analysis output
`reliability/results.json`; and this protocol with any deviations.
