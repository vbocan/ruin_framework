# Flags Reference

## Disqualifying Flags

These cap the final score at 25 (CRITICAL classification).

| Flag | Condition | Rationale |
|------|-----------|-----------|
| `FORMALISM_THEATER` | Concept Level ≤2 AND Formalism >20 | Decorative math on trivial topic |
| `DISPROPORTIONATE_FORMALISM` | Formalism >2× expected upper bound | Excessive formalism for complexity |
| `IRRELEVANT_SELF_CITATION` | Any self-citation with similarity <0.3 | Citation padding |
| `CITATION_RING_INDICATOR` | Mutual citation on unrelated topics | Coordinated citation manipulation |

## High Severity Flags (-15 points)

| Flag | Condition | Rationale |
|------|-----------|-----------|
| `ORPHAN_DEFINITIONS` | DUR <0.1 AND definitions >10 | Definitions never used |
| `THEOREMLESS_FORMALISM` | Definitions >5 AND theorems =0 | Formal apparatus with no results |
| `EXCESSIVE_SELF_CITATION` | SCR >30% | Citation padding |
| `UNSUPPORTED_CLAIMS` | CER <0.33 | Claims without evidence |

## Medium Severity Flags (-5 points)

| Flag | Condition | Rationale |
|------|-----------|-----------|
| `NO_LIMITATIONS` | No limitations acknowledged | Lack of scientific humility |
| `ELEVATED_SELF_CITATION` | SCR 20-30% | Borderline self-promotion |

## Metrics

**DUR (Definition Usage Ratio):**
```
DUR = definitions_referenced_later / total_definitions
```

**SCR (Self-Citation Ratio):**
```
SCR = self_citations / total_citations
```

**CER (Claim-Evidence Ratio):**
```
CER = evidence_sentences / claim_sentences
```

## Detection Notes

### Formalism Theater Detection

1. Classify concept complexity (Level 1-5)
2. Count formal elements (definitions, theorems, proofs)
3. Calculate formalism complexity
4. Compare to expected range
5. Flag if disproportionate

### Self-Citation Analysis

1. Extract reference list
2. Identify self-citations (author name matching)
3. For each self-citation:
   - Extract title/abstract from cited work (if accessible)
   - Compute topical similarity to current paper
   - Flag if similarity <0.3

### Citation Ring Detection

1. Check if cited authors cite this author back
2. Compare topics between papers
3. Flag if mutual citation exists on unrelated topics
