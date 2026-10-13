import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "blocks.py"
spec = importlib.util.spec_from_file_location("craft_blocks", SCRIPT)
blocks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blocks)
URL = "https://example.craft.me/abc123"


class BlockTests(unittest.TestCase):
    def test_merge_and_source_reuse(self):
        before, after = "# Personal\r\n", "\r\n<!-- plugin:start -->\nPlugin\n<!-- plugin:end -->"
        old = before + "<!-- custom:start -->\nOld\n<!-- custom:end -->" + after
        updated = blocks.merge(old, "# New", URL, "custom")
        self.assertTrue(updated.startswith(before))
        self.assertTrue(updated.endswith(after))
        self.assertIn(f"Source: <{URL}>", updated)
        self.assertIn("refresh with the craft-to-agents skill", updated)
        self.assertEqual(blocks.merge(updated, "# New", URL, "custom"), updated)
        self.assertEqual(blocks.find_block(updated, URL), "custom")
        other = blocks.merge(updated, "Other rules", "https://example.craft.me/other", "other")
        self.assertTrue(other.startswith(updated))

    def test_append_when_absent(self):
        appended = blocks.merge("# Personal\n", "# New", URL, "custom")
        self.assertTrue(appended.startswith("# Personal\n"))
        self.assertIn("<!-- custom:start -->", appended)
        self.assertEqual(blocks.merge("", "# New", URL, "custom").splitlines()[0], "<!-- custom:start -->")

    def test_custom_hint_and_no_hint(self):
        self.assertIn("(refresh with the terse skill)", blocks.merge("", "Rules", URL, "custom", "terse"))
        self.assertNotIn("refresh with", blocks.merge("", "Rules", URL, "custom", ""))

    def test_invalid_markers_and_collisions(self):
        for old in ["<!-- custom:start -->", "<!-- custom:end -->", "<!-- custom:end --><!-- custom:start -->",
                    "<!-- custom:start --><!-- custom:start --><!-- custom:end -->"]:
            with self.assertRaises(ValueError):
                blocks.merge(old, "Rules", URL, "custom")
        with self.assertRaises(ValueError):
            blocks.merge("", "<!-- custom:end -->", URL, "custom")
        with self.assertRaises(ValueError):
            blocks.merge("", "Rules", URL, "bad-->name")

    def test_find_block_ambiguity(self):
        two = "<!-- a:start -->\nSource: <{0}>\n<!-- a:end -->\n<!-- b:start -->\nSource: <{0}>\n<!-- b:end -->".format(URL)
        with self.assertRaises(ValueError):
            blocks.find_block(two, URL)
        self.assertIsNone(blocks.find_block("", URL))

    def test_write_idempotency_and_failure_safety(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "config" / "AGENTS.md"
            self.assertTrue(blocks.write(target, "Rules", URL, "custom").startswith("Updated:"))
            original = target.read_bytes()
            timestamp = target.stat().st_mtime_ns
            self.assertTrue(blocks.write(target, "Rules", URL, "custom").startswith("Unchanged:"))
            self.assertEqual(target.stat().st_mtime_ns, timestamp)
            with self.assertRaises(ValueError):
                blocks.write(target, "<!-- custom:end -->", URL, "custom")
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(list(target.parent.iterdir()), [target])


if __name__ == "__main__":
    unittest.main()
