# Output Format Reference

## Directory Structure

```
output/
└── {JOURNAL_ACRONYM}/
    ├── {batch_id}_{paper_id}.json
    ├── {batch_id}_{paper_id}_provenance.md
    └── ...
```

**Batch ID format:** `{year}-v{volume}[-n{issue}]`

Examples:
- `2022-v25-n1_paper708.json`
- `2022-v25-n1_paper708_provenance.md`

## JSON Schema

```json
{
  "paper_id": "string",
  "batch_id": "string",

  "source": {
    "journal_acronym": "string",
    "journal_name": "string",
    "journal_issn": "string | null",
    "volume": "number",
    "issue": "number | null",
    "year": "number"
  },

  "paper": {
    "title": "string",
    "authors": ["string"],
    "abstract": "string",
    "keywords": ["string"],
    "doi": "string | null",
    "pages": "string | null"
  },

  "scores": {
    "formalism": "number (0-100)",
    "citation_integrity": "number (0-100)",
    "structural_integrity": "number (0-100)",
    "artifact_availability": "number (0-100)",
    "intellectual_integrity": "number (0-100)",
    "composite": "number (0-100)",
    "final": "number (0-100)"
  },

  "flags": ["string"],

  "verdict": {
    "classification": "CRITICAL | CONCERNING | LIMITED | ADEQUATE | STRONG",
    "disqualified": "boolean",
    "summary": "string"
  },

  "analysis_timestamp": "ISO 8601",
  "analysis_version": "string"
}
```

## Provenance Markdown Template

```markdown
# RUIN Analysis: {Paper Title}

## Paper Information

| Field | Value |
|-------|-------|
| **Title** | {title} |
| **Authors** | {authors} |
| **Journal** | {journal_name} ({journal_acronym}) |
| **Volume/Issue** | {volume}({issue}), {year} |
| **Pages** | {pages} |
| **DOI** | {doi} |

---

## Executive Summary

| | |
|---|---|
| **Classification** | {classification} |
| **Final Score** | {final}/100 |
| **Status** | {DISQUALIFIED or PASSED} |
| **Reason** | {primary flag or "No disqualifying issues"} |

{1-2 paragraph summary of findings}

---

## Formalism Analysis

### Formal Elements Found

| Element | Count |
|---------|-------|
| Definitions | {n} |
| With constraints | {n} |
| Theorems | {n} |
| Proofs | {n} |
| Equations | {n} |

### Concept Complexity Assessment

**Topic:** {brief topic description}

**Assigned Level:** {1-5} ({level name})

**Rationale:** {why this level was assigned}

### Formalism Complexity

| Metric | Value |
|--------|-------|
| Calculated complexity | {n} |
| Expected range (Level {L}) | {min}-{max} |
| Ratio | {n}x upper bound |

**Assessment:** {proportionate or disproportionate}

### Specific Issues

{List any problematic definitions/equations with quotes and analysis}

### Formalism Score: {score}/100

**Flags:** {list flags or "None"}

---

## Citation Integrity Analysis

### Overview

| Metric | Value |
|--------|-------|
| Total references | {n} |
| Self-citations | {n} |
| Self-citation ratio | {pct}% |
| Status | {Normal/Elevated/High/Excessive} |

### Self-Citation Assessment

| Ref | Title | Similarity | Relevant |
|-----|-------|------------|----------|
| [{n}] | {title} | {score} | {Yes/No} |

{Assessment of self-citation patterns}

### Citation Score: {score}/100

**Flags:** {list flags or "None"}

---

## Structural Integrity Analysis

| Metric | Value |
|--------|-------|
| Claim sentences | {n} |
| Evidence sentences | {n} |
| Claim-evidence ratio | {ratio} |
| Limitations section | {Yes/No} |
| Limitation sentences | {n} |
| Code available | {Yes/No} |
| Data available | {Yes/No} |

{If code URL available: **Code URL:** {url}}

### Structural Score: {score}/100

---

## Score Summary

| Dimension | Score | Weight | Contribution |
|-----------|-------|--------|--------------|
| Formalism | {n} | 40% | {n} |
| Citation Integrity | {n} | 35% | {n} |
| Structural Integrity | {n} | 25% | {n} |
| **Intellectual Integrity** | **{n}** | 75% | {n} |
| Artifact Availability | {n} | 25% | {n} |
| **Composite** | **{n}** | | |
| **Final (capped)** | **{n}** | | |

---

## Flags

### Disqualifying

- **{FLAG_NAME}**: {explanation}

### High Severity

- **{FLAG_NAME}**: {explanation}

### Medium Severity

- **{FLAG_NAME}**: {explanation}

---

## Conclusion

{2-3 paragraph conclusion with:
- Summary of key findings
- Most significant issues
- Recommendation}

---

*RUIN Framework v1.0 — {date}*
```
