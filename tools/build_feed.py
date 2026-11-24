#!/usr/bin/env python3
"""Build feed.xml (the podcast RSS feed Spotify reads) and index.html from episodes/*.json.

Usage: python3 tools/build_feed.py

Rules:
- Episode 0 is included when episodes/ep000.json exists.
- Day N is included only when every day from first_day (28) to N is present, so the feed
  never has gaps. Days past a gap (for example Days 148-180 before Days 82-147 exist) are
  held back automatically and listed in the output.
- pubDate is fixed per episode: pubdate_anchor + N minutes. Apps list episodes in day order,
  and an episode's date never changes once it is published.
- Only the metadata JSON is read, never the MP3s, so this works in a sparse checkout.
"""
import glob, html, json, os, re, sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES_LIMIT = 1024 ** 3  # GitHub Pages published-site limit (1 GB)


def esc(s):
    return html.escape(str(s), quote=True)


def split_title(title):
    """'Day 28 · Week 4, Day 0 — Body: smaller than salt — what the embryo is…'
    -> ('Day 28 · Week 4 — Body: smaller than salt', 'What the embryo is….')"""
    t = re.sub(r"(Week \d+), Day \d+", r"\1", title.strip())
    parts = t.split(" — ")
    main, sub = (" — ".join(parts[:2]), " — ".join(parts[2:])) if len(parts) > 2 else (t, "")
    if len(main) > 150:
        main = main[:147].rsplit(" ", 1)[0] + "…"
    if sub:
        sub = sub[0].upper() + sub[1:]
        if sub[-1] not in ".!?…":
            sub += "."
    return main, sub


def source_text(s):
    if isinstance(s, (list, tuple)):
        title = s[0] if s else ""
        url = s[1] if len(s) > 1 else ""
        return title, url
    m = re.search(r"https?://\S+", str(s))
    return (str(s), m.group(0).rstrip(").,") if m else "")


def duration(sec):
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}"


