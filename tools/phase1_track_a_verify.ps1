param(
    [string]$DemoName = "navier-stokes",
    [string]$OutDir = "artifacts\phase1\navier_stokes\run_002",
    [string]$SigningKey = "tests\fixtures\keys\ci_ed25519_test.sk",
    [string]$PublicKey = "tests\fixtures\keys\ci_ed25519_test.pub",
    [string]$Repo = "Mopati123/hpl-spec",
    [string]$ReferenceAnchorManifest = "references\phase1\navier_stokes\machine_a_d878e95\anchor_manifest.json",
    [string]$ReferenceAnchorLeaves = "references\phase1\navier_stokes\machine_a_d878e95\anchor_leaves.json",
    [switch]$EnableIo,
    [switch]$EnableNet
)

$ErrorActionPreference = "Stop"

$requiredInputs = @(
    @{ Name = "signing key"; Path = $SigningKey },
    @{ Name = "public key"; Path = $PublicKey },
    @{ Name = "reference anchor manifest"; Path = $ReferenceAnchorManifest },
    @{ Name = "reference anchor leaves"; Path = $ReferenceAnchorLeaves }
)
foreach ($item in $requiredInputs) {
    if (-not (Test-Path $item.Path)) {
        throw "Missing $($item.Name): $($item.Path)"
    }
}

$demoArgs = @{
    DemoName = $DemoName
    OutDir = $OutDir
    SigningKey = $SigningKey
    PublicKey = $PublicKey
    Repo = $Repo
    ReferenceAnchorManifest = $ReferenceAnchorManifest
    ReferenceAnchorLeaves = $ReferenceAnchorLeaves
}
if ($EnableIo.IsPresent) {
    $demoArgs.EnableIo = $true
}
if ($EnableNet.IsPresent) {
    $demoArgs.EnableNet = $true
}

$null = & .\tools\phase1_anchor_demo.ps1 @demoArgs

$candidateManifest = Join-Path $OutDir "anchor\anchor_manifest.json"
$candidateLeaves = Join-Path $OutDir "anchor\anchor_leaves.json"
if (-not (Test-Path $candidateManifest)) {
    throw "Candidate anchor manifest not found: $candidateManifest"
}
if (-not (Test-Path $candidateLeaves)) {
    throw "Candidate anchor leaves not found: $candidateLeaves"
}

$compareOutput = & python tools\compare_anchor_contract.py `
    --machine-a-manifest $ReferenceAnchorManifest `
    --machine-a-leaves $ReferenceAnchorLeaves `
    --machine-b-manifest $candidateManifest `
    --machine-b-leaves $candidateLeaves

$compareJson = $compareOutput |
    Where-Object { $_ -is [string] -and $_.Trim().StartsWith("{") } |
    Select-Object -First 1
if (-not $compareJson) {
    throw "Comparator did not emit JSON output."
}

$compare = $compareJson | ConvertFrom-Json
$contractMatch = [bool]$compare.CONTRACT_MATCH
$merkleMatch = [bool]$compare.MERKLE_MATCH

$summary = @{
    demo = $DemoName
    out_dir = $OutDir
    reference_manifest = $ReferenceAnchorManifest
    reference_leaves = $ReferenceAnchorLeaves
    candidate_manifest = $candidateManifest
    candidate_leaves = $candidateLeaves
    CONTRACT_MATCH = $contractMatch
    MERKLE_MATCH = $merkleMatch
    ROOT_CAUSE = "$($compare.ROOT_CAUSE)"
    NEXT_ACTION = "$($compare.NEXT_ACTION)"
}

$summary | ConvertTo-Json -Depth 6
if (-not $contractMatch -or -not $merkleMatch) {
    exit 1
}
exit 0
