#!/usr/bin/env python3
"""Check that each episode's duration and audio.size match its MP3 file."""

import re
import sys
from pathlib import Path

from mutagen.mp3 import MP3

POSTS_DIR = Path("_posts")
AUDIO_DIR = Path("assets/audio")


def mp3_duration(path: Path) -> str:
    seconds = int(MP3(path).info.length)
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}:{secs:02d}"


def main() -> None:
    errors: list[str] = []

    for post in sorted(POSTS_DIR.glob("*.md")):
        text = post.read_text(encoding="utf-8")
        if "layout: episode" not in text:
            continue

        duration = re.search(r'^duration: "?([^"\n]+)"?', text, re.MULTILINE)
        audio_url = re.search(r'^  url: "?([^"\n]+)"?', text, re.MULTILINE)
        size = re.search(r"^  size: (\d+)", text, re.MULTILINE)

        if not duration or not audio_url or not size:
            errors.append(f"{post}: missing duration, audio.url, or audio.size")
            continue

        mp3 = AUDIO_DIR / audio_url.group(1)
        if not mp3.is_file():
            errors.append(f"{post}: missing audio file {mp3}")
            continue

        expected_duration = mp3_duration(mp3)
        if duration.group(1) != expected_duration:
            errors.append(
                f"{post}: duration {duration.group(1)!r} != {expected_duration!r}",
            )

        actual_size = mp3.stat().st_size
        if int(size.group(1)) != actual_size:
            errors.append(
                f"{post}: size {size.group(1)} != {actual_size}",
            )

    if errors:
        print("Episode metadata check failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    print("Episode metadata OK.")


if __name__ == "__main__":
    main()
