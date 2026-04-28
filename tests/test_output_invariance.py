import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tomodachi_macrogen import main

COLOR_ORDERS = ("frequency", "original-palette", "luminance", "hue")
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "example.json"


class TestOutputInvariance(unittest.TestCase):
    def test_color_order_keeps_preview_pixel_matrix_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            baseline: bytes | None = None

            for color_order in COLOR_ORDERS:
                with self.subTest(color_order=color_order):
                    out_dir = Path(tmp) / color_order
                    argv = [
                        "tomodachi_macrogen.py",
                        str(FIXTURE),
                        "--out",
                        str(out_dir),
                        "--color-order",
                        color_order,
                    ]
                    with patch("sys.argv", argv):
                        self.assertEqual(main(), 0)

                    self.assertTrue((out_dir / "README_RUN.md").exists())
                    self.assertTrue((out_dir / "README_RUN-en.md").exists())
                    pixels = _read_preview_pixels(out_dir / "preview_quantized.png")
                    if baseline is None:
                        baseline = pixels
                    self.assertEqual(pixels, baseline)


def _read_preview_pixels(path: Path) -> bytes:
    with Image.open(path) as image:
        return image.convert("RGBA").tobytes()


if __name__ == "__main__":
    unittest.main()
