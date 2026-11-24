"""Validate local Markdown links and Linux/Waydroid fork documentation."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MD_LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")


class DocumentationNavigationTests(unittest.TestCase):
    def test_waydroid_readme_links_point_to_existing_files(self):
        locations = [ROOT / "README.md", DOCS / "LINUX.md", ROOT / "CONTRIBUTORS.md", ROOT / "AGENTS.md"]
        for source in locations:
            text = source.read_text(encoding="utf-8")
            for target in MD_LINK.findall(text):
                if target.startswith(("https://", "http://", "mailto:", "#")):
                    continue
                relative = target.partition("#")[0]
                if not relative:
                    continue
                with self.subTest(source=str(source.relative_to(ROOT)), link=relative):
                    self.assertTrue((source.parent / relative).is_file())

    def test_linux_guide_documents_adb_path_and_waydroid(self):
        linux = (DOCS / "LINUX.md").read_text(encoding="utf-8")
        self.assertIn("ADB_PATH", linux)
        self.assertIn("Waydroid", linux)
        self.assertIn("sh run-linux.sh", linux)


if __name__ == "__main__":
    unittest.main()
