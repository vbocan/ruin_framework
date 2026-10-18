# Citation analysis (manuscript Sections 4.5 and 4.7)

## Association with citation counts (Section 4.5)

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

## Computed checks of the citation judgments (Section 4.7)

The model judges each paper's self-citation ratio and the relevance of its
self-citations while it reads. These scripts compute both without it. Outputs are
committed next to the scripts; the commands regenerate them.

1. **Reference lists** (`references/`). GROBID 0.8.2 splits each research paper's
   reference list into references (no consolidation, raw strings kept):

   ```bash
   docker run -d --name grobid -p 8070:8070 -e JAVA_TOOL_OPTIONS="-XX:-UseContainerSupport" lfoppiano/grobid:0.8.2
   python citations/references/extract_references.py --corpus /path/to/ROMJIST_corpus --run journal-analysis/ROMJIST_2026-10-04
   ```

   One JSON file per issue: for each PDF, the references in order with authors,
   title, year and the raw string. Without the `JAVA_TOOL_OPTIONS` setting
   GROBID's JVM can fail on hosts with cgroup v2.

2. **Self-citation count** (`self_citation_check.py`, standard library). Matches each
   raw reference against the paper's authors (surname, and initials where given,
   after rejoining names split at a detached diacritic) and applies the 20% and 30%
   lines in code; compares the result with the model's flags, stated ratios,
   reference counts and listed references.

   ```bash
   python citations/self_citation_check.py --run journal-analysis/ROMJIST_2026-10-04
   ```

3. **Field baseline** (`baseline/`, standard library, keyless OpenAlex API).
   `openalex_selfcitation.py` samples 2,000 computer science journal articles
   (seed 20261018) and counts reference-side self-citation by OpenAlex author
   identifier; `openalex_romjist.py` measures the ROMJIST articles OpenAlex
   indexes the same way and sets them beside the name-matched count. The sample
   is drawn by OpenAlex's seeded `sample` parameter, so a later run of the first
   script draws the same articles only while the index is unchanged; the
   committed CSVs are the published sample.

   ```bash
   python citations/baseline/openalex_selfcitation.py --n 2000 --seed 20261018
   python citations/baseline/openalex_romjist.py --run journal-analysis/ROMJIST_2026-10-04
   ```

4. **Relevance** (`relevance/`). SPECTER2 (`allenai/specter2_base`, CLS embedding)
   of each paper's title and abstract and of each reference's title; compares the
   self-citations named in `IRRELEVANT_SELF_CITATION` flags with the paper's other
   self-citations. CPU is enough; the image fetches the model weights at build time.

   ```bash
   docker build -t ruin-specter2 citations/relevance
   docker run --rm -v "$PWD:/work" -w /work ruin-specter2        python citations/relevance/specter2_relevance.py --run journal-analysis/ROMJIST_2026-10-04
   ```
