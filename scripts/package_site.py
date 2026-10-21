#!/usr/bin/env python3
"""Package the static website for GitHub Pages and check local asset URLs."""

from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "_site"


def check_url(value, document):
    url = urlsplit(value)
    if url.scheme or url.netloc or not url.path:
        return
    if url.path.startswith("/"):
        raise ValueError(f"Use a relative asset URL for the repository subpath: {value}")
    target = (document.parent / unquote(url.path)).resolve()
    if not target.is_relative_to(DESTINATION) or not target.is_file():
        raise FileNotFoundError(f"Missing deployment asset referenced by {document.name}: {value}")


class AssetParser(HTMLParser):
    def handle_starttag(self, tag, attributes):
        for name, value in attributes:
            if name in {"href", "src", "poster"} and value:
                check_url(value, DESTINATION / "index.html")


def main():
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    DESTINATION.mkdir()

    for filename in ["index.html", ".nojekyll", "UniKey.pdf"]:
        shutil.copy2(ROOT / filename, DESTINATION / filename)
    for directory in ["assets", "data", "media"]:
        shutil.copytree(
            ROOT / directory,
            DESTINATION / directory,
            ignore=shutil.ignore_patterns("sources", "__pycache__", "*.pyc"),
        )

    social = ROOT / "output/social"
    if social.is_dir():
        for source in sorted(social.iterdir()):
            if source.is_file() and source.suffix.lower() in {".mp4", ".jpg"}:
                target = DESTINATION / "output/social" / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

    AssetParser().feed((DESTINATION / "index.html").read_text())
    for stylesheet in (DESTINATION / "assets").rglob("*.css"):
        for match in re.finditer(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", stylesheet.read_text()):
            check_url(match[1].strip(), stylesheet)

    files = [path for path in DESTINATION.rglob("*") if path.is_file()]
    size = sum(path.stat().st_size for path in files)
    print(f"Packaged {len(files)} files ({size / 1024 / 1024:.1f} MiB) in {DESTINATION}")
    print("PASS: local HTML and stylesheet assets resolve within the deployment bundle")


if __name__ == "__main__":
    main()
