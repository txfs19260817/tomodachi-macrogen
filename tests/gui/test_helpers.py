from pathlib import Path

from tomodachi_gui import (
    build_macro_file_infos,
    build_part_color_map,
    is_hex_color,
    is_macro_file_skip_allowed,
)


def test_build_part_color_map_uses_color_split_part_hex_values() -> None:
    manifest = {
        "parts": [
            {"file": "color_01_FFFFFF.txt", "hex": "#ffffff"},
            {"file": "nested/color_02_000000.txt", "hex": "#000000"},
            {"file": "manifest.json"},
            {"file": "bad.txt", "hex": "not-a-color"},
        ]
    }

    assert build_part_color_map(manifest) == {
        "color_01_FFFFFF.txt": "#FFFFFF",
        "color_02_000000.txt": "#000000",
    }


def test_is_hex_color_requires_rrggbb_hash_format() -> None:
    assert is_hex_color("#A1b2C3")
    assert not is_hex_color("A1b2C3")
    assert not is_hex_color("#12345")
    assert not is_hex_color("#12345Z")


def test_build_macro_file_infos_joins_manifest_part_metadata() -> None:
    paths = [
        Path("out/color_01_FFFFFF.txt"),
        Path("out/color_02_000000.txt"),
        Path("out/manifest.json"),
    ]
    manifest = {
        "parts": [
            {
                "file": "color_01_FFFFFF.txt",
                "hex": "#ffffff",
                "palette_source": "hsb",
                "pixel_count": 30,
                "line_count": 12,
                "frame_count": 300,
                "path_strategy": "tsp",
            },
            {
                "file": "color_02_000000.txt",
                "hex": "#000000",
                "palette_source": "game",
                "pixel_count": "20",
                "line_count": "8",
                "frame_count": "200",
                "path_strategy": "snake",
            },
        ]
    }

    infos = build_macro_file_infos(paths, manifest)

    assert infos[0].color_hex == "#FFFFFF"
    assert infos[0].palette_source == "hsb"
    assert infos[0].pixel_count == 30
    assert infos[0].line_count == 12
    assert infos[0].path_strategy == "tsp"
    assert infos[1].color_hex == "#000000"
    assert infos[1].palette_source == "game"
    assert infos[1].pixel_count == 20
    assert infos[1].frame_count == 200
    assert infos[1].path_strategy == "snake"
    assert infos[2].color_hex is None
    assert infos[2].pixel_count is None
    assert infos[2].path_strategy is None


def test_macro_file_skip_is_allowed_only_for_non_84_color_output() -> None:
    assert is_macro_file_skip_allowed({"split_strategy": "color", "palette_source": "auto"})
    assert not is_macro_file_skip_allowed({"split_strategy": "color", "palette_source": "game"})
