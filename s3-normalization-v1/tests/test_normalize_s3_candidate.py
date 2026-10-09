import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from normalize_s3_candidate import normalize

RUN = Path(__file__).resolve().parents[1] / "example" / "input"


@unittest.skipUnless((RUN / "expanded.json").exists(), "v17 candidate artifact unavailable")
class S3CandidateNormalizationChecks(unittest.TestCase):
    def test_readable_projection_reconstructs_topology_and_keeps_open_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "normalized"
            result = normalize(RUN, out)
            rendered = (out / "normal-form.txt").read_text()
            receipt = (out / "reduction-receipt.txt").read_text()
            provenance = (out / "provenance.txt").read_text()
            example = RUN.parent / "output"
            self.assertTrue(result["topology_roundtrip"])
            self.assertIn("(SUPERVISE A0 (PARALLEL (PAIR B1 C1) (PAIR B2 C2)))", rendered)
            self.assertIn("c5: gate-checks execution — UNRESOLVED", rendered)
            self.assertEqual(result["qwen_unresolved"], 5)
            self.assertEqual(result["open_slots"], 11)
            self.assertIn("semantic_equivalence_to_entire_S3: NOT_ESTABLISHED", receipt)
            self.assertIn("clause-013 bytes[", provenance)
            self.assertIn("source A typed pair output", provenance)
            self.assertEqual(rendered, (example / "normal-form.txt").read_text())
            self.assertEqual(receipt, (example / "reduction-receipt.txt").read_text())


if __name__ == "__main__":
    unittest.main()
