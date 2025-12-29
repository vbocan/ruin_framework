# Scoring Reference

## Pre-Scoring: The Necessity Test

**Before calculating ANY score, evaluate formalism necessity.**

For each formal element (definition, theorem, equation):

| Question | If YES | If NO |
|----------|--------|-------|
| Could this be said in plain English? | Unnecessary | May be necessary |
| Would removing it change the implementation? | Necessary | Unnecessary |
| Does it enable proofs/bounds? | Necessary | Unnecessary |

**If ANY unnecessary formal element exists in a Level 1-2 paper → Flag and cap at 25.**

---

## Component Scores (0-100 each)

### Formalism Score

**Step 1: Classify Concept Complexity (BE STRICT)**

| Level | Name | Examples | Max Expected |
|-------|------|----------|--------------|
| 1 | Trivial | Apps, API integrations, prototypes, surveys | 5 |
| 2 | Low | Standard ML apps, empirical comparisons | 15 |
| 3 | Medium | Novel algorithms, new models with proofs | 40 |
| 4 | High | Protocol proofs, type systems, complexity | 80 |
| 5 | Very High | Turing proofs, crypto hardness, verification | 150 |

**Classification Rules:**
- Paper calls existing APIs? → Level 1
- Paper applies existing algorithm to new domain? → Level 2
- Paper proposes new algorithm with complexity proof? → Level 3
- Paper proves safety/liveness properties? → Level 4
- Paper proves computational universality? → Level 5

**Default to LOWER level when uncertain.**

**Step 2: Count Formal Elements**

```
formalism_complexity = definitions × 2 + theorems × 3 + proofs × 4
```

**Step 3: Check Proportionality**

| Result | Assessment |
|--------|------------|
| Within expected range | Proportionate |
| 1-2× upper bound | Elevated (warning) |
| >2× upper bound | DISPROPORTIONATE_FORMALISM flag |

**Step 4: Apply Necessity Test**

Even if formalism is within range, check:
- Are the definitions used in proofs? If not → Orphan definitions
- Could the equations be replaced with English? If yes → Theater

**Score Calculation:**

```
if disqualifying_flag:
    formalism_score = 0
elif necessity_test_failures > 0:
    formalism_score = max(0, 60 - (necessity_failures × 15))
elif proportionate:
    formalism_score = 80 + (quality_bonus)
elif elevated:
    formalism_score = 60
else:
    formalism_score = 40
```

---

### Citation Integrity Score

**Self-Citation Ratio (SCR):**

```
SCR = self_citations / total_citations
```

| SCR | Assessment | Score |
|-----|------------|-------|
| ≤15% | Normal | 90-100 |
| 15-20% | Elevated | 75-85 |
| 20-30% | High | 50-70 |
| >30% | Excessive | Flag, cap at 40 |

**Topical Similarity (for each self-citation):**

| Similarity | Assessment |
|------------|------------|
| ≥0.5 | Related (OK) |
| 0.3-0.5 | Marginal (warning) |
| <0.3 | Unrelated → IRRELEVANT_SELF_CITATION flag |

**Score = base_score - (unrelated_cites × 20)**

---

### Structural Integrity Score

**Claim-Evidence Ratio (CER):**

```
CER = evidence_sentences / claim_sentences
```

| CER | Assessment | Score Impact |
|-----|------------|--------------|
| ≥1.0 | Well-supported | +10 |
| 0.5-1.0 | Adequate | 0 |
| 0.33-0.5 | Weak | -10 |
| <0.33 | Unsupported | Flag, -20 |

**Limitations:**

| Presence | Score Impact |
|----------|--------------|
| Dedicated section | +10 |
| Inline acknowledgment | +5 |
| None | -5, NO_LIMITATIONS flag |

**Artifacts:**

| Availability | Score |
|--------------|-------|
| Code + Data public | 100 |
| Code only | 60 |
| Data only | 40 |
| "Available on request" | 20 |
| Neither | 0 |

---

### Artifact Availability Score

| Status | Score |
|--------|-------|
| Public repository with working code + data | 100 |
| Public repository with code | 70 |
| Public dataset | 50 |
| Claims availability but not verified | 30 |
| Nothing available | 0 |

---

## Composite Formulas

```
intellectual_integrity = 0.40 × formalism_score +
                         0.35 × citation_integrity +
                         0.25 × structural_integrity

composite = 0.75 × intellectual_integrity +
            0.25 × artifact_availability

# CRITICAL: Apply flags AFTER composite calculation
if any_disqualifying_flag:
    final = min(composite, 25)
else:
    final = composite - high_severity_penalties - medium_severity_penalties
```

---

## Classification

| Score | Classification | Meaning |
|-------|----------------|---------|
| 80-100 | STRONG | High quality, appropriate formalism |
| 60-79 | ADEQUATE | Acceptable, minor issues |
| 40-59 | LIMITED | Significant concerns |
| 25-39 | CONCERNING | Serious issues, may be disqualified |
| 0-24 | CRITICAL | Disqualified (flagged) |

---

## Scoring Checklist

For each paper:

- [ ] Classify concept complexity (default LOW)
- [ ] Inventory formal elements
- [ ] Apply Necessity Test to each element
- [ ] Check for theater patterns (set notation for lists, etc.)
- [ ] Calculate formalism complexity score
- [ ] Compare to expected range
- [ ] Calculate SCR and check self-citations
- [ ] Calculate CER
- [ ] Check for limitations section
- [ ] Check artifact availability
- [ ] Apply all applicable flags
- [ ] Calculate final score
- [ ] Assign classification

---

## Example: Paper 708 Re-scored

**Concept Level:** 1 (mobile app calling APIs)

**Expected formalism:** 0-5

**Actual formalism:**
- 2 definitions (tag cloud, concept) = 4
- 4 equations (set operations) = 8 (treated as theorems for scoring)
- Total: 12

**But wait - apply Necessity Test:**
- Set notation for list operations? YES → Theater
- Could be English? YES → Unnecessary

**Flags triggered:**
- `FORMALISM_THEATER` (Level 1 + unnecessary formalism)
- `UNNECESSARY_SET_THEORY` (set ops for arrays)

**Score:** Capped at 25

**Classification:** CRITICAL

---

*End of Scoring Reference*
