param(
    [string]$DemoName = "navier-stokes",
    [string]$OutDir = "artifacts\phase1\navier_stokes\run_002",
    [string]$SigningKey = "tests\fixtures\keys\ci_ed25519_test.sk",
    [string]$PublicKey = "tests\fixtures\keys\ci_ed25519_test.pub",
    [string]$Repo = "Mopati123/hpl-spec",
    [string]$ReferenceAnchorManifest = "references\phase1\navier_stokes\machine_a_f06023a\anchor_manifest.json",
    [string]$ReferenceAnchorLeaves = "references\phase1\navier_stokes\machine_a_f06023a\anchor_leaves.json",
    [string]$WorktreeDir = "..\hpl-spec-tracka-ref",
    [switch]$SkipTests,
    [switch]$RecreateVenv
)

$ErrorActionPreference = "Stop"

$args = @(
    "tools\phase1_track_a_run.py",
    "--demo-name", $DemoName,
    "--out-dir", $OutDir,
    "--signing-key", $SigningKey,
    "--public-key", $PublicKey,
    "--repo", $Repo,
    "--reference-manifest", $ReferenceAnchorManifest,
    "--reference-leaves", $ReferenceAnchorLeaves,
    "--worktree-dir", $WorktreeDir
)
if ($SkipTests.IsPresent) {
    $args += "--skip-tests"
}
if ($RecreateVenv.IsPresent) {
    $args += "--recreate-venv"
}

& python @args
exit $LASTEXITCODE
