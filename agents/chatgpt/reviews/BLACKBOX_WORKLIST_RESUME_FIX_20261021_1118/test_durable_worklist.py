import json
import tempfile
import unittest
from pathlib import Path
from durable_worklist import Worklist


class ResumeTests(unittest.TestCase):
    def test_full_queue_survives_more_than_30_pending(self):
        with tempfile.TemporaryDirectory() as td:
            q = Worklist(td, [f"doc{i}" for i in range(130)], policy_id="v1")
            seen = []
            def process(node):
                seen.append(node)
                return {"targets": [], "source_sha256": node}
            first = q.run(process, max_items=3)
            self.assertEqual(first["pending"], 127)
            saved = json.loads((Path(td) / "worklist.json").read_text())
            self.assertEqual(len(saved["pending"]), 127)
            second = Worklist(td, policy_id="v1").run(process)
            self.assertEqual(second["phase"], "WORKLIST_DRAINED")
            self.assertEqual(len(seen), 130)
            self.assertEqual(len(set(seen)), 130)

    def test_references_cycle_and_canonical_alias(self):
        with tempfile.TemporaryDirectory() as td:
            q = Worklist(td, ["A"], policy_id="v1", normalize=str.lower)
            def process(node):
                return {"targets": ["B", "b"] if node == "a" else ["A"]}
            result = q.run(process)
            self.assertEqual(result["done"], 2)
            self.assertEqual(result["pending"], 0)

    def test_expired_deadline_does_no_work(self):
        with tempfile.TemporaryDirectory() as td:
            q = Worklist(td, ["a"], policy_id="v1")
            result = q.run(lambda _: self.fail("must not run"), deadline="2000-01-01T00:00:00+00:00")
            self.assertEqual(result["pending"], 1)
            self.assertEqual(result["phase"], "DEADLINE_CHECKPOINT")

    def test_scope_exclusion_and_failure_continue(self):
        with tempfile.TemporaryDirectory() as td:
            q = Worklist(td, ["bad", "good"], policy_id="v1", admit=lambda n: n != "excluded")
            def process(node):
                if node == "bad":
                    raise OSError("fixture read failure")
                return {"targets": ["excluded"]}
            result = q.run(process)
            self.assertEqual((result["done"], result["failed"], result["excluded"]), (1, 1, 1))

    def test_interruption_retains_current_and_all_remaining(self):
        with tempfile.TemporaryDirectory() as td:
            q = Worklist(td, ["a", "b"], policy_id="v1")
            def interrupted(node):
                raise KeyboardInterrupt()
            with self.assertRaises(KeyboardInterrupt):
                q.run(interrupted)
            result = Worklist(td, policy_id="v1").run(lambda n: {"targets": []})
            self.assertEqual(result["done"], 2)

    def test_policy_change_does_not_reuse_state_silently(self):
        with tempfile.TemporaryDirectory() as td:
            Worklist(td, ["a"], policy_id="v1")
            with self.assertRaises(ValueError):
                Worklist(td, policy_id="v2")

    def test_serialization_failure_keeps_pending_on_disk(self):
        with tempfile.TemporaryDirectory() as td:
            q = Worklist(td, ["a", "b"], policy_id="v1")
            with self.assertRaises(TypeError):
                q.run(lambda n: {"targets": [], "invalid": object()})
            restored = Worklist(td, policy_id="v1")
            self.assertEqual(list(restored.pending), ["a", "b"])


    def test_adapter_end_to_end_in_fixture_only(self):
        import hashlib
        import run_rule_resume as adapter
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "business"
            old_out = root / "_OPS" / "inventory"
            mirror = root / "hub_inventory"
            shards = old_out / "shards"
            shards.mkdir(parents=True)
            mirror.mkdir(parents=True)
            a, b = root / "a.md", root / "b.md"
            a.write_text("fixture a", encoding="utf-8")
            b.write_text("fixture b", encoding="utf-8")
            nodes = [{"path": str(a)}, {"path": str(b)}]
            (shards / "RULES_ACTIVE_SHARD_000.jsonl").write_text(
                "\n".join(json.dumps(n) for n in nodes), encoding="utf-8")
            base_source = Path(td) / "fixture_base.py"
            fixture = (
                "from pathlib import Path\nimport hashlib\n"
                "classify_token_v5 = True\nDOC_SUFFIX = {'.md'}\n"
                + "ROOT = Path(" + repr(str(root)) + ")\n"
                + "OUT = Path(" + repr(str(old_out)) + ")\n"
                + "HUB = Path(" + repr(str(mirror)) + ")\n"
                + "SHARDS = Path(" + repr(str(shards)) + ")\n"
                + "def build_rule_id_index(seeds): return {}\n"
                + "def strict_read(p):\n"
                + " b=p.read_bytes(); return {'ok':True,'text':b.decode(),'encoding':'utf-8','sha256':hashlib.sha256(b).hexdigest()}\n"
                + "def load_text_from_read(rd): return rd['text']\n"
                + "def extract_tokens(text):\n"
                + " yield (1,'rule_id_plain','STATUS_R1')\n"
                + " if text=='fixture a': yield (2,'backtick_path',str(ROOT/'b.md'))\n"
                + " else: yield (2,'backtick_path',str(ROOT/'a.md'))\n"
                + "def classify_ref(tok,src,line,field,idx):\n"
                + " return [{'src':str(src),'line':line,'raw_token':tok,'resolved':tok,'edge_status':'RESOLVED'}]\n"
            )
            base_source.write_text(fixture, encoding="utf-8")
            output = old_out / "continuation"
            argv = ["run_rule_resume.py", "--base-source", str(base_source),
                    "--output", str(output), "--deadline", "2099-01-01T00:00:00+00:00"]
            with patch.object(adapter, "BASE_SHA", hashlib.sha256(base_source.read_bytes()).hexdigest()), patch("sys.argv", argv):
                adapter.main()
            summary = json.loads((output / "SUMMARY.json").read_text())
            self.assertEqual((summary["done"], summary["pending"]), (2, 0))
            results = [json.loads(p.read_text()) for p in
                       (output / "worklist" / "node_results").glob("*.json")]
            self.assertTrue(all(len(r["identifier_candidates"]) == 1 for r in results))
            self.assertTrue(all(len(r["edges"]) == 1 for r in results))
            self.assertFalse(summary["system_inventory_acceptance"])

if __name__ == "__main__":
    unittest.main(verbosity=2)

