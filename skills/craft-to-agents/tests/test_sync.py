import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync.py"
spec = importlib.util.spec_from_file_location("craft_sync", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)
URL = "https://example.craft.me/abc123"


def block(text, **style):
    return {"content": text, "style": json.dumps(style)}


class CraftSyncTests(unittest.TestCase):
    def test_url(self):
        self.assertEqual(sync.parse_url(URL + "/?tracking=1"), (URL, "abc123"))
        for url in ["http://example.craft.me/abc123", "https://evil.test/abc123", URL + "/extra", "https://user@example.craft.me/abc123"]:
            with self.assertRaises(ValueError):
                sync.parse_url(url)

    def test_formatting_and_ignore(self):
        document = {"blocks": [
            block("Workflow", textStyle="title"),
            block("Steps", textStyle="subtitle"),
            block("Plan: use docs/", listStyle="numbered", userDefinedListNumber=2,
                  _runAttributes=[{"isBold": True, "range": [0, 5]}, {"isCode": True, "range": [10, 5]}]),
            block("Rule", listStyle="bullet"),
            block("IGNORE", textStyle="title"),
            block("Never copied"),
            block("Later section", textStyle="title"),
        ]}
        self.assertEqual(sync.render(document), "# Workflow\n\n## Steps\n\n2. **Plan:** use `docs/`\n\n- Rule")
        self.assertEqual(sync.render({"blocks": [block("Mention IGNORE normally")]}), "Mention IGNORE normally")
        with self.assertRaises(ValueError):
            sync.render({"blocks": [block("IGNORE", textStyle="title"), block("Excluded")]})

    def test_unicode_and_embedded_backticks(self):
        document = {"blocks": [block("😀 use fd and `x`", _runAttributes=[
            {"isCode": True, "range": [7, 2]}, {"isCode": True, "range": [14, 3]},
        ])]}
        self.assertEqual(sync.render(document), "😀 use `fd` and `` `x` ``")

    def test_merge_and_source_reuse(self):
        before, after = "# Personal\r\n", "\r\n<!-- plugin:start -->\nPlugin\n<!-- plugin:end -->"
        old = before + "<!-- custom:start -->\nOld\n<!-- custom:end -->" + after
        updated, name = sync.merge(old, "# New", URL, "abc123", "custom")
        self.assertEqual(name, "custom")
        self.assertTrue(updated.startswith(before))
        self.assertTrue(updated.endswith(after))
        self.assertIn(f"Source: <{URL}>", updated)
        self.assertIn("refresh with the craft-to-agents skill", updated)
        self.assertEqual(sync.merge(updated, "# New", URL, "abc123"), (updated, "custom"))
        other, _ = sync.merge(updated, "Other rules", "https://example.craft.me/other", "other")
        self.assertTrue(other.startswith(updated))

    def test_invalid_markers_and_collisions(self):
        for old in ["<!-- custom:start -->", "<!-- custom:end -->", "<!-- custom:end --><!-- custom:start -->",
                    "<!-- custom:start --><!-- custom:start --><!-- custom:end -->"]:
            with self.assertRaises(ValueError):
                sync.merge(old, "Rules", URL, "abc123", "custom")
        with self.assertRaises(ValueError):
            sync.merge("", "<!-- custom:end -->", URL, "abc123", "custom")
        with self.assertRaises(ValueError):
            sync.merge("", "Rules", URL, "abc123", "bad-->name")

    def test_files_idempotency_and_failure_safety(self):
        response = subprocess.CompletedProcess([], 0, stdout=json.dumps({"blocks": [block("Rules")]}).encode())
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "config" / "AGENTS.md"
            with patch.object(sync.subprocess, "run", return_value=response):
                self.assertTrue(sync.sync(URL, target).startswith("Updated:"))
                original = target.read_bytes()
                timestamp = target.stat().st_mtime_ns
                self.assertTrue(sync.sync(URL, target).startswith("Unchanged:"))
                self.assertEqual(target.stat().st_mtime_ns, timestamp)
            with patch.object(sync.subprocess, "run", side_effect=subprocess.CalledProcessError(22, "curl")):
                with self.assertRaises(subprocess.CalledProcessError):
                    sync.sync(URL, target)
            empty = subprocess.CompletedProcess([], 0, stdout=b'{"blocks":[]}')
            with patch.object(sync.subprocess, "run", return_value=empty):
                with self.assertRaises(ValueError):
                    sync.sync(URL, target)
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(list(target.parent.iterdir()), [target])


if __name__ == "__main__":
    unittest.main()
