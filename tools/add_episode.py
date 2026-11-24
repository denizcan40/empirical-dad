#!/usr/bin/env python3
"""Add (or replace) one episode in the repo.

Usage: python3 tools/add_episode.py <archive-episode.json> <episode.mp3>

Copies the MP3 to audio/<key>.mp3 byte for byte and writes episodes/<key>.json with the
fields the feed needs plus the file's size, duration and SHA-256, so build_feed.py never
has to open the audio again (scheduled runs use a sparse checkout without old MP3s).
<key> is ep000 for Episode 0 and dayNNN for Day NNN, taken from the JSON's "n".
"""
import hashlib, json, os, shutil, subprocess, sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH_FILE_LIMIT = 95 * 1024 * 1024  # GitHub rejects files over 100 MB


def main(src_json, mp3):
    e = json.load(open(src_json, encoding="utf-8"))
    n = e.get("n", e.get("day"))
    n = 0 if n in (None, "", "0") else int(n)
    key = "ep000" if n == 0 else f"day{n:03d}"

    size = os.path.getsize(mp3)
    if size > GH_FILE_LIMIT:
        sys.exit(f"{mp3} is {size} bytes, too large for GitHub")
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", mp3], capture_output=True, text=True, check=True).stdout.strip()
    sha = hashlib.sha256(open(mp3, "rb").read()).hexdigest()

    dst = os.path.join(ROOT, "audio", f"{key}.mp3")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.abspath(mp3) != os.path.abspath(dst):
        shutil.copyfile(mp3, dst)
    if hashlib.sha256(open(dst, "rb").read()).hexdigest() != sha:
        sys.exit("copy check failed")

    meta_path = os.path.join(ROOT, "episodes", f"{key}.json")
    old = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else {}
    meta = {
        "n": n,
        "key": key,
        "title": e.get("title", ""),
        "week": e.get("week", ""),
        "summary": e.get("summary", ""),
        "action": e.get("action", ""),
        "sources": e.get("sources", []),
        "audio": f"audio/{key}.mp3",
        "bytes": size,
        "seconds": round(float(dur)),
        "sha256": sha,
        "added": old.get("added") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
    json.dump(meta, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{key}: {size} bytes, {meta['seconds'] / 60:.1f} min, sha256 {sha[:12]}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
