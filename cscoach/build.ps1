param([string]$Vp = 'vp')
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    $env:CI = 'true'
    $env:CSC_IDENTITY_AUTO_DISCOVERY = 'false'
    & $Vp install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
    & $Vp check
    if ($LASTEXITCODE -ne 0) { throw 'Code checks failed' }
    & $Vp run test
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
    & $Vp run deadcode
    if ($LASTEXITCODE -ne 0) { throw 'Dead-code check failed' }
    & $Vp run build
    if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
    & $Vp run package --dir --win --publish never
    if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
    $destination = Join-Path (Get-Location) 'dist\win-unpacked'
    Copy-Item (Join-Path $PSScriptRoot 'csdm-cscoach.cmd') $destination
    Copy-Item 'scripts\cscoach-cli.mjs' $destination
    Copy-Item 'LICENSE' (Join-Path $destination 'LICENSE-csdm.txt')
    $revision = (& git rev-parse HEAD).Trim()
    $package = Get-Content package.json -Raw | ConvertFrom-Json
    $manifest = [ordered]@{
        version = $package.version
        upstream = '3ba51c9d'
        revision = $revision
        builtAt = [DateTime]::UtcNow.ToString('o')
        analyzerSha256 = (Get-FileHash (Join-Path $destination 'resources\static\csda.exe') -Algorithm SHA256).Hash
        pluginSha256 = (Get-FileHash (Join-Path $destination 'resources\static\cs2\server.dll') -Algorithm SHA256).Hash
        installation = 'portable; official installation preserved'
    }
    $manifest | ConvertTo-Json | Set-Content (Join-Path $destination 'cscoach-build.json') -Encoding UTF8
} finally {
    Pop-Location
}
