import unittest

from src.gui_i18n import configure_i18n, set_locale, tr


class TestGuiI18n(unittest.TestCase):
    def test_gui_translation_switches_between_zh_and_en(self) -> None:
        configure_i18n("zh")
        self.assertEqual(tr("generate.button"), "生成宏")
        self.assertEqual(tr("hero.title"), "Tomodachi 面部彩绘宏生成器")

        set_locale("en")
        self.assertEqual(tr("hero.title"), "Tomodachi Face Paint Macro Generator")
        self.assertEqual(tr("generate.button"), "Generate")
        self.assertEqual(tr("generate.open_living_grid"), "Open Living the Grid")
        self.assertEqual(tr("draw.open_readme"), "Read Run Instructions")
        self.assertEqual(tr("draw.cancel"), "Cancel")

    def test_gui_translation_formats_preview_meta(self) -> None:
        configure_i18n("en")

        text = tr(
            "preview.meta",
            name="example.json",
            width=36,
            height=36,
            brush_px=7,
            colors=12,
            palette="auto",
        )

        self.assertIn("brush 7px", text)

    def test_gui_translation_formats_transfer_progress(self) -> None:
        configure_i18n("en")

        text = tr("progress.transfer", percent="12.3%", queue="50", eta="01:23")

        self.assertEqual(text, "12.3%  queue=50  ETA 01:23")


if __name__ == "__main__":
    unittest.main()
