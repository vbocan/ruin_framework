"""Canonical RUIN scoring rules.

This module is the single authority for every *derived* quantity in a RUIN
analysis. The division of labour it enforces is deliberate:

    The model supplies judgments.   Code supplies arithmetic.

An analysis run (whether performed by a language model or a human assessor)
produces only the fields that require judgment:

    * the four component scores -- formalism, citation_integrity,
      structural_integrity, artifact_availability
    * the set of flags raised
    * the narrative provenance record

Everything else -- intellectual_integrity, composite, final, the
disqualification decision, and the classification band -- is *derived* from
those judgments by :func:`derive`. Derived fields are never authored by the
assessor.

Earlier revisions of this pipeline let the assessor report derived fields
directly. Because a language model performs arithmetic unreliably, the
published batch files drifted from their own specification: weighted sums were
mis-added, the disqualification cap was applied to some flagged papers but not
others, and classification bands were occasionally assigned inconsistently with
the score they accompanied. Centralising the arithmetic here removes that class
of error by construction, and :mod:`rescore` re-derives the published corpus so
that the archived data and the specification agree exactly.

Reference: framework/scoring.md, framework/flags.md.
"""

from __future__ import annotations

from typing import Iterable, Mapping

# ---------------------------------------------------------------------------
# Component weights
# ---------------------------------------------------------------------------

#: Weights combining the three intellectual-integrity components.
FORMALISM_WEIGHT = 0.40
CITATION_WEIGHT = 0.35
STRUCTURAL_WEIGHT = 0.25

#: Weights combining intellectual integrity with artifact availability.
INTELLECTUAL_WEIGHT = 0.75
ARTIFACT_WEIGHT = 0.25

# ---------------------------------------------------------------------------
# Flag severity
# ---------------------------------------------------------------------------

#: Flags that cap the final score at :data:`DISQUALIFYING_CAP`.
#:
#: A disqualifying flag denotes a condition severe enough that no combination
#: of strengths on other dimensions compensates for it.
DISQUALIFYING_FLAGS = frozenset({
    "FORMALISM_THEATER",
    "UNNECESSARY_SET_THEORY",
    "DECORATIVE_DEFINITIONS",
    "DISPROPORTIONATE_FORMALISM",
    "IRRELEVANT_SELF_CITATION",
    "CITATION_RING_INDICATOR",
    "EXCESSIVE_SELF_CITATION",
})

#: Flags deducting :data:`HIGH_SEVERITY_PENALTY` points each.
HIGH_SEVERITY_FLAGS = frozenset({
    "ORPHAN_DEFINITIONS",
    "THEOREMLESS_FORMALISM",
    "UNSUPPORTED_CLAIMS",
})

#: Flags deducting :data:`MEDIUM_SEVERITY_PENALTY` points each.
MEDIUM_SEVERITY_FLAGS = frozenset({
    "ELEVATED_FORMALISM",
    "NO_LIMITATIONS",
    "ELEVATED_SELF_CITATION",
})

#: Flags recording a processing outcome rather than a quality judgment. A
#: record carrying one of these is not a research paper and is excluded from
#: every statistic the manuscript reports.
TECHNICAL_FLAGS = frozenset({
    "EDITORIAL",
    "PDF_CORRUPTED",
})

#: Ceiling imposed on a disqualified paper's final score.
#:
#: The value is 24 rather than 25 so that a disqualified paper lands inside the
#: CRITICAL band (0-24). A cap of 25 would place it in CONCERNING, contradicting
#: the intent that disqualification and CRITICAL classification coincide.
DISQUALIFYING_CAP = 24.0

HIGH_SEVERITY_PENALTY = 15.0
MEDIUM_SEVERITY_PENALTY = 5.0

# ---------------------------------------------------------------------------
# Classification bands
# ---------------------------------------------------------------------------

#: Lower bound of each classification band, ordered from highest to lowest.
CLASSIFICATION_BANDS = (
    (80.0, "STRONG"),
    (60.0, "ADEQUATE"),
    (40.0, "LIMITED"),
    (25.0, "CONCERNING"),
    (0.0, "CRITICAL"),
)

#: Record types. Only ``research`` records enter the reported statistics.
RECORD_RESEARCH = "research"
RECORD_EDITORIAL = "editorial"
RECORD_UNREADABLE = "unreadable"

COMPONENT_FIELDS = (
    "formalism",
    "citation_integrity",
    "structural_integrity",
    "artifact_availability",
)

DERIVED_FIELDS = ("intellectual_integrity", "composite", "final")


def classify(final: float) -> str:
    """Return the classification band for a final score."""
    for threshold, label in CLASSIFICATION_BANDS:
        if final >= threshold:
            return label
    return "CRITICAL"


def record_type(flags: Iterable[str]) -> str:
    """Classify a record as research, editorial, or unreadable, from its flags."""
    flagset = set(flags)
    if "PDF_CORRUPTED" in flagset:
        return RECORD_UNREADABLE
    if "EDITORIAL" in flagset:
        return RECORD_EDITORIAL
    return RECORD_RESEARCH


def is_research(flags: Iterable[str]) -> bool:
    """True when a record is a research paper eligible for scoring."""
    return record_type(flags) == RECORD_RESEARCH


def derive(components: Mapping[str, float], flags: Iterable[str]) -> dict:
    """Derive every scored quantity from component scores and flags.

    Parameters
    ----------
    components:
        Mapping supplying the four component scores named in
        :data:`COMPONENT_FIELDS`, each on a 0-100 scale.
    flags:
        The flags raised for this paper.

    Returns
    -------
    dict
        ``intellectual_integrity``, ``composite`` and ``final`` scores, the
        ``disqualified`` decision, and the ``classification`` band. Scores are
        rounded to two decimal places; the final score is clamped to [0, 100].

    Raises
    ------
    KeyError
        If a component score is absent.
    ValueError
        If a component score falls outside [0, 100].
    """
    flagset = set(flags)

    missing = [f for f in COMPONENT_FIELDS if components.get(f) is None]
    if missing:
        raise KeyError(f"missing component score(s): {', '.join(missing)}")

    for field in COMPONENT_FIELDS:
        value = float(components[field])
        if not 0.0 <= value <= 100.0:
            raise ValueError(f"{field} = {value} outside [0, 100]")

    intellectual = (
        FORMALISM_WEIGHT * float(components["formalism"])
        + CITATION_WEIGHT * float(components["citation_integrity"])
        + STRUCTURAL_WEIGHT * float(components["structural_integrity"])
    )
    composite = (
        INTELLECTUAL_WEIGHT * intellectual
        + ARTIFACT_WEIGHT * float(components["artifact_availability"])
    )

    disqualified = bool(flagset & DISQUALIFYING_FLAGS)
    if disqualified:
        final = min(composite, DISQUALIFYING_CAP)
    else:
        final = composite
        final -= HIGH_SEVERITY_PENALTY * len(flagset & HIGH_SEVERITY_FLAGS)
        final -= MEDIUM_SEVERITY_PENALTY * len(flagset & MEDIUM_SEVERITY_FLAGS)

    final = max(0.0, min(100.0, final))

    return {
        "intellectual_integrity": round(intellectual, 2),
        "composite": round(composite, 2),
        "final": round(final, 2),
        "disqualified": disqualified,
        "classification": classify(round(final, 2)),
    }
