# The Empirical Dad: podcast feed

Evidence-based parenting for dads who don't plan to slow down.

This repository hosts the podcast's audio and RSS feed on GitHub Pages:

- Feed: https://denizcan40.github.io/empirical-dad/feed.xml (this is the URL you give Spotify)
- Episode list: https://denizcan40.github.io/empirical-dad/

## Layout

| Path | What it is |
|---|---|
| `channel.json` | Show details: title, description, category, cover file, owner email |
| `cover.jpg` | Show artwork, square JPEG, 1400 to 3000 px (add it by hand) |
| `audio/ep000.mp3`, `audio/dayNNN.mp3` | Episode audio, byte for byte as rendered (Kokoro `af_heart`, mono, 32 kbps) |
| `episodes/ep000.json`, `episodes/dayNNN.json` | Per-episode metadata for the feed, including size, duration and SHA-256 of the MP3 |
| `tools/add_episode.py` | Adds one episode: copies the MP3 and writes its metadata |
| `tools/build_feed.py` | Rebuilds `feed.xml` and `index.html` from `episodes/*.json` |

## How episodes get here

The scheduled task "The Empirical Dad — back-catalog build" runs twice a day. Each run renders
new days, publishes them to the claude.ai archive as before, then commits the MP3s here, rebuilds
`feed.xml` and pushes to `main`. GitHub Pages republishes within a minute or two, and Spotify picks
up new feed items on its next refresh.

To add an episode by hand:

```bash
python3 tools/add_episode.py path/to/day082.json path/to/day082.mp3
python3 tools/build_feed.py
git add -A && git commit -m "Add Day 82" && git push
```

## Feed rules (enforced by `build_feed.py`)

- Episode 0, then Day 28 onward with no gaps. A day only appears once every earlier day is in,
  so Days 148–180 wait until Days 28–147 are all here.
- Each episode's publish date is fixed (23 Nov 2026 00:00 UTC plus N minutes), so apps list them in
  day order and a date never changes after publishing.
- GitHub Pages sites are limited to 1 GB. At about 6 MB an episode that is roughly 160 episodes;
  `build_feed.py` warns at 85%.

## One-time setup

1. Settings → Pages → Build and deployment → Source: "Deploy from a branch", branch `main`, folder `/ (root)`.
2. Add `cover.jpg` and fill `owner_email` in `channel.json` (Spotify sends a verification code there).
3. In Spotify for Creators, add the show by RSS feed with the feed URL above.
