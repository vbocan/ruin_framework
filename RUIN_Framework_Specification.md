# RUIN: Rigor, Utility, Impact, Necessity

## A Framework for Automated Assessment of Academic Paper Utility

**Version:** 0.5 (Draft)
**Date:** December 2025
**Status:** Conceptual Framework

---

## 1. Problem Statement

### 1.1 The Quartile Fallacy

Academic journals are ranked by quartiles (Q1-Q4) based on citation metrics, primarily the Journal Impact Factor (JIF). This system conflates *attention* with *value*:

- A highly-cited paper may be cited because it is wrong (controversial)
- A highly-cited paper may be cited because it is trendy (hype cycle)
- A practically transformative paper may receive few citations (practitioners don't publish)
- A methodologically flawed paper may be published in Q1 if it appears rigorous

**The core problem:** No systematic mechanism exists to assess whether published research provides genuine utility versus the appearance of contribution.

### 1.2 The Formalism Theater Phenomenon

A specific pathology exists in computer science publishing: the use of formal mathematical notation to dress up trivial concepts. This "formalism theater" includes:

- Defining obvious structures as tuples without adding constraints
- Introducing set-theoretic notation for simple engineering descriptions
- Creating an appearance of rigor without enabling proofs or guarantees
- Using jargon inflation to obscure conceptual simplicity

**Example (anonymized):** A paper defining a "life documentation system" as a formal tuple (V, A, M) where V = video stream, A = audio stream, M = metadata. The formalism adds no analytical power—it merely restates "the system captures video, audio, and metadata" in notation.

### 1.3 Research Objectives

This framework aims to:

1. Define measurable signals of real-world research utility
2. Detect unnecessary formalism through structural analysis
3. Enable automated scoring without human judgment in the evaluation loop
4. Provide separate treatment for recent papers (no adoption history) and mature papers (observable outcomes)
5. Challenge the adequacy of citation-based quartile rankings

---

## 2. Theoretical Foundation

### 2.1 Utility Decomposition

Research utility is decomposed into two orthogonal dimensions:

```
                    INTRINSIC QUALITY
                    (Paper itself)
                          │
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    Conceptual       Methodological    Formalism
    Contribution     Soundness         Necessity
         │                │                │
         └────────────────┼────────────────┘
                          │
    ══════════════════════╪══════════════════════
                          │
         ┌────────────────┼────────────────┐
         │                │                │
      Artifact         Adoption         Impact
      Existence        Metrics          Footprint
         │                │                │
         └────────────────┼────────────────┘
                          │
                    EXTRINSIC IMPACT
                    (Real-world outcomes)
```

**Intrinsic Quality:** Assessable from the paper alone, applicable to any paper regardless of age.

**Extrinsic Impact:** Requires observable real-world outcomes, applicable only to papers with sufficient history (typically 3+ years).

### 2.2 The Formalism Necessity Principle

Formalism in a research paper is **necessary** if and only if it satisfies at least one of the following conditions:

1. **Enables Proof:** The formalism permits proving properties (correctness, termination, complexity bounds, security guarantees) that could not be established informally.

2. **Enforces Constraints:** The formal definitions include constraints (invariants, preconditions, type restrictions) that restrict the space of valid instances.

3. **Enables Generalization:** The formalism abstracts over specific instances in a way that enables application to a class of problems.

4. **Prevents Ambiguity:** The natural language equivalent would be genuinely ambiguous in ways that matter for the contribution.

Formalism is **unnecessary** (decorative) if:

- It merely names components without constraining them
- It restates prose descriptions in notation
- It is introduced but never referenced in analysis
- The implementation ignores it entirely

### 2.3 The Triviality Threshold

A concept has an inherent complexity baseline. Formalism complexity should be proportionate to concept complexity.

| Concept Class | Inherent Complexity | Expected Formalism |
|---------------|--------------------|--------------------|
| Data capture (logs, recordings) | Very Low | Minimal or none |
| CRUD operations | Low | Schema definitions only |
| Standard algorithms | Medium | Complexity analysis |
| Distributed protocols | High | Correctness proofs |
| Type systems | High | Soundness proofs |
| Cryptographic protocols | Very High | Security proofs |

**Red Line Principle:** When formalism complexity vastly exceeds concept complexity, the paper crosses a threshold into formalism theater. This is a disqualifying signal regardless of other factors.

---

## 3. Scoring Dimensions

### 3.1 Dimension Overview

The RUIN score comprises five dimensions, each scored 0-100:

| Dimension | Symbol | Applicable To | Weight (Mature) | Weight (Recent) |
|-----------|--------|---------------|-----------------|-----------------|
| Formalism Necessity | F | All papers | 0.20 | 0.40 |
| Structural Integrity | S | All papers | 0.15 | 0.30 |
| Artifact Existence | A | All papers | 0.15 | 0.20 |
| Adoption Metrics | D | Mature only | 0.25 | 0.05 |
| Impact Footprint | I | Mature only | 0.25 | 0.05 |

**Mature papers:** 3+ years since publication
**Recent papers:** < 3 years since publication

### 3.2 Dimension F: Formalism Necessity Score

This dimension assesses whether formal notation earns its presence.

#### 3.2.1 Component Signals

**F1: Definition Utilization Ratio (DUR)**

```
DUR = (Definitions referenced in theorems/proofs/analysis) / (Total definitions introduced)
```

- Extract all labeled definitions (Definition 1, Def. 2, etc.)
- Search for references to each definition in subsequent text
- Definitions referenced only in their own section score 0
- Definitions referenced in proofs/theorems score 1

Scoring:
- DUR ≥ 0.8: 100 points
- DUR 0.5-0.8: 70 points
- DUR 0.2-0.5: 40 points
- DUR < 0.2: 10 points

**F2: Theorem Density (TD)**

```
TD = (Theorems + Lemmas + Propositions with proofs) / (Pages of formal content)
```

Papers with heavy formalism should have correspondingly heavy analytical results.

Scoring:
- TD ≥ 1.0 (1+ theorem per formal page): 100 points
- TD 0.5-1.0: 70 points
- TD 0.1-0.5: 40 points
- TD < 0.1: 10 points
- TD = 0 (no theorems despite formalism): 0 points (RED FLAG)

**F3: Constraint Density in Definitions (CDD)**

Analyze each definition for constraining elements:

Constraining elements (positive signals):
- Universal quantifiers: ∀
- Existential quantifiers: ∃
- Subset/membership constraints: ⊆, ∈, ∉
- Inequality constraints: <, >, ≤, ≥, ≠
- Logical connectives with constraints: ∧, ∨, →, ↔
- Type constraints: :: , : Type

Non-constraining elements (neutral):
- Tuple formation: (a, b, c)
- Set enumeration: {x, y, z}
- Simple equality: =
- Naming: "let X be..."

```
CDD = (Definitions with ≥1 constraint) / (Total definitions)
```

Scoring:
- CDD ≥ 0.7: 100 points
- CDD 0.4-0.7: 70 points
- CDD 0.2-0.4: 40 points
- CDD < 0.2: 10 points

**F4: Formalism-Implementation Alignment (FIA)**

If the paper contains implementation (pseudocode, algorithms, code):

- Extract identifiers from formal sections
- Extract identifiers from implementation sections
- Calculate Jaccard similarity

```
FIA = |Formal_IDs ∩ Implementation_IDs| / |Formal_IDs ∪ Implementation_IDs|
```

Scoring:
- FIA ≥ 0.6: 100 points
- FIA 0.3-0.6: 70 points
- FIA 0.1-0.3: 40 points
- FIA < 0.1: 10 points (formalism disconnected from implementation)
- No implementation present: 50 points (neutral)

**F5: Concept-Formalism Proportionality (CFP)**

This is the critical "red line" detector.

Step 1: Extract the abstract and introduction (plain English description)
Step 2: Measure concept complexity proxies:
  - Number of distinct technical terms introduced
  - Presence of inherently complex concepts (see Section 2.3 table)
  - Reference to known-hard problems

Step 3: Measure formalism complexity:
  - Number of formal definitions
  - Number of unique symbols introduced
  - Nesting depth of formal expressions

Step 4: Calculate proportionality:

```
CFP = Concept_Complexity_Score / Formalism_Complexity_Score
```

Where both scores are normalized to [0, 1].

Scoring:
- CFP ≥ 0.8 (concept ≥ formalism): 100 points
- CFP 0.5-0.8: 70 points
- CFP 0.3-0.5: 40 points
- CFP < 0.3 (formalism >> concept): 0 points (RED FLAG)

#### 3.2.2 Composite Formalism Score

```
F = 0.20 * F1 + 0.25 * F2 + 0.20 * F3 + 0.15 * F4 + 0.20 * F5
```

#### 3.2.3 Red Flag Override

If ANY of the following conditions are met, the paper is flagged regardless of other scores:

- F2 (Theorem Density) = 0 AND total definitions > 5
- F5 (Concept-Formalism Proportionality) < 0.3
- F1 (Definition Utilization) < 0.1 AND total definitions > 10

A flagged paper receives a maximum RUIN score of 30, indicating "formalism theater detected."

---

### 3.3 Dimension S: Structural Integrity Score

This dimension assesses methodological soundness through structural signals.

#### 3.3.1 Component Signals

**S1: Claim-Evidence Ratio (CER)**

Extract sentences containing:
- Claim markers: "novel", "improves", "outperforms", "first", "significant", "better", "faster", "more accurate"
- Evidence markers: "Table", "Figure", "p <", "p =", "significant at", "confidence interval", "measured", "observed"

```
CER = Evidence_Sentences / Claim_Sentences
```

Scoring:
- CER ≥ 2.0: 100 points
- CER 1.0-2.0: 80 points
- CER 0.5-1.0: 50 points
- CER < 0.5: 20 points

**S2: Baseline Recency (BR)**

Extract cited baseline/comparison methods. Calculate median publication year of baselines.

```
BR = Paper_Year - Median_Baseline_Year
```

Scoring:
- BR ≤ 3 years: 100 points
- BR 3-5 years: 70 points
- BR 5-10 years: 40 points
- BR > 10 years: 10 points (comparing to obsolete methods)

**S3: Limitation Acknowledgment (LA)**

Search for limitation-indicating language:
- "limitation", "does not", "cannot", "fails when", "future work", "assumes", "restricted to"

```
LA = 1 if limitation section exists OR limitation sentences ≥ 3, else 0
```

Scoring:
- Explicit limitations section: 100 points
- Limitations mentioned (≥3 sentences): 70 points
- Minimal limitations (1-2 sentences): 40 points
- No limitations mentioned: 10 points

**S4: Reproducibility Indicators (RI)**

Check for presence of:
- Data availability statement: +25 points
- Code availability statement: +25 points
- Detailed hyperparameters/configuration: +25 points
- Environment specification (versions, hardware): +25 points

```
RI = sum of applicable indicators
```

#### 3.3.2 Composite Structural Score

```
S = 0.30 * S1 + 0.25 * S2 + 0.20 * S3 + 0.25 * S4
```

---

### 3.4 Dimension A: Artifact Existence Score

This dimension verifies that claimed artifacts actually exist.

#### 3.4.1 Component Signals

**A1: Repository Existence (RE)**

- Extract URLs from paper (regex for github.com, gitlab.com, bitbucket.org, etc.)
- HTTP HEAD request to verify existence

Scoring:
- Repository exists and is public: 100 points
- Repository exists but is private/restricted: 50 points
- URL mentioned but 404: 10 points
- No repository mentioned: 0 points

**A2: Repository Vitality (RV)**

If repository exists:
- Check last commit date
- Check commit count
- Check if commits exist after paper submission date

```
RV = f(commits_after_paper, total_commits, days_since_last_commit)
```

Scoring:
- Active (commits within 1 year, >10 total): 100 points
- Maintained (commits within 2 years): 70 points
- Stale (no commits for 2+ years): 30 points
- Dead (only initial commit): 10 points

**A3: Package Publication (PP)**

Check if artifact is published on package registries:
- npm (JavaScript)
- PyPI (Python)
- NuGet (.NET)
- Maven Central (Java)
- crates.io (Rust)
- CRAN (R)

Scoring:
- Published on major registry: 100 points
- Published on minor/domain registry: 70 points
- Not published: 0 points

**A4: Data Availability (DA)**

Check for dataset availability:
- Zenodo DOI
- Figshare link
- Institutional repository
- Direct download link

Scoring:
- Data available with DOI: 100 points
- Data available via URL: 70 points
- Data "available upon request": 20 points
- No data availability: 0 points

#### 3.4.2 Composite Artifact Score

```
A = 0.35 * A1 + 0.25 * A2 + 0.20 * A3 + 0.20 * A4
```

---

### 3.5 Dimension D: Adoption Metrics Score

This dimension measures real-world uptake. **Only applicable to papers ≥3 years old.**

#### 3.5.1 Component Signals

**D1: Repository Engagement (RE)**

From GitHub/GitLab API:
- Stars
- Forks
- Watchers

Normalized against field median (software engineering papers).

Scoring (percentile-based):
- Top 10%: 100 points
- Top 25%: 80 points
- Top 50%: 60 points
- Bottom 50%: 30 points
- No repository: 0 points

**D2: Download Metrics (DM)**

From package registries:
- Weekly downloads
- Total downloads
- Download trend (increasing/stable/decreasing)

Scoring (percentile-based within field):
- Top 10%: 100 points
- Top 25%: 80 points
- Top 50%: 60 points
- Bottom 50%: 30 points
- Not published: 0 points

**D3: Dependent Projects (DP)**

From Libraries.io or registry APIs:
- Number of packages depending on this artifact
- Number of repositories importing/using this

Scoring:
- ≥100 dependents: 100 points
- 10-100 dependents: 70 points
- 1-10 dependents: 40 points
- 0 dependents: 10 points

**D4: External Contributors (EC)**

From repository:
- Contributors beyond paper authors
- Pull requests from external users
- Issues opened by external users

Scoring:
- ≥10 external contributors: 100 points
- 3-10 external contributors: 70 points
- 1-2 external contributors: 40 points
- 0 external contributors: 10 points

#### 3.5.2 Composite Adoption Score

```
D = 0.30 * D1 + 0.25 * D2 + 0.25 * D3 + 0.20 * D4
```

---

### 3.6 Dimension I: Impact Footprint Score

This dimension measures broader real-world presence. **Only applicable to papers ≥3 years old.**

#### 3.6.1 Component Signals

**I1: Citation Quality (CQ)**

From Semantic Scholar / OpenAlex:
- Total citations
- Citations from industry-affiliated authors
- Citations in patents
- Self-citation ratio

```
CQ = f(total_citations, industry_citations, patent_citations) * (1 - self_citation_ratio)
```

Scoring (percentile-based):
- Top 10% in venue: 100 points
- Top 25%: 80 points
- Top 50%: 60 points
- Bottom 50%: 30 points

**I2: Practitioner References (PR)**

From web search:
- Stack Overflow mentions (questions/answers citing paper)
- Blog posts referencing the work
- Tutorial/course materials
- Conference talk slides

Scoring:
- ≥20 practitioner references: 100 points
- 10-20 references: 80 points
- 5-10 references: 60 points
- 1-5 references: 40 points
- 0 references: 10 points

**I3: Educational Adoption (EA)**

- Wikipedia citations
- Textbook references
- Course syllabus appearances
- Educational platform mentions (Coursera, edX, etc.)

Scoring:
- Wikipedia + textbook: 100 points
- Wikipedia OR textbook: 70 points
- Course materials only: 50 points
- None: 10 points

**I4: Industry Adoption Signals (IA)**

- Patents citing the paper
- Industry blog posts (engineering blogs from known companies)
- Product documentation references
- Job postings mentioning the technology

Scoring:
- Patent citations: 100 points
- Industry engineering blogs: 80 points
- Product documentation: 60 points
- Indirect signals only: 30 points
- None: 10 points

#### 3.6.2 Composite Impact Score

```
I = 0.30 * I1 + 0.25 * I2 + 0.20 * I3 + 0.25 * I4
```

---

## 4. Composite RUIN Score Calculation

### 4.1 For Mature Papers (≥3 years)

```
RUIN_mature = 0.20 * F + 0.15 * S + 0.15 * A + 0.25 * D + 0.25 * I
```

### 4.2 For Recent Papers (<3 years)

```
RUIN_recent = 0.40 * F + 0.30 * S + 0.20 * A + 0.05 * D + 0.05 * I
```

Note: D and I receive minimal weight for recent papers due to insufficient observation time. The score is dominated by intrinsic quality signals (F, S) and artifact existence (A).

### 4.3 Red Flag Override

If any red flag conditions from Section 3.2.3 are triggered:

```
RUIN_final = min(RUIN_calculated, 30)
FLAG = "FORMALISM_THEATER_DETECTED"
```

### 4.4 Score Interpretation

| Score Range | Interpretation |
|-------------|----------------|
| 80-100 | High utility: Genuine contribution with real-world impact |
| 60-80 | Moderate utility: Sound work with some practical relevance |
| 40-60 | Limited utility: Technically acceptable but limited evidence of value |
| 20-40 | Low utility: Questionable contribution or formalism concerns |
| 0-20 | Minimal utility: Likely formalism theater or no observable impact |

### 4.5 Classification Thresholds for Journal-Level Analysis

When analyzing journals to count papers with utility concerns, use the following tiered classification system:

#### 4.5.1 Tiered Classification

| Score Range | Classification | Label | Description |
|-------------|----------------|-------|-------------|
| < 25 | **Critical** | `CRITICAL_CONCERN` | Likely formalism theater or no demonstrated value whatsoever |
| 25-40 | **Concerning** | `LOW_UTILITY` | Significant utility gaps; questionable contribution |
| 40-55 | **Limited** | `LIMITED_UTILITY` | Acceptable but unexceptional; minimal impact evidence |
| 55-70 | **Adequate** | `ADEQUATE` | Solid work with some demonstrated practical relevance |
| > 70 | **Strong** | `HIGH_UTILITY` | Genuine contribution with clear real-world footprint |

#### 4.5.2 Recommended Binary Threshold

For counting "low quality" or "low utility" papers in a journal:

**Primary threshold: 40**

Papers scoring below 40 are classified as having utility concerns.

Rationale:
- Captures papers with formalism theater (F-score failures)
- Captures papers with no artifacts or adoption (A/D/I failures)
- Aligns with "Low utility" interpretation band
- Validated against pilot cases (see Section 4.5.4)

#### 4.5.3 Alternative Thresholds

| Threshold | Use Case | Trade-off |
|-----------|----------|-----------|
| **30** (strict) | Identifying clear formalism theater | High precision, may miss papers that are merely useless |
| **40** (balanced) | General utility assessment | Balanced precision/recall |
| **50** (aggressive) | Stringent quality bar | Higher false positive rate, use with caution |

#### 4.5.4 Threshold Validation Cases

The thresholds were validated against manually-assessed papers:

| Paper | RUIN Score | Classification | Assessment |
|-------|------------|----------------|------------|
| LifeTags++ (ROMJIST 2022) | 21 | Critical | Formalism theater: trivial concept over-formalized |
| Fall Detection (ROMJIST 2020) | 34.5 | Concerning | Sound method but no artifacts, no adoption |

Both papers correctly fall below the 40 threshold, but for different reasons:
- LifeTags++ fails on **formalism necessity** (decorative notation)
- Fall Detection fails on **practical availability** (no implementation to use)

This demonstrates RUIN's multi-dimensional assessment: papers can fail on rigor OR utility.

#### 4.5.5 Red Flag Integration

In addition to score thresholds, track red flags separately:

| Flag | Meaning | Severity |
|------|---------|----------|
| `FORMALISM_THEATER_DETECTED` | Decorative formalism identified | Critical |
| `TRIVIAL_CONCEPT_OVER_FORMALIZED` | Level 1-2 concept with excessive formalism | Critical |
| `DISPROPORTIONATE_FORMALISM` | Formalism >> concept complexity | High |
| `ORPHAN_DEFINITIONS` | Definitions introduced but never used | Medium |

A paper can score above 40 but still have red flags (e.g., if adoption metrics inflate the score despite formalism concerns). Report both.

---

## 5. Handling Recent Papers: The Intrinsic Analysis Protocol

For papers less than 3 years old, extrinsic signals are unreliable. The framework relies on intrinsic analysis with emphasis on formalism detection.

### 5.1 The Triviality Detection Algorithm

This algorithm determines if a paper formalizes trivial concepts unnecessarily.

#### Step 1: Concept Extraction

From abstract and introduction, extract:
- Primary problem statement
- Core technical concepts
- Domain/application area

#### Step 2: Concept Complexity Classification

Match extracted concepts against complexity taxonomy:

**Complexity Level 1 (Trivial):**
- Data logging, recording, capture
- File format conversion
- Simple CRUD operations
- Configuration management
- Basic UI interactions
- Wrapper/adapter implementations

**Complexity Level 2 (Low):**
- Standard data structures
- Common design patterns
- Straightforward optimizations
- Integration of existing tools
- Domain-specific applications of known techniques

**Complexity Level 3 (Medium):**
- Novel algorithms with complexity analysis
- System architectures with tradeoffs
- Empirical studies with statistical analysis
- Comparisons requiring controlled experiments

**Complexity Level 4 (High):**
- Distributed systems with consistency requirements
- Security protocols requiring formal verification
- Type systems with soundness requirements
- Optimization problems with provable bounds
- Machine learning with theoretical guarantees

**Complexity Level 5 (Very High):**
- Cryptographic protocols
- Formal verification of critical systems
- Complexity-theoretic results
- Novel mathematical foundations

#### Step 3: Formalism Complexity Measurement

Count and categorize formal elements:

| Element Type | Weight |
|--------------|--------|
| Simple definition (naming only) | 1 |
| Definition with constraints | 2 |
| Lemma without proof | 2 |
| Lemma with proof | 4 |
| Theorem without proof | 3 |
| Theorem with proof | 5 |
| Complexity analysis | 3 |
| Formal verification | 5 |

```
Formalism_Complexity = Σ (element_count * weight)
```

#### Step 4: Proportionality Assessment

```
Expected_Formalism_Range = f(Concept_Complexity_Level)

Level 1: 0-5
Level 2: 0-15
Level 3: 10-40
Level 4: 30-80
Level 5: 60-150
```

If `Formalism_Complexity > 2 * Expected_Upper_Bound`:
- Flag as DISPROPORTIONATE_FORMALISM

If `Concept_Complexity_Level ≤ 2` AND `Formalism_Complexity > 20`:
- Flag as TRIVIAL_CONCEPT_OVER_FORMALIZED

### 5.2 Recent Paper Score Confidence

For recent papers, report score with confidence interval:

```
RUIN_recent ± confidence_margin

Where confidence_margin = 15 for papers < 1 year
                        = 10 for papers 1-2 years
                        = 5 for papers 2-3 years
```

The confidence margin decreases as more time passes and early adoption signals emerge.

---

## 6. Data Sources and APIs

### 6.1 Paper Metadata and Content

| Source | Data Provided | API |
|--------|---------------|-----|
| Semantic Scholar | Citations, abstracts, authors, venues | api.semanticscholar.org |
| OpenAlex | Citations, institutions, open access status | api.openalex.org |
| CrossRef | DOIs, references, metadata | api.crossref.org |
| arXiv | Preprints, source files, categories | arxiv.org/api |
| DBLP | CS publication records | dblp.org/search/publ/api |

### 6.2 Artifact Verification

| Source | Data Provided | API |
|--------|---------------|-----|
| GitHub | Repository stats, commits, contributors | api.github.com |
| GitLab | Repository stats | gitlab.com/api/v4 |
| npm | Package downloads, dependents | registry.npmjs.org |
| PyPI | Package downloads | pypi.org/pypi/[pkg]/json |
| Libraries.io | Cross-registry dependencies | libraries.io/api |
| Zenodo | Dataset availability | zenodo.org/api |

### 6.3 Impact Signals

| Source | Data Provided | API |
|--------|---------------|-----|
| Google Patents | Patent citations | patents.google.com |
| Stack Exchange | Q&A mentions | api.stackexchange.com |
| Wikipedia | Encyclopedia citations | en.wikipedia.org/w/api.php |
| Web Search | General web presence | (various) |

---

## 7. Validation Strategy

### 7.1 Predictive Validation (No Human Judgment)

**Protocol:**

1. Select papers from 2015-2018 (sufficient history)
2. Calculate RUIN scores using only 2018-available signals
3. Measure correlation with 2025 outcomes:
   - GitHub stars (2025)
   - Package downloads (2025)
   - Citation count (2025)
   - Continued development activity

**Success criteria:**
- RUIN score should predict long-term outcomes better than venue impact factor
- RUIN score should not correlate strongly with impact factor (measuring different things)

### 7.2 Extreme Case Validation

**Protocol:**

1. Identify papers with known extreme outcomes:
   - **Clearly impactful:** Tools with >10k GitHub stars, cited in textbooks
   - **Clearly negligible:** Zero citations after 5 years, dead repositories

2. Calculate RUIN scores
3. Verify separation: impactful papers should score >70, negligible papers should score <30

### 7.3 Formalism Theater Detection Validation

**Protocol:**

1. Programmatically identify papers with high formalism density
2. Calculate F5 (Concept-Formalism Proportionality)
3. Manual spot-check of papers flagged as TRIVIAL_CONCEPT_OVER_FORMALIZED
4. Calculate precision: what fraction of flagged papers are genuinely problematic?

Target: >80% precision on formalism theater detection

---

## 8. Limitations and Scope

### 8.1 Explicitly Out of Scope

This framework is designed for **computer science papers with potential practical application**. It is NOT appropriate for:

- Pure mathematics (different validity criteria)
- Theoretical physics (different timescales)
- Humanities and social sciences (different evidence standards)
- Survey/review papers (synthesis vs original contribution)
- Negative results papers (valuable but won't show adoption)

### 8.2 Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Bias toward applied work | Penalizes legitimate theory | Separate track for foundational CS theory |
| Temporal lag | Cannot assess very recent papers reliably | Confidence intervals, provisional scores |
| Gaming potential | Authors may create fake artifacts | Multi-signal detection, anomaly flagging |
| Field variation | Different CS subfields have different norms | Field-specific normalization |
| Language bias | English-centric sources | Acknowledged limitation |

### 8.3 Ethical Considerations

- Scores should not be used for individual career decisions
- Journal-level aggregates are more reliable than paper-level scores
- Framework should be transparent to enable critique
- Negative assessments should be verifiable through cited evidence

---

## 9. Implementation Roadmap

### Phase 1: Proof of Concept

- Single subfield (Software Engineering)
- Two journals (one practical, one formal)
- 100 papers from 2018-2020
- Manual verification of automated signals

### Phase 2: Calibration

- Expand to 500 papers across 5 venues
- Determine field-specific normalization parameters
- Validate formalism detection precision
- Tune component weights based on predictive validity

### Phase 3: Scale

- Full automation pipeline
- Coverage of major CS venues
- Historical analysis (2010-2022)
- Public dashboard with methodology documentation

### Phase 4: Analysis and Publication

- Journal-level RUIN profiles vs impact factors
- Trend analysis: is formalism theater increasing?
- Subfield comparisons
- Policy recommendations for publishers and funding agencies

---

## 10. Building the Case Against Quartile Rankings

This section outlines how to construct a compelling, evidence-based argument challenging the adequacy of citation-based quartile rankings using RUIN analysis.

### 10.1 The Core Argument

**Thesis:** Journal quartile rankings (Q1-Q4) based on citation metrics conflate *attention* with *value*. A paper can be highly cited yet provide minimal real-world utility, while genuinely useful work may receive few citations.

**RUIN provides evidence for this thesis by:**
1. Measuring utility independently of citations
2. Detecting formalism theater that passes peer review
3. Quantifying the prevalence of low-utility papers in high-impact venues
4. Demonstrating weak correlation between utility and impact factor

### 10.2 Four Pillars of Evidence

To build a compelling case, gather evidence across four dimensions:

#### Pillar 1: Low Correlation Between RUIN and Impact Factor

**Analysis:**
```
For each journal:
  1. Calculate RUIN scores for N papers (N ≥ 50)
  2. Obtain journal Impact Factor (JIF)
  3. Calculate Pearson correlation: r(mean_RUIN, JIF)
```

**Expected finding:** Weak correlation (|r| < 0.3)

**Interpretation:** If RUIN and JIF were measuring the same thing, correlation would be strong. Weak correlation demonstrates they capture different constructs—RUIN measures utility, JIF measures attention.

**Visualization:**
```
                    RUIN Score vs Impact Factor
    100 ┤
        │                    ○
     80 ┤        ○                      ○
        │    ○       ○   ○
     60 ┤  ○    ○ ○    ○     ○    ○
  RUIN  │    ○     ○  ○   ○      ○
     40 ┤ ○    ○   ○ ○  ○    ○
        │   ○  ○ ○    ○   ○
     20 ┤○       ○
        │
      0 ┼────────────────────────────────
        0     2     4     6     8    10
                 Impact Factor

        r = 0.18 (weak correlation)
```

#### Pillar 2: High Variance in RUIN Scores Within Q1 Journals

**Analysis:**
```
For Q1 journals:
  1. Calculate RUIN scores for all sampled papers
  2. Compute variance, standard deviation, and range
  3. Report score distribution (quartiles within the journal)
```

**Expected finding:** High variance within Q1 journals

**Interpretation:** If Q1 status guaranteed quality, variance would be low. High variance demonstrates that Q1 contains both excellent and poor papers—the quartile label provides weak signal about individual paper quality.

**Visualization:**
```
RUIN Score Distribution Within Q1 Journals
═══════════════════════════════════════════

Journal A (IF: 8.2)     ├────[████████████]────────┤
                        0    25   40    60    80  100

Journal B (IF: 6.5)     ├──────[████████]──────────┤
                        0    30   45    65    85  100

Journal C (IF: 7.8)     ├───[██████████████]──────┤
                        0  20   35    55    75  100

                        ▲         ▲
                   Low-utility  High-utility
                    papers       papers

All three Q1 journals contain papers across the full utility spectrum.
```

#### Pillar 3: Formalism Theater Prevalence in High-Impact Venues

**Analysis:**
```
For each journal:
  1. Count papers with RED FLAGS triggered
  2. Calculate prevalence: flagged_papers / total_papers
  3. Compare prevalence across quartiles
```

**Expected finding:** Formalism theater exists even in Q1 journals

**Interpretation:** If peer review at top venues reliably filtered out decorative formalism, prevalence would be near zero. Non-zero prevalence demonstrates that appearing rigorous (formalism theater) can pass review at prestigious venues.

**Report format:**
```
Formalism Theater Prevalence by Quartile
════════════════════════════════════════

Quartile    Papers    Flagged    Prevalence
────────    ──────    ───────    ──────────
Q1          200       18         9.0%
Q2          200       24         12.0%
Q3          200       31         15.5%
Q4          200       42         21.0%

Key finding: Even Q1 journals have ~9% formalism theater rate.
This means approximately 1 in 11 Q1 papers exhibits decorative
formalism that adds no analytical value.
```

#### Pillar 4: Extreme Case Examples

**Analysis:**
Identify papers at the extremes of the RUIN-vs-citation distribution:

| Quadrant | RUIN | Citations | Example Type |
|----------|------|-----------|--------------|
| **High-High** | >70 | High | Genuine success (validates that useful work can be recognized) |
| **High-Low** | >70 | Low | Hidden gems (useful work overlooked by citations) |
| **Low-High** | <40 | High | Attention without utility (challenges citation validity) |
| **Low-Low** | <40 | Low | Appropriate obscurity (system working correctly) |

**The critical quadrant is Low-High:** Papers with low utility but high citations directly contradict the premise that citations indicate value.

**Example analysis:**
```
Case Study: Paper X
───────────────────
Venue: Q1 Journal (IF: 7.5)
Citations: 89
RUIN Score: 24

Breakdown:
  F (Formalism): 15/100 - RED FLAG: Trivial concept over-formalized
  S (Structure): 55/100 - Adequate methodology
  A (Artifact): 0/100 - No code or data provided
  D (Adoption): 5/100 - No evidence of real-world use
  I (Impact): 35/100 - Citations but no practitioner uptake

Analysis: This paper received 89 citations despite providing no
usable artifact and formalizing a trivial concept. Citations came
from other papers in the same niche, not from practical adoption.
This exemplifies attention without utility.
```

### 10.3 Journal Analysis Report Template

When analyzing a journal, produce a comprehensive report:

```
════════════════════════════════════════════════════════════════════
RUIN ANALYSIS REPORT: [Journal Name]
════════════════════════════════════════════════════════════════════

JOURNAL METADATA
────────────────
Impact Factor: X.XX
Quartile: Q1/Q2/Q3/Q4
Papers Analyzed: N
Time Period: YYYY-YYYY

SCORE DISTRIBUTION
──────────────────
Mean RUIN Score:        XX.X
Median RUIN Score:      XX.X
Standard Deviation:     XX.X
Range:                  XX - XX

Distribution by Classification:
  Critical   (< 25):    XX%  ████████
  Concerning (25-40):   XX%  ██████████████
  Limited    (40-55):   XX%  ████████████████████
  Adequate   (55-70):   XX%  ██████████████
  Strong     (> 70):    XX%  ██████

RED FLAGS
─────────
Papers with any red flag:           XX (XX.X%)
  FORMALISM_THEATER_DETECTED:       XX
  TRIVIAL_CONCEPT_OVER_FORMALIZED:  XX
  DISPROPORTIONATE_FORMALISM:       XX
  ORPHAN_DEFINITIONS:               XX

DIMENSION BREAKDOWN
───────────────────
Average scores by dimension:
  F (Formalism Necessity):  XX.X/100
  S (Structural Integrity): XX.X/100
  A (Artifact Existence):   XX.X/100
  D (Adoption Metrics):     XX.X/100
  I (Impact Footprint):     XX.X/100

Weakest dimension: [X] - indicates systematic gap in [interpretation]

CORRELATION ANALYSIS
────────────────────
Correlation (RUIN vs Citations):     r = X.XX
Correlation (RUIN vs Impact Factor): r = X.XX

Interpretation: [Weak/Moderate/Strong] correlation suggests
[RUIN captures different construct / aligns with existing metrics]

KEY FINDINGS
────────────
1. [Finding about utility distribution]
2. [Finding about formalism theater prevalence]
3. [Finding about artifact availability]
4. [Comparison with journal's stated scope/mission]

NOTABLE PAPERS
──────────────
Highest RUIN (XX): [Paper title] - [Brief description]
Lowest RUIN (XX):  [Paper title] - [Brief description]
Most cited but low RUIN: [Paper title] - [Citation count, RUIN score]

════════════════════════════════════════════════════════════════════
```

### 10.4 Interpreting Statistical Measures

This section provides guidance on interpreting the statistical measures in journal analysis reports.

#### 10.4.1 Standard Deviation (SD)

**What it measures:** How spread out the scores are from the average. It answers: "How much do individual papers vary from the typical paper in this journal?"

**Interpretation thresholds:**

| SD Value | Interpretation |
|----------|----------------|
| **Low (< 10)** | Papers are consistently similar in quality. The journal has uniform standards. |
| **Medium (10-20)** | Normal variation. Mix of stronger and weaker papers. |
| **High (> 20)** | Wild inconsistency. Some excellent papers, some poor ones. The journal label tells you little about any individual paper. |

**Example:**
```
Journal A: Mean RUIN = 55, SD = 8
  Papers cluster tightly: most score 47-63
  Interpretation: Consistent quality, predictable

Journal B: Mean RUIN = 55, SD = 25
  Papers spread widely: scores range from 30 to 80
  Interpretation: Same average, but unreliable—
  some papers are strong, others are weak
```

**For the quartile argument:** High SD within Q1 journals is damning evidence. It proves that "Q1" doesn't guarantee individual paper quality—you could get a 75 or a 25, both wearing the Q1 label.

#### 10.4.2 Mean vs Median

| Measure | Definition | Best When |
|---------|------------|-----------|
| **Mean** | Sum of all scores ÷ number of papers | Distribution is symmetric, no extreme outliers |
| **Median** | The middle score when sorted | Distribution is skewed or has outliers |

**Why report both:**

```
Journal C: 10 papers with scores
  [65, 62, 58, 55, 54, 52, 48, 45, 22, 18]

  Mean:   47.9
  Median: 53.0
```

The mean (47.9) is dragged down by two poor papers (22, 18). The median (53.0) better represents the "typical" paper—half score above 53, half below.

**Interpreting the gap:**

| Scenario | What It Suggests |
|----------|------------------|
| Mean ≈ Median | Symmetric distribution. Journal is consistently mediocre or consistently good. |
| Mean < Median | Left-skewed. A few terrible papers drag down the average. Most papers are okay, but the journal occasionally publishes poor work. |
| Mean > Median | Right-skewed. A few excellent papers inflate the average. Most papers are mediocre, but occasional strong work gets through. |

**Reporting recommendation:**

If mean and median differ by more than 5 points, note it explicitly:

> "The 5-point gap between mean (47.9) and median (53.0) indicates a left-skewed distribution with outlier low-quality papers."

#### 10.4.3 Statistical Significance for Journal Comparisons

When comparing two journals, consider whether observed differences are meaningful:

| Sample Size (per journal) | Meaningful Difference |
|---------------------------|----------------------|
| N < 20 | Differences < 10 points may be noise |
| N = 20-50 | Differences > 5 points likely meaningful |
| N > 50 | Differences > 3 points likely meaningful |

For formal statistical testing, use a two-sample t-test or Mann-Whitney U test to determine if journal mean/median differences are statistically significant.

### 10.5 Constructing the Narrative

When presenting findings, structure the argument as follows:

**1. Establish the problem (Introduction)**
- Citation metrics dominate research assessment
- Quartile rankings influence hiring, funding, promotion
- Implicit assumption: high citations = high quality/utility

**2. Introduce RUIN as an alternative lens (Methods)**
- Measures utility through multiple independent signals
- Detects formalism theater automatically
- Does not rely on citations (orthogonal measurement)

**3. Present the four pillars of evidence (Results)**
- Low correlation between RUIN and impact factor
- High variance within Q1 journals
- Non-trivial formalism theater prevalence
- Extreme case examples (high citations, low utility)

**4. Interpret implications (Discussion)**
- Q1 status does not guarantee individual paper quality
- Formalism theater passes peer review at top venues
- Citation counts conflate attention with value
- Current system may incentivize appearance over substance

**5. Propose complementary assessment (Conclusion)**
- RUIN as additional signal, not replacement
- Multi-dimensional evaluation over single metrics
- Transparency about what metrics actually measure

### 10.6 Anticipated Objections and Responses

| Objection | Response |
|-----------|----------|
| "RUIN is biased toward applied work" | Acknowledged. RUIN measures practical utility, not theoretical elegance. For pure theory, different criteria apply. This is a feature, not a bug—it reveals that "quality" is multidimensional. |
| "Low RUIN papers may become important later" | Possible. Use confidence intervals for recent papers. For mature papers (5+ years), lack of adoption is meaningful signal. |
| "Who decides what's 'trivial'?" | The triviality taxonomy is explicit and auditable. Disagreement about classification is legitimate scholarly debate—but the current system has no such transparency. |
| "This could harm researchers unfairly" | Report journal-level aggregates, not individual paper scores. Use for systemic analysis, not career decisions. |
| "Impact factor works well enough" | For what purpose? IF predicts future citations. RUIN predicts practical utility. These are different goals. If you care about real-world impact, IF is the wrong metric. |

### 10.7 Success Criteria

The argument against quartile rankings succeeds if:

1. **Empirical:** Demonstrated weak correlation (|r| < 0.3) between RUIN and impact factor across multiple venues

2. **Illustrative:** Identified concrete examples of high-citation/low-utility papers in Q1 journals

3. **Systematic:** Quantified formalism theater prevalence showing non-trivial rates even in top venues

4. **Constructive:** Proposed RUIN as complementary signal rather than attacking existing metrics as worthless

5. **Reproducible:** Published methodology and (ideally) tool enabling others to verify and extend findings

---

## 11. Practical Next Steps

This section outlines concrete actions for initiating work on the RUIN framework.

### 11.1 Pilot Testing Protocol

Before building automation, manually validate the scoring logic:

1. **Select 10-20 papers you have personally read**
   - Include papers you consider genuinely valuable
   - Include papers you consider suspect or low-quality
   - Include a mix of recent and mature papers

2. **Walk through scoring manually**
   - Apply each dimension (F, S, A, D, I) by hand
   - Document where the scoring rubric is ambiguous
   - Note cases where your intuition disagrees with the calculated score

3. **Identify specification gaps**
   - Which signals were hard to extract?
   - Which thresholds felt wrong?
   - What patterns did you notice that aren't captured?

4. **Iterate on the specification**
   - Refine scoring thresholds based on pilot results
   - Add missing patterns to the Formalism Pattern Library
   - Adjust weights if certain dimensions dominate inappropriately

### 11.2 Pattern Library Expansion

The Formalism Pattern Library (Appendix A) should grow through ongoing observation:

**Collection Process:**
- When reading papers, note formalism patterns (both legitimate and decorative)
- Document each pattern with:
  - A concrete example (anonymized if from a real paper)
  - Detection heuristics (how an automated system could identify it)
  - Classification rationale (why it is legitimate or decorative)

**Pattern Categories to Expand:**
- Domain-specific patterns (e.g., ML papers, systems papers, PL papers)
- Emerging anti-patterns (new forms of formalism theater)
- Edge cases (patterns that are context-dependent)

**Goal:** Build a comprehensive detection ruleset that improves precision over time.

### 11.3 Venue Selection for Proof of Concept

The proof of concept should compare venues with contrasting orientations:

**Recommended Pairings:**

| Practical Venue | Formal Venue | Rationale |
|-----------------|--------------|-----------|
| SoftwareX | TOPLAS | Maximum contrast: pure software vs pure PL theory |
| JSS (Journal of Systems and Software) | TOSEM | Both respected, different orientations |
| JOSS (Journal of Open Source Software) | Formal Aspects of Computing | Artifact-focused vs proof-focused |
| EMSE (Empirical Software Engineering) | Science of Computer Programming | Empirical vs formal methods |

**Selection Criteria:**
- Both venues should be established (sufficient paper volume)
- Both should be in the same broad field (software/CS)
- Impact factors should be comparable (controls for prestige effects)
- Papers should be accessible (open access preferred for automation)

**Initial Recommendation:** Start with **JSS vs TOSEM**
- Both are Q1 in Software Engineering
- Large paper volumes (statistical power)
- Different editorial orientations (practical vs formal)
- Findings would be directly relevant to the SE community

### 11.4 Publication Strategy for the Framework Itself

This meta-research—a framework critiquing publication quality metrics—is itself publishable.

**Potential Venues:**

| Venue | Angle | Fit |
|-------|-------|-----|
| **Scientometrics** | Novel bibliometric methodology | High (core audience) |
| **JASIST** | Information science, research assessment | High |
| **Quantitative Science Studies** | Open access, quantitative methods | High |
| **EMSE** | Empirical study of SE publication patterns | Medium-High |
| **CACM** | Viewpoint/opinion piece on publication quality | Medium (if framed broadly) |
| **SoftwareX** | The RUIN tool itself as software contribution | Medium (tool must exist) |
| **PLoS ONE** | Broad science audience, open access | Medium |

**Recommended Publication Arc:**

1. **First publication:** Methodology paper in Scientometrics or JASIST
   - Focus: Framework design, validation approach, initial results
   - Contribution: Novel metric for research utility assessment

2. **Second publication:** Empirical study in EMSE or JSS
   - Focus: Large-scale analysis of SE venues using RUIN
   - Contribution: Evidence on formalism theater prevalence, utility vs citations

3. **Third publication:** Tool paper in SoftwareX or JOSS
   - Focus: The automated RUIN scoring system
   - Contribution: Reusable tool for the community

4. **Optional:** Position paper in CACM or IEEE Software
   - Focus: Implications for publication policy, funding decisions
   - Contribution: Agenda-setting for research assessment reform

**The Irony:**
Publishing a critique of citation-based metrics will itself be judged by citation-based metrics. This tension should be acknowledged explicitly in the paper—it strengthens rather than weakens the argument.

**Mitigating Reviewer Resistance:**
- Emphasize that RUIN complements (not replaces) existing metrics
- Acknowledge limitations prominently
- Frame as "additional signal" rather than "replacement"
- Include validation showing RUIN captures something different from impact factor

---

## 12. Appendix A: Formalism Pattern Library

### A.1 Decorative Formalism Patterns (Red Flags)

**Pattern: Tuple-Everything**
```
"Let S = (A, B, C) where A is the set of users, B is the set of items,
and C is the set of interactions."
```
Red flag: Pure naming, no constraints. Equivalent to "The system has users, items, and interactions."

**Pattern: Set-Theoretic Obviousness**
```
"We define the operation process: Input → Output such that
∀i ∈ Input, process(i) ∈ Output"
```
Red flag: Restates that a function maps inputs to outputs.

**Pattern: Orphan Definitions**
```
Definition 1: [complex formal definition]
Definition 2: [complex formal definition]
...
Section 4 Implementation: [no reference to definitions]
```
Red flag: Definitions never used.

**Pattern: Pseudo-Formalism**
```
"Algorithm 1: The XYZ Algorithm
Input: data
Output: result
1. Process the data
2. Return the result"
```
Red flag: Pseudocode that could be English prose.

### A.2 Legitimate Formalism Patterns

**Pattern: Proof-Enabling Definition**
```
"Definition: A schedule S is serializable iff ∃ serial schedule S'
such that S ≡ S' under conflict equivalence.

Theorem: Algorithm A produces only serializable schedules.
Proof: [References definition, proves property]"
```
Legitimate: Definition enables proof of important property.

**Pattern: Constraint-Rich Structure**
```
"A well-formed query tree T = (N, E, λ) where:
- N is a set of nodes with N = N_scan ∪ N_join ∪ N_project
- E ⊆ N × N forms a tree structure
- λ: N → Schema, with ∀(n,m) ∈ E: compatible(λ(n), λ(m))
- |{n ∈ N : parent(n) = ⊥}| = 1"
```
Legitimate: Constraints are meaningful and enable verification.

---

## 13. Appendix B: Glossary

| Term | Definition |
|------|------------|
| RUIN Score | Rigor, Utility, Impact, Necessity — composite score (0-100) |
| Formalism Theater | Use of formal notation to create appearance of rigor without analytical value |
| Intrinsic Quality | Properties assessable from paper alone |
| Extrinsic Impact | Properties requiring real-world observation |
| DUR | Definition Utilization Ratio |
| CFP | Concept-Formalism Proportionality |
| Red Flag | Condition that caps maximum possible score |

---

## 14. Document History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | December 2025 | Initial draft |
| 0.2 | December 2025 | Added Section 11 (Practical Next Steps) |
| 0.3 | December 2025 | Added Section 4.5 (Classification Thresholds); Added Section 10 (Building the Case Against Quartile Rankings); Renumbered sections |
| 0.4 | December 2025 | Renamed acronym expansion from "Research Utility and Impact Necessity" to "Rigor, Utility, Impact, Necessity" |
| 0.5 | December 2025 | Added Section 10.4 (Interpreting Statistical Measures): SD interpretation, mean vs median guidance, significance thresholds |

---

*This framework is a work in progress. Feedback and critique are welcome.*
