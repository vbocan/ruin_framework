# Output Format Reference

## Directory Structure

```
output/
└── {JOURNAL_ACRONYM}/
    ├── {batch_id}.json
    └── ...
```

**One file per batch.** The app aggregates across batch files for journal-level statistics.

**Batch ID format:** `{year}-v{volume}[-n{issue}]`

Examples:
- `2022-v25-n1.json`
- `2024-v208.json`

## JSON Schema

```json
{
  "batch_id": "string",
  "analysis_timestamp": "ISO 8601",
  "analysis_version": "string",

  "source": {
    "journal_acronym": "string",
    "journal_name": "string",
    "journal_issn": "string | null",
    "volume": "number",
    "issue": "number | null",
    "year": "number"
  },

  "papers": [
    {
      "paper_id": "string",
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
      "flag_details": {
        "FLAG_NAME": "explanation string"
      },
      "verdict": {
        "classification": "CRITICAL | CONCERNING | LIMITED | ADEQUATE | STRONG",
        "disqualified": "boolean",
        "summary": "string"
      },
      "provenance": "markdown string"
    }
  ]
}
```

## Provenance Content

The `provenance` field contains analytical narrative in markdown. It **complements** the structured data (doesn't duplicate it).

### Include

- Concept complexity assessment (topic, level, rationale)
- Formal elements and proportionality reasoning
- Self-citation assessment with relevance judgments
- Specific issues found (quotes, examples)
- Conclusion synthesis

### Exclude (app renders from structured data)

- Paper metadata table
- Score summary table
- Raw flag list

## Provenance Template

```markdown
## Formalism Analysis

### Concept Complexity
**Topic:** [brief description of what the paper is about]
**Level:** [1-5] ([Trivial/Low/Medium/High/Very High])
**Rationale:** [why this complexity level was assigned]

### Formal Elements
- Definitions: [n] (with constraints: [n])
- Theorems: [n]
- Proofs: [n]
- Equations: [n]

### Proportionality
Calculated complexity: [n]
Expected range (Level [L]): [min]-[max]
Ratio: [n]x upper bound

**Assessment:** [Proportionate/Disproportionate] — [reasoning]

### Issues
[Specific quotes or examples of problematic formalism, or "None identified"]

---

## Citation Analysis

[Narrative assessment of self-citations]
[Any concerning patterns or "No issues identified"]

---

## Structural Analysis

[Observations on claim-evidence balance]
[Artifact availability notes]

---

## Conclusion

[1-2 paragraph synthesis of findings and recommendation]
```

## Example

**File:** `output/ROMJIST/2025-v28-n4.json`

```json
{
  "batch_id": "2025-v28-n4",
  "analysis_timestamp": "2025-12-29T10:00:00Z",
  "analysis_version": "1.0",
  "source": {
    "journal_acronym": "ROMJIST",
    "journal_name": "Romanian Journal of Information Science and Technology",
    "journal_issn": "1453-8245",
    "volume": 28,
    "issue": 4,
    "year": 2025
  },
  "papers": [
    {
      "paper_id": "paper811",
      "paper": {
        "title": "112 Emergency Video Call Response Pipeline",
        "authors": ["F. Balaban", "I. Sacala", "M. Petrescu-Nita"],
        "abstract": "...",
        "keywords": ["emergency response", "deep learning"],
        "doi": null,
        "pages": "399-410"
      },
      "scores": {
        "formalism": 85,
        "citation_integrity": 90,
        "structural_integrity": 65,
        "artifact_availability": 40,
        "intellectual_integrity": 79,
        "composite": 69,
        "final": 69
      },
      "flags": [],
      "flag_details": {},
      "verdict": {
        "classification": "ADEQUATE",
        "disqualified": false,
        "summary": "Systems integration paper with appropriate minimal formalism."
      },
      "provenance": "## Formalism Analysis\n\n### Concept Complexity\n**Topic:** Systems integration combining video communication with pre-trained deep learning classifier\n**Level:** 2 (Low)\n**Rationale:** Core contribution is pipeline architecture and dataset creation, not algorithmic novelty.\n\n### Formal Elements\n- Definitions: 0\n- Theorems: 0\n- Equations: 3 (standard metrics)\n\n### Proportionality\nCalculated complexity: 3\nExpected range (Level 2): 0-15\nRatio: 0.2x upper bound\n\n**Assessment:** Proportionate — minimal equations describe standard accuracy metrics.\n\n### Issues\nNone identified.\n\n---\n\n## Citation Analysis\n\nNo self-citations (0/16 references). Reference list covers relevant prior work.\n\n---\n\n## Structural Analysis\n\nBrief limitations section present. Dataset shared via OneDrive; no code provided.\n\n---\n\n## Conclusion\n\nCompetent applied research with appropriate formalism for concept complexity. Main limitation is missing code for reproducibility."
    }
  ]
}
```
