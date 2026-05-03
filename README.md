# RUIN Framework

Code and data accompanying:

> Bocan V, Bălaș VE. RUIN: An Automated Framework for Assessing Intellectual Integrity and Reproducibility in Computer Science Publications. *PeerJ Computer Science* (under review).

RUIN (**R**igor, **U**tility, **I**ntegrity, **N**ecessity) shifts paper assessment from citation counting to content-level analysis along four dimensions: formalism proportionality, citation integrity, structural soundness, and artifact availability. The framework is implemented as a Claude Code skill that drives a nine-step analysis pipeline over PDF papers.

## Repository layout

```
.
├── .claude/skills/ruin-analysis/   # The framework, encoded as an LLM skill
│   ├── SKILL.md                    #   Main analysis protocol (nine steps)
│   ├── flags.md                    #   Flag reference (severities + conditions)
│   ├── scoring.md                  #   Scoring model and classification bands
│   └── output-format.md            #   JSON output schema
├── tools/
│   ├── Download-ROMJIST.ps1        # ROMJIST corpus downloader
│   └── README.md
├── samples/                        # Single-batch worked example
│   ├── input/                      #   ROMJIST 2022 v25 n1 (paper708 = LifeTags++)
│   └── output/                     #   RUIN analysis result for the same batch
└── journal-analysis/
    └── ROMJIST_29.12.2025/         # Full validation run: 416 papers, 57 batches
                                    #   one JSON per issue, 2010-2025
```

## Reproducing the ROMJIST validation run

1. **Download the corpus.** Run `tools/Download-ROMJIST.ps1` (60–90 min). This populates a folder of batch directories matching the validation layout.

2. **Open Claude Code in this repository.** The `.claude/skills/ruin-analysis/` skill auto-loads. Set the model to Sonnet 4.6 (`/model claude-sonnet-4-6`) — the same family used to produce the published baseline, minimising methodological drift.

3. **Run the skill, batch by batch.** For each batch folder:

   > Run the ruin-analysis skill on `{batch_folder}` and write the output JSON to `journal-analysis/ROMJIST_{run_date}/`.

   The skill reads PDFs, applies the nine-step protocol, and writes one JSON file per batch matching the schema in `.claude/skills/ruin-analysis/output-format.md`. Batches are independent; resumability is automatic (the output directory is the source of truth — re-running picks up only batches missing a JSON file).

4. **Inspect results.** Each batch JSON contains per-paper metadata, component scores (formalism, citation integrity, structural integrity, artifact availability, intellectual integrity, composite, final), triggered flags with evidence, classification verdict, and a complete provenance record.

## Worked example

`samples/input/` contains a single batch (ROMJIST 2022, Volume 25, Issue 1) with one paper — Aiordachioae & Vatavu (2022), *LifeTags++* — that the manuscript discusses as a worked example of formalism theater. The corresponding RUIN output is in `samples/output/ROMJIST/2022-v25-n1.json`. Use this pair to inspect the framework's behaviour on a single, fully documented case before launching a full corpus run.

## Validation dataset

`journal-analysis/ROMJIST_29.12.2025/` contains the per-batch JSON files for all 416 ROMJIST research papers published between 2010 and 2025. These files are the primary data behind the manuscript's results, tables, and figures. Aggregating across the 57 batch JSONs reproduces the score distributions, flag occurrences, dimension means, and temporal trajectory reported in the paper.

## License

Code and data: see repository licence headers. The framework specification (`.claude/skills/ruin-analysis/`) and the ROMJIST analysis output are released to support replication, extension, and contestation.
