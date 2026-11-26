# Visor companion packs

Community appearances, cursor art, and recorded voices for Visor. The [Visor
pack guide](https://github.com/hyperme-sh/visor/blob/main/docs/companion-packs.md)
defines format 1 and explains how to install a pack locally.

## Packs to remix

| Pack | Appearance | Voice |
| --- | --- | --- |
| [Ember Cat](packs/ember-cat) | Orange tabby with a slow blink | Warm, mid-pitched English |
| [Scout Dog](packs/scout-dog) | Golden puppy that wags while working | Low, steady English |
| [Clover Rabbit](packs/clover-rabbit) | Lavender rabbit with a sleeping pose | Bright, high-pitched English |
| [Visor Beetle](packs/visor-beetle) | Original Visor animation loops and cursor sprites | Pair it with any installed voice |
| [Desk Bot](packs/desk-bot) | Two pixel-art poses | Two-tone electronic cue |

The three animal packs include editable SVGs, voice lines, and voice settings in
their `source/` folders. With Python 3, `rsvg-convert`, and `espeak-ng`
available, regenerate the PNG and WAV files for a pack after editing its source.

```sh
python3 tools/render_examples.py packs/ember-cat
```

Visor uses the included PNG and WAV files. Pick an appearance and a voice
independently to try them together. The [beetle remix guide](packs/visor-beetle/source/README.md)
points to its original artwork and timing references.

## Contribute a pack

Fork this repository and open a pull request adding one folder under `packs/`.
Use a lowercase ID such as `my-rabbit`. Keep the pack's `pack.json`, PNGs, and
WAVs at the top of its folder. A single still image or one recorded cue is a
complete contribution. Use `null` or omit a cue when you have no asset for it.

Add a `LICENSE` that permits sharing and modification. Include attribution for
all artwork and recordings and permission to redistribute and remix a voice.
Contributors can include editable sources under `source/` for other creators.

Create `catalog.json` in the pack folder with your credit and license identifier.
You can name the previews to show in Visor. An appearance preview can use a
referenced sprite or cursor. A voice preview uses a referenced recording. If
you leave a preview unspecified, the catalog picks one from the referenced
assets, preferring a sprite over a cursor when both are available.

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
byte length for its archive and the previews for its media.

At the asset revision the files are `packs/<id>.pack.json`, `packs/<id>.png`
and `packs/<id>.wav`. The archive is a JSON object with `format: 1` and a
`files` array of `[filename, base64]` pairs. It carries bounded regular files
with flat names, pack assets, license, and attribution. The source revision
identifies the accepted contributor commit. The asset revision independently
identifies the downloadable bytes. See [Visor #359](https://github.com/hyperme-sh/visor/issues/359).

The repository tooling and guide use the [MIT license](LICENSE). Each pack declares its own media license.
