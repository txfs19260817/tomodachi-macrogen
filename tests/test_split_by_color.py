import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.living_grid import load_living_grid_json
from tomodachi_macrogen import build_living_grid_colors, generate_color_split_macros, main

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "example.json"


class TestSplitByColor(unittest.TestCase):
    def test_split_by_color_writes_one_file_per_used_color(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "color_parts"
            argv = [
                "tomodachi_macrogen.py",
                str(FIXTURE),
                "--out",
                str(out_dir),
                "--split-by-color",
            ]
            with patch("sys.argv", argv):
                self.assertEqual(main(), 0)

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["split_strategy"], "color")
            self.assertEqual(len(manifest["parts"]), manifest["palette_color_count"])
            self.assertTrue(all(part["assigned_slot"] == 0 for part in manifest["parts"]))
            self.assertFalse(list(out_dir.glob("image_part*.txt")))
            self.assertEqual(
                len(list(out_dir.glob("color_*.txt"))),
                manifest["palette_color_count"],
            )
            self.assertEqual(
                _read_pixels(out_dir / "reconstructed_from_macro.png"),
                _read_pixels(out_dir / "preview_quantized.png"),
            )

    def test_each_color_macro_returns_to_top_left(self) -> None:
        grid = load_living_grid_json(FIXTURE)
        colors = build_living_grid_colors(grid, "original-palette")
        config = {"palette_slots": 9}

        writers = generate_color_split_macros(config, grid, colors)

        self.assertTrue(writers)
        for _color, writer in writers:
            self.assertEqual(writer.canvas_position(), (0, 0))


def _read_pixels(path: Path) -> bytes:
    with Image.open(path) as image:
        return image.convert("RGBA").tobytes()


if __name__ == "__main__":
    unittest.main()
