# Citation analysis (manuscript Section 4.5)

1. **Export from Web of Science** (needs institutional access). Advanced Search:

   ```
   SO=("ROMANIAN JOURNAL OF INFORMATION SCIENCE AND TECHNOLOGY") AND PY=(2010-2025)
   ```

   Export all records as Excel or tab-delimited with a record content that includes Times
   Cited (WoS Core). The published analysis used an export of 21 August 2026 (596 records);
   citation counts grow over time, so a later export will differ somewhat.

2. **Join to the RUIN scores** on normalised titles (fuzzy and title-prefix fallbacks;
   unmatched papers get a missing value, never zero):

   ```bash
   python scripts/export_scores.py --include-non-research --output ruin_scores.csv
   python citations/merge_wos_citations.py wos_export.xlsx ruin_scores.csv merged.csv
   ```

3. **Analyse**: Spearman correlations raw, partialled on publication year, and pooled within
   year (Fisher's *z*); per-dimension estimates; Mann–Whitney comparisons.

   ```bash
   python citations/citation_correlation.py merged.csv
   ```

Requires pandas and openpyxl in addition to `scripts/requirements.txt`; the Docker image in
`reliability/Dockerfile` has them.
