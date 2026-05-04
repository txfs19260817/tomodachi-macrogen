import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.living_grid import load_living_grid_json
from src.path_planner import plan_color_pixels
from tomodachi_macrogen import (
    GenerationOptions,
    build_living_grid_colors,
    generate_color_split_macros,
    generate_macros,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "example.json"


class TestSplitByColor(unittest.TestCase):
    def test_split_by_color_writes_one_file_per_used_color(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = generate_macros(
                FIXTURE,
                GenerationOptions(
                    output_root=tmp,
                    timestamp="color_parts",
                    split_by_color=True,
                ),
            )
            out_dir = result.out_dir

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
            self.assertTrue((out_dir / "README_RUN.html").exists())
            self.assertTrue((out_dir / "README_RUN-en.html").exists())

    def test_each_color_macro_starts_with_hard_reset_but_does_not_return_at_end(self) -> None:
        grid = load_living_grid_json(FIXTURE)
        colors = build_living_grid_colors(grid, "original-palette")
        config = {
            "palette_slots": 9,
            "canvas_reset_right_steps": 2,
            "canvas_reset_down_steps": 1,
            "timing": {
                "canvas_reset_hold_frames": 3,
                "canvas_reset_settle_frames": 2,
                "movement_hold_frames": 1,
                "movement_release_frames": 1,
            },
        }

        writers = generate_color_split_macros(config, grid, colors)

        self.assertTrue(writers)
        for color, writer in writers:
            lines = [line.text for line in writer.lines]
            self.assertIn("{} (0 0 128 128) 3", lines)
            expected_path = plan_color_pixels(grid.indices, color.color_index, start=(0, 0))
            self.assertEqual(writer.canvas_position(), expected_path[-1])

    def test_game_palette_coordinates_select_84_color_tab_without_hsb_tab(self) -> None:
        payload = {
            "source": "living-the-grid.com",
            "version": 2,
            "width": 2,
            "height": 1,
            "brush": {"mode": "smooth", "px": 3},
            "canvas": {"preset": "square", "w": 6, "h": 3},
            "palette": [
                {
                    "hex": "#FFFFFF",
                    "rgb": [255, 255, 255],
                    "press": {"h": 201, "s": 0, "b": 110},
                    "game": {"row": 1, "col": 1},
                }
            ],
            "pixels": [[0, 0]],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "game.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            result = generate_macros(
                input_path,
                GenerationOptions(output_root=tmp, timestamp="out"),
            )
            out_dir = result.out_dir

            part = (out_dir / "image_part1.txt").read_text(encoding="utf-8")
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["canvas_cell_step"], 3)
            self.assertEqual(manifest["palette_source"], "game")
            self.assertNotIn("{R1}", part)
            self.assertIn("{L1}", part)
            self.assertNotIn("{L U}", part)
            self.assertIn("{D}", part)
            self.assertEqual(part.count("{A R}"), 3)

    def test_color_split_game_palette_files_share_palette_position(self) -> None:
        payload = {
            "source": "living-the-grid.com",
            "version": 2,
            "width": 2,
            "height": 1,
            "brush": {"mode": "smooth", "px": 1},
            "canvas": {"preset": "square", "w": 2, "h": 1},
            "palette": [
                {
                    "hex": "#FFFFFF",
                    "rgb": [255, 255, 255],
                    "press": {"h": 201, "s": 0, "b": 110},
                    "game": {"row": 1, "col": 1},
                },
                {
                    "hex": "#F0F0F8",
                    "rgb": [240, 240, 248],
                    "press": {"h": 120, "s": 5, "b": 100},
                    "game": {"row": 2, "col": 3},
                },
            ],
            "pixels": [[0, 1]],
        }
        config = {
            "canvas_reset_right_steps": 0,
            "canvas_reset_down_steps": 0,
            "timing": {
                "tap_hold_frames": 1,
                "tap_release_frames": 1,
                "menu_open_frames": 1,
                "screen_settle_frames": 1,
                "menu_close_frames": 1,
                "movement_hold_frames": 1,
                "movement_release_frames": 1,
                "canvas_reset_hold_frames": 1,
                "canvas_reset_settle_frames": 1,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "game.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            grid = load_living_grid_json(input_path)
            colors = build_living_grid_colors(grid, "original-palette")

            writers = generate_color_split_macros(config, grid, colors)

        first_lines = _lines_before_canvas_reset([line.text for line in writers[0][1].lines])
        second_lines = _lines_before_canvas_reset([line.text for line in writers[1][1].lines])
        self.assertNotIn("{L U} 1", first_lines + second_lines)
        self.assertEqual(first_lines.count("{D} 1"), 1)
        self.assertEqual(second_lines.count("{R} 1"), 2)
        self.assertEqual(second_lines.count("{D} 1"), 1)

    def test_known_game_palette_rgb_uses_game_palette_without_explicit_coordinates(self) -> None:
        payload = {
            "source": "living-the-grid.com",
            "version": 2,
            "width": 1,
            "height": 1,
            "brush": {"mode": "smooth", "px": 1},
            "canvas": {"preset": "square", "w": 1, "h": 1},
            "palette": [
                {
                    "hex": "#EBEBEB",
                    "rgb": [235, 235, 235],
                    "press": {"h": 0, "s": 0, "b": 91},
                }
            ],
            "pixels": [[0]],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "auto.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            result = generate_macros(
                input_path,
                GenerationOptions(output_root=tmp, timestamp="out"),
            )
            out_dir = result.out_dir

            part = (out_dir / "image_part1.txt").read_text(encoding="utf-8")
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["palette_source"], "game")
            self.assertNotIn("{R1}", part)
            self.assertIn("{L1}", part)
            self.assertNotIn("{L U}", part)
            self.assertIn("{D}", part)

    def test_unknown_palette_rgb_uses_full_color_picker(self) -> None:
        payload = {
            "source": "living-the-grid.com",
            "version": 2,
            "width": 1,
            "height": 1,
            "brush": {"mode": "smooth", "px": 1},
            "canvas": {"preset": "square", "w": 1, "h": 1},
            "palette": [
                {
                    "hex": "#123456",
                    "rgb": [18, 52, 86],
                    "press": {"h": 100, "s": 100, "b": 50},
                }
            ],
            "pixels": [[0]],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "auto.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            result = generate_macros(
                input_path,
                GenerationOptions(output_root=tmp, timestamp="out"),
            )
            out_dir = result.out_dir

            part = (out_dir / "image_part1.txt").read_text(encoding="utf-8")
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["palette_source"], "auto")
            self.assertIn("{R1}", part)


def _read_pixels(path: Path) -> bytes:
    with Image.open(path) as image:
        return image.convert("RGBA").tobytes()


def _lines_before_canvas_reset(lines: list[str]) -> list[str]:
    return lines[: lines.index("{} (0 0 128 128) 1")]


if __name__ == "__main__":
    unittest.main()
