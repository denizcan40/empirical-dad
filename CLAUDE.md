# Rules for Claude sessions in this repository

- This repo is the public GitHub Pages host for The Empirical Dad's audio and RSS feed. Everything here is public.
- Never commit names, dates or personal details of anyone, credentials, tokens or email addresses other than `owner_email` in `channel.json`.
- Add episodes only with `tools/add_episode.py <archive json> <mp3>`, then run `tools/build_feed.py`. Never edit `feed.xml` or `index.html` by hand.
- Never re-encode, trim or lower the bitrate of an MP3. Audio goes in byte for byte as rendered.
- Never change `pubdate_anchor` in `channel.json` or an episode's `key`/guid: Spotify uses them to identify episodes.
- Do not rewrite history or force-push `main`.
- Scheduled runs use a sparse checkout without old MP3s. Commit only the files you add or change.
