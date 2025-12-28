# Scoring Reference

## Component Scores (0-100 each)

### Formalism Score

Based on:
- Definition count and quality (constraints present?)
- Theorem/proof presence
- Proportionality to concept complexity

**Formalism Complexity Calculation:**
```
complexity = definitions × 2 + theorems × 3 + proofs × 4
```

Compare to expected range for concept level:

| Level | Expected Range |
|-------|---------------|
| 1 | 0-5 |
| 2 | 0-15 |
| 3 | 10-40 |
| 4 | 30-80 |
| 5 | 60-150 |

If complexity > 2× upper bound → `DISPROPORTIONATE_FORMALISM`

### Citation Integrity Score

| Self-Citation Ratio | Assessment | Score Impact |
|---------------------|------------|--------------|
| ≤15% | Normal | No penalty |
| 15-20% | Elevated | -5 |
| 20-30% | High | -15 |
| >30% | Excessive | Flag |

**Topical Similarity** (for each self-citation):

| Score | Assessment |
|-------|------------|
| ≥0.5 | Related |
| 0.3-0.5 | Possibly related |
| <0.3 | Unrelated → Flag |

### Structural Integrity Score

**Claim-Evidence Ratio (CER):**
```
CER = evidence_sentences / claim_sentences
```

| CER | Assessment |
|-----|------------|
| ≥1.0 | Good |
| 0.5-1.0 | Adequate |
| 0.33-0.5 | Weak |
| <0.33 | Unsupported → Flag |

**Other factors:**
- Limitations section present: +10
- Limitations acknowledged inline: +5
- No limitations: -5 and flag

### Artifact Availability Score

| Availability | Score |
|--------------|-------|
| Code + Data | 100 |
| Code only | 60 |
| Data only | 40 |
| Neither | 0 |

## Composite Formulas

```
intellectual_integrity = 0.40 × formalism +
                         0.35 × citation_integrity +
                         0.25 × structural_integrity

composite = 0.75 × intellectual_integrity +
            0.25 × artifact_availability

final = min(composite, 25) if disqualifying_flag else composite
```

## Classification

| Score | Classification |
|-------|----------------|
| 80-100 | STRONG |
| 60-79 | ADEQUATE |
| 40-59 | LIMITED |
| 25-39 | CONCERNING |
| 0-24 | CRITICAL |
