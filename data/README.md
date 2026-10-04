# Paper-level dataset

`ruin_scores.csv` is the flat, one-row-per-paper view of the validation run. It
is generated from the batch JSONs in `journal-analysis/ROMJIST_29.12.2025/`,
which remain the archive of record:

```bash
python scripts/export_scores.py --output data/ruin_scores.csv
```

The file as shipped holds the **404 research papers** of the ROMJIST 2010–2025
corpus across 56 issues. The nine non-research records — eight editorials and
one unreadable PDF — are excluded by default, because every statistic the
manuscript reports is computed over research papers only. Pass
`--include-non-research` to emit all 421; their score columns come out blank
rather than zero, so a downstream mean cannot silently absorb them.

## Columns

| Column | Type | Notes |
|---|---|---|
| `paper_id` | string | Unique within the file. |
| `year`, `volume`, `issue` | integer | From the issue the paper appeared in, not from the PDF. |
| `batch_id` | string | The analysis batch, one per issue. 56 distinct values. |
| `title`, `first_author`, `n_authors`, `pages` | string / integer | As extracted from the paper. |
| `doi` | string | **See the caveat below.** Blank for most rows. |
| `record_type` | enum | `research`, `editorial`, `unreadable`. |
| `concept_level` | 1–5 | Judged. The concept-complexity level; see `framework/scoring.md`. Load-bearing: a formalism flag caps the score only at Levels 1–2. |
| `formalism`, `citation_integrity`, `structural_integrity`, `artifact_availability` | 0–100 | Judged. The four component scores. |
| `intellectual_integrity`, `composite`, `final` | 0–100 | **Derived**, never judged. Computed by `scripts/ruin_scoring.py`. |
| `classification` | enum | **Derived.** `STRONG`, `ADEQUATE`, `LIMITED`, `CONCERNING`, `CRITICAL`. |
| `disqualified` | boolean | **Derived.** True for the 17 papers whose score is capped at 24. |
| `flags` | string | Pipe-separated (`A|B`), empty when no flag fired. |
| `artifact_category` | enum | Judged. `code_and_data`, `code`, `data`, `claimed`, `none`, or `unassessed` (one paper whose PDF is no longer served). `artifact_availability` is this category's anchor; see `framework/scoring.md`. |
| `artifact_relevant` | boolean | Judged. False for papers with nothing that could be released (pure theory, proofs). Does not change the score. |

The judged/derived split is the point of the pipeline, not a formatting
detail. An assessor supplies the component scores, the concept level, the
flags and the provenance narrative; everything else is arithmetic, and
`python scripts/rescore.py --check` fails if the archive and the specification
have drifted apart.

## Caveat: the `doi` column is not a registration record

`doi` carries only the identifier **printed in the paper's own PDF**, as the analysing agent
recorded it. In the current run it is populated for 21 rows, all from 2025, even though the
journal registered DOIs from 2023 onwards. The column answers "did the agent record a DOI
from the page?", not "does the paper have a DOI?". For registration, query Crossref:

```bash
curl -s "https://api.crossref.org/journals/1453-8245/works?filter=type:journal-article&rows=0&facet=published:*"
```

