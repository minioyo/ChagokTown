# Project-local batch launcher. Override ASEPRITE_EXE when the executable moves.
$ErrorActionPreference = 'Stop'

$asepriteExe = if ($env:ASEPRITE_EXE) {
    $env:ASEPRITE_EXE
} else {
    'D:\Project\aseprite\build\bin\aseprite.exe'
}

if (-not (Test-Path -LiteralPath $asepriteExe -PathType Leaf)) {
    throw "Aseprite not found: $asepriteExe. Set ASEPRITE_EXE to the executable path."
}

# Piping waits for this Windows GUI executable and keeps its CLI output visible.
& $asepriteExe --batch @args | Out-Host
exit $LASTEXITCODE
