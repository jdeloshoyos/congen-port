"""Headless tests for the version declaration."""

from __future__ import annotations

import importlib.metadata
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import congen2  # noqa: E402

SEMVER = re.compile(
    r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


class VersionTests(unittest.TestCase):
    def test_version_is_semver(self):
        self.assertRegex(congen2.__version__, SEMVER)

    def test_installed_metadata_matches(self):
        try:
            installed = importlib.metadata.version("congen2")
        except importlib.metadata.PackageNotFoundError:
            self.skipTest("congen2 is not installed")
        self.assertEqual(installed, congen2.__version__)


if __name__ == "__main__":
    unittest.main()
