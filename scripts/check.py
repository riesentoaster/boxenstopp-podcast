#!/usr/bin/env python3
"""Check and fix MP3 titles and episode metadata. Use --fix to auto-fix, then fail if anything changed."""

import argparse
import re
import sys
from pathlib import Path

import yaml
from mutagen.id3 import TIT2
from mutagen.mp3 import MP3

POSTS_DIR = Path("_posts")
AUDIO_DIR = Path("assets/audio")
PODCAST = "Boxenstopp Predigt-Podcast"
TITLE_SEP = " \u2013 "
STEM_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")


def title_from_filename(stem: str) -> str | None:
    match = STEM_PATTERN.fullmatch(stem)
    if not match:
        return None
    date, slug = match.groups()
    return f"{PODCAST}{TITLE_SEP}{date}{TITLE_SEP}{slug.replace('-', ' ')}"


def mp3_duration(path: Path) -> str:
    seconds = int(MP3(path).info.length)
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def parse_post(path: Path) -> tuple[dict, str] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    _, front_matter, body = text.split("---", 2)
    return yaml.safe_load(front_matter) or {}, text


def check_mp3s(*, fix: bool) -> tuple[int, list[str]]:
    fixed, errors = 0, []
    for path in sorted(AUDIO_DIR.glob("*.mp3")):
        want = title_from_filename(path.stem)
        if not want:
            continue

        mp3 = MP3(path)
        have = str(mp3.tags["TIT2"]) if mp3.tags and mp3.tags.get("TIT2") else None
        if have == want:
            continue

        if fix:
            if mp3.tags is None:
                mp3.add_tags()
            mp3.tags.delall("TIT2")
            mp3.tags.add(TIT2(encoding=3, text=want))
            mp3.save()
            fixed += 1
            print(f"fixed title: {path.name}")
        else:
            errors.append(f"{path}: title {have!r} != {want!r}")
    return fixed, errors


def check_episodes(*, fix: bool) -> tuple[int, list[str]]:
    fixed, errors = 0, []
    for post in sorted(POSTS_DIR.glob("*.md")):
        parsed = parse_post(post)
        if not parsed:
            continue
        meta, text = parsed
        if meta.get("layout") != "episode":
            continue

        audio = meta.get("audio") or {}
        url = audio.get("url")
        if not url:
            errors.append(f"{post}: missing audio.url")
            continue

        mp3 = AUDIO_DIR / url
        if not mp3.is_file():
            errors.append(f"{post}: missing audio file {mp3}")
            continue

        want_duration = mp3_duration(mp3)
        want_size = mp3.stat().st_size
        have_duration = str(meta.get("duration", ""))
        have_size = audio.get("size")

        problems = []
        if not have_duration or have_size is None:
            problems.append("missing duration or audio.size")
        if have_duration != want_duration:
            problems.append(f"duration {have_duration!r} != {want_duration!r}")
        if have_size is not None and int(have_size) != want_size:
            problems.append(f"size {have_size} != {want_size}")

        if not problems:
            continue

        if fix:
            updated = text
            if have_duration != want_duration:
                updated = re.sub(
                    r"^duration:.*$",
                    f'duration: "{want_duration}"',
                    updated,
                    count=1,
                    flags=re.MULTILINE,
                )
            if have_size is None or int(have_size) != want_size:
                updated = re.sub(
                    r"(^audio:\n(?:  .+\n)*?  size: ).*$",
                    rf"\g<1>{want_size}",
                    updated,
                    count=1,
                    flags=re.MULTILINE,
                )
            if updated != text:
                post.write_text(updated, encoding="utf-8")
                fixed += 1
                print(f"fixed metadata: {post.name}")
        else:
            errors.append(f"{post}: {'; '.join(problems)}")
    return fixed, errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args()

    fixed = 0
    if args.fix:
        fixed += check_mp3s(fix=True)[0]
        fixed += check_episodes(fix=True)[0]

    errors = check_mp3s(fix=False)[1] + check_episodes(fix=False)[1]
    if errors:
        print("Checks failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    if fixed:
        print(
            f"Fixed {fixed} file(s). Review the changes and commit again.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("All content checks passed.")


if __name__ == "__main__":
    main()
