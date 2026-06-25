$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python312 = Join-Path $root ".venv312\Scripts\python.exe"
$python = Join-Path $root ".venv\Scripts\python.exe"

if (Test-Path $python312) {
    $python = $python312
} elseif (-not (Test-Path $python)) {
    $python = "python"
}

& $python (Join-Path $root "scripts\run_gesture_camera.py") `
    --model (Join-Path $root "best.pt") `
    --camera 0 `
    --conf 0.15 `
    --xoe-conf 0.20 `
    --nam-conf 0.50 `
    --chi-conf 0.10 `
    --action-conf 0.20 `
    --imgsz 640 `
    --width 960 `
    --height 720 `
    --buffer 3 `
    --stable-ratio 0.67 `
    --dwell 1.2 `
    --infer-fps 10 `
    --max-box-area 0.90 `
    --min-box-area 0.001 `
    --min-aspect 0.1 `
    --max-aspect 5.0
