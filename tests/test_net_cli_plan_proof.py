import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_cli(args, cwd=ROOT):
    return subprocess.run(
        [sys.executable, "-m", "hpl.cli", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class NetCliPlanProofTests(unittest.TestCase):
    def test_net_shadow_cli_generates_plan_runtime_and_bundle_evidence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "net_shadow_out"

            result = _run_cli(
                [
                    "demo",
                    "net-shadow",
                    "--out-dir",
                    str(out_dir),
                    "--input",
                    "examples/momentum_trade.hpl",
                    "--endpoint",
                    "net://demo",
                    "--message",
                    "hello",
                    "--enable-net",
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)

            summary = json.loads(result.stdout.strip().splitlines()[-1])
            self.assertFalse(summary["ok"])
            self.assertIn("signing_key required for net-shadow demo", summary["errors"])

            work_dir = out_dir / "work"
            plan_path = work_dir / "plan.json"
            runtime_path = work_dir / "runtime.json"
            manifest_path = Path(summary["bundle_path"]) / "bundle_manifest.json"

            self.assertTrue(plan_path.exists())
            self.assertTrue(runtime_path.exists())
            self.assertTrue(manifest_path.exists())

            plan = _read_json(plan_path)
            runtime = _read_json(runtime_path)
            manifest = _read_json(manifest_path)

            self.assertEqual(plan.get("status"), "planned")
            self.assertEqual(runtime.get("status"), "completed")

            expected_steps = [
                "NET_CONNECT",
                "NET_HANDSHAKE",
                "NET_KEY_EXCHANGE",
                "NET_SEND",
                "NET_RECV",
                "NET_CLOSE",
            ]
            actual_steps = [
                step.get("effect_type")
                for step in plan.get("steps", [])
                if isinstance(step, dict)
            ]
            self.assertEqual(actual_steps, expected_steps)

            expected_files = [
                "net_connect_request.json",
                "net_connect_response.json",
                "net_connect_event.json",
                "net_handshake_request.json",
                "net_handshake_response.json",
                "net_handshake_event.json",
                "net_key_exchange_request.json",
                "net_key_exchange_response.json",
                "net_key_exchange_event.json",
                "net_send_request.json",
                "net_send_response.json",
                "net_send_event.json",
                "net_recv_request.json",
                "net_recv_response.json",
                "net_recv_event.json",
                "net_close_request.json",
                "net_close_response.json",
                "net_close_event.json",
                "net_session_manifest.json",
                "redaction_report.json",
            ]

            for filename in expected_files:
                self.assertTrue((work_dir / filename).exists(), filename)

            self.assertIn("net_lane_v1", manifest)
            self.assertTrue(manifest["net_lane_v1"]["ok"])
            self.assertEqual(manifest["net_lane_v1"]["missing_required"], [])

            session = _read_json(work_dir / "net_session_manifest.json")
            self.assertEqual(session.get("endpoint"), "net://demo")
            self.assertEqual(session.get("crypto_policy_id"), "QKX1")
            self.assertEqual(session.get("redaction_policy_id"), "R1")

            connect_request = _read_json(work_dir / "net_connect_request.json")
            connect_response = _read_json(work_dir / "net_connect_response.json")
            connect_event = _read_json(work_dir / "net_connect_event.json")

            self.assertEqual(
                connect_response.get("request_id"),
                connect_request.get("request_id"),
            )
            self.assertEqual(
                connect_event.get("request_id"),
                connect_request.get("request_id"),
            )


if __name__ == "__main__":
    unittest.main()