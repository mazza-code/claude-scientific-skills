#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module():
    module_path = Path(__file__).with_name("generate_schematic_ai.py")
    module_dir = str(module_path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
    spec = importlib.util.spec_from_file_location("generate_schematic_ai", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SchematicReviewTests(unittest.TestCase):
    def test_review_image_no_choices_returns_three_values(self):
        mod = _load_module()
        cls = mod.ScientificSchematicGenerator
        obj = cls.__new__(cls)
        obj.verbose = False
        obj.QUALITY_THRESHOLDS = cls.QUALITY_THRESHOLDS
        obj.review_model = "dummy-review-model"
        obj._image_to_base64 = lambda _path: "data:image/png;base64,ZmFrZQ=="
        obj._make_request = lambda **_kwargs: {"choices": []}
        obj._log = lambda _msg: None

        result = cls.review_image(
            obj,
            image_path="dummy.png",
            original_prompt="dummy prompt",
            iteration=1,
            doc_type="default",
            max_iterations=2,
        )

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "Image generated successfully")
        self.assertEqual(result[1], 8.0)
        self.assertFalse(result[2])


if __name__ == "__main__":
    unittest.main()
