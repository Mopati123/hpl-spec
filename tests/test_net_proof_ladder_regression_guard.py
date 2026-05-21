from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

NET_PROOF_LADDER = {
    "N1": {
        "path": "tests/test_net_token_gate.py",
        "tokens": (
            "NETPermissionDenied",
            "NETEndpointNotAllowed",
            "NETBudgetExceeded",
        ),
    },
    "N2": {
        "path": "tests/test_net_evidence_bundle.py",
        "tokens": ("net_lane_v1", "missing_required"),
    },
    "N3": {
        "path": "tests/test_net_adapter_contract.py",
        "tokens": ("HPL_NET_ADAPTER", "request_id"),
    },
    "N4": {
        "path": "tests/test_net_session_lifecycle.py",
        "tokens": ("NET_CONNECT", "NET_CLOSE", "net_session_manifest"),
    },
    "N5": {
        "path": "tests/test_net_cli_plan_proof.py",
        "tokens": ("net-shadow", "bundle_manifest.json"),
    },
    "N6": {
        "path": "tests/test_net_signed_bundle_proof.py",
        "tokens": ("bundle_manifest.sig", "verify_bundle_manifest_signature"),
    },
    "N7": {
        "path": "tests/test_net_anchor_ready_proof.py",
        "tokens": ("sha256:", "net_lane_v1"),
    },
    "N8": {
        "path": "tests/test_net_epoch_anchor_verification_proof.py",
        "tokens": ("--require-epoch", "signature_ok", "epoch_ok"),
    },
    "N9": {
        "path": "tests/test_net_epoch_refusal_proof.py",
        "tokens": ("signature verification failed", "refusal"),
    },
    "N10": {
        "path": "tests/test_net_refusal_bundle_completeness.py",
        "tokens": ("signature_ok", "summary", "refusal"),
    },
    "N11": {
        "path": "tests/test_net_refusal_bundle_signature_proof.py",
        "tokens": ("bundle_manifest.sig", "verify_bundle_manifest_signature"),
    },
    "N12": {
        "path": "tests/test_net_refusal_anchor_ready_proof.py",
        "tokens": ("sha256:", "commitment"),
    },
    "N13": {
        "path": "tests/test_net_valid_refusal_duality_proof.py",
        "tokens": ("CONTRACT_KEYS", "summary_ok", "verification_signature_ok"),
    },
}


def test_net_proof_ladder_n1_through_n13_is_represented_in_order():
    assert tuple(NET_PROOF_LADDER) == tuple(f"N{index}" for index in range(1, 14))


def test_net_proof_ladder_files_exist_and_preserve_core_invariants():
    for label, proof in NET_PROOF_LADDER.items():
        proof_path = ROOT / proof["path"]
        assert proof_path.exists(), f"{label} proof file is missing: {proof_path}"

        source = proof_path.read_text(encoding="utf-8")
        missing = [token for token in proof["tokens"] if token not in source]
        assert not missing, f"{label} proof {proof_path} is missing tokens: {missing}"
