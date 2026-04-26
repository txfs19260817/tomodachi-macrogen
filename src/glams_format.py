from collections.abc import Iterable, Sequence
from dataclasses import dataclass

VALID_BUTTONS = {
    "A",
    "B",
    "X",
    "Y",
    "U",
    "D",
    "L",
    "R",
    "L1",
    "R1",
    "L2",
    "R2",
    "PLUS",
    "MINUS",
    "HOME",
    "CAPTURE",
}


BUTTON_ALIASES = {
    "UP": "U",
    "DOWN": "D",
    "LEFT": "L",
    "RIGHT": "R",
    "ZL": "L2",
    "ZR": "R2",
    "LB": "L1",
    "RB": "R1",
}


@dataclass(frozen=True)
class MacroLine:
    text: str
    frames: int
    safe_split_after: bool = False


def normalize_button(button: str) -> str:
    normalized = button.strip().upper()
    normalized = BUTTON_ALIASES.get(normalized, normalized)
    if normalized not in VALID_BUTTONS:
        raise ValueError(f"Unsupported GLaMS/SwiCC button: {button!r}")
    return normalized


def normalize_buttons(buttons: str | Iterable[str] | None) -> tuple[str, ...]:
    if buttons is None:
        return ()
    if isinstance(buttons, str):
        return (normalize_button(buttons),)
    normalized = tuple(normalize_button(button) for button in buttons)
    return tuple(dict.fromkeys(normalized))


def format_buttons(buttons: str | Iterable[str] | None) -> str:
    normalized = normalize_buttons(buttons)
    if not normalized:
        return "{}"
    return "{" + " ".join(normalized) + "}"


def format_controller_state(
    buttons: str | Iterable[str] | None,
    frames: int,
    *,
    safe_split_after: bool = False,
) -> MacroLine:
    if frames <= 0:
        raise ValueError("frames must be greater than zero")
    return MacroLine(f"{format_buttons(buttons)} {frames}", frames, safe_split_after)


def format_stick(
    lx: int,
    ly: int,
    rx: int,
    ry: int,
    frames: int,
    *,
    buttons: Sequence[str] | None = None,
    safe_split_after: bool = False,
) -> MacroLine:
    if frames <= 0:
        raise ValueError("frames must be greater than zero")
    values = (lx, ly, rx, ry)
    if any(value < 0 or value > 255 for value in values):
        raise ValueError("stick values must be in the range 0..255")
    return MacroLine(
        f"{format_buttons(buttons)} ({lx} {ly} {rx} {ry}) {frames}",
        frames,
        safe_split_after,
    )
