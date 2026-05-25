# RUIN Framework

> Reproduces RUIN's evaluation of 415 ROMJIST research papers (2010–2025) — including the 48.3/100 artifact-availability deficit and the 2024 formalism-theater spike — from the open framework specification and per-paper JSON outputs.

Code, data, and specification accompanying:

> Bocan V, Bălaș VE. RUIN: An Automated Framework for Assessing Intellectual Integrity and Reproducibility in Computer Science Publications. *PeerJ Computer Science* (submitted).

RUIN (**R**igor, **U**tility, **I**ntegrity, **N**ecessity) shifts paper assessment from citation counting to content-level analysis along four dimensions: formalism proportionality, citation integrity, structural soundness, and artifact availability. The framework is encoded as a runtime-agnostic specification that an LLM agent executes against PDF papers to produce structured per-paper assessments.

## Repository layout

```
.
├── framework/                          # Canonical framework specification
│   ├── SKILL.md                        #   Main analysis protocol (nine steps)
│   ├── flags.md                        #   Flag reference (severities + conditions)
│   ├── scoring.md                      #   Scoring model and classification bands
│   ├── output-format.md                #   JSON output schema
│   └── README.md                       #   How to run under Claude Code or any other LLM
├── .claude/skills/ruin-analysis/       # Claude-Code-specific mirror (same four files)
├── tools/
│   ├── Download-ROMJIST.ps1            # ROMJIST corpus downloader
│   └── README.md
├── samples/                            # Single-batch worked example
│   ├── input/                          #   ROMJIST 2022 v25 n1 (paper708 = LifeTags++)
│   └── output/                         #   RUIN analysis result for the same batch
├── journal-analysis/
│   └── ROMJIST_29.12.2025/             # Full validation run: 415 research papers,
│                                       #   57 batches, one JSON per issue, 2010–2025
├── scripts/
│   ├── aggregate.py                    # Reproduces published tables, figures, statistics
│   └── requirements.txt
├── CITATION.cff
├── CHANGELOG.md
├── LICENSE                             # MIT — applies to code
└── LICENSE-CC-BY-4.0                   # applies to framework spec + analysis data
```

## Reproducing the published numbers (one command)

The repository ships with every JSON file the manuscript's results are derived from. To regenerate Tables 3 and 4, Figure 4, and the headline statistics:

```bash
pip install -r scripts/requirements.txt
python scripts/aggregate.py
```

Outputs land in `scripts/output/`:

| Output | Manuscript reference |
|--------|----------------------|
| `tables/table3_flags.csv` | Table 3 — flag occurrences |
| `tables/table4_yearly_scores.csv` | Table 4 — per-year means |
| `figures/figure4_temporal.png` | Figure 4 — temporal trajectory |
| `tables/headline_stats.json` | Mean composite (73.4), artifact availability (48.3), CV (4.4%), regression slopes, Fisher's exact OR for 2024 |

This is the path from the open dataset to every number in the Results section.

## Reproducing the full pipeline (from PDFs)

When you want to re-run RUIN against the ROMJIST corpus end-to-end — for example to test an updated specification, a different LLM model, or to extend the corpus past 2025:

1. **Download the corpus.** Run `tools/Download-ROMJIST.ps1` (60–90 min). This populates a folder of batch directories matching the validation layout described in `tools/README.md`.

2. **Load the framework specification.** Point your LLM runtime at `framework/` (or, if using Claude Code, the mirrored `.claude/skills/ruin-analysis/`). The four documents (`SKILL.md`, `flags.md`, `scoring.md`, `output-format.md`) together encode the nine-step protocol. See [framework/README.md](framework/README.md) for how to use the specification with non-Claude-Code runtimes.

3. **Run the analysis, batch by batch.** Each batch is independent and resumable — the output directory is the source of truth, so re-running picks up only batches missing a JSON file. Under Claude Code:

   > Run the ruin-analysis skill on `{batch_folder}` and write the output JSON to `journal-analysis/ROMJIST_{run_date}/`.

4. **Aggregate.** Run `python scripts/aggregate.py --input journal-analysis/ROMJIST_{run_date}/` to regenerate tables, figures, and headline statistics for the new run.

## Worked example

`samples/input/` contains a single batch (ROMJIST 2022, Volume 25, Issue 1) with one paper — Aiordachioae & Vatavu (2022), *LifeTags++* — that the manuscript discusses as a worked example of formalism theater. The corresponding analysis output is in `samples/output/ROMJIST/2022-v25-n1.json`. Use this pair to inspect the framework's behaviour on a single, fully documented case before launching a full corpus run.

## Validation dataset

`journal-analysis/ROMJIST_29.12.2025/` contains the per-batch JSON files for all 415 ROMJIST research papers published between 2010 and 2025. These files are the primary data behind the manuscript's results. Each JSON contains per-paper metadata, component scores (formalism, citation integrity, structural integrity, artifact availability, intellectual integrity, composite, final), triggered flags with evidence, classification verdict, and a complete provenance record.

## Replication and contestation

We welcome external replication runs on other journals, other disciplines, or with other LLM runtimes — and we welcome challenges to specific scoring decisions. Both are best filed as GitHub issues using the [replication template](.github/ISSUE_TEMPLATE/replication.md), which asks for the runtime, model version, framework specification version, and a JSON output you can point to. The framework treats disagreement as data: well-evidenced contestations may inform future revisions of `framework/flags.md` and `framework/scoring.md`.

## Citation

If you use this framework or dataset, please cite both the paper and this repository.

```bibtex
@article{bocan2026ruin,
  title   = {{RUIN}: An Automated Framework for Assessing Intellectual Integrity
             and Reproducibility in Computer Science Publications},
  author  = {Bocan, Valer and Bălaș, Valentina E.},
  journal = {PeerJ Computer Science},
  year    = {2026},
  note    = {Submitted}
}

@software{bocan2025ruin_repo,
  title   = {{RUIN} Framework — Specification and Validation Dataset},
  author  = {Bocan, Valer and Bălaș, Valentina E.},
  year    = {2025},
  url     = {https://github.com/vbocan/ruin_framework}
}
```

GitHub displays a "Cite this repository" button from [CITATION.cff](CITATION.cff).

## Licence

- **Code** (PowerShell scripts under `tools/`, Python scripts under `scripts/`) — MIT, see [LICENSE](LICENSE).
- **Framework specification** (`framework/`, mirrored at `.claude/skills/ruin-analysis/`) and **analysis data** (`journal-analysis/`, `samples/output/`) — Creative Commons Attribution 4.0 International, see [LICENSE-CC-BY-4.0](LICENSE-CC-BY-4.0).
