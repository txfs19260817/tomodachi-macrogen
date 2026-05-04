from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class TimingConfig:
    tap_hold_frames: int = 2
    tap_release_frames: int = 1
    draw_hold_frames: int = 2
    draw_release_frames: int = 1
    movement_hold_frames: int = 1
    movement_release_frames: int = 1
    movement_chunk_size: int = 0
    movement_chunk_settle_frames: int = 0
    canvas_reset_hold_frames: int = 180
    canvas_reset_settle_frames: int = 25
    menu_open_frames: int = 8
    menu_close_frames: int = 8
    screen_settle_frames: int = 4
    slot_anchor_hold_frames: int = 18
    slot_anchor_release_frames: int = 2
    slot_step_hold_frames: int = 2
    slot_step_release_frames: int = 1
    slot_settle_frames: int = 2
    game_palette_anchor_hold_frames: int | None = None
    game_palette_anchor_settle_frames: int | None = None
    hue_anchor_hold_frames: int = 30
    hue_anchor_release_frames: int = 2
    hue_step_hold_frames: int = 2
    hue_step_release_frames: int = 1
    colour_rect_anchor_hold_frames: int = 45
    colour_rect_anchor_settle_frames: int = 4
    colour_rect_step_hold_frames: int = 1
    colour_rect_step_release_frames: int = 1

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> TimingConfig:
        data = data or {}
        defaults = cls()
        return cls(
            tap_hold_frames=_as_int(data, "tap_hold_frames", defaults.tap_hold_frames),
            tap_release_frames=_as_int(
                data,
                "tap_release_frames",
                defaults.tap_release_frames,
            ),
            draw_hold_frames=_as_int(
                data,
                "draw_hold_frames",
                _as_int(data, "tap_hold_frames", defaults.tap_hold_frames),
            ),
            draw_release_frames=_as_int(
                data,
                "draw_release_frames",
                _as_int(data, "tap_release_frames", defaults.tap_release_frames),
            ),
            movement_hold_frames=_as_int(
                data,
                "movement_hold_frames",
                defaults.movement_hold_frames,
            ),
            movement_release_frames=_as_int(
                data,
                "movement_release_frames",
                defaults.movement_release_frames,
            ),
            movement_chunk_size=_as_int(
                data,
                "movement_chunk_size",
                defaults.movement_chunk_size,
            ),
            movement_chunk_settle_frames=_as_int(
                data,
                "movement_chunk_settle_frames",
                defaults.movement_chunk_settle_frames,
            ),
            canvas_reset_hold_frames=_as_int(
                data,
                "canvas_reset_hold_frames",
                defaults.canvas_reset_hold_frames,
            ),
            canvas_reset_settle_frames=_as_int(
                data,
                "canvas_reset_settle_frames",
                defaults.canvas_reset_settle_frames,
            ),
            menu_open_frames=_as_int(data, "menu_open_frames", defaults.menu_open_frames),
            menu_close_frames=_as_int(
                data,
                "menu_close_frames",
                defaults.menu_close_frames,
            ),
            screen_settle_frames=_as_int(
                data,
                "screen_settle_frames",
                defaults.screen_settle_frames,
            ),
            slot_anchor_hold_frames=_as_int(
                data,
                "slot_anchor_hold_frames",
                defaults.slot_anchor_hold_frames,
            ),
            slot_anchor_release_frames=_as_int(
                data,
                "slot_anchor_release_frames",
                defaults.slot_anchor_release_frames,
            ),
            slot_step_hold_frames=_as_int(
                data,
                "slot_step_hold_frames",
                defaults.slot_step_hold_frames,
            ),
            slot_step_release_frames=_as_int(
                data,
                "slot_step_release_frames",
                defaults.slot_step_release_frames,
            ),
            slot_settle_frames=_as_int(
                data,
                "slot_settle_frames",
                defaults.slot_settle_frames,
            ),
            game_palette_anchor_hold_frames=_as_optional_int(
                data,
                "game_palette_anchor_hold_frames",
                defaults.game_palette_anchor_hold_frames,
            ),
            game_palette_anchor_settle_frames=_as_optional_int(
                data,
                "game_palette_anchor_settle_frames",
                defaults.game_palette_anchor_settle_frames,
            ),
            hue_anchor_hold_frames=_as_int(
                data,
                "hue_anchor_hold_frames",
                defaults.hue_anchor_hold_frames,
            ),
            hue_anchor_release_frames=_as_int(
                data,
                "hue_anchor_release_frames",
                defaults.hue_anchor_release_frames,
            ),
            hue_step_hold_frames=_as_int(
                data,
                "hue_step_hold_frames",
                defaults.hue_step_hold_frames,
            ),
            hue_step_release_frames=_as_int(
                data,
                "hue_step_release_frames",
                defaults.hue_step_release_frames,
            ),
            colour_rect_anchor_hold_frames=_as_int(
                data,
                "colour_rect_anchor_hold_frames",
                defaults.colour_rect_anchor_hold_frames,
            ),
            colour_rect_anchor_settle_frames=_as_int(
                data,
                "colour_rect_anchor_settle_frames",
                defaults.colour_rect_anchor_settle_frames,
            ),
            colour_rect_step_hold_frames=_as_int(
                data,
                "colour_rect_step_hold_frames",
                defaults.colour_rect_step_hold_frames,
            ),
            colour_rect_step_release_frames=_as_int(
                data,
                "colour_rect_step_release_frames",
                defaults.colour_rect_step_release_frames,
            ),
        )

    @property
    def game_palette_hold_frames(self) -> int:
        if self.game_palette_anchor_hold_frames is not None:
            return self.game_palette_anchor_hold_frames
        return self.slot_anchor_hold_frames

    @property
    def game_palette_settle_frames(self) -> int:
        if self.game_palette_anchor_settle_frames is not None:
            return self.game_palette_anchor_settle_frames
        return self.slot_anchor_release_frames


