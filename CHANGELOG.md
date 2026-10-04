# Changelog

All notable changes to the RUIN framework specification and analysis pipeline.

The format follows [Keep a Changelog](https://keepachangelog.com/). The framework
specification is versioned independently of the corpus analysis runs — the
`analysis_version` field inside each batch JSON records which specification
revision produced that file.

## [Run ROMJIST_2026-10-04] — 2026-10-04

A complete re-analysis of the corpus and its test–retest study, under the
protocol in `reliability/`.

- Run 1: all 421 analysable records (404 research papers) analysed with Claude
  Opus 5.5 under specification 1.2.0, one independent agent per issue, over text
  pre-extracted with `pdftotext -layout`.
- Runs 2 and 3: a 30-paper sample (6 per concept level, seed 20261004)
  analysed twice more, independently. Final score MAD 2.61, ICC(2,1) 0.92;
  classification Fleiss κ 0.77, concept level 0.74, artifact category 1.00.
- New: `scripts/finalize_run.py`, `reliability/extract_text.py`,
  `draw_sample.py`, `analyze.py`, `pdf_manifest.py`.
- The script defaults now point at the current run. The earlier run and its
  artifact re-assessment are kept under `journal-analysis/ROMJIST_29.12.2025/`.

## [1.2.0] — 2026-10-04

The artifact-availability component is re-assessed from the source PDFs, and
the models behind every judged field are now recorded.

### Framework specification
- **Artifact availability is categorical.** The assessor assigns one of
  `code_and_data`, `code`, `data`, `claimed`, `none`, and the score is the
  category's anchor (100/70/50/30/0) through `ruin_scoring.artifact_score`.
  Interpolation between anchors is removed. The first run's provenance showed
  interpolated scores crediting artifacts that were described but never
  released ("MATLAB code mentioned but not publicly available" scored 70), and
  250 of 415 provenance records said nothing about artifacts at all.
- `framework/scoring.md` carried two artifact tables with different anchors
  (100/60/40/20/0 under structural integrity, 100/70/50/30/0 under artifact
  availability). The first is removed; artifacts never entered the structural
  score.
- The output schema gains `models` (per batch) and `artifact_assessment`
  (per paper: category, relevance, quoted evidence, assessor, date, original
  score).

### Analysis pipeline
- New: `scripts/artifact_evidence.py`, `scripts/artifact_agreement.py`,
  `scripts/apply_artifact_rescore.py`.
- `rescore.py --check` now fails when an artifact score disagrees with its
  category's anchor, when an assessment carries no evidence, and when a paper
  carries both self-citation flags, whose bands are disjoint.
- `export_scores.py` adds `artifact_category` and `artifact_relevant`.

### ROMJIST_29.12.2025 data
- Artifact availability re-assessed for all 406 research papers by two
  independent passes (Claude Opus 5.5) over extracted evidence: agreement
  400/406, Cohen's κ = 0.95; six disagreements adjudicated with recorded
  reasons. One paper (tansu2025) keeps its original score: its PDF returns 404
  at the publisher.
- Mean artifact availability 48.3 → 9.9; mean final score 73.6 → 64.2;
  111 papers change classification band. Flags, levels, and the other three
  components are unchanged.
- radescu2015: `ELEVATED_SELF_CITATION` removed; it also carried
  `EXCESSIVE_SELF_CITATION`. Final score unchanged at 24.
- Every batch records `models.analysis = claude-opus-4-5`, as recorded by the
  authors (the run did not log it), and `models.artifact_reassessment =
  claude-opus-5-5`.

## [1.1.0] — 2026-08-21

Corrections found while auditing the corpus against the manuscript. The
specification changes are the substantive ones; the data changes follow from
re-deriving the archive under the corrected rules.

### Framework specification
- **A formalism flag now disqualifies only at concept Level 1-2.**
  `FORMALISM_THEATER` carried that condition in prose from the first release,
  but it was absent from the scoring pseudocode and from `ruin_scoring.py`, so
  the cap was applied at every level. The condition now covers the whole
  formalism family — `FORMALISM_THEATER`, `UNNECESSARY_SET_THEORY`,
  `DECORATIVE_DEFINITIONS`, `DISPROPORTIONATE_FORMALISM` — and appears in
  `framework/scoring.md`, `framework/flags.md`, and the implementation. Above
  Level 2 such a flag is still raised and still counted; it no longer caps the
  score. The three citation flags disqualify at any level, as before.
- `UNNECESSARY_SET_THEORY` moved from "level ≤ 3" to Level 1-2, harmonising it
  with the rest of the family. No paper in the ROMJIST corpus is affected.
- `concept_level` is now a structured field on every paper record rather than a
  line of prose inside `provenance`. It gates the rule above, so it has to be
  machine-readable. `framework/output-format.md` specifies it and
  `scripts/ruin_scoring.py` requires it.

### Dataset
- Two papers were capped at 24 by the missing precondition and are no longer
  disqualified: a Level 3 modelling platform, and a Level 5 formal-language-theory
  paper flagged on six instances of the membership operator while scoring 94 on
  formalism — the highest band in the corpus. Both keep their flag.
- An eighth editorial, "Perspectives in Fuzzy Logic and Fuzzy Systems", was typed
  as research and scored 68.81. Its own abstract opens "Editorial introducing
  special issue on fuzzy systems". It now carries the `EDITORIAL` flag, which
  takes the research corpus from 407 papers to 406.
- `paper_id` is now unique. Four ids each covered two different papers in
  different issues, so any join on the id — the only identifier in the exported
  CSV — silently mis-joined them. Disambiguated with the a/b suffix the corpus
  already used elsewhere.
- The worked example under `samples/` was never rescored and still carried
  derived fields from the era when the cap was 25. It now matches the
  specification.

### Tooling
- `scripts/rescore.py` also searches the abstract for editorial self-description,
  not just the title. The editorial above ran to four pages, so the short-record
  check did not reach it, and its title reads like a survey. The abstract test
  deliberately omits the bare "introduction" alternative that the title test
  uses: it matched *Gandy-Păun-Rozenberg Machines*, a Level 5 theory paper whose
  abstract opens "Introduction of...".
- `scripts/export_scores.py` emits `concept_level`.
- `.claude/skills/ruin-analysis/` was a stale copy of `framework/`: it capped at
  25, omitted `EXCESSIVE_SELF_CITATION`, predated the judged/derived split, and
  linked to two files that no longer exist. It is now a true mirror.

### Documentation
- `data/README.md` documents `ruin_scores.csv`: every column, which fields are
  judged and which derived, and the caveat that the `doi` column records only
  the identifier printed in each PDF. It is populated for 38 rows and empty for
  the whole 2024 volume, although Crossref holds 27 registered DOIs for that
  year, so counting blanks gives 368 papers without an identifier where the
  registration record gives 322. Anyone replicating the manuscript's
  persistent-identifier figures needs Crossref, not this column.
- The repository layout in `README.md` had not been updated since the scoring
  scripts were added; it now lists `data/`, `ruin_scoring.py`, `rescore.py` and
  `export_scores.py`.
- The validation-dataset section described the archive as "415 ROMJIST research
  papers". It is 415 records, of which 406 are research papers.

## [1.0.0] — 2025-12-29

Initial public release accompanying the PeerJ Computer Science submission.

### Framework specification
- Four-dimensional assessment (formalism, citation integrity, structural
  integrity, artifact availability) with composite scoring.
- Five-level concept-complexity classification.
- Three-question Necessity Test for formal elements.
- Flag catalogue: disqualifying (cap-at-24), high-severity (-15), medium-
  severity (-5), and technical flags.
- JSON output schema with full provenance records per paper.

### Dataset
- ROMJIST validation corpus: 415 research papers, 57 batches, 2010–2025.
- One JSON file per batch in `journal-analysis/ROMJIST_29.12.2025/`.

### Tooling
- `tools/Download-ROMJIST.ps1` — corpus downloader.
- `scripts/aggregate.py` — reproduces the manuscript's headline tables,
  figures, and statistics from the batch JSONs.
