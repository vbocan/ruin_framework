"""Test whether RUIN scores carry information that citation counts do not.

Input: merged.csv from merge_wos_citations.py (RUIN scores + WoS times-cited).

The manuscript's complementarity claim is that RUIN measures something citation
counts miss. That is an assertion about *independence*, and a null result only
supports it if the analysis had the power to detect a real association. So this
script reports confidence intervals throughout and states the smallest effect the
sample could have detected, rather than resting on p > 0.05.

Citation counts grow with age, so the raw correlation is confounded by publication
year: older papers have more citations regardless of quality. Three treatments are
reported -- raw, partialled on year, and pooled within-year -- and the within-year
estimate is the one to quote.

Only numpy/pandas are required. With scipy installed the p-values would be exact
rather than normal-approximated; at n ~ 400 the difference is immaterial.

    python citation_correlation.py merged.csv
"""

import math
import sys
import numpy as np
import pandas as pd

DIMENSIONS = [
    ("final", "RUIN final score"),
    ("composite", "Composite (pre-flag)"),
    ("intellectual_integrity", "Intellectual integrity"),
    ("formalism", "Formalism proportionality"),
    ("citation_integrity", "Citation integrity"),
    ("structural_integrity", "Structural soundness"),
    ("artifact_availability", "Artifact availability"),
]

NORM_CDF = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))


def spearman(x, y):
    """Spearman rho with a Fisher-z 95% CI and a two-sided p-value."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    n = len(x)
    if n < 5:
        return None
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    r = float(np.corrcoef(rx, ry)[0, 1])
    r = min(max(r, -0.999999), 0.999999)
    se = 1.0 / math.sqrt(n - 3)
    z = math.atanh(r)
    lo, hi = math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)
    p = 2 * (1 - NORM_CDF(abs(z) / se))
    return dict(n=n, r=r, lo=lo, hi=hi, p=p)


def partial_spearman(x, y, ctrl):
    """Spearman of x and y after linearly removing ctrl from both (on ranks)."""
    df = pd.DataFrame({"x": x, "y": y, "c": ctrl}).dropna()
    if len(df) < 6:
        return None
    R = df.rank()
    resid = {}
    C = np.column_stack([np.ones(len(R)), R["c"].to_numpy()])
    for col in ("x", "y"):
        v = R[col].to_numpy()
        beta, *_ = np.linalg.lstsq(C, v, rcond=None)
        resid[col] = v - C @ beta
    r = float(np.corrcoef(resid["x"], resid["y"])[0, 1])
    n = len(df)
    se = 1.0 / math.sqrt(n - 4)          # one control variable
    z = math.atanh(min(max(r, -0.999999), 0.999999))
    return dict(n=n, r=r, lo=math.tanh(z - 1.96 * se), hi=math.tanh(z + 1.96 * se),
                p=2 * (1 - NORM_CDF(abs(z) / se)))


def within_year(df, col):
    """Fisher-z weighted pooling of per-year Spearman correlations."""
    zs, ws, used, dropped = [], [], 0, 0
    for _, g in df.groupby("year"):
        g = g[[col, "citations"]].dropna()
        if len(g) < 8 or g["citations"].nunique() < 3:
            dropped += 1
            continue
        s = spearman(g[col], g["citations"])
        if not s:
            dropped += 1
            continue
        zs.append(math.atanh(min(max(s["r"], -0.999999), 0.999999)))
        ws.append(s["n"] - 3)
        used += 1
    if not zs:
        return None
    zs, ws = np.array(zs), np.array(ws, float)
    zbar = float((zs * ws).sum() / ws.sum())
    se = 1.0 / math.sqrt(ws.sum())
    return dict(years=used, dropped=dropped, r=math.tanh(zbar),
                lo=math.tanh(zbar - 1.96 * se), hi=math.tanh(zbar + 1.96 * se),
                p=2 * (1 - NORM_CDF(abs(zbar) / se)))


def mann_whitney(a, b):
    """Two-sided Mann-Whitney U, normal approximation with tie correction."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    n1, n2 = len(a), len(b)
    if n1 < 3 or n2 < 3:
        return None
    allv = np.concatenate([a, b])
    ranks = pd.Series(allv).rank().to_numpy()
    R1 = ranks[:n1].sum()
    U1 = R1 - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    _, cnt = np.unique(allv, return_counts=True)
    N = n1 + n2
    tie = (cnt ** 3 - cnt).sum()
    sd = math.sqrt(n1 * n2 / 12 * ((N + 1) - tie / (N * (N - 1))))
    if sd == 0:
        return None
    z = (U1 - mu) / sd
    return dict(n1=n1, n2=n2, U=U1, p=2 * (1 - NORM_CDF(abs(z))),
                med1=float(np.median(a)), med2=float(np.median(b)))


