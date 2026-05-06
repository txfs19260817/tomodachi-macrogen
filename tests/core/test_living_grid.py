import json
import tempfile
import unittest
from pathlib import Path

from src.core.living_grid import infer_canvas_start_offset, load_living_grid_json

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class TestLivingGrid(unittest.TestCase):
    def test_loads_living_grid_json(self) -> None:
        path = _write_fixture()

        grid = load_living_grid_json(path)

        self.assertEqual(grid.source, "living-the-grid.com")
        self.assertEqual((grid.width, grid.height), (2, 2))
        self.assertEqual(len(grid.palette), 2)
        self.assertEqual(grid.palette[0].press.h, 201)
        self.assertEqual(grid.palette[1].pixel_count, 2)
        self.assertEqual(grid.preview.size, (2, 2))

    def test_rejects_bad_source(self) -> None:
        path = _write_fixture({"source": "example.com"})

        with self.assertRaisesRegex(ValueError, "source"):
            load_living_grid_json(path)

    def test_rejects_out_of_range_pixel(self) -> None:
        path = _write_fixture({"pixels": [[0, 2], [1, 0]]})

        with self.assertRaisesRegex(ValueError, "outside palette range"):
            load_living_grid_json(path)

    def test_allows_transparent_null_pixels(self) -> None:
        path = _write_fixture({"pixels": [[0, None], [1, 0]]})

        grid = load_living_grid_json(path)

        self.assertEqual(grid.indices[0][1], None)
        self.assertEqual(grid.palette[0].pixel_count, 2)
        self.assertEqual(grid.palette[1].pixel_count, 1)
        self.assertEqual(grid.preview.getpixel((1, 0)), (0, 0, 0, 0))

    def test_reads_brush_px_and_optional_game_palette_target(self) -> None:
        path = _write_fixture(
            {
                "brush": {"mode": "smooth", "px": 3},
                "palette": [
                    {
                        "hex": "#FFFFFF",
                        "rgb": [255, 255, 255],
                        "press": {"h": 201, "s": 0, "b": 110},
                        "game": {"row": 1, "col": 1},
                    },
                    {
                        "hex": "#000000",
                        "rgb": [0, 0, 0],
                        "press": {"h": 201, "s": 0, "b": 0},
                        "label": "Extra 2",
                    },
                ],
            }
        )

        grid = load_living_grid_json(path)

        self.assertEqual(grid.brush_px, 3)
        self.assertEqual(grid.palette[0].game.row, 1)
        self.assertEqual(grid.palette[0].game.col, 1)
        self.assertEqual(grid.palette[1].game.kind, "extra")
        self.assertEqual(grid.palette[1].game.row, 2)

    def test_infers_game_palette_target_from_known_rgb(self) -> None:
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "example_game.json"

        grid = load_living_grid_json(fixture)

        self.assertTrue(all(entry.game is not None for entry in grid.palette))
        self.assertEqual((grid.palette[0].game.kind, grid.palette[0].game.row), ("grid", 2))
        self.assertEqual(grid.palette[0].game.col, 1)
        self.assertEqual((grid.palette[-1].game.kind, grid.palette[-1].game.row), ("extra", 7))

    def test_infers_centered_canvas_start_offsets(self) -> None:
        self.assertEqual(
            infer_canvas_start_offset({"preset": "bookcover", "w": 180, "h": 256}, 180, 256),
            (38, 0),
        )
        self.assertEqual(
            infer_canvas_start_offset({"preset": "tvscreen", "w": 256, "h": 131}, 256, 131),
            (0, 62),
        )
        self.assertEqual(
            infer_canvas_start_offset({"preset": "videogame", "w": 256, "h": 144}, 256, 144),
            (0, 56),
        )
        self.assertEqual(
            infer_canvas_start_offset({"preset": "floor", "w": 172, "h": 256}, 172, 256),
            (42, 0),
        )
        self.assertEqual(
            infer_canvas_start_offset({"preset": "square", "w": 6, "h": 3}, 2, 2),
            (0, 0),
        )

    def test_reads_centered_canvas_offsets_from_fixtures(self) -> None:
        cases = [
            ("example_bookcover.json", (180, 256), "book", (38, 0)),
            ("example_videogame.json", (256, 144), "videogame", (0, 56)),
        ]
        for filename, size, preset, offset in cases:
            with self.subTest(filename=filename):
                grid = load_living_grid_json(FIXTURES / filename)

                self.assertEqual((grid.width, grid.height), size)
                self.assertEqual(grid.canvas.get("preset"), preset)
                self.assertEqual(grid.canvas_start_offset, offset)


def _write_fixture(overrides: dict[str, object] | None = None) -> Path:
    data = {
        "source": "living-the-grid.com",
        "version": 2,
        "width": 2,
        "height": 2,
        "brush": {"mode": "smooth", "px": 1},
        "canvas": {"preset": "square", "w": 2, "h": 2},
        "palette": [
            {
                "hex": "#FFFFFF",
                "rgb": [255, 255, 255],
                "press": {"h": 201, "s": 0, "b": 110},
            },
            {
                "hex": "#000000",
                "rgb": [0, 0, 0],
                "press": {"h": 201, "s": 0, "b": 0},
            },
        ],
        "pixels": [[0, 1], [1, 0]],
    }
    if overrides:
        data.update(overrides)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as file:
        json.dump(data, file)
        return Path(file.name)


if __name__ == "__main__":
    unittest.main()