def main():
    ch = json.load(open(os.path.join(ROOT, "channel.json"), encoding="utf-8"))
    base = ch["base_url"].rstrip("/")
    anchor = datetime.strptime(ch["pubdate_anchor"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    first = int(ch.get("first_day", 28))

    eps = {}
    for p in glob.glob(os.path.join(ROOT, "episodes", "*.json")):
        e = json.load(open(p, encoding="utf-8"))
        eps[int(e["n"])] = e

    included, held = [], []
    if 0 in eps:
        included.append(eps[0])
    n = first
    while n in eps:
        included.append(eps[n])
        n += 1
    held = sorted(k for k in eps if k != 0 and k >= n)
    next_needed = n

    items = []
    for e in sorted(included, key=lambda e: e["n"], reverse=True):
        title, sub = split_title(e["title"])
        if e["n"] == 0:
            title = e["title"].split(" — ")[0] if len(e["title"]) > 150 else e["title"]
        paras = [x for x in (sub, e.get("summary", ""), f"Today's action: {e['action']}" if e.get("action") else "") if x]
        plain = "\n\n".join(paras + [ch["disclaimer"]])
        if len(plain) > 3900:
            keep = 3900 - len(ch["disclaimer"]) - len(paras[-1]) - 10
            paras[-2 if len(paras) > 1 else 0] = paras[-2 if len(paras) > 1 else 0][:keep].rsplit(" ", 1)[0] + "…"
            plain = "\n\n".join(paras + [ch["disclaimer"]])
        srcs = []
        for s in e.get("sources", []):
            t, u = source_text(s)
            srcs.append(f'<li><a href="{esc(u)}">{esc(t)}</a></li>' if u else f"<li>{esc(t)}</li>")
        rich = "".join(f"<p>{esc(p)}</p>" for p in plain.split("\n\n"))
        if srcs:
            rich += "<p>Sources:</p><ul>" + "".join(srcs) + "</ul>"
        pub = format_datetime(anchor + timedelta(minutes=e["n"]))
        num = f"\n      <itunes:episode>{e['n']}</itunes:episode>" if e["n"] > 0 else ""
        items.append(f"""    <item>
      <title>{esc(title)}</title>
      <description>{esc(plain)}</description>
      <content:encoded><![CDATA[{rich.replace(']]>', ']]&gt;')}]]></content:encoded>
      <enclosure url="{esc(base + '/' + e['audio'])}" length="{e['bytes']}" type="audio/mpeg"/>
      <guid isPermaLink="false">empirical-dad-{e['key']}</guid>
      <pubDate>{pub}</pubDate>
      <itunes:title>{esc(title)}</itunes:title>{num}
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:duration>{duration(e['seconds'])}</itunes:duration>
      <itunes:explicit>{'true' if ch['explicit'] else 'false'}</itunes:explicit>
    </item>""")

    owner_email = ch.get("owner_email", "").strip()
    owner = f"""
    <itunes:owner>
      <itunes:name>{esc(ch['owner_name'])}</itunes:name>
      <itunes:email>{esc(owner_email)}</itunes:email>
    </itunes:owner>""" if owner_email else ""
    newest = max((e["n"] for e in included), default=0)
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{esc(ch['title'])}</title>
    <link>{esc(base)}/</link>
    <atom:link href="{esc(base)}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>{esc(ch['language'])}</language>
    <description>{esc(ch['description'])}</description>
    <itunes:summary>{esc(ch['description'])}</itunes:summary>
    <itunes:subtitle>{esc(ch['subtitle'])}</itunes:subtitle>
    <itunes:author>{esc(ch['author'])}</itunes:author>{owner}
    <itunes:image href="{esc(base + '/' + ch['cover'])}"/>
    <image><url>{esc(base + '/' + ch['cover'])}</url><title>{esc(ch['title'])}</title><link>{esc(base)}/</link></image>
    <itunes:category text="{esc(ch['category'])}"><itunes:category text="{esc(ch['subcategory'])}"/></itunes:category>
    <itunes:explicit>{'true' if ch['explicit'] else 'false'}</itunes:explicit>
    <itunes:type>{esc(ch['type'])}</itunes:type>
    <lastBuildDate>{format_datetime(anchor + timedelta(minutes=newest))}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""
    open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8").write(feed)

    rows = "".join(
        f'<li><a href="{esc(e["audio"])}">{esc(split_title(e["title"])[0] if e["n"] else e["title"])}</a> · {round(e["seconds"] / 60)} min</li>'
        for e in sorted(included, key=lambda e: e["n"]))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(ch['title'])}</title><link rel="alternate" type="application/rss+xml" href="feed.xml">
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem;color:#1d2433}}a{{color:#c2571a}}li{{margin:.3rem 0}}</style></head>
<body><h1>{esc(ch['title'])}</h1><p>{esc(ch['subtitle'])}</p><p>{esc(ch['description'])}</p>
<p><a href="feed.xml">RSS feed</a></p><ol>{rows}</ol><p><small>{esc(ch['disclaimer'])}</small></p></body></html>
"""
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(page)

    total = sum(e["bytes"] for e in eps.values())
    print(f"feed.xml: {len(included)} episodes"
          + (f" (Ep. 0 + Days {first}–{next_needed - 1})" if next_needed > first else ""))
    print(f"next day needed for the feed to grow: Day {next_needed}")
    if held:
        print(f"held back (gap before them): Days {held[0]}–{held[-1]} ({len(held)} episodes)")
    print(f"audio in repo: {total / 1e6:.0f} MB of the 1,000 MB GitHub Pages limit")
    if total > 0.85 * PAGES_LIMIT:
        print("WARNING: audio is over 85% of the GitHub Pages limit; audio needs another host soon")
    if not owner_email:
        print("note: channel.json owner_email is empty (Spotify's RSS check emails a code to it)")
    if not os.path.exists(os.path.join(ROOT, ch["cover"])):
        print(f"note: {ch['cover']} is missing (Spotify needs 1400-3000 px square artwork)")


if __name__ == "__main__":
    main()
