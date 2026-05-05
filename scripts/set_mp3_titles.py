#!/usr/bin/env python3
"""Set MP3 title from filenames like YYYY-MM-DD-Episode-Teil-1.mp3 (needs ffmpeg)."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_AUDIO_DIR = Path("assets/audio")
PODCAST = "Boxenstopp Predigt-Podcast"
TITLE_SEP = " \u2013 "
STEM_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
FFMPEG_BASE = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y"]


def rewrite_mp3(mp3_path: Path) -> None:
    match = STEM_PATTERN.fullmatch(mp3_path.stem)
    if not match:
        print("skip:", mp3_path, file=sys.stderr)
        return
    date_part, slug = match.group(1), match.group(2)
    episode_title = slug.replace("-", " ")
    title = f"{PODCAST}{TITLE_SEP}{date_part}{TITLE_SEP}{episode_title}"
    temp_path = mp3_path.with_suffix(".tmp.mp3")
    try:
        subprocess.run(
            [
                *FFMPEG_BASE,
                "-i",
                str(mp3_path),
                "-map",
                "0",
                "-c",
                "copy",
                "-metadata",
                f"title={title}",
                str(temp_path),
            ],
            check=True,
        )
        temp_path.replace(mp3_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
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
