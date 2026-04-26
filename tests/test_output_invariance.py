import itertools
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tomodachi_macrogen import main

COLOR_ORDERS = ("frequency", "original-palette", "luminance", "hue")
PATH_MODES = ("safe-pixel", "nearest", "horizontal-runs")
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "example.json"


class TestOutputInvariance(unittest.TestCase):
    def test_color_order_and_mode_keep_pixel_matrix_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            baseline: bytes | None = None

            for color_order, mode in itertools.product(COLOR_ORDERS, PATH_MODES):
                with self.subTest(color_order=color_order, mode=mode):
                    out_dir = Path(tmp) / f"{color_order}_{mode}"
                    argv = [
                        "tomodachi_macrogen.py",
                        str(FIXTURE),
                        "--out",
                        str(out_dir),
                        "--preview-only",
                        "--color-order",
                        color_order,
                        "--mode",
                        mode,
                    ]
                    with patch("sys.argv", argv):
                        self.assertEqual(main(), 0)

                    pixels = _read_preview_pixels(out_dir / "preview_quantized.png")
                    if baseline is None:
                        baseline = pixels
                    self.assertEqual(pixels, baseline)


def _read_preview_pixels(path: Path) -> bytes:
    with Image.open(path) as image:
        return image.convert("RGBA").tobytes()


if __name__ == "__main__":
    unittest.main()
