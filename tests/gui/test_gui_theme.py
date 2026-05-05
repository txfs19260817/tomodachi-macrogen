from src.gui.gui_theme import build_theme_style


def test_light_theme_defines_table_palette() -> None:
    stylesheet = build_theme_style("light").stylesheet

    assert "QTableWidget, QTableView" in stylesheet
    assert "background: #fffdf8" in stylesheet
    assert "alternate-background-color: #f6eddc" in stylesheet
    assert "QHeaderView::section" in stylesheet


def test_dark_theme_defines_table_palette() -> None:
    stylesheet = build_theme_style("dark").stylesheet

    assert "QTableWidget, QTableView" in stylesheet
    assert "background: #151b1d" in stylesheet
    assert "alternate-background-color: #1b2225" in stylesheet
    assert "QHeaderView::section" in stylesheet
