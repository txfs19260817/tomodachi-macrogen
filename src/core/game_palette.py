type GamePaletteTargetData = tuple[str, int, int | None]

GAME_PALETTE_GRID: tuple[tuple[str, ...], ...] = (
    (
        "#FFFFFF",
        "#F1EFF8",
        "#F0F0F8",
        "#F0F7FF",
        "#F0FBF4",
        "#F0F4EE",
        "#F5FAF0",
        "#FDFDEE",
        "#FEF3EF",
        "#FAF0F0",
        "#FDEDDC",
    ),
    (
        "#EBEBEB",
        "#CFC8E9",
        "#C7CDE7",
        "#C8E9FD",
        "#C8F1D7",
        "#C7DBC8",
        "#DAEEC8",
        "#FBF9C8",
        "#FCD6C9",
        "#EFC9C8",
        "#E4CFB0",
    ),
    (
        "#D5D5D3",
        "#A592D7",
        "#919FD5",
        "#92D6FD",
        "#92E6BA",
        "#92BD94",
        "#BBE294",
        "#FAF592",
        "#FBB491",
        "#E29691",
        "#CAA976",
    ),
    (
        "#BCBCBC",
        "#6527C2",
        "#004AC0",
        "#06C2FE",
        "#00DA90",
        "#019616",
        "#92D314",
        "#F9F000",
        "#F78400",
        "#D42700",
        "#91610D",
    ),
    (
        "#9C9D9A",
        "#5620AA",
        "#003FA4",
        "#02A5D8",
        "#03BC7B",
        "#03800E",
        "#7DB50C",
        "#D6CE00",
        "#D57100",
        "#B62100",
        "#774200",
    ),
    (
        "#727272",
        "#421785",
        "#003281",
        "#0084AB",
        "#009360",
        "#00650C",
        "#628E0D",
        "#A9A200",
        "#A85801",
        "#901600",
        "#5D380C",
    ),
    (
        "#000000",
        "#22094C",
        "#001648",
        "#014963",
        "#025435",
        "#013800",
        "#355100",
        "#605D00",
        "#602E01",
        "#510C00",
        "#34220D",
    ),
)

GAME_PALETTE_EXTRAS: tuple[str, ...] = (
    "#FE2500",
    "#FFFB00",
    "#07F900",
    "#02FDFF",
    "#0432FE",
    "#8836FF",
    "#FF36C3",
)


def find_game_palette_target(
    hex_value: str,
    rgb: tuple[int, int, int],
) -> GamePaletteTargetData | None:
    target = GAME_PALETTE_BY_HEX.get(_normalize_hex(hex_value))
    if target is not None:
        return target
    return GAME_PALETTE_BY_RGB.get(rgb)


def _normalize_hex(value: str) -> str:
    raw = value.strip().upper()
    if not raw:
        return ""
    if not raw.startswith("#"):
        raw = f"#{raw}"
    return raw


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    hex_value = _normalize_hex(value)
    return (
        int(hex_value[1:3], 16),
        int(hex_value[3:5], 16),
        int(hex_value[5:7], 16),
    )


def _build_hex_lookup() -> dict[str, GamePaletteTargetData]:
    lookup: dict[str, GamePaletteTargetData] = {}
    for row_index, row in enumerate(GAME_PALETTE_GRID, start=1):
        for col_index, hex_value in enumerate(row, start=1):
            lookup[_normalize_hex(hex_value)] = ("grid", row_index, col_index)
    for extra_index, hex_value in enumerate(GAME_PALETTE_EXTRAS, start=1):
        lookup[_normalize_hex(hex_value)] = ("extra", extra_index, None)
    return lookup


GAME_PALETTE_BY_HEX = _build_hex_lookup()
GAME_PALETTE_BY_RGB = {
    _hex_to_rgb(hex_value): target
    for hex_value, target in GAME_PALETTE_BY_HEX.items()
}
