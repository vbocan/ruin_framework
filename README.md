# RUIN Framework

> Reproduces RUIN's evaluation of 404 ROMJIST research papers (2010–2025), run with Claude Opus 5.5 under specification 1.2.0, together with a test–retest study whose protocol was fixed in advance and a retest of every capped paper, from the open framework specification and per-paper JSON outputs.

Code, data, and specification accompanying:

> Bocan V, Bălaș VE. RUIN: A Language-Model-Assisted Screen for Formalism, Citation Practice, and Artifact Availability in Computer Science Publications. *Scientometrics* (submitted).

RUIN (**R**igor, **U**tility, **I**ntegrity, **N**ecessity) shifts paper assessment from citation counting to content-level analysis along four dimensions: formalism proportionality, citation integrity, structural soundness, and artifact availability. The framework is encoded as a runtime-agnostic specification that an LLM agent executes against the text of each paper to produce structured per-paper assessments, from which a script computes every score.

RUIN is an experimental screen for assisted assessment, not a validated measure of integrity or quality. Its flags point a reader to specific passages with the evidence attached; its validity against expert judgment has not been established, several of its thresholds are design choices, and its labels are not findings about the conduct of any author.

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
│   ├── input/                          #   ROMJIST 2022 v25 n1 (paper708 = LifeTags++, download)
│   └── output/                         #   RUIN analysis result for the same batch
├── journal-analysis/
│   ├── ROMJIST_2026-10-04/             # Current run: 421 records, 404 research papers,
│   │                                   #   56 batches, one JSON per issue (Claude Opus 5.5)
│   └── ROMJIST_29.12.2025/             # Earlier run (Claude Opus 4.5), superseded; one JSON
│                                       #   per issue, 2010–2025
├── data/
│   ├── ruin_scores.csv                 # One row per research paper (404 rows)
│   └── README.md                       #   Column dictionary, and what `doi` does not mean
├── scripts/
│   ├── ruin_scoring.py                 # Canonical scoring rules — the sole authority
│   │                                   #   for every derived field
│   ├── rescore.py                      # Audits/repairs derived fields in the batch JSONs
│   ├── export_scores.py                # Flattens the batch JSONs into data/ruin_scores.csv
│   ├── aggregate.py                    # Reproduces published tables, figures, statistics
│   ├── classification_stability.py     # Section 4.6 and Table 5 (called by aggregate.py)
│   └── requirements.txt
├── CITATION.cff
├── CHANGELOG.md
├── LICENSE                             # MIT — applies to code
└── LICENSE-CC-BY-4.0                   # applies to framework spec + analysis data
```

**To repeat the experiment, start with [REPRODUCE.md](REPRODUCE.md)**: four levels, from re-deriving every number in minutes to re-running the model, each with the exact commands and the output to expect.

## Reproducing the published numbers (one command)

The repository ships with every JSON file the manuscript's results are derived from. To regenerate Tables 1–5, Figure 4, and the headline statistics:

```bash
pip install -r scripts/requirements.txt
python scripts/aggregate.py
```

Outputs land in `scripts/output/`:

| Output | Manuscript reference |
|--------|----------------------|
| `tables/table1_classification.csv` | Table 1 — classification distribution |
| `tables/table2_dimensions.csv` | Table 2 — dimension scores |
| `tables/table3_flags.csv` | Table 3 — flag occurrences |
| `tables/table4_yearly_scores.csv` | Table 4 — per-year means |
| `figures/figure4_temporal.png` | Figure 4 — temporal trajectory |
| `tables/table5_rule_sensitivity.csv` | Table 5 — bands under alternative scoring rules |
| `tables/classification_stability.json` | Section 4.6 — the double count, rule and model sensitivity, recorded self-citation ratios |
| `tables/headline_stats.json` | Mean final score (42.7), artifact availability (11.4), disqualified papers (148), formalism-theater rate (17.8%), annual-mean CV and regression |

This is the path from the open dataset to every number in the Results section except the citation analysis of Section 4.5, which needs a licensed Web of Science export (see `citations/`), and the run-4 retest, analysed by `reliability/capped/analyze.py`.

## Reproducing the full pipeline (from PDFs)

When you want to re-run RUIN against the ROMJIST corpus end-to-end — for example to test an updated specification, a different LLM model, or to extend the corpus past 2025:

1. **Download the corpus.** Run `tools/Download-ROMJIST.ps1` (60–90 min). This populates a folder of batch directories matching the batch layout described in `tools/README.md`.

2. **Load the framework specification.** Point your LLM runtime at `framework/` (or, if using Claude Code, the mirrored `.claude/skills/ruin-analysis/`). The four documents (`SKILL.md`, `flags.md`, `scoring.md`, `output-format.md`) together encode the nine-step protocol. See [framework/README.md](framework/README.md) for how to use the specification with non-Claude-Code runtimes.

3. **Run the analysis, batch by batch.** Each batch is independent and resumable — the output directory is the source of truth, so re-running picks up only batches missing a JSON file. Under Claude Code:

   > Run the ruin-analysis skill on `{batch_folder}` and write the output JSON to `journal-analysis/ROMJIST_{run_date}/`.

4. **Aggregate.** Run `python scripts/aggregate.py --input journal-analysis/ROMJIST_{run_date}/` to regenerate tables, figures, and headline statistics for the new run.

## The current run and its reliability

The results the manuscript reports come from `journal-analysis/ROMJIST_2026-10-04/`: every analysable file of the 2010–2025 corpus (421 records, 404 research papers), analysed on 2026-10-04 by **Claude Opus 5.5** (`claude-opus-5-5`) under specification 1.2.0 (tag `spec-1.2.0`), one independent agent per issue. `framework/` now holds 1.2.1, which corrects the specification text without changing any rule used to compute a published score (see [CHANGELOG.md](CHANGELOG.md)). The protocol was committed before the run and is in [`reliability/`](reliability/):

| File | Contents |
|------|----------|
| `reliability/PROTOCOL.md` | Run conditions, sampling rule, metrics, fixed before any analysis |
| `reliability/RUN_INSTRUCTIONS.md` | The exact instruction text every analysing agent followed |
| `reliability/DEVIATIONS.md` | The one amendment (pre-extracted text input) and the files excluded as not being papers |
| `reliability/pdf_manifest.csv` | SHA-256 of every source PDF and of its extracted text; the PDFs themselves are the journal's and are not redistributed |
| `reliability/sample.csv` | The 30-paper test–retest sample, drawn from run 1 by `draw_sample.py` |
| `reliability/runs/run2/`, `run3/` | Two further independent analyses of the sample |
| `reliability/results.json` | Output of `analyze.py`: MAD, ICC(2,1), Fleiss κ, per-flag agreement |
| `reliability/capped/` | Run 4: protocol, sample, and results of a supplementary retest of all 148 capped papers and 40 uncapped controls |
| `reliability/runs/run4/` | The run-4 analyses |

To reproduce from scratch: download the corpus with `tools/Download-ROMJIST.ps1`, check it against the manifest, run `reliability/extract_text.py`, analyse each issue with the published instructions, then `scripts/finalize_run.py`, `scripts/rescore.py --write`, and `reliability/analyze.py`.

### Earlier run

`journal-analysis/ROMJIST_29.12.2025/` is the first corpus run (December 2025, Claude Opus 4.5, specification 2.0 as then numbered), kept for the record. Its artifact component was later re-assessed; the evidence and both passes are in its `artifact_reassessment/` folder. It is superseded by the current run and the manuscript does not report it.

## Worked example

`samples/input/` describes a single batch (ROMJIST 2022, Volume 25, Issue 1) with one paper — Aiordachioae & Vatavu (2022), *LifeTags++* — that the manuscript discusses as a worked example of formalism theater. The PDF is the publisher's and is not redistributed; [`samples/input/papers/README.md`](samples/input/papers/README.md) gives its URL and SHA-256. The corresponding analysis output is in `samples/output/ROMJIST/2022-v25-n1.json`. Use this pair to inspect the framework's behaviour on a single, fully documented case before launching a full corpus run.

## Dataset

`journal-analysis/ROMJIST_2026-10-04/` contains the per-batch JSON files for all 421 ROMJIST records published between 2010 and 2025, of which 404 are research papers, 16 editorial records, and one an unreadable scan. These files are the primary data behind the manuscript's results. Each JSON contains per-paper metadata, component scores (formalism, citation integrity, structural integrity, artifact availability, intellectual integrity, composite, final), triggered flags with evidence, classification verdict, and a complete provenance record.

For a flat, one-row-per-paper view of the same run see [`data/ruin_scores.csv`](data/README.md), whose README documents every column — including which are judged and which are derived, and why the `doi` column is not a record of DOI registration.

## Replication and contestation

We welcome external replication runs on other journals, other disciplines, or with other LLM runtimes — and we welcome challenges to specific scoring decisions. Both are best filed as GitHub issues using the [replication template](.github/ISSUE_TEMPLATE/replication.md), which asks for the runtime, model version, framework specification version, and a JSON output you can point to. The framework treats disagreement as data: well-evidenced contestations may inform future revisions of `framework/flags.md` and `framework/scoring.md`.

## Citation

If you use this framework or dataset, please cite both the paper and this repository.

```bibtex
@article{bocan2026ruin,
  title   = {{RUIN}: A Language-Model-Assisted Screen for Formalism, Citation
             Practice, and Artifact Availability in Computer Science Publications},
  author  = {Bocan, Valer and Bălaș, Valentina E.},
  journal = {Scientometrics},
  year    = {2026},
  note    = {Submitted}
}

@software{bocan2026ruin_repo,
  title   = {{RUIN} framework: Specification, analysis pipeline, and {ROMJIST}
             2010--2025 dataset},
  author  = {Bocan, Valer and Bălaș, Valentina E.},
  year    = {2026},
  version = {1.2.1},
  url     = {https://github.com/vbocan/ruin_framework}
}
```

GitHub displays a "Cite this repository" button from [CITATION.cff](CITATION.cff).

## Licence

- **Code** (PowerShell scripts under `tools/`, Python scripts under `scripts/`) — MIT, see [LICENSE](LICENSE).
- **Framework specification** (`framework/`, mirrored at `.claude/skills/ruin-analysis/`) and **analysis data** (`journal-analysis/`, `samples/output/`) — Creative Commons Attribution 4.0 International, see [LICENSE-CC-BY-4.0](LICENSE-CC-BY-4.0).