def fmt(s):
    if not s:
        return "  (too few observations)"
    star = "*" if s["p"] < 0.05 else " "
    return (f"rho = {s['r']:+.3f}  [{s['lo']:+.3f}, {s['hi']:+.3f}]  "
            f"p = {s['p']:.3g}{star}   n = {s.get('n', '-')}")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "merged.csv"
    df = pd.read_csv(path)
    df["citations"] = pd.to_numeric(df["citations"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    for c, _ in DIMENSIONS:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    rows_in_file = len(df)
    # Editorials and the unreadable PDF are not research output and carry no
    # score; exclude them explicitly so the denominators below are the corpus
    # the manuscript reports, not the raw record count.
    if "record_type" in df.columns:
        non_research = int((df["record_type"] != "research").sum())
        df = df[df["record_type"] == "research"]
    else:
        non_research = 0
    total = len(df)

    df = df.dropna(subset=["citations", "final"])
    n = len(df)
    print(f"=== coverage ===")
    print(f"records in file            : {rows_in_file}")
    print(f"non-research excluded      : {non_research}")
    print(f"research papers            : {total}")
    print(f"with citations and a score : {n}  ({n/total*100:.1f}%)")
    z = int((df["citations"] == 0).sum())
    print(f"zero-citation papers       : {z}  ({z/n*100:.1f}%)")
    print(f"citations: median={df['citations'].median():.0f} "
          f"mean={df['citations'].mean():.1f} max={df['citations'].max():.0f}")

    # Smallest |rho| this sample could detect at 80% power, alpha .05 two-sided.
    mde = math.tanh(2.802 / math.sqrt(max(n - 3, 1)))
    print(f"\nminimum detectable |rho| (80% power, alpha .05): {mde:.3f}")
    print("a null result is only informative if the CI excludes effects above this.")

    print(f"\n=== RUIN final score vs citations ===")
    print(f"raw            : {fmt(spearman(df['final'], df['citations']))}")
    print(f"partial on year: {fmt(partial_spearman(df['final'], df['citations'], df['year']))}")
    w = within_year(df, "final")
    if w:
        print(f"within-year    : rho = {w['r']:+.3f}  [{w['lo']:+.3f}, {w['hi']:+.3f}]  "
              f"p = {w['p']:.3g}   ({w['years']} years pooled, {w['dropped']} dropped)")

    print(f"\n=== per dimension (partialled on publication year) ===")
    for col, label in DIMENSIONS:
        print(f"{label:26s} {fmt(partial_spearman(df[col], df['citations'], df['year']))}")

    print(f"\n=== artifact availability ===")
    print("Frachtenberg (2022) reports ~75% more citations for papers with shared")
    print("artifacts. If RUIN's artifact score is valid, it should reproduce that sign.")
    hi = df[df["artifact_availability"] >= 70]["citations"]
    lo = df[df["artifact_availability"] <= 30]["citations"]
    mw = mann_whitney(hi, lo)
    if mw:
        print(f"  code+data available (>=70): n={mw['n1']}, median citations {mw['med1']:.0f}")
        print(f"  little or nothing   (<=30): n={mw['n2']}, median citations {mw['med2']:.0f}")
        print(f"  Mann-Whitney p = {mw['p']:.3g}")

    print(f"\n=== flagged vs unflagged ===")
    df["flagged"] = df["flags"].fillna("").astype(str).str.len() > 0
    mw = mann_whitney(df[df["flagged"]]["citations"], df[~df["flagged"]]["citations"])
    if mw:
        print(f"  flagged   : n={mw['n1']}, median citations {mw['med1']:.0f}")
        print(f"  unflagged : n={mw['n2']}, median citations {mw['med2']:.0f}")
        print(f"  Mann-Whitney p = {mw['p']:.3g}")

    print("\n=== how to read this ===")
    print("A near-zero within-year rho whose CI sits inside +/-0.2 supports the")
    print("complementarity claim: RUIN varies where citations do not. A clearly")
    print("positive rho would mean RUIN is partly re-measuring citation impact and")
    print("the complementarity framing needs revising. Either outcome is publishable;")
    print("what is not publishable is leaving the question open in a scientometrics venue.")


if __name__ == "__main__":
    main()
