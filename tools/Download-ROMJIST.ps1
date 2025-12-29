<#
.SYNOPSIS
    Downloads ROMJIST papers and creates metadata files for RUIN analysis.

.DESCRIPTION
    This script downloads all papers from the Romanian Journal of Information
    Science and Technology (ROMJIST) starting from a configurable year.

    It creates:
    - A flat folder of PDFs with naming: {year}-v{vol}-n{issue}_{paperid}.pdf
    - Batch metadata files (source.json) for each volume/issue

.NOTES
    Configure the variables in the CONFIGURATION section below.
    Run from PowerShell: .\Download-ROMJIST.ps1
#>

#region CONFIGURATION
# ============================================================================
# Modify these variables as needed
# ============================================================================

# Year range (Volume 13 = 2010, Volume 28 = 2025)
$StartYear = 2010
$EndYear = 2025

# Output folder (relative to script location or absolute paths)
$OutputFolder = ".\romjist"

# Base URL
$BaseUrl = "https://romjist.ro"

# Delay between requests (seconds) - be polite to the server
$RequestDelay = 1

# Skip already downloaded files
$SkipExisting = $true

#endregion

#region JOURNAL METADATA
# ============================================================================
# ROMJIST structure mapping
# ============================================================================

# Volume to year mapping
$VolumeYearMap = @{
    13 = 2010; 14 = 2011; 15 = 2012; 16 = 2013; 17 = 2014
    18 = 2015; 19 = 2016; 20 = 2017; 21 = 2018; 22 = 2019
    23 = 2020; 24 = 2021; 25 = 2022; 26 = 2023; 27 = 2024
    28 = 2025
}

# Reverse mapping
$YearVolumeMap = @{}
foreach ($vol in $VolumeYearMap.Keys) {
    $YearVolumeMap[$VolumeYearMap[$vol]] = $vol
}

# Old format issues (2010-2017, Volumes 13-20): content/cuprins{vol}_{issue}.html
# New format issues (2018-2025, Volumes 21-28): contents-{id}.html

# New format issue ID mapping (Volume 21+ uses sequential IDs)
$NewFormatIssueIds = @{
    # Volume 21 (2018)
    "21_1" = 71; "21_2" = 72; "21_3" = 73; "21_4" = 74
    # Volume 22 (2019)
    "22_1" = 75; "22_2" = 76; "22_3-4" = 77
    # Volume 23 (2020)
    "23_1" = 78; "23_2" = 79; "23_S" = 80; "23_3" = 81; "23_4" = 82; "23_T" = 83
    # Volume 24 (2021)
    "24_1" = 84; "24_2" = 85; "24_3" = 86; "24_4" = 87
    # Volume 25 (2022)
    "25_1" = 88; "25_2" = 89; "25_3-4" = 90
    # Volume 26 (2023)
    "26_1" = 91; "26_2" = 92; "26_3-4" = 93
    # Volume 27 (2024)
    "27_1" = 94; "27_2" = 95; "27_3-4" = 96
    # Volume 28 (2025)
    "28_1" = 97; "28_2" = 98; "28_3" = 99; "28_4" = 100
}

# Issues per volume (for old format volumes)
$OldFormatIssues = @{
    13 = @(1, 2, 3, 4)
    14 = @(1, 2, 3, 4)
    15 = @(1, 2, 3, 4)
    16 = @(1, 2, 3, 4)
    17 = @(1, 2, 3, 4)
    18 = @(1, 2, 3, 4)
    19 = @(1, 2, 3, 4)
    20 = @(1, 2, 3, 4)
}

#endregion

#region FUNCTIONS
# ============================================================================

function Get-IssuePageUrl {
    param (
        [int]$Volume,
        [string]$Issue
    )

    if ($Volume -le 20) {
        # Old format
        return "$BaseUrl/content/cuprins${Volume}_${Issue}.html"
    } else {
        # New format
        $key = "${Volume}_${Issue}"
        if ($NewFormatIssueIds.ContainsKey($key)) {
            $id = $NewFormatIssueIds[$key]
            return "$BaseUrl/contents-${id}.html"
        }
        return $null
    }
}

function Get-PapersFromIssuePage {
    param (
        [string]$Url,
        [int]$Volume,
        [string]$Issue,
        [int]$Year
    )

    $papers = @()

    try {
        Write-Host "  Fetching: $Url" -ForegroundColor Gray
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -ErrorAction Stop
        $content = $response.Content

        if ($Volume -le 20) {
            # Old format: pdf/##_author.pdf (relative to /content/)
            $pdfPattern = 'href="(pdf/([^"]+\.pdf))"'
            $matches = [regex]::Matches($content, $pdfPattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)

            foreach ($match in $matches) {
                $pdfPath = $match.Groups[1].Value
                $pdfName = $match.Groups[2].Value
                $pdfUrl = "$BaseUrl/content/$pdfPath"

                $papers += @{
                    Url = $pdfUrl
                    Filename = $pdfName
                }
            }
        } else {
            # New format: full-texts/paper###.pdf
            $pdfPattern = 'href="(full-texts/(paper\d+\.pdf))"'
            $matches = [regex]::Matches($content, $pdfPattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)

            foreach ($match in $matches) {
                $pdfPath = $match.Groups[1].Value
                $pdfName = $match.Groups[2].Value
                $pdfUrl = "$BaseUrl/$pdfPath"

                $papers += @{
                    Url = $pdfUrl
                    Filename = $pdfName
                }
            }
        }
    }
    catch {
        Write-Host "  ERROR fetching $Url : $_" -ForegroundColor Red
    }

    return $papers
}

