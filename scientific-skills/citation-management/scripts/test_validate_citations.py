#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path


def _load_module():
    module_path = Path(__file__).with_name("validate_citations.py")
    spec = importlib.util.spec_from_file_location("validate_citations", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ValidateCitationsTests(unittest.TestCase):
    def test_valid_entries_counts_unique_high_error_entries(self):
        mod = _load_module()
        validator = mod.CitationValidator()

        validator.parse_bibtex_file = lambda _path: [
            {"type": "article", "key": "entry1", "fields": {"title": "T"}}
        ]

        def _fake_validate_entry(_entry):
            return (
                [
                    {"type": "e1", "severity": "high", "message": "x"},
                    {"type": "e2", "severity": "high", "message": "y"},
                ],
                [],
            )

        validator.validate_entry = _fake_validate_entry
        validator.detect_duplicates = lambda _entries: []

        report = validator.validate_file("dummy.bib", check_dois=False)
        self.assertEqual(report["total_entries"], 1)
        self.assertEqual(report["valid_entries"], 0)


if __name__ == "__main__":
    unittest.main()

