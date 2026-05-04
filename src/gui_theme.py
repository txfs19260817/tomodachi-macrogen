from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeStyle:
    stylesheet: str
    link_color: str


def build_theme_style(theme: str) -> ThemeStyle:
    colors = _DARK_COLORS if theme.casefold() == "dark" else _LIGHT_COLORS
    return ThemeStyle(
        link_color=colors["primary"],
        stylesheet=f"""
        QMainWindow {{ background: {colors["window"]}; }}
        QWidget {{ color: {colors["text"]}; }}
        QMenuBar {{
            background: {colors["card"]};
            color: {colors["text"]};
            border-bottom: 1px solid {colors["card_border"]};
        }}
        QMenuBar::item {{
            background: transparent;
            color: {colors["text"]};
            padding: 5px 10px;
        }}
        QMenuBar::item:selected {{
            background: {colors["button_hover"]};
            color: {colors["text"]};
        }}
        QMenu {{
            background: {colors["card"]};
            color: {colors["text"]};
            border: 1px solid {colors["card_border"]};
            padding: 4px;
        }}
        QMenu::item {{
            color: {colors["text"]};
            padding: 6px 28px 6px 22px;
            background: transparent;
        }}
        QMenu::item:selected {{
            background: {colors["primary"]};
            color: {colors["primary_text"]};
        }}
        QMenu::indicator {{
            width: 14px;
            height: 14px;
        }}
        QFrame#PreviewCard, QFrame#ControlCard {{
            background: {colors["card"]};
            border: 1px solid {colors["card_border"]};
            border-radius: 18px;
        }}
        QLabel#Hero {{
            color: {colors["text"]};
            font-size: 28px;
            font-weight: 800;
        }}
        QLabel#SectionTitle {{
            color: {colors["text"]};
            font-size: 18px;
            font-weight: 700;
        }}
        QLabel#ExternalLink {{
            font-weight: 650;
            padding: 0 0 2px 2px;
        }}
        QLabel#Muted {{ color: {colors["muted"]}; }}
        QLabel#PreviewLabel {{
            background: {colors["preview"]};
            border: 1px dashed {colors["preview_border"]};
            border-radius: 14px;
            color: {colors["muted"]};
        }}
        QGroupBox {{
            border: 1px solid {colors["card_border"]};
            border-radius: 12px;
            margin-top: 12px;
            padding: 14px 10px 10px 10px;
            color: {colors["text"]};
            font-weight: 700;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: {colors["text"]};
            background: {colors["card"]};
        }}
        QLineEdit, QComboBox, QListWidget {{
            background: {colors["field"]};
            border: 1px solid {colors["field_border"]};
            border-radius: 8px;
            padding: 7px;
            color: {colors["text"]};
            selection-background-color: {colors["primary"]};
            selection-color: {colors["primary_text"]};
        }}
        QCheckBox {{
            color: {colors["text"]};
            spacing: 8px;
            font-weight: 600;
        }}
        QPushButton {{
            background: {colors["button"]};
            border: 1px solid {colors["button_border"]};
            border-radius: 9px;
            padding: 8px 12px;
            color: {colors["text"]};
            font-weight: 650;
        }}
        QPushButton:hover {{ background: {colors["button_hover"]}; }}
        QPushButton:disabled {{
            color: {colors["disabled_text"]};
            background: {colors["button_disabled"]};
        }}
        QPushButton#PrimaryButton {{
            background: {colors["primary"]};
            color: {colors["primary_text"]};
            border: 1px solid {colors["primary"]};
        }}
        QPushButton#PrimaryButton:hover {{ background: {colors["primary_hover"]}; }}
        QProgressBar {{
            background: {colors["field"]};
            border: 1px solid {colors["field_border"]};
            border-radius: 8px;
            height: 18px;
            color: {colors["text"]};
            text-align: center;
        }}
        QProgressBar::chunk {{
            background: {colors["chunk"]};
            border-radius: 7px;
        }}
        """,
    )


_DARK_COLORS = {
    "window": "#161b1d",
    "card": "#20282b",
    "card_border": "#3d4b50",
    "preview": "#14191b",
    "preview_border": "#52656b",
    "text": "#f3eadc",
    "muted": "#b7aa98",
    "field": "#151b1d",
    "field_border": "#4b5b60",
    "button": "#344247",
    "button_hover": "#415258",
    "button_border": "#5a6d73",
    "button_disabled": "#273033",
    "disabled_text": "#81776a",
    "primary": "#d58b3a",
    "primary_hover": "#e39a4a",
    "primary_text": "#1a130c",
    "chunk": "#d58b3a",
}

_LIGHT_COLORS = {
    "window": "#efe7d7",
    "card": "#fffaf0",
    "card_border": "#dac7a8",
    "preview": "#f6eddc",
    "preview_border": "#c8ad85",
    "text": "#2c241c",
    "muted": "#796b5a",
    "field": "#fffdf8",
    "field_border": "#d2bea0",
    "button": "#ead9bd",
    "button_hover": "#f2e3cb",
    "button_border": "#c8ad85",
    "button_disabled": "#e6ded0",
    "disabled_text": "#9b8c78",
    "primary": "#21666c",
    "primary_hover": "#2b777e",
    "primary_text": "#fff8ea",
    "chunk": "#d58b3a",
}