function Save-SourceJson {
    param (
        [string]$OutputPath,
        [int]$Volume,
        [string]$Issue,
        [int]$Year
    )

    $issueNum = $null
    if ($Issue -match '^\d+$') {
        $issueNum = [int]$Issue
    }

    $sourceData = @{
        journal = @{
            acronym = "ROMJIST"
            name = "Romanian Journal of Information Science and Technology"
            issn = "1453-8245"
        }
        batch = @{
            volume = $Volume
            year = $Year
        }
    }

    if ($null -ne $issueNum) {
        $sourceData.batch.issue = $issueNum
    } else {
        $sourceData.batch.issue_label = $Issue
    }

    $json = $sourceData | ConvertTo-Json -Depth 4
    $json | Out-File -FilePath $OutputPath -Encoding UTF8
}

function Get-IssuesToProcess {
    param (
        [int]$Volume
    )

    if ($Volume -le 20) {
        return $OldFormatIssues[$Volume]
    } else {
        # Extract issues from NewFormatIssueIds
        $issues = @()
        foreach ($key in $NewFormatIssueIds.Keys) {
            if ($key.StartsWith("${Volume}_")) {
                $issue = $key -replace "^${Volume}_", ""
                $issues += $issue
            }
        }
        return $issues | Sort-Object
    }
}

#endregion

#region MAIN
# ============================================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "ROMJIST Paper Downloader" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Start Year: $StartYear"
Write-Host "  End Year:   $EndYear"
Write-Host "  Output:     $OutputFolder"
Write-Host ""

# Create output folder
New-Item -ItemType Directory -Path $OutputFolder -Force | Out-Null

$totalPapers = 0
$downloadedPapers = 0
$skippedPapers = 0
$failedPapers = 0

# Process each year
for ($year = $StartYear; $year -le $EndYear; $year++) {
    if (-not $YearVolumeMap.ContainsKey($year)) {
        Write-Host "Skipping year $year (no volume mapping)" -ForegroundColor Yellow
        continue
    }

    $volume = $YearVolumeMap[$year]
    Write-Host ""
    Write-Host "Processing Volume $volume ($year)" -ForegroundColor Green
    Write-Host ("-" * 40)

    $issues = Get-IssuesToProcess -Volume $volume

    foreach ($issue in $issues) {
        $issueNorm = "$issue" -replace '-', ''
        $batchId = "${year}-v${volume}-n${issueNorm}"

        Write-Host ""
        Write-Host "  Issue $issue (Batch: $batchId)" -ForegroundColor Cyan

        # Get issue page URL
        $issueUrl = Get-IssuePageUrl -Volume $volume -Issue $issue

        if ($null -eq $issueUrl) {
            Write-Host "    No URL mapping for Volume $volume Issue $issue" -ForegroundColor Yellow
            continue
        }

        # Create batch folder with source.json
        $batchFolder = Join-Path $OutputFolder $batchId
        New-Item -ItemType Directory -Path $batchFolder -Force | Out-Null

        $sourceJsonPath = Join-Path $batchFolder "source.json"
        Save-SourceJson -OutputPath $sourceJsonPath -Volume $volume -Issue $issue -Year $year
        Write-Host "    Created: source.json" -ForegroundColor Gray

        # Get papers from issue page
        Start-Sleep -Seconds $RequestDelay
        $papers = Get-PapersFromIssuePage -Url $issueUrl -Volume $volume -Issue $issue -Year $year

        Write-Host "    Found $($papers.Count) papers" -ForegroundColor Gray

        foreach ($paper in $papers) {
            $totalPapers++
            # Papers go inside batch folder
            $destPath = Join-Path $batchFolder $paper.Filename

            if ($SkipExisting -and (Test-Path $destPath)) {
                Write-Host "    SKIP (exists): $($paper.Filename)" -ForegroundColor DarkGray
                $skippedPapers++
                continue
            }

            try {
                Write-Host "    Downloading: $($paper.Filename)" -ForegroundColor White
                Start-Sleep -Seconds $RequestDelay
                Invoke-WebRequest -Uri $paper.Url -OutFile $destPath -UseBasicParsing -ErrorAction Stop
                $downloadedPapers++
            }
            catch {
                Write-Host "    FAILED: $($paper.Filename) - $_" -ForegroundColor Red
                $failedPapers++
            }
        }
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Download Complete" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  Total papers found: $totalPapers"
Write-Host "  Downloaded:         $downloadedPapers" -ForegroundColor Green
Write-Host "  Skipped (existing): $skippedPapers" -ForegroundColor DarkGray
Write-Host "  Failed:             $failedPapers" -ForegroundColor $(if ($failedPapers -gt 0) { "Red" } else { "Green" })
Write-Host ""
Write-Host "Output location:" -ForegroundColor Yellow
Write-Host "  $((Resolve-Path $OutputFolder -ErrorAction SilentlyContinue) ?? $OutputFolder)"
Write-Host ""
Write-Host "Structure:" -ForegroundColor Yellow
Write-Host "  romjist/"
Write-Host "    {batch_id}/"
Write-Host "      source.json"
Write-Host "      *.pdf"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  Each batch folder is ready for RUIN analysis."
Write-Host ""

#endregion
