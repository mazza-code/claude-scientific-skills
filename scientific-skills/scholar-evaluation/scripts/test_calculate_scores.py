#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path


def _load_module():
    module_path = Path(__file__).with_name("calculate_scores.py")
    spec = importlib.util.spec_from_file_location("calculate_scores", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CalculateScoresTests(unittest.TestCase):
    def test_partial_dimension_weighted_average_not_inflated(self):
        mod = _load_module()
        scores = {"methodology": 4.0}
        result = mod.calculate_weighted_average(scores, mod.DEFAULT_WEIGHTS)
        self.assertAlmostEqual(result, 4.0, places=6)

    def test_uniform_scores_stay_uniform(self):
        mod = _load_module()
        scores = {k: 3.0 for k in mod.DEFAULT_WEIGHTS.keys()}
        result = mod.calculate_weighted_average(scores, mod.DEFAULT_WEIGHTS)
        self.assertAlmostEqual(result, 3.0, places=6)


if __name__ == "__main__":
    unittest.main()

