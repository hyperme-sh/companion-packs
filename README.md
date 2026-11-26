# Visor companion packs

Community appearances, cursor art, and recorded voices for Visor. The [Visor
pack guide](https://github.com/hyperme-sh/visor/blob/main/docs/companion-packs.md)
defines format 1 and explains how to install a pack locally.

## Contribute a pack

Fork this repository and open a pull request adding one folder under `packs/`.
Use a lowercase ID such as `my-rabbit`. Keep the pack's `pack.json`, PNGs, and
WAVs at the top of its folder. A single still image or one recorded cue is a
complete contribution. Use `null` or omit a cue when you have no asset for it.

Add a `LICENSE` that permits sharing and modification. Include attribution for
all artwork and recordings and permission to redistribute and remix a voice.
Contributors can include editable sources under `source/` for other creators.

Create `catalog.json` in the pack folder with your credit, license identifier,
and the previews to show in Visor. An appearance preview can use a referenced
sprite or cursor. A voice preview uses a referenced recording.

```json
{
  "author": "Your name",
  "license": "CC0-1.0",
  "art_preview": "idle.png",
  "voice_preview": "hello.wav"
}
```

The check workflow validates contributions and builds the catalog from the
repository contents. Use `python3 tools/catalog.py check` to check the format.
Accepted packs appear in the catalog published from `main`. A source repository
or local installation remains an independent way to share and remix a pack.

## Catalog contract

The `catalog` branch serves `catalog.json` over GitHub raw content. Format 1
contains a source revision, an immutable asset revision, and the list of packs.
Each pack lists its ID, name, author, license, supported media and SHA-256 and
byte length for its archive and optional previews.

At the asset revision the files are `packs/<id>.pack.json`, `packs/<id>.png`
and `packs/<id>.wav`. The archive is a JSON object with `format: 1` and a
`files` array of `[filename, base64]` pairs. It carries bounded regular files
with flat names, pack assets, license, and attribution. The source revision
identifies the accepted contributor commit. The asset revision independently
identifies the downloadable bytes. See [Visor #359](https://github.com/hyperme-sh/visor/issues/359).
