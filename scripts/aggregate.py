"""Aggregate per-batch RUIN JSON outputs into the tables, figures, and headline
statistics reported in the accompanying manuscript.

Usage
-----
    python scripts/aggregate.py \\
        --input journal-analysis/ROMJIST_29.12.2025 \\
        --output scripts/output

Outputs (written under --output):
    tables/table1_classification.csv    Classification distribution
    tables/table2_dimensions.csv        Dimension-specific mean scores
    tables/table3_flags.csv             Flag occurrences across the corpus
    tables/table4_yearly_scores.csv     Per-year mean scores and paper counts
    tables/headline_stats.json          Corpus-level statistics referenced in
                                        the manuscript body (means, CV,
                                        regression, Fisher's exact)
    figures/figure4_temporal.png        Composite score and flag rate by year

Every derived quantity comes from :mod:`ruin_scoring`, the single authority for
RUIN's scoring rules. Before aggregating, this script verifies that each
archived record already agrees with those rules and aborts if any does not, so
that a published table can never be produced from data that has drifted from
the specification. Run ``python scripts/rescore.py --write`` to repair drift.

Dependencies: numpy, scipy, matplotlib (see scripts/requirements.txt).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ruin_scoring as rs  # noqa: E402


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_batches(input_dir: Path) -> list[dict]:
    """Load every batch JSON in input_dir."""
    files = sorted(input_dir.glob("*.json"))
    if not files:
        raise SystemExit(f"No batch JSONs found under {input_dir}")
    batches = []
    for f in files:
        with f.open(encoding="utf-8") as fh:
            batches.append(json.load(fh))
    return batches


def iter_research_papers(batches: Iterable[dict]):
    """Yield ``(year, batch_id, paper)`` for every research paper.

    Editorials and unreadable PDFs are excluded. They are not research output,
    and scoring them -- in particular scoring an unreadable PDF as zero --
    would depress every statistic they entered.
    """
    for batch in batches:
        year = batch["source"]["year"]
        bid = batch["batch_id"]
        for p in batch.get("papers", []):
            if rs.is_research(p.get("flags", [])):
                yield year, bid, p


def verify_consistency(papers: list[tuple[int, str, dict]]) -> None:
    """Abort unless every record's derived fields match the scoring rules."""
    bad = []
    for year, bid, p in papers:
        derived = rs.derive(p["scores"], p.get("flags", []), p.get("concept_level"))
        for field in rs.DERIVED_FIELDS:
            if abs(float(p["scores"][field]) - derived[field]) > 0.01:
                bad.append(f"{bid}::{p['paper_id']}::{field}")
        if p["verdict"].get("classification") != derived["classification"]:
            bad.append(f"{bid}::{p['paper_id']}::classification")
    if bad:
        raise SystemExit(
            f"{len(bad)} record(s) disagree with framework/scoring.md, e.g. "
            f"{bad[:3]}.\nRun: python scripts/rescore.py --write"
        )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def classification_table(papers: list[tuple[int, str, dict]]) -> list[dict]:
    """Table 1: distribution of papers across classification bands."""
    n = len(papers)
    counter = Counter(p["verdict"]["classification"] for _, _, p in papers)
    order = [label for _, label in rs.CLASSIFICATION_BANDS]
    bounds = {
        "STRONG": "80-100", "ADEQUATE": "60-79", "LIMITED": "40-59",
        "CONCERNING": "25-39", "CRITICAL": "0-24",
    }
    return [
        {
            "classification": label,
            "range": bounds[label],
            "papers": counter.get(label, 0),
            "percent": round(100 * counter.get(label, 0) / n, 1),
        }
        for label in order
    ]


def dimension_table(papers: list[tuple[int, str, dict]]) -> list[dict]:
    """Table 2: mean score on each assessment dimension."""
    fields = [
        ("citation_integrity", "Citation integrity"),
        ("structural_integrity", "Structural integrity"),
        ("intellectual_integrity", "Intellectual integrity"),
        ("formalism", "Formalism"),
        ("final", "Final score"),
        ("artifact_availability", "Artifact availability"),
    ]
    rows = []
    for key, label in fields:
        values = [p["scores"][key] for _, _, p in papers]
        rows.append({
            "dimension": label,
            "mean": round(float(np.mean(values)), 1),
            "sd": round(float(np.std(values, ddof=1)), 1),
            "median": round(float(np.median(values)), 1),
        })
    return rows


def flag_table(papers: list[tuple[int, str, dict]]) -> list[dict]:
    """Table 3: flag counts and percentages across the research-paper corpus."""
    n = len(papers)
    counter: Counter[str] = Counter()
    for _, _, p in papers:
        for fl in p.get("flags", []):
            counter[fl] += 1

    def severity(flag: str) -> str:
        if flag in rs.DISQUALIFYING_FLAGS:
            return "disqualifying"
        if flag in rs.HIGH_SEVERITY_FLAGS:
            return "high"
        if flag in rs.MEDIUM_SEVERITY_FLAGS:
            return "medium"
        return "other"

    return [
        {
            "flag": flag,
            "severity": severity(flag),
            "count": cnt,
            "percent": round(100 * cnt / n, 1),
        }
        for flag, cnt in counter.most_common()
    ]


