# RUIN Framework Tools

Three downloaders, one per journal in the validation corpus. Each produces a flat tree of batch folders ready for RUIN analysis.

| Script | Journal | Tier | Backend |
|--------|---------|------|---------|
| `Download-ROMJIST.ps1` | Romanian J. of Information Science and Technology | Mid (indexed CS) | PowerShell |
| `Download-JAIR.ps1` | Journal of Artificial Intelligence Research | Top (Q1, diamond OA) | PowerShell |
| `Download-IJCNIS.ps1` | International J. of Computer Network and Information Security (MECS Press) | Predatory (Beall-listed) | PowerShell |

## Common output convention

Each batch folder contains a `source.json` with journal/batch metadata and the PDFs for that batch. The RUIN pipeline reads any folder matching this pattern.

```
{journal_acronym}/
├── {batch_id}/
│   ├── source.json
│   └── *.pdf
```

## Download-ROMJIST.ps1

Downloads all papers from ROMJIST.

```powershell
cd D:\Repositories\ruin_framework\tools
.\Download-ROMJIST.ps1
```

Configuration block at the top of the script: `$StartYear`, `$EndYear`, `$OutputFolder`, `$RequestDelay`, `$SkipExisting`.

Batch ID format: `{year}-v{vol}-n{issue}`. Estimated runtime: 60-90 min for full 2010-2025 range (~600 papers).

## Download-JAIR.ps1

Downloads all papers from JAIR within a year range. JAIR is diamond OA on OJS with no anti-scraping; pure PowerShell.

```powershell
.\Download-JAIR.ps1
```

Batch ID format: `{year}-v{vol}` (one batch per volume; JAIR maps each volume to one OJS issue containing all that volume's papers).

The script enumerates volumes by scraping the public archive listing pages (`/index.php/jair/issue/archive` and `/archive/2`), so adding a year requires no manual volume-to-year table. To extend below 2010, raise `$ArchivePagesToScan`.

Estimated runtime: 90-120 min for 2010-2025 (~1000-1400 papers across 48 volumes; per-volume size has grown over the years).

## Download-IJCNIS.ps1

Downloads all papers from the International Journal of Computer Network and Information Security, published by MECS Press. The journal appeared on Beall's list of potentially predatory publishers and is widely cited in scientometrics literature as exemplifying permissive editorial practices in computer science.

```powershell
.\Download-IJCNIS.ps1
```

Volume-to-year mapping: Volume N = year (2008 + N), so 2010-2025 covers Volumes 2-17 (16 volumes × 6 issues × ~7 articles ≈ 672 papers).

Batch ID format: `{year}-v{vol}-n{issue}`. The script enumerates issues from `/ijcnis/archives.html`, then constructs PDF URLs directly using MECS Press's predictable naming pattern (`/ijcnis/ijcnis-v{V}-n{I}/IJCNIS-V{V}-N{I}-{N}.pdf`).

Estimated runtime: ~30 min for 2010-2025.

## Estimated download times (full pipeline)

| Range | Papers | Time |
|-------|--------|------|
| ROMJIST 2010-2025 | ~600 | 60-90 min |
| JAIR 2010-2025    | ~1000-1400 | 90-120 min |
| IJCNIS 2010-2025  | ~672 | ~30 min |

All three together: ~2300-2700 papers, half a day with breaks.

## Predatory journal selection note (WCMC superseded)

An earlier version targeted Hindawi's *Wireless Communications and Mobile Computing* (WCMC), delisted from Web of Science in 2023 after compromised peer review. That dataset turned out to be inaccessible: post-Wiley-acquisition, `downloads.hindawi.com/...` 302-redirects to `onlinelibrary.wiley.com/doi/epdf/...`, an authenticated PDF viewer behind aggressive Cloudflare protection. We tried plain HTTP, `curl_cffi` with `chrome142` impersonation, headless Playwright, and FlareSolverr — none returned binary PDF content. The WCMC corpus is effectively privatized.

IJCNIS replaces WCMC. The narrative shifts from "a journal that *passed* citation metrics for years before being delisted" to "a journal long flagged by independent observers as predatory." Less dramatic, but the comparison to JAIR/ROMJIST still demonstrates RUIN's discriminative validity across the quality spectrum.

The orphaned `Download-WCMC.ps1`, `download_wcmc_pdfs.py`, and `wcmc/` Crossref manifests are kept on disk in case the access situation changes.

## Preparing for analysis

Each batch folder is self-contained. Point the RUIN analysis pipeline at any individual batch folder, or iterate across the full journal tree.
