import sys
from dataclasses import dataclass
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))

DEFAULT_CONFIG = RESOURCE_ROOT / "config.default.json"
RUN_README_TEMPLATE = RESOURCE_ROOT / "README_RUN.template.md"
RUN_README_EN_TEMPLATE = RESOURCE_ROOT / "README_RUN-en.template.md"
RUN_README_HTML = RESOURCE_ROOT / "README_RUN.html"
RUN_README_EN_HTML = RESOURCE_ROOT / "README_RUN-en.html"


@dataclass(frozen=True)
class BundledResource:
    relative_path: str
    output_name: str

    @property
    def path(self) -> Path:
        return RESOURCE_ROOT / self.relative_path


RUN_README_OUTPUTS = (
    BundledResource("README_RUN.template.md", "README_RUN.md"),
    BundledResource("README_RUN-en.template.md", "README_RUN-en.md"),
    BundledResource("README_RUN.html", "README_RUN.html"),
    BundledResource("README_RUN-en.html", "README_RUN-en.html"),
)

BUNDLED_DATA_FILES = ("config.default.json",) + tuple(
    resource.relative_path for resource in RUN_README_OUTPUTS
)