def yearly_table(papers: list[tuple[int, str, dict]]) -> list[dict]:
    """Table 4: per-year means for each component score and the composite."""
    bucket: dict[int, list[dict]] = defaultdict(list)
    for year, _, p in papers:
        bucket[year].append(p["scores"])

    rows = []
    for year in sorted(bucket):
        scores = bucket[year]

        def mean(field: str) -> float:
            return round(sum(s[field] for s in scores) / len(scores), 2)

        rows.append({
            "year": year,
            "papers": len(scores),
            "formalism": mean("formalism"),
            "citation_integrity": mean("citation_integrity"),
            "structural_integrity": mean("structural_integrity"),
            "artifact_availability": mean("artifact_availability"),
            "intellectual_integrity": mean("intellectual_integrity"),
            "composite": mean("composite"),
            "final": mean("final"),
        })
    return rows


def flag_rates(papers: list[tuple[int, str, dict]], flag: str) -> dict[int, dict]:
    """Per-year rate of one flag, plus its issue-level concentration."""
    by_year: dict[int, dict] = defaultdict(
        lambda: {"papers": 0, "flagged": 0, "by_issue": Counter()}
    )
    for year, batch_id, p in papers:
        by_year[year]["papers"] += 1
        if flag in p.get("flags", []):
            by_year[year]["flagged"] += 1
            by_year[year]["by_issue"][batch_id] += 1
    return {
        year: {
            "papers": d["papers"],
            "flagged": d["flagged"],
            "rate_pct": round(100 * d["flagged"] / d["papers"], 2),
            "issues_with_flags": dict(d["by_issue"]),
        }
        for year, d in sorted(by_year.items())
    }


