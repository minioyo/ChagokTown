$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:/Project/Etc/ChagokTown'
$rumiRaw = 'art/raw/rumi/rumi_concept_v004.png'
if (Test-Path -LiteralPath $rumiRaw) { throw 'Refusing to overwrite the generated original.' }
Copy-Item -LiteralPath 'C:/Users/hy/.codex/generated_images/01a1a52f-bf61-7bf2-a196-d0ac612bd760/exec-81505f7d-3ec7-4e1e-b56b-450cb6247b52.png' -Destination $rumiRaw
& 'C:/Program Files/PowerShell/7/pwsh.exe' -NoProfile -File tools/art/aseprite.ps1 --script art/review/rumi/prepare_v004.lua
if ($LASTEXITCODE -ne 0) { throw 'Aseprite export failed.' }
python -B art/review/rumi/inspect_v002.py v004
if ($LASTEXITCODE -ne 0) { throw 'v004 inspection failed.' }
