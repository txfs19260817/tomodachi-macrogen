import json
import tempfile
import unittest
from pathlib import Path

from src.living_grid import load_living_grid_json


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
