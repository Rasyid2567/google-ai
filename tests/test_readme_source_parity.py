"""Verify the Waydroid-focused fork README retains safety notices and structure."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReadmeSourceParityTests(unittest.TestCase):
    def test_readme_contains_waydroid_guide_and_safety_notices(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in (
            "[!CAUTION]",
            "[!NOTE]",
            "Waydroid",
            "waydroidsu",
            "sudo waydroid init -s GAPPS -f",
            "sh run-linux.sh --check",
            "sh run-linux.sh --list",
            "sh run-linux.sh",
            "2–5",
            "16.5.9",
            "3 × US$1 = US$3",
            "Verified in Google Play → Next",
        ):
            self.assertIn(required, readme)
        self.assertNotIn("tailscale", readme.lower())
        self.assertEqual(readme.count("```") % 2, 0)

    def test_credits_are_centralized(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for target in ("CONTRIBUTORS.md", "THIRD_PARTY_NOTICES.md", "DISCLAIMER.md", "SECURITY.md"):
            self.assertTrue((ROOT / target).is_file(), target)
            self.assertIn(f"({target})", readme)

    def test_screenshot_exists(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        images = re.findall(r"images/[A-Za-z0-9._-]+[.]png", readme)
        self.assertEqual(len(images), 1)
        self.assertTrue((ROOT / images[0]).is_file())


if __name__ == "__main__":
    unittest.main()
