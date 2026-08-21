# Changelog

All notable changes to the RUIN framework specification and analysis pipeline.

The format follows [Keep a Changelog](https://keepachangelog.com/). The framework
specification is versioned independently of the corpus analysis runs — the
`analysis_version` field inside each batch JSON records which specification
revision produced that file.

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
