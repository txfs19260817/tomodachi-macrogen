from tomodachi_gui import build_part_color_map, is_hex_color


def test_build_part_color_map_uses_color_split_part_hex_values() -> None:
    manifest = {
        "parts": [
            {"file": "color_01_FFFFFF.txt", "hex": "#ffffff"},
            {"file": "nested/color_02_000000.txt", "hex": "#000000"},
            {"file": "image_part1.txt"},
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
