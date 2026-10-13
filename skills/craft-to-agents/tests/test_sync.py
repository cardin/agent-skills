import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("craft_sync", SCRIPTS / "sync.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)
URL = "https://example.craft.me/abc123"


def fake_read_craft(directory, *, url=URL, share_id="abc123", markdown="Rules", exit_code=0):
    """Write a stand-in fetch.py so the binder can be tested without the network."""
    path = Path(directory) / "fetch.py"
    path.write_text(textwrap.dedent(f"""
        import json, sys
        if {exit_code}:
            sys.exit({exit_code})
        json.dump({{"url": {url!r}, "host": "example.craft.me",
                   "share_id": {share_id!r}, "markdown": {markdown!r}}}, sys.stdout)
    """))
    return path


class BinderTests(unittest.TestCase):
    def test_sync_writes_block_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            script = fake_read_craft(directory)
            target = Path(directory) / "AGENTS.md"
            self.assertTrue(sync.sync(URL, target, read_craft_script=script).startswith("Updated:"))
            content = target.read_text()
            self.assertIn("<!-- craft-abc123:start -->", content)
            self.assertIn(f"Source: <{URL}>", content)
            timestamp = target.stat().st_mtime_ns
            self.assertTrue(sync.sync(URL, target, read_craft_script=script).startswith("Unchanged:"))
            self.assertEqual(target.stat().st_mtime_ns, timestamp)

    def test_existing_source_block_is_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            script = fake_read_craft(directory)
            target = Path(directory) / "AGENTS.md"
            target.write_text(f"<!-- legacy:start -->\nSource: <{URL}>\n\nOld\n<!-- legacy:end -->\n")
            status = sync.sync(URL, target, read_craft_script=script)
            self.assertIn("[legacy]", status)
            self.assertNotIn("craft-abc123", target.read_text())

    def test_custom_block_name(self):
        with tempfile.TemporaryDirectory() as directory:
            script = fake_read_craft(directory)
            target = Path(directory) / "AGENTS.md"
            self.assertIn("[my-rules]", sync.sync(URL, target, "my-rules", read_craft_script=script))

    def test_missing_read_craft_reports_clear_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                sync.locate_read_craft(str(Path(directory) / "absent.py"))

    def test_locates_sibling_read_craft(self):
        self.assertEqual(sync.locate_read_craft().name, "fetch.py")
        self.assertIn("read-craft", str(sync.locate_read_craft()))

    def test_failed_fetch_leaves_file_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            script = fake_read_craft(directory, exit_code=22)
            target = Path(directory) / "AGENTS.md"
            target.write_text("# Keep\n")
            original = target.read_bytes()
            with self.assertRaises(subprocess.CalledProcessError):
                sync.sync(URL, target, read_craft_script=script)
            self.assertEqual(target.read_bytes(), original)

    def test_empty_import_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            script = fake_read_craft(directory, markdown="   ")
            target = Path(directory) / "AGENTS.md"
            with self.assertRaises(ValueError):
                sync.sync(URL, target, read_craft_script=script)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
