#!/usr/bin/env python3
"""Fetch, cache, rotate and display alpaca photos for fastfetch."""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = Path(os.environ.get("ALPACA_FETCH_CACHE", Path.home() / "Library/Caches/alpaca-fetch"))
STATE = CACHE / "state.json"
CONFIG = ROOT / "fastfetch.jsonc"
MAX_IMAGES = 20
REFRESH_AFTER = 6 * 60 * 60
USER_AGENT = "alpaca-fetch/1.0 (https://commons.wikimedia.org/)"


def request_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=8) as response:
        return json.load(response)


def image_files() -> list[Path]:
    return sorted(CACHE.glob("*.jpg"))


def crop_square(source: Path, destination: Path) -> bool:
    """Use the native macOS image tool to produce a predictable square JPEG."""
    temp = destination.with_suffix(".working.jpg")
    try:
        subprocess.run(["sips", "-Z", "640", str(source), "--out", str(temp)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        size = subprocess.check_output(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(temp)], text=True)
        dimensions = [int(line.split()[-1]) for line in size.splitlines() if line.strip().split()[-1].isdigit()]
        side = min(dimensions[-2:]) if len(dimensions) >= 2 else 640
        subprocess.run(["sips", "--cropToHeightWidth", str(side), str(side), str(temp), "--out", str(destination)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        temp.unlink(missing_ok=True)
        source.unlink(missing_ok=True)
        return True
    except (OSError, subprocess.SubprocessError, ValueError):
        temp.unlink(missing_ok=True)
        source.unlink(missing_ok=True)
        return False


def refresh() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    offset = random.randrange(0, 80, 10)
    query = urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": "alpaca filetype:bitmap", "gsrnamespace": 6,
        "gsrlimit": 40, "gsroffset": offset, "prop": "imageinfo",
        "iiprop": "url", "iiurlwidth": 640,
    })
    try:
        pages = request_json("https://commons.wikimedia.org/w/api.php?" + query).get("query", {}).get("pages", {})
    except (OSError, ValueError):
        return len(image_files())

    existing = {p.stem for p in image_files()}
    candidates = list(pages.values())
    random.shuffle(candidates)
    for page in candidates:
        if len(existing) >= MAX_IMAGES:
            break
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        if not url:
            continue
        stem = f"{page.get('pageid', random.randrange(10**9))}"
        if stem in existing:
            continue
        raw = CACHE / f".{stem}.download"
        destination = CACHE / f"{stem}.jpg"
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=12) as response, raw.open("wb") as output:
                shutil.copyfileobj(response, output)
            if crop_square(raw, destination):
                existing.add(stem)
        except OSError:
            raw.unlink(missing_ok=True)

    STATE.write_text(json.dumps({"last_refresh": int(time.time())}) + "\n")
    return len(image_files())


def choose_image() -> Path | None:
    files = image_files()
    if not files:
        refresh()
        files = image_files()
    if not files:
        return None
    state = {}
    try:
        state = json.loads(STATE.read_text())
    except (OSError, ValueError):
        pass
    index = (int(state.get("next", 0)) % len(files))
    state.update({"next": index + 1})
    STATE.write_text(json.dumps(state) + "\n")
    return files[index]


def start_background_refresh() -> None:
    try:
        last = json.loads(STATE.read_text()).get("last_refresh", 0)
    except (OSError, ValueError):
        last = 0
    if time.time() - last > REFRESH_AFTER:
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--refresh"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL, start_new_session=True)


def fastfetch() -> int:
    image = choose_image()
    start_background_refresh()
    command = ["fastfetch", "--config", str(CONFIG)]
    if image:
        term = os.environ.get("TERM_PROGRAM", "")
        if term == "iTerm.app":
            command += ["--logo-type", "iterm"]
        elif (os.environ.get("KITTY_WINDOW_ID") or
              term in {"WezTerm", "WezTerm-gui", "ghostty", "Ghostty"}):
            command += ["--logo-type", "kitty"]
        else:
            # Plain Terminal.app has no bitmap protocol. Do not let fastfetch
            # silently convert the photo into ASCII or block trying to do so.
            image = None
        if image:
            command += ["--logo", str(image), "--logo-width", "26", "--logo-height", "13"]
    return subprocess.call(command)


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "next"
    if command in {"refresh", "--refresh"}:
        print(f"alpaca-fetch: {refresh()} image(s) cached")
        return 0
    if command == "status":
        print(f"cache: {CACHE}\nimages: {len(image_files())}/{MAX_IMAGES}")
        return 0
    if command == "fastfetch":
        return fastfetch()
    image = choose_image()
    if image:
        print(image)
        start_background_refresh()
    return 0 if image else 1


if __name__ == "__main__":
    raise SystemExit(main())
