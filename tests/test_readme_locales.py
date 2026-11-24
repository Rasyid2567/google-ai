"""Verify Waydroid fork README and Linux guide billing/safety coverage."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReadmeLocalesTests(unittest.TestCase):
    def test_readme_links_safety_and_linux_guidance(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for item in (
            "[!CAUTION]",
            "[!NOTE]",
            "2–5",
            "Google Play",
            "sh run-linux.sh",
            "(docs/LINUX.md)",
            "(DISCLAIMER.md)",
            "(SECURITY.md)",
            "(CONTRIBUTORS.md)",
            "(THIRD_PARTY_NOTICES.md)",
        ):
            self.assertIn(item, text)

    def test_linux_guide_has_no_device_specific_tailscale_instructions(self):
        for path in (ROOT / "README.md", ROOT / "docs/LINUX.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("tailscale", text.lower())


if __name__ == "__main__":
    unittest.main()
