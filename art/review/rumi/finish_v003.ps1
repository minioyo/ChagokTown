$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:/Project/Etc/ChagokTown'
$rumiRaw = 'art/raw/rumi/rumi_concept_v003.png'
if (Test-Path -LiteralPath $rumiRaw) { throw 'Refusing to overwrite the generated original.' }
Copy-Item -LiteralPath 'C:/Users/hy/.codex/generated_images/01a1a52f-bf61-7bf2-a196-d0ac612bd760/exec-8c05ac18-7113-4ad1-b4c4-4f4f2fcf1602.png' -Destination $rumiRaw
& 'C:/Program Files/PowerShell/7/pwsh.exe' -NoProfile -File tools/art/aseprite.ps1 --script art/review/rumi/prepare_v003.lua
if ($LASTEXITCODE -ne 0) { throw 'Aseprite export failed.' }
python -B art/review/rumi/inspect_v002.py v002
if ($LASTEXITCODE -ne 0) { throw 'v002 inspection failed.' }
python -B art/review/rumi/inspect_v002.py v003
if ($LASTEXITCODE -ne 0) { throw 'v003 inspection failed.' }
