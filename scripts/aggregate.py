"""Aggregate per-batch RUIN JSON outputs into the tables, figures, and headline
statistics reported in the accompanying manuscript.

Usage
-----
    python scripts/aggregate.py \\
        --input journal-analysis/ROMJIST_29.12.2025 \\
        --output scripts/output

Outputs (written under --output):
    tables/table3_flags.csv             Flag occurrences across the corpus
    tables/table4_yearly_scores.csv     Per-year mean scores and paper counts
    tables/headline_stats.json          Corpus-level statistics referenced in
                                        the manuscript body (means, CV,
                                        regression slopes, Fisher's exact)
    figures/figure4_temporal.png        Composite score and theater rate by year

Dependencies: numpy, scipy, matplotlib (see scripts/requirements.txt).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt


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
    """Yield (year, batch_id, paper) for every research paper.

    Papers carrying the EDITORIAL or PDF_CORRUPTED technical flag are skipped:
    the manuscript reports figures over research papers only.
    """
    technical = {"EDITORIAL", "PDF_CORRUPTED"}
    for batch in batches:
        year = batch["source"]["year"]
        bid = batch["batch_id"]
        for p in batch.get("papers", []):
            flags = set(p.get("flags", []))
            if flags & technical:
                continue
            yield year, bid, p


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def flag_table(papers: list[tuple[int, str, dict]]) -> list[dict]:
    """Table 3: flag counts and percentages across the research-paper corpus."""
    n = len(papers)
    counter: Counter[str] = Counter()
    for _, _, p in papers:
        for fl in p.get("flags", []):
            counter[fl] += 1
    rows = [
        {"flag": flag, "count": cnt, "percent": round(100 * cnt / n, 2)}
        for flag, cnt in counter.most_common()
    ]
    return rows


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


def theater_rates(papers: list[tuple[int, str, dict]]) -> dict[int, dict]:
    """Per-year FORMALISM_THEATER rate, plus issue-level concentration for 2024."""
    by_year: dict[int, dict] = defaultdict(lambda: {"papers": 0, "flagged": 0, "by_issue": Counter()})
    for year, batch_id, p in papers:
        by_year[year]["papers"] += 1
        if "FORMALISM_THEATER" in p.get("flags", []):
            by_year[year]["flagged"] += 1
            by_year[year]["by_issue"][batch_id] += 1
    out = {}
    for year, data in sorted(by_year.items()):
        out[year] = {
            "papers": data["papers"],
            "flagged": data["flagged"],
            "rate_pct": round(100 * data["flagged"] / data["papers"], 2),
            "issues_with_flags": dict(data["by_issue"]),
        }
    return out


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
    # Effective degrees of freedom = n - 2.
    n = len(xs)
    dof = n - 2
    # Weighted residual variance.
    sigma2 = (w * residuals ** 2).sum() / dof
    se_slope = math.sqrt(sigma2 / sxx)
    t_stat = slope / se_slope
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=dof))
    ss_tot = (w * (ys - y_mean) ** 2).sum()
    ss_res = (w * residuals ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {
        "slope": slope,
        "intercept": intercept,
        "t": t_stat,
        "df": dof,
        "p": p_value,
        "r2": r2,
    }


def headline_stats(papers, flag_rows, year_rows, theater_by_year) -> dict:
    n = len(papers)
    finals = [p[2]["scores"]["final"] for p in papers]
    composites = [p[2]["scores"]["composite"] for p in papers]
    artifacts = [p[2]["scores"]["artifact_availability"] for p in papers]
    intellectuals = [p[2]["scores"]["intellectual_integrity"] for p in papers]

    flag_lookup = {r["flag"]: r for r in flag_rows}

    annual_years = np.array([r["year"] for r in year_rows], dtype=float)
    annual_paper_counts = np.array([r["papers"] for r in year_rows], dtype=float)
    annual_composites = np.array([r["composite"] for r in year_rows], dtype=float)

    composite_reg = weighted_regression(annual_years, annual_composites, annual_paper_counts)

    theater_years = np.array(sorted(theater_by_year.keys()), dtype=float)
    theater_rates_arr = np.array([theater_by_year[int(y)]["rate_pct"] for y in theater_years])
    theater_weights = np.array([theater_by_year[int(y)]["papers"] for y in theater_years], dtype=float)
    theater_reg = weighted_regression(theater_years, theater_rates_arr, theater_weights)

    # Fisher's exact: 2024 vs rest of corpus, FORMALISM_THEATER yes/no.
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

    composite_cv = float(np.std(annual_composites, ddof=1) / np.mean(annual_composites))

    return {
        "n_papers": n,
        "n_batches": len({p[1] for p in papers}),
        "year_range": [int(min(annual_years)), int(max(annual_years))],
        "means": {
            "final": round(float(np.mean(finals)), 2),
            "composite": round(float(np.mean(composites)), 2),
            "intellectual_integrity": round(float(np.mean(intellectuals)), 2),
            "artifact_availability": round(float(np.mean(artifacts)), 2),
        },
        "annual_composite": {
            "min": float(annual_composites.min()),
            "max": float(annual_composites.max()),
            "cv_pct": round(100 * composite_cv, 2),
            "regression": {
                "slope_per_year": round(composite_reg["slope"], 3),
                "t": round(composite_reg["t"], 2),
                "df": composite_reg["df"],
                "p": round(composite_reg["p"], 3),
                "r2": round(composite_reg["r2"], 3),
            },
        },
        "formalism_theater": {
            "corpus_rate_pct": flag_lookup.get("FORMALISM_THEATER", {}).get("percent", 0.0),
            "first_decade_2010_2019": {
                "rate_pct": round(
                    100
                    * sum(
                        d["flagged"]
                        for y, d in theater_by_year.items()
                        if 2010 <= y <= 2019
                    )
                    / max(
                        1,
                        sum(
                            d["papers"]
                            for y, d in theater_by_year.items()
                            if 2010 <= y <= 2019
                        ),
                    ),
                    2,
                ),
            },
            "annual": {int(y): theater_by_year[int(y)] for y in theater_years},
            "regression": {
                "slope_pct_per_year": round(theater_reg["slope"], 3),
                "t": round(theater_reg["t"], 2),
                "df": theater_reg["df"],
                "p": round(theater_reg["p"], 3),
                "r2": round(theater_reg["r2"], 3),
            },
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
    composites = [r["composite"] for r in year_rows]
    theater = [theater_by_year[y]["rate_pct"] for y in years]

    fig, ax1 = plt.subplots(figsize=(9, 5))
    color1 = "#1f77b4"
    ax1.plot(years, composites, marker="o", color=color1, label="Mean composite score")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Mean composite score (0–100)", color=color1)
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.set_ylim(0, 100)

    ax2 = ax1.twinx()
    color2 = "#d62728"
    ax2.bar(years, theater, alpha=0.25, color=color2, label="FORMALISM_THEATER rate (%)")
    ax2.set_ylabel("FORMALISM_THEATER rate (%)", color=color2)
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.set_ylim(0, max(30, max(theater) + 5))

    fig.suptitle("ROMJIST temporal dynamics — composite score vs. theater rate")
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
        "--input",
        type=Path,
        default=Path("journal-analysis/ROMJIST_29.12.2025"),
        help="Directory containing per-batch JSON files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("scripts/output"),
        help="Directory to write tables and figures into.",
    )
    args = parser.parse_args()

    batches = load_batches(args.input)
    papers = list(iter_research_papers(batches))

    flag_rows = flag_table(papers)
    year_rows = yearly_table(papers)
    theater_by_year = theater_rates(papers)
    headline = headline_stats(papers, flag_rows, year_rows, theater_by_year)

    write_csv(flag_rows, args.output / "tables" / "table3_flags.csv")
    write_csv(year_rows, args.output / "tables" / "table4_yearly_scores.csv")
    write_json(headline, args.output / "tables" / "headline_stats.json")
    plot_temporal(year_rows, theater_by_year, args.output / "figures" / "figure4_temporal.png")

    print(f"Loaded {len(batches)} batches; {len(papers)} research papers.")
    print(f"Mean composite: {headline['means']['composite']}")
    print(f"Mean artifact availability: {headline['means']['artifact_availability']}")
    print(
        f"FORMALISM_THEATER rate (corpus): {headline['formalism_theater']['corpus_rate_pct']}%"
    )
    fisher = headline["formalism_theater"]["fisher_2024_vs_rest"]
    print(f"Fisher 2024 vs. rest: OR = {fisher['odds_ratio']}, p = {fisher['p']:.2e}")
    print(f"Outputs written under {args.output.resolve()}")


if __name__ == "__main__":
    main()
