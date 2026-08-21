# Paper-level dataset

`ruin_scores.csv` is the flat, one-row-per-paper view of the validation run. It
is generated from the batch JSONs in `journal-analysis/ROMJIST_29.12.2025/`,
which remain the archive of record:

```bash
python scripts/export_scores.py --output data/ruin_scores.csv
```

The file as shipped holds the **406 research papers** of the ROMJIST 2010–2025
corpus across 56 issues. The nine non-research records — eight editorials and
one unreadable PDF — are excluded by default, because every statistic the
manuscript reports is computed over research papers only. Pass
`--include-non-research` to emit all 415; their score columns come out blank
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

The judged/derived split is the point of the pipeline, not a formatting
detail. An assessor supplies the component scores, the concept level, the
flags and the provenance narrative; everything else is arithmetic, and
`python scripts/rescore.py --check` fails if the archive and the specification
have drifted apart.

## Caveat: the `doi` column is not a registration record

`doi` carries only the identifier **printed in the paper's own PDF**. It is
populated for 38 rows: 17 in 2023 and 21 in 2025, and *none at all* in 2024,
even though Crossref holds 27 registered DOIs for that volume. The 2024 issues
simply did not print theirs.

So this column answers "did the paper show a DOI on the page?", not "does the
paper have a DOI?". Counting blanks gives 368 papers without an identifier;
the figure the manuscript reports in Section 4.7 is **322**, which is the count
of corpus papers published before the journal's first DOI year, verified
against the Crossref registration record:

```bash
curl -s "https://api.crossref.org/journals/1453-8245/works?filter=type:journal-article&rows=0&facet=published:*"
```

That query returns 106 journal-article DOIs under prefix 10.59277, distributed
2023 = 27, 2024 = 27, 2025 = 38, 2026 = 14, and nothing earlier. Use Crossref,
not this column, for any claim about persistent-identifier coverage.
