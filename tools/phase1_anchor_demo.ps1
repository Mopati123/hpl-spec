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
    [switch]$EnableIo,
    [switch]$EnableNet,
    [string]$ReferenceAnchorManifest = "",
    [string]$ReferenceAnchorLeaves = ""
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path ".").Path
$env:PYTHONPATH = (Resolve-Path ".\src").Path

if ($EnableIo.IsPresent) {
    $env:HPL_IO_ENABLED = "1"
    if (-not $env:HPL_IO_ADAPTER) {
        $env:HPL_IO_ADAPTER = "mock"
    }
}

if ($EnableNet.IsPresent) {
    $env:HPL_NET_ENABLED = "1"
    if (-not $env:HPL_NET_ADAPTER) {
        $env:HPL_NET_ADAPTER = "mock"
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
if ($EnableNet.IsPresent) {
    $demoArgs += "--enable-net"
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
$leavesPath = Join-Path $anchorOut "anchor_leaves.json"
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

$machineContract = [ordered]@{
    git_commit = "$($manifest.git_commit)"
    leaf_rule = "$($manifest.leaf_rule)"
    leaf_count = [int]$manifest.leaf_count
    bundle_manifest_digest = "$($manifest.bundle_manifest_digest)"
    leaves_digest = "$($manifest.leaves_digest)"
    merkle_root = "$($manifest.merkle_root)"
}

$machineContractPath = Join-Path $anchorOut "machine_contract.json"
$machineContract | ConvertTo-Json -Depth 6 | Set-Content -Path $machineContractPath -Encoding UTF8

$contractMatch = $true
$merkleMatch = $true
$rootCause = "none"
$nextAction = "none"
$firstDivergentLeaf = $null
$referenceContract = $null

if ($ReferenceAnchorManifest) {
    if (-not (Test-Path $ReferenceAnchorManifest)) {
        throw "Reference anchor manifest not found: $ReferenceAnchorManifest"
    }
    $refManifest = Get-Content $ReferenceAnchorManifest -Raw | ConvertFrom-Json
    $referenceContract = [ordered]@{
        git_commit = "$($refManifest.git_commit)"
        leaf_rule = "$($refManifest.leaf_rule)"
        leaf_count = [int]$refManifest.leaf_count
        bundle_manifest_digest = "$($refManifest.bundle_manifest_digest)"
        leaves_digest = "$($refManifest.leaves_digest)"
        merkle_root = "$($refManifest.merkle_root)"
    }

    $contractFields = @("git_commit", "leaf_rule", "leaf_count", "bundle_manifest_digest", "leaves_digest")
    foreach ($field in $contractFields) {
        if ($machineContract[$field] -ne $referenceContract[$field]) {
            $contractMatch = $false
        }
    }

    if (-not $contractMatch) {
        $rootCause = "Reference anchor is from a different contract state"
        $nextAction = "Align contract state (commit/rule/leaves) before comparing merkle root"
        Write-Host "Reference anchor is from a different contract state. Refusing comparison."
        throw "contract_state_mismatch"
    }

    if ($machineContract.merkle_root -ne $referenceContract.merkle_root) {
        $merkleMatch = $false
        $rootCause = "contract matched, merkle mismatched"
        $nextAction = "Run deterministic leaf diff"
        if ($ReferenceAnchorLeaves -and (Test-Path $ReferenceAnchorLeaves)) {
            $localLeaves = (Get-Content $leavesPath -Raw | ConvertFrom-Json).inputs
            $refLeaves = (Get-Content $ReferenceAnchorLeaves -Raw | ConvertFrom-Json).inputs
            $limit = [Math]::Min($localLeaves.Count, $refLeaves.Count)
            for ($i = 0; $i -lt $limit; $i++) {
                $a = $localLeaves[$i]
                $b = $refLeaves[$i]
                if ("$($a.path)" -ne "$($b.path)" -or "$($a.leaf_hash)" -ne "$($b.leaf_hash)") {
                    $firstDivergentLeaf = [ordered]@{
                        index = $i
                        machine_leaf = [ordered]@{
                            relpath = "$($a.path)"
                            file_hash = "$($a.sha256)"
                            leaf_hash = "$($a.leaf_hash)"
                        }
                        reference_leaf = [ordered]@{
                            relpath = "$($b.path)"
                            file_hash = "$($b.sha256)"
                            leaf_hash = "$($b.leaf_hash)"
                        }
                    }
                    break
                }
            }
        }
    } else {
        $merkleMatch = $true
        $rootCause = "contract matched and merkle matched"
        $nextAction = "Track A green"
    }
}

$summary = @{
    ok = $true
    demo = $DemoName
    bundle_path = $bundleDir
    bundle_id = $manifest.bundle_id
    merkle_root = $manifest.merkle_root
    anchor_manifest = $manifestPath
    machine_contract_path = $machineContractPath
    machine_contract = $machineContract
    reference_contract = $referenceContract
    CONTRACT_MATCH = $contractMatch
    MERKLE_MATCH = $merkleMatch
    ROOT_CAUSE = $rootCause
    NEXT_ACTION = $nextAction
    first_divergent_leaf = $firstDivergentLeaf
}

$summary | ConvertTo-Json -Depth 6
