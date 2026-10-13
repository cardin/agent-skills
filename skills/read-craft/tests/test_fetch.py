import importlib.util
import json
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch.py"
spec = importlib.util.spec_from_file_location("read_craft_fetch", SCRIPT)
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)
URL = "https://example.craft.me/abc123"


def block(text, **style):
    return {"content": text, "style": json.dumps(style)}


class ReadCraftTests(unittest.TestCase):
    def test_url(self):
        self.assertEqual(fetch.parse_url(URL + "/?tracking=1"), (URL, "abc123"))
        for url in ["http://example.craft.me/abc123", "https://evil.test/abc123", URL + "/extra", "https://user@example.craft.me/abc123"]:
            with self.assertRaises(ValueError):
                fetch.parse_url(url)

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
        self.assertEqual(fetch.render(document), "# Workflow\n\n## Steps\n\n2. **Plan:** use `docs/`\n\n- Rule")
        self.assertEqual(fetch.render({"blocks": [block("Mention IGNORE normally")]}), "Mention IGNORE normally")
        with self.assertRaises(ValueError):
            fetch.render({"blocks": [block("IGNORE", textStyle="title"), block("Excluded")]})

    def test_unicode_and_embedded_backticks(self):
        document = {"blocks": [block("😀 use fd and `x`", _runAttributes=[
            {"isCode": True, "range": [7, 2]}, {"isCode": True, "range": [14, 3]},
        ])]}
        self.assertEqual(fetch.render(document), "😀 use `fd` and `` `x` ``")

    def test_compact_bullet_list_and_paragraph_spacing(self):
        document = {"blocks": [
            block("Rules", textStyle="title"),
            block("Introduction"),
            block("First", listStyle="bullet"),
            block(""),
            block("Second", listStyle="bullet"),
            block("Conclusion"),
            block("Another paragraph"),
        ]}
        self.assertEqual(fetch.render(document), "# Rules\n\nIntroduction\n\n- First\n- Second\n\nConclusion\n\nAnother paragraph")

    def test_compact_numbered_list_and_list_transitions(self):
        document = {"blocks": [
            block("First", listStyle="numbered", userDefinedListNumber=1),
            block("Second", listStyle="numbered", userDefinedListNumber=2),
            block("Bullet", listStyle="bullet"),
            block("Another bullet", listStyle="bullet"),
            block("Next section", textStyle="subtitle"),
            block("New list", listStyle="numbered", userDefinedListNumber=1),
        ]}
        self.assertEqual(fetch.render(document), "1. First\n2. Second\n\n- Bullet\n- Another bullet\n\n## Next section\n\n1. New list")

    def test_empty_document_is_an_error(self):
        for document in ({"blocks": []}, {"blocks": [block("   ")]}):
            with self.assertRaises(ValueError):
                fetch.render(document)


if __name__ == "__main__":
    unittest.main()
