---
name: ruin-analysis
description: Analyzes academic papers using the RUIN framework. Evaluates formalism proportionality, citation integrity, structural quality, and artifact availability. Use when reviewing papers, detecting formalism theater, assessing citation manipulation, or generating quality reports.
allowed-tools: Read, Write, Bash(docker:*), Bash(pdftotext:*), Glob, Grep
---

# RUIN Framework Analysis

Analyze academic papers for intellectual integrity using the RUIN framework.

## Core Principle

**Formalism should be proportional to conceptual complexity.** A paper about logging doesn't need set theory. A paper about distributed consensus does.

**The Necessity Test:** Before accepting ANY formal element, ask: *"Would a competent programmer need this math to implement this?"* If the answer is no, it's formalism theater.

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

**Reading PDFs:**
- First, attempt to read the PDF using the Read tool
- If the Read tool fails with "PDF too large", fall back to text extraction:
  ```bash
  pdftotext "path/to/file.pdf" -
  ```
- Text-only extraction loses images/figures but captures all text content

**Analysis steps:**
1. **Extract metadata** - title, authors, abstract, keywords, DOI, pages
2. **Parse structure** - sections, references, formal elements
3. **Classify concept complexity** - BE STRICT (see classification guide below)
4. **Apply necessity test** - for EACH formal element, ask if it's needed
5. **Assess formalism** - count AND evaluate necessity
6. **Analyze citations** - self-citation ratio, topical similarity
7. **Check structure** - claim-evidence ratio, limitations, artifacts

### Step 3: Score and Classify

Use formulas from [scoring.md](scoring.md).

Apply flags from [flags.md](flags.md).

### Step 4: Output

Generate a single batch file per [output-format.md](output-format.md):
- `output/{JOURNAL_ACRONYM}/{batch_id}.json` - contains all papers with embedded provenance

---

## Concept Complexity Classification (STRICT)

**CRITICAL: Default to lower levels. Only elevate with clear justification.**

### Level 1 - Trivial (Expected Formalism: 0-5)

Papers that describe:
- Data logging, capture, or storage systems
- CRUD applications
- API integrations without novel algorithms
- Mobile/web apps that consume existing services
- System architectures that combine existing components
- Surveys or literature reviews
- Prototype descriptions

**Examples:**
- App that calls Clarifai API and stores results in Firebase = Level 1
- Web scraper with database storage = Level 1
- Dashboard that displays sensor data = Level 1
- System that integrates three existing services = Level 1

**Formalism at this level is almost always theater.** Set notation, category theory, formal definitions - none are needed to describe these systems.

### Level 2 - Low (Expected Formalism: 0-15)

Papers that describe:
- Standard design patterns applied to new domains
- Straightforward ML applications (train model, report accuracy)
- Simple optimizations of existing methods
- Empirical studies with basic statistics
- Configuration or parameter tuning studies

**Examples:**
- CNN applied to new image classification task = Level 2
- Fuzzy logic applied to supplier selection = Level 2
- Performance comparison of existing algorithms = Level 2

**Formalism beyond basic equations is suspicious.** If the paper can be fully understood without the formalism, it's theater.

### Level 3 - Medium (Expected Formalism: 10-40)

Papers that:
- Propose genuinely novel algorithms with complexity analysis
- Develop new mathematical models with validation
- Prove non-trivial properties of systems
- Extend theoretical frameworks substantively

**Examples:**
- New sorting algorithm with O(n log n) proof = Level 3
- Novel neural architecture with theoretical grounding = Level 3
- New optimization technique with convergence analysis = Level 3

### Level 4 - High (Expected Formalism: 30-80)

Papers that:
- Develop distributed protocols with safety/liveness proofs
- Create type systems with soundness proofs
- Prove computational complexity results
- Establish cryptographic security guarantees

### Level 5 - Very High (Expected Formalism: 60-150)

Papers that:
- Prove Turing completeness/universality
- Establish cryptographic hardness assumptions
- Develop formal verification frameworks
- Prove undecidability results

---

## Formalism Theater Detection

### The Necessity Test (APPLY TO EVERY FORMAL ELEMENT)

For each definition, theorem, or equation, ask:

1. **Could this be said in plain English?** If yes, formalism adds no value.
2. **Would removing this math change the implementation?** If no, it's decorative.
3. **Does this enable something English cannot?** (e.g., precise complexity bounds, proofs)

### Common Theater Patterns

**AUTOMATIC FLAGS - These patterns are almost always theater:**

| Pattern | Example | Reality |
|---------|---------|---------|
| Set notation for lists | CT = {ci = (wi, fi) \| i ∈ [1,n]} | It's an array |
| Set operations for list ops | CT₁ ∪ CT₂ | `list1 + list2` |
| Category theory for web apps | Morphisms between components | Function calls |
| Formal definitions for data structures | "Definition 1: A Widget is a tuple (x, y, z)" | It's a class/struct |
| Greek letters for config params | "Let α be the learning rate" | `learning_rate = 0.01` |
| Formal grammars for simple formats | BNF for JSON-like config | Just show the JSON |

### Zero Tolerance Rule

**For Level 1-2 papers:** ANY of the above patterns triggers `FORMALISM_THEATER` flag, regardless of count.

The old rule was: "Level ≤2 AND Formalism >20"

The new rule is: "Level ≤2 AND (Formalism >15 OR unnecessary_formal_elements > 0)"

---

## Red Flags

### Disqualifying (cap score at 25)

| Flag | Condition |
|------|-----------|
| `FORMALISM_THEATER` | Level 1-2 concept with ANY unnecessary formalism |
| `DISPROPORTIONATE_FORMALISM` | Formalism >2x expected upper bound |
| `UNNECESSARY_SET_THEORY` | Set notation used for basic list/array operations |
| `DECORATIVE_DEFINITIONS` | Formal definitions that could be plain English |
| `IRRELEVANT_SELF_CITATION` | Self-cite with similarity <0.3 |
| `CITATION_RING_INDICATOR` | Mutual citation on unrelated topics |

### High Severity (-15 points)

| Flag | Condition |
|------|-----------|
| `ORPHAN_DEFINITIONS` | Definitions introduced but never used |
| `THEOREMLESS_FORMALISM` | Many definitions, zero theorems |
| `EXCESSIVE_SELF_CITATION` | SCR >30% |
| `UNSUPPORTED_CLAIMS` | CER <0.33 |

See [flags.md](flags.md) for complete list.

---

## Full Specification

For complete details, see:
- [RUIN_Framework_Analytical.md](../../../RUIN_Framework_Analytical.md) - operational spec
- [RUIN_Framework_Narrative.md](../../../RUIN_Framework_Narrative.md) - theoretical foundation
