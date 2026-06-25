param(
    [int]$EveryN = 6,
    [int]$MaxPerVideo = 800,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

function Get-ProjectPython {
    $candidates = @(
        (Join-Path $root ".venv\Scripts\python.exe"),
        "python",
        "py"
    )

    foreach ($candidate in $candidates) {
        try {
            $output = & $candidate --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        } catch {
            continue
        }
    }

    throw "No working Python found. Install Python 3.11+, then recreate .venv and install requirements.txt."
}

$python = Get-ProjectPython
$argsList = @(
    (Join-Path $root "training\01_extract_frames.py"),
    "--every-n", $EveryN,
    "--max-per-video", $MaxPerVideo
)

if ($Clean) {
    $argsList += "--clean"
}

& $python @argsList
