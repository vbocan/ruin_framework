# Changelog

All notable changes to the RUIN framework specification and analysis pipeline.

The format follows [Keep a Changelog](https://keepachangelog.com/). The framework
specification is versioned independently of the corpus analysis runs — the
`analysis_version` field inside each batch JSON records which specification
revision produced that file.

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