def weighted_regression(xs: np.ndarray, ys: np.ndarray, weights: np.ndarray) -> dict:
    """Weighted least-squares regression of y on x. Returns slope, t, p, R^2."""
    w = weights
    wsum = w.sum()
    x_mean = (w * xs).sum() / wsum
    y_mean = (w * ys).sum() / wsum
    sxx = (w * (xs - x_mean) ** 2).sum()
    sxy = (w * (xs - x_mean) * (ys - y_mean)).sum()
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    y_hat = intercept + slope * xs
    residuals = ys - y_hat
    dof = len(xs) - 2
    sigma2 = (w * residuals ** 2).sum() / dof
    se_slope = math.sqrt(sigma2 / sxx)
    t_stat = slope / se_slope
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=dof))
    ss_tot = (w * (ys - y_mean) ** 2).sum()
    ss_res = (w * residuals ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {
        "slope": slope, "intercept": intercept,
        "t": t_stat, "df": dof, "p": p_value, "r2": r2,
    }


def headline_stats(papers, flag_rows, year_rows, theater_by_year) -> dict:
    n = len(papers)
    finals = [p[2]["scores"]["final"] for p in papers]
    composites = [p[2]["scores"]["composite"] for p in papers]
    artifacts = [p[2]["scores"]["artifact_availability"] for p in papers]
    intellectuals = [p[2]["scores"]["intellectual_integrity"] for p in papers]

    flag_lookup = {r["flag"]: r for r in flag_rows}

    annual_years = np.array([r["year"] for r in year_rows], dtype=float)
    annual_counts = np.array([r["papers"] for r in year_rows], dtype=float)
    annual_finals = np.array([r["final"] for r in year_rows], dtype=float)

    score_reg = weighted_regression(annual_years, annual_finals, annual_counts)

    # Fisher's exact: 2024 vs. the rest of the corpus, flagged yes/no.
    #
    # A regression of the annual flag rate on year is deliberately NOT reported.
    # The series is a spike-and-revert (0% through 2019, a 2024 peak, 0% again
    # in 2025), which a linear model cannot represent: any slope it returns is
    # an artefact of the single 2024 peak. Fisher's exact test on the 2024
    # cohort is the statistic the data actually supports.
    y2024 = theater_by_year.get(2024, {"papers": 0, "flagged": 0})
    total_flagged = sum(d["flagged"] for d in theater_by_year.values())
    total_papers = sum(d["papers"] for d in theater_by_year.values())
    rest_flagged = total_flagged - y2024["flagged"]
    rest_papers = total_papers - y2024["papers"]
    table_2x2 = [
        [y2024["flagged"], y2024["papers"] - y2024["flagged"]],
        [rest_flagged, rest_papers - rest_flagged],
    ]
    fisher_or, fisher_p = stats.fisher_exact(table_2x2, alternative="greater")

    first_decade_flagged = sum(
        d["flagged"] for y, d in theater_by_year.items() if 2010 <= y <= 2019
    )
    first_decade_papers = sum(
        d["papers"] for y, d in theater_by_year.items() if 2010 <= y <= 2019
    )

    cv = float(np.std(annual_finals, ddof=1) / np.mean(annual_finals))
    disqualified = sum(1 for p in papers if p[2]["verdict"]["disqualified"])

    return {
        "n_research_papers": n,
        "n_batches": len({p[1] for p in papers}),
        "n_disqualified": disqualified,
        "year_range": [int(annual_years.min()), int(annual_years.max())],
        "means": {
            "final": round(float(np.mean(finals)), 1),
            "composite": round(float(np.mean(composites)), 1),
            "intellectual_integrity": round(float(np.mean(intellectuals)), 1),
            "artifact_availability": round(float(np.mean(artifacts)), 1),
        },
        "annual_final": {
            "min": float(annual_finals.min()),
            "max": float(annual_finals.max()),
            "cv_pct": round(100 * cv, 1),
            "regression": {
                "slope_per_year": round(score_reg["slope"], 3),
                "t": round(score_reg["t"], 2),
                "df": score_reg["df"],
                "p": round(score_reg["p"], 3),
                "r2": round(score_reg["r2"], 3),
            },
        },
        "formalism_theater": {
            "corpus_rate_pct": flag_lookup.get("FORMALISM_THEATER", {}).get("percent", 0.0),
            "first_decade_2010_2019_rate_pct": round(
                100 * first_decade_flagged / max(1, first_decade_papers), 2
            ),
            "annual": theater_by_year,
            "fisher_2024_vs_rest": {
                "table": table_2x2,
                "odds_ratio": round(float(fisher_or), 2),
                "p": float(fisher_p),
            },
        },
    }


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def plot_temporal(year_rows: list[dict], theater_by_year: dict, path: Path) -> None:
    years = [r["year"] for r in year_rows]
    finals = [r["final"] for r in year_rows]
    theater = [theater_by_year[y]["rate_pct"] for y in years]

    fig, ax1 = plt.subplots(figsize=(9, 5))
    color1 = "#1f77b4"
    ax1.plot(years, finals, marker="o", color=color1, label="Mean final score")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Mean final score (0-100)", color=color1)
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.set_ylim(0, 100)

    ax2 = ax1.twinx()
    color2 = "#d62728"
    ax2.bar(years, theater, alpha=0.25, color=color2, label="Disproportionate formalism (%)")
    ax2.set_ylabel("Disproportionate formalism rate (%)", color=color2)
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.set_ylim(0, max(30, max(theater) + 5))

    fig.suptitle("ROMJIST temporal dynamics - mean score vs. flag rate")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--input", type=Path,
        default=Path("journal-analysis/ROMJIST_29.12.2025"),
        help="Directory containing per-batch JSON files.",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("scripts/output"),
        help="Directory to write tables and figures into.",
    )
    args = parser.parse_args()

    batches = load_batches(args.input)
    papers = list(iter_research_papers(batches))
    verify_consistency(papers)

    total_records = sum(len(b.get("papers", [])) for b in batches)

    cls_rows = classification_table(papers)
    dim_rows = dimension_table(papers)
    flag_rows = flag_table(papers)
    year_rows = yearly_table(papers)
    theater_by_year = flag_rates(papers, "FORMALISM_THEATER")
    headline = headline_stats(papers, flag_rows, year_rows, theater_by_year)
    headline["n_total_records"] = total_records
    headline["n_excluded_non_research"] = total_records - len(papers)

    write_csv(cls_rows, args.output / "tables" / "table1_classification.csv")
    write_csv(dim_rows, args.output / "tables" / "table2_dimensions.csv")
    write_csv(flag_rows, args.output / "tables" / "table3_flags.csv")
    write_csv(year_rows, args.output / "tables" / "table4_yearly_scores.csv")
    write_json(headline, args.output / "tables" / "headline_stats.json")
    plot_temporal(year_rows, theater_by_year, args.output / "figures" / "figure4_temporal.png")

    print(f"Records loaded:      {total_records} across {len(batches)} batches")
    print(f"Non-research:        {headline['n_excluded_non_research']} (editorials, unreadable)")
    print(f"Research papers:     {len(papers)}")
    print(f"Mean final score:    {headline['means']['final']}")
    print(f"Mean artifact avail: {headline['means']['artifact_availability']}")
    print(f"Disqualified:        {headline['n_disqualified']}")
    print(
        f"Disproportionate formalism: "
        f"{headline['formalism_theater']['corpus_rate_pct']}% corpus, "
        f"{headline['formalism_theater']['first_decade_2010_2019_rate_pct']}% in 2010-2019"
    )
    fisher = headline["formalism_theater"]["fisher_2024_vs_rest"]
    print(f"Fisher 2024 vs rest: OR = {fisher['odds_ratio']}, p = {fisher['p']:.2e}")
    print(f"Outputs written under {args.output.resolve()}")


if __name__ == "__main__":
    main()
