---
name: ruin-analysis
description: Analyzes academic papers using the RUIN framework. Evaluates formalism proportionality, citation integrity, structural quality, and artifact availability. Use when reviewing papers, detecting formalism theater, assessing citation manipulation, or generating quality reports.
allowed-tools: Read, Write, Bash(docker:*), Glob, Grep
---

# RUIN Framework Analysis

Analyze academic papers for intellectual integrity using the RUIN framework.

## Core Principle

**Formalism should be proportional to conceptual complexity.** A paper about logging doesn't need set theory. A paper about distributed consensus does.

## When to Use

- User asks to "analyze a paper" or "review this paper"
- User mentions "formalism", "citation integrity", or "paper quality"
- User wants to check for "formalism theater" or "citation manipulation"
- User provides a batch folder with `source.json` and PDFs

## Analysis Workflow

### Step 1: Read Input

Check for `source.json` in the input folder:
```json
{
  "journal": { "acronym": "...", "name": "...", "issn": "..." },
  "batch": { "volume": N, "issue": N, "year": N }
}
```

### Step 2: For Each PDF

1. **Extract metadata** - title, authors, abstract, keywords, DOI, pages
2. **Parse structure** - sections, references, formal elements
3. **Assess formalism** - count definitions, theorems, proofs; classify concept complexity
4. **Analyze citations** - self-citation ratio, topical similarity
5. **Check structure** - claim-evidence ratio, limitations, artifacts

### Step 3: Score and Classify

Use formulas from [scoring.md](scoring.md).

Apply flags from [flags.md](flags.md).

### Step 4: Output

Generate a single batch file per [output-format.md](output-format.md):
- `output/{JOURNAL_ACRONYM}/{batch_id}.json` - contains all papers with embedded provenance

## Quick Reference

| Concept Level | Examples | Expected Formalism |
|---------------|----------|-------------------|
| 1 - Trivial | Logging, CRUD, data capture | 0-5 |
| 2 - Low | Standard patterns, integration | 0-15 |
| 3 - Medium | Novel algorithms, empirical studies | 10-40 |
| 4 - High | Distributed protocols, type systems | 30-80 |
| 5 - Very High | Cryptographic proofs, verification | 60-150 |

## Red Flags

**Disqualifying (cap score at 25):**
- `FORMALISM_THEATER` - Level 1-2 concept with formalism >20
- `DISPROPORTIONATE_FORMALISM` - Formalism >2x expected upper bound
- `IRRELEVANT_SELF_CITATION` - Self-cite with similarity <0.3
- `CITATION_RING_INDICATOR` - Mutual citation on unrelated topics

See [flags.md](flags.md) for complete list.

## Full Specification

For complete details, see:
- [RUIN_Framework_Analytical.md](../../../RUIN_Framework_Analytical.md) - operational spec
- [RUIN_Framework_Narrative.md](../../../RUIN_Framework_Narrative.md) - theoretical foundation
