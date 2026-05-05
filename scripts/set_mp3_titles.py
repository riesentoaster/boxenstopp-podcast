#!/usr/bin/env python3
"""Set MP3 title from filenames like YYYY-MM-DD-Episode-Teil-1.mp3 (mutagen ID3 edit)."""

import argparse
import re
import sys
from pathlib import Path

try:
    from mutagen.id3 import TIT2
    from mutagen.mp3 import MP3
except ImportError:
    sys.exit(
        "mutagen is required: pip install mutagen "
        "(or use pre-commit, which installs it for this hook)",
    )

DEFAULT_AUDIO_DIR = Path("assets/audio")
PODCAST = "Boxenstopp Predigt-Podcast"
TITLE_SEP = " \u2013 "
STEM_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")


def rewrite_mp3(mp3_path: Path) -> None:
    match = STEM_PATTERN.fullmatch(mp3_path.stem)
    if not match:
        print("skip:", mp3_path, file=sys.stderr)
        return
    date_part, slug = match.group(1), match.group(2)
    episode_title = slug.replace("-", " ")
    title = f"{PODCAST}{TITLE_SEP}{date_part}{TITLE_SEP}{episode_title}"

    audio = MP3(str(mp3_path))
    if audio.tags is None:
        audio.add_tags()
    audio.tags.delall("TIT2")
    audio.tags.add(TIT2(encoding=3, text=title))
    audio.save()

    print(title)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write ID3 titles from filenames (Boxenstopp Predigt-Podcast – date – episode).",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=DEFAULT_AUDIO_DIR,
        type=Path,
        help=f"Folder of MP3s (default: {DEFAULT_AUDIO_DIR})",
    )
    parsed = parser.parse_args()
    audio_dir = parsed.directory
    if not audio_dir.is_dir():
        sys.exit(f"not a directory: {audio_dir}")

    for mp3_path in sorted(audio_dir.glob("*.mp3")):
        rewrite_mp3(mp3_path)


if __name__ == "__main__":
    main()