@dataclass(frozen=True)
class StickConfig:
    min: int = 0
    neutral: int = 128
    max: int = 255

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> StickConfig:
        data = data or {}
        defaults = cls()
        return cls(
            min=_as_int(data, "min", defaults.min),
            neutral=_as_int(data, "neutral", defaults.neutral),
            max=_as_int(data, "max", defaults.max),
        )


@dataclass(frozen=True)
class AppConfig:
    canvas_origin_x: int = 0
    canvas_origin_y: int = 0
    canvas_cell_step: int | None = None
    color_order: str = "original-palette"
    palette_slots: int = 9
    game_palette_rows: int = 7
    game_palette_cols: int = 11
    game_palette_extras: int = 7
    hue_slider_steps: int = 202
    colour_rect_width: int = 212
    colour_rect_height: int = 111
    anchor_colour_rect_method: str = "analog"
    canvas_reset_right_steps: int = 192
    canvas_reset_down_steps: int = 77
    split_lines: int | None = 50000
    timing: TimingConfig = field(default_factory=TimingConfig)
    stick: StickConfig = field(default_factory=StickConfig)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> AppConfig:
        data = data or {}
        defaults = cls()
        return cls(
            canvas_origin_x=_as_int(data, "canvas_origin_x", defaults.canvas_origin_x),
            canvas_origin_y=_as_int(data, "canvas_origin_y", defaults.canvas_origin_y),
            canvas_cell_step=_as_optional_int(
                data,
                "canvas_cell_step",
                defaults.canvas_cell_step,
            ),
            color_order=str(data.get("color_order", defaults.color_order)),
            palette_slots=_as_int(data, "palette_slots", defaults.palette_slots),
            game_palette_rows=_as_int(
                data,
                "game_palette_rows",
                defaults.game_palette_rows,
            ),
            game_palette_cols=_as_int(
                data,
                "game_palette_cols",
                defaults.game_palette_cols,
            ),
            game_palette_extras=_as_int(
                data,
                "game_palette_extras",
                defaults.game_palette_extras,
            ),
            hue_slider_steps=_as_int(
                data,
                "hue_slider_steps",
                defaults.hue_slider_steps,
            ),
            colour_rect_width=_as_int(
                data,
                "colour_rect_width",
                defaults.colour_rect_width,
            ),
            colour_rect_height=_as_int(
                data,
                "colour_rect_height",
                defaults.colour_rect_height,
            ),
            anchor_colour_rect_method=str(
                data.get(
                    "anchor_colour_rect_method",
                    defaults.anchor_colour_rect_method,
                )
            ),
            canvas_reset_right_steps=_as_int(
                data,
                "canvas_reset_right_steps",
                defaults.canvas_reset_right_steps,
            ),
            canvas_reset_down_steps=_as_int(
                data,
                "canvas_reset_down_steps",
                defaults.canvas_reset_down_steps,
            ),
            split_lines=_as_optional_int(data, "split_lines", defaults.split_lines),
            timing=TimingConfig.from_mapping(_as_mapping(data.get("timing"))),
            stick=StickConfig.from_mapping(_as_mapping(data.get("stick"))),
        )

    @property
    def effective_canvas_cell_step(self) -> int:
        return self.canvas_cell_step if self.canvas_cell_step is not None else 1

    def with_canvas_cell_step(self, value: int) -> AppConfig:
        return replace(self, canvas_cell_step=int(value))

    def with_overrides(
        self,
        *,
        palette_slots: int | None = None,
        color_order: str | None = None,
        split_lines: int | None = None,
    ) -> AppConfig:
        updates: dict[str, Any] = {}
        if palette_slots is not None:
            updates["palette_slots"] = palette_slots
        if color_order is not None:
            updates["color_order"] = color_order
        if split_lines is not None:
            updates["split_lines"] = split_lines
        return replace(self, **updates) if updates else self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ConfigInput = AppConfig | Mapping[str, Any] | None


def as_app_config(config: ConfigInput) -> AppConfig:
    if isinstance(config, AppConfig):
        return config
    return AppConfig.from_mapping(config)


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = deepcopy(dict(base))
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _as_int(data: Mapping[str, Any], key: str, default: int) -> int:
    return int(data.get(key, default))


def _as_optional_int(
    data: Mapping[str, Any],
    key: str,
    default: int | None,
) -> int | None:
    value = data.get(key, default)
    return None if value is None else int(value)


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None
