# Flags Reference

## The Necessity Test

**Before evaluating any flag, apply this test to each formal element:**

1. **Could this be said in plain English?** → If yes, it's unnecessary
2. **Would a competent programmer need this math?** → If no, it's decorative
3. **Does it enable proofs or bounds that English cannot?** → If no, it's theater

---

## Disqualifying Flags

These cap the final score at 25 (CRITICAL classification).

### FORMALISM_THEATER

**Condition:** Level 1-2 concept with ANY unnecessary formalism

**Detection:**
- Concept Level is 1 or 2 (see classification guide)
- Paper contains formal elements that fail the Necessity Test
- Count doesn't matter - even ONE unnecessary formal element triggers this

**Examples that trigger:**
- Set notation for array operations (CT₁ ∪ CT₂ for list concatenation)
- Formal tuple definitions for data structures
- Category theory vocabulary for simple function calls
- Greek letters decorating config parameters
- "Definition 1:" for something expressible in plain English

**Rationale:** A paper about a mobile app that calls APIs doesn't need set theory. Period.

### UNNECESSARY_SET_THEORY

**Condition:** Set notation used for basic programming operations

**Detection patterns:**
- `{x | condition}` for what is actually a filtered list
- `A ∪ B` for list concatenation or merging
- `A ∩ B` for finding common elements
- `A \ B` for list difference
- Formal set membership for array lookup

**Trigger:** Automatic disqualification if concept level ≤ 3 and no mathematical proof depends on these operations.

**Rationale:** If the operation is `list1 + list2` in code, writing CT₁ ∪ CT₂ is academic cosplay.

### DECORATIVE_DEFINITIONS

**Condition:** Formal "Definition N:" blocks for concepts that need no formal definition

**Detection patterns:**
- "Definition 1: A [noun] is a tuple (a, b, c) where..."
- Formal definitions for standard data structures
- Definitions that are never referenced in proofs
- Definitions that could be replaced with "we store X, Y, and Z"

**Trigger:** Any definition that fails: "Does removing this change what a programmer would build?"

### DISPROPORTIONATE_FORMALISM

**Condition:** Formalism complexity > 2× expected upper bound for concept level

**Calculation:**
```
formalism_score = definitions × 2 + theorems × 3 + proofs × 4

Expected upper bounds:
- Level 1: 5
- Level 2: 15
- Level 3: 40
- Level 4: 80
- Level 5: 150

Trigger: formalism_score > 2 × upper_bound
```

### IRRELEVANT_SELF_CITATION

**Condition:** Any self-citation with topical similarity < 0.3

**Detection:**
- Identify self-citations (author name matching)
- Assess topical relevance to current paper
- Flag if cited work is on unrelated topic

**Rationale:** Citing your own unrelated work is citation padding.

### CITATION_RING_INDICATOR

**Condition:** Mutual citation pattern on unrelated topics

**Detection:**
- Author A cites Author B on topic X
- Author B cites Author A on topic Y
- Topics X and Y have low similarity

**Rationale:** Indicates coordinated citation manipulation.

---

## High Severity Flags (-15 points)

### ORPHAN_DEFINITIONS

**Condition:** Definition Usage Ratio (DUR) < 0.1 AND definitions > 5

```
DUR = definitions_referenced_later / total_definitions
```

**Detection:** Definitions introduced in Section 2-3 but never used in proofs, algorithms, or analysis.

**Rationale:** Unused definitions are pure theater.

### THEOREMLESS_FORMALISM

**Condition:** Definitions > 5 AND theorems = 0

**Rationale:** Formal apparatus that produces no formal results.

### EXCESSIVE_SELF_CITATION

**Condition:** Self-Citation Ratio (SCR) > 30%

```
SCR = self_citations / total_citations
```

### UNSUPPORTED_CLAIMS

**Condition:** Claim-Evidence Ratio (CER) < 0.33

```
CER = evidence_sentences / claim_sentences
```

**Detection:** Many assertions, few citations or experimental results to back them.

---

## Medium Severity Flags (-5 points)

### NO_LIMITATIONS

**Condition:** Paper acknowledges no limitations

**Detection:** No "Limitations" section AND no inline acknowledgment of constraints.

### ELEVATED_SELF_CITATION

**Condition:** SCR between 20-30%

---

## Flag Detection Procedure

### For Each Paper:

1. **Classify concept complexity FIRST** (be strict, default low)
2. **Inventory all formal elements:**
   - Definitions (numbered or inline)
   - Theorems/Lemmas/Propositions
   - Proofs
   - Equations with formal notation
3. **Apply Necessity Test to EACH element**
4. **Check for theater patterns:**
   - Set notation for lists?
   - Tuple definitions for data?
   - Greek letters for configs?
   - Definitions without proofs?
5. **Calculate ratios:**
   - SCR (self-citation ratio)
   - DUR (definition usage ratio)
   - CER (claim-evidence ratio)
6. **Apply flags based on conditions**

### Concept Level Quick Reference

| Level | Example Topics | Formalism Expectation |
|-------|---------------|----------------------|
| 1 | App descriptions, API integrations, prototypes | Zero tolerance for formal notation |
| 2 | Standard ML applications, empirical comparisons | Basic equations only |
| 3 | Novel algorithms, new models | Justified formalism OK |
| 4 | Protocol proofs, type systems | Formalism expected |
| 5 | Complexity proofs, verification | Heavy formalism required |

---

## Examples

### Paper 708 (LifeTags++) - SHOULD BE FLAGGED

**What it is:** Mobile app calling Clarifai API, storing in Firebase, displaying tag clouds

**Concept Level:** 1 (API integration, data display)

**Formal elements found:**
- CT = {ci = (wi, fi, θi) | i ∈ [1,n]} — set notation for tag array
- CT₁ ∪ CT₂ — set union for combining tag lists
- CT₁ \ CT₂ — set difference for filtering

**Necessity Test:**
- Could be said in English? YES ("combine the tags from both cameras")
- Would programmer need this math? NO (`tags = cam1_tags + cam2_tags`)
- Enables proofs? NO

**Flags:**
- `FORMALISM_THEATER` - Level 1 with unnecessary formalism
- `UNNECESSARY_SET_THEORY` - Set ops for list operations

**Correct classification:** CRITICAL (score capped at 25)

### Paper with legitimate formalism

**What it is:** New distributed consensus algorithm

**Concept Level:** 4 (distributed protocols)

**Formal elements:**
- Safety property definitions
- Liveness proofs
- Complexity bounds

**Necessity Test:**
- Could be said in English? NO (proofs require precision)
- Would programmer need this? YES (correctness depends on it)
- Enables proofs? YES

**Flags:** None

**Correct classification:** Based on quality of proofs

---

*End of Flags Reference*
