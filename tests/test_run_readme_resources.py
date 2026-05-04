from src.resources import APP_ICON, BUNDLED_DATA_FILES, RUN_README_OUTPUTS, SOURCE_ROOT
from tomodachi_build_gui import DATA_FILES


def test_run_readme_markdown_and_html_keep_user_sections() -> None:
    zh_md = (SOURCE_ROOT / "README_RUN.template.md").read_text(encoding="utf-8")
    zh_html = (SOURCE_ROOT / "README_RUN.html").read_text(encoding="utf-8")
    en_md = (SOURCE_ROOT / "README_RUN-en.template.md").read_text(encoding="utf-8")
    en_html = (SOURCE_ROOT / "README_RUN-en.html").read_text(encoding="utf-8")

    assert "## 第一次使用" in zh_md
    assert "<h2>第一次使用</h2>" in zh_html
    assert "## 以后每次绘画" in zh_md
    assert "<h2>以后每次绘画</h2>" in zh_html
    assert "## First Use" in en_md
    assert "<h2>First Use</h2>" in en_html
    assert "## Every Later Run" in en_md
    assert "<h2>Every Later Run</h2>" in en_html
    assert "把画笔重置为 1px" in zh_md
    assert "左下角黑色（R7C1）" in zh_md
    assert "全色 / HSB 模式只需要画笔是 1px" in zh_md
    assert "84 色模式不允许跳过" in zh_md
    assert "可以先删除不想发送的颜色文件" in zh_md
    assert "reset the brush to 1 px" in en_md
    assert "lower-left black swatch (R7C1)" in en_md
    assert "full-color / HSB mode only requires the brush to be 1 px" in en_md
    assert "84-color mode cannot skip files" in en_md
    assert "delete unwanted color files first" in en_md


def test_bundled_data_files_include_all_run_readmes() -> None:
    assert DATA_FILES == BUNDLED_DATA_FILES
    assert {resource.relative_path for resource in RUN_README_OUTPUTS} <= set(DATA_FILES)


def test_bundled_data_files_include_app_icon() -> None:
    assert APP_ICON.exists()
    assert "assets/app-icon.png" in DATA_FILES
