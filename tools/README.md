# RUIN Framework Tools

## Download-ROMJIST.ps1

Downloads all papers from ROMJIST (Romanian Journal of Information Science and Technology) and creates batch folders for RUIN analysis.

### Configuration

Edit the script to modify:

```powershell
$StartYear = 2010      # First year to download (Volume 13)
$EndYear = 2025        # Last year to download (Volume 28)
$OutputFolder = ".\romjist"   # Where batch folders go
$RequestDelay = 1      # Seconds between requests (be polite)
$SkipExisting = $true  # Skip already downloaded files
```

### Run

```powershell
cd D:\Repositories\ruin_framework\tools
.\Download-ROMJIST.ps1
```

### Output Structure

Each batch folder contains `source.json` and all PDFs for that issue:

```
romjist/
├── 2010-v13-n1/
│   ├── source.json
│   ├── 01_de@20pasquale.pdf
│   ├── 02_bozanic.pdf
│   └── ...
├── 2022-v25-n1/
│   ├── source.json
│   ├── paper703.pdf
│   ├── paper708.pdf
│   └── ...
└── ...
```

### Paper Naming

Original filenames from the website are preserved.

### Preparing for Analysis

Each batch folder is ready for RUIN analysis. Copy or reference a batch folder directly.

### Estimated Download

| Range | Papers | Time (est.) |
|-------|--------|-------------|
| 2020-2025 | ~200 | 15-30 min |
| 2015-2025 | ~400 | 30-60 min |
| 2010-2025 | ~600 | 60-90 min |

Times depend on network speed and server response.
