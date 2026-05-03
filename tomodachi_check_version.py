import argparse
import re
import sys
import tomllib
from pathlib import Path

SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$",
)


def project_version(pyproject_path: Path) -> str:
    with pyproject_path.open("rb") as file:
        data = tomllib.load(file)
    return str(data["project"]["version"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate project semantic version.")
    parser.add_argument(
        "--tag",
        help="Optional git tag to compare with pyproject version, for example v1.0.0.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(__file__).resolve().parent
    version = project_version(root / "pyproject.toml")

    if not SEMVER_PATTERN.fullmatch(version):
        print(f"pyproject.toml version is not semantic versioning: {version}", file=sys.stderr)
        return 1

    if args.tag:
        expected_tag = f"v{version}"
        if args.tag != expected_tag:
            print(
                f"tag {args.tag!r} does not match pyproject.toml version {version!r}; "
                f"expected {expected_tag!r}",
                file=sys.stderr,
            )
            return 1

    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
