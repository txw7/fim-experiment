import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "typed-rule-tower-v2" / "evidence"


class S3ContractNetworkArtifactTests(unittest.TestCase):
    def test_web_bundle_discloses_absent_model_trace_and_candidate_status(self):
        page = (EVIDENCE / "s3-contract-network.html").read_text()
        graph = json.loads((EVIDENCE / "s3-contract-network.json").read_text())
        trace = json.loads((EVIDENCE / "s3-contract-prompt-trace.json").read_text())

        self.assertIn("Prompt / output trace:", page)
        self.assertIn("no Jev, Laya, or Qwen call produced this network", page)
        self.assertEqual(trace["status"], "NO_MODEL_CALLS_RECORDED")
        self.assertEqual(trace["requests"], [])
        self.assertEqual(trace["responses"], [])
        self.assertEqual(graph["status"], "INCOMPLETE_CANDIDATE")
        self.assertEqual(graph["native_admission"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
