# Downloader

`Download-ROMJIST.ps1` downloads all research papers from the Romanian Journal of Information Science and Technology (ROMJIST), the corpus used to validate the RUIN framework.

## Usage

```powershell
cd D:\Repositories\ruin_framework\tools
.\Download-ROMJIST.ps1
```

Configuration block at the top of the script: `$StartYear`, `$EndYear`, `$OutputFolder`, `$RequestDelay`, `$SkipExisting`. Default range is 2010–2025 (the validation corpus).

## Output layout

```
{OutputFolder}/
├── 2010-v13-n1/
│   ├── source.json
│   ├── 2010-v13-n1-paper1.pdf
│   ├── 2010-v13-n1-paper2.pdf
│   └── ...
├── 2010-v13-n2/
│   └── ...
└── ...
```

Batch ID format: `{year}-v{volume}-n{issue}`. Each `source.json` records journal identity (acronym, name, ISSN) and batch metadata (volume, issue, year). The RUIN analysis pipeline reads any folder matching this layout.

Estimated runtime: 60–90 minutes for the full 2010–2025 range (~600 papers).
