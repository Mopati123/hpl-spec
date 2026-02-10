$ErrorActionPreference = "Stop"

param(
    [Parameter(Mandatory = $true)]
    [string]$DemoName,
    [Parameter(Mandatory = $true)]
    [string]$OutDir,
    [Parameter(Mandatory = $true)]
    [string]$SigningKey,
    [Parameter(Mandatory = $true)]
    [string]$PublicKey,
    [string]$Repo = "Mopati123/hpl-spec",
    [switch]$EnableIo
)

$root = (Resolve-Path ".").Path
$env:PYTHONPATH = (Resolve-Path ".\src").Path

if ($EnableIo.IsPresent) {
    $env:HPL_IO_ENABLED = "1"
    if (-not $env:HPL_IO_ADAPTER) {
        $env:HPL_IO_ADAPTER = "mock"
    }
}

$demoArgs = @(
    "-m", "hpl.cli", "demo", $DemoName,
    "--out-dir", $OutDir,
    "--signing-key", $SigningKey,
    "--pub", $PublicKey
)

if ($EnableIo.IsPresent) {
    $demoArgs += "--enable-io"
}

$demoJson = & python @demoArgs | Out-String
$demo = $demoJson | ConvertFrom-Json
if (-not $demo.ok) {
    throw "Demo failed: $($demo.errors -join ', ')"
}

$bundleDir = $demo.bundle_path
if (-not $bundleDir) {
    throw "Bundle path missing from demo output"
}

$anchorOut = Join-Path $OutDir "anchor"

& python tools\anchor_generator.py `
    $bundleDir `
    --out-dir $anchorOut `
    --repo $Repo `
    --signing-key $SigningKey `
    --public-key $PublicKey | Out-Null

& python tools\verify_anchor.py `
    $bundleDir `
    (Join-Path $anchorOut "anchor_manifest.json") `
    --public-key $PublicKey | Out-Null

$manifestPath = Join-Path $anchorOut "anchor_manifest.json"
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

$summary = @{
    ok = $true
    demo = $DemoName
    bundle_path = $bundleDir
    bundle_id = $manifest.bundle_id
    merkle_root = $manifest.merkle_root
    anchor_manifest = $manifestPath
}

$summary | ConvertTo-Json -Depth 6
