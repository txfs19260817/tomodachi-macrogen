import unittest
from pathlib import Path

from tomodachi_macrogen import OUTPUT_ROOT, resolve_output_dir


class TestOutputDir(unittest.TestCase):
    def test_default_uses_input_filename_stem(self) -> None:
        self.assertEqual(
            resolve_output_dir(None, Path("downloads/example.json")),
            OUTPUT_ROOT / "example",
        )

    def test_default_without_input_uses_calibration(self) -> None:
        self.assertEqual(resolve_output_dir(None), OUTPUT_ROOT / "calibration")

    def test_relative_out_stays_under_output_root(self) -> None:
        self.assertEqual(
            resolve_output_dir("custom", Path("example.json")),
            OUTPUT_ROOT / "custom",
        )


if __name__ == "__main__":
    unittest.main()
