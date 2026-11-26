"""Validate contributor packs and produce deterministic, data-only archives."""

import argparse
import base64
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?")
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
REVISION = re.compile(r"[0-9a-f]{40}")
WINDOWS_RESERVED = re.compile(r"(?:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\..*)?", re.I)
CURSORS = {"pointer", "crawl", "fly", "reach", "click1", "click2", "type1", "type2",
           "busy1", "busy2", "busy3", "busy4"}
BUNDLE_LIMIT = 100 * 1024 * 1024


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n").encode()


def parse_object(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key {key}")
            result[key] = value
        return result

    decoded = json.loads(data, object_pairs_hook=unique)
    require(isinstance(decoded, dict), "expected a JSON object")
    return decoded


def metadata(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def safe_name(name):
    return isinstance(name, str) and NAME.fullmatch(name) and not name.endswith(".") and not WINDOWS_RESERVED.fullmatch(name)


def read_file(path, limit):
    require(path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= limit,
            f"{path.name} must be a bounded regular file")
    return path.read_bytes()


def label(value, maximum):
    return (isinstance(value, str) and bool(value.strip()) and len(value.encode()) <= maximum
            and all(ord(c) >= 32 and ord(c) != 127 for c in value))


def cue_key(key):
    if key == "default":
        return True
    part, separator, value = key.partition(":")
    return separator and part in {"state", "verb", "mode", "mood", "vibe"} and label(value, 260)


def png_size(data):
    require(data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR", "expected PNG with IHDR")
    offset = 8
    chunks = set()
    while offset + 12 <= len(data):
        size = struct.unpack_from(">I", data, offset)[0]
        end = offset + 8 + size
        name = data[offset + 4:offset + 8]
        require(end + 4 <= len(data), "truncated PNG")
        require(zlib.crc32(data[offset + 4:end]) == struct.unpack_from(">I", data, end)[0], "invalid PNG checksum")
        chunks.add(name)
        offset = end + 4
        if name == b"IEND":
            break
    require(offset == len(data) and {b"IHDR", b"IDAT", b"IEND"} <= chunks and b"acTL" not in chunks,
            "expected a complete single-frame PNG")
    return struct.unpack_from(">II", data, 16)


def validate_wav(path, data):
    require(data[:4] == b"RIFF" and data[8:12] == b"WAVE" and len(data) >= 44
            and struct.unpack_from("<I", data, 4)[0] == len(data) - 8, f"{path.name} is not a complete WAV")
    offset = 12
    pcm_format = None
    pcm_bytes = None
    while offset + 8 <= len(data):
        kind = data[offset:offset + 4]
        size = struct.unpack_from("<I", data, offset + 4)[0]
        end = offset + 8 + size
        require(end + size % 2 <= len(data), f"{path.name} has a truncated WAV chunk")
        if kind == b"fmt ":
            require(size >= 16 and pcm_format is None, f"{path.name} has an invalid WAV format")
            pcm_format = struct.unpack_from("<HHIIHH", data, offset + 8)
        elif kind == b"data":
            require(pcm_bytes is None, f"{path.name} has duplicate WAV data")
            pcm_bytes = size
        offset = end + size % 2
    require(offset == len(data) and pcm_format and pcm_bytes, f"{path.name} has incomplete WAV data")
    encoding, channels, rate, byte_rate, alignment, bits = pcm_format
    require(encoding == 1 and channels == 1 and 8000 <= rate <= 48000 and byte_rate == rate * 2
            and alignment == 2 and bits == 16 and pcm_bytes % 2 == 0 and pcm_bytes <= rate * 6,
            f"{path.name} must contain up to three seconds of mono 16-bit PCM")


def read_pack(folder):
    pack_id = folder.name
    require(ID.fullmatch(pack_id) and safe_name(pack_id) and not folder.is_symlink(), "invalid pack folder")
    manifest_data = read_file(folder / "pack.json", 32 * 1024)
    manifest = parse_object(manifest_data)
    require(type(manifest.get("format")) is int and manifest["format"] == 1 and label(manifest.get("name"), 128),
            "expected format 1 and a pack name")
    identity = parse_object(read_file(folder / "catalog.json", 4096))
    require(set(identity) <= {"author", "license", "art_preview", "voice_preview"}
            and label(identity.get("author"), 128) and label(identity.get("license"), 64), "expected author and license")
    license_data = read_file(folder / "LICENSE", 64 * 1024)
    files = {"pack.json": manifest_data, "LICENSE": license_data}
    if (folder / "ATTRIBUTION.md").exists():
        files["ATTRIBUTION.md"] = read_file(folder / "ATTRIBUTION.md", 64 * 1024)
    else:
        files["ATTRIBUTION.md"] = f'{manifest["name"]} by {identity["author"]}\nLicense: {identity["license"]}\n'.encode()

    def assets(medium, key_check):
        value = manifest.get(medium, {})
        require(isinstance(value, dict) and len(value) <= 64 and all(map(key_check, value)),
                f"invalid {medium} bindings")
        return [entry for entry in value.values() if entry is not None]

    def media(name, extension, maximum):
        require(safe_name(name) and name.endswith(extension), f"invalid {extension} filename")
        if name not in files:
            files[name] = read_file(folder / name, maximum)
        require(len(files[name]) <= maximum, f"{name} is too large")
        return files[name]

    sprite_names = set()
    for clip in assets("sprites", cue_key):
        require(isinstance(clip, dict) and set(clip) <= {"frames", "ms_per_frame", "loop"}, "invalid sprite clip")
        frames = clip.get("frames")
        interval = clip.get("ms_per_frame")
        require(isinstance(frames, list) and len(frames) <= 16
                and (interval is None or (type(interval) is int and 40 <= interval <= 10_000))
                and type(clip.get("loop", False)) is bool, "invalid sprite timing or frame count")
        for name in frames:
            data = media(name, ".png", 1024 * 1024)
            require(png_size(data) == (400, 520), f"{name} must be 400 by 520")
            sprite_names.add(name)
    require(len(sprite_names) <= 64, "too many sprite files")
    cursor_names = set()
    for name in assets("cursor", CURSORS.__contains__):
        require(png_size(media(name, ".png", 32 * 1024)) == (32, 32), f"{name} must be 32 by 32")
        cursor_names.add(name)
    voice_names = set()
    for name in assets("voice", cue_key):
        validate_wav(folder / name, media(name, ".wav", 300 * 1024))
        voice_names.add(name)
    require(len(voice_names) <= 16, "too many voice files")
    art = sprite_names | cursor_names
    require(art or voice_names, "include at least one usable asset")
    require(len({name.lower() for name in files}) == len(files), "filenames must be distinct on Windows")
    bundle = json_bytes({"format": 1, "files": [
        [name, base64.b64encode(data).decode()] for name, data in sorted(files.items())
    ]})
    require(len(bundle) <= BUNDLE_LIMIT, "pack archive exceeds 100 MiB")
    entry = {"id": pack_id, "name": manifest["name"], "author": identity["author"], "license": identity["license"],
             "media": (["appearance"] if art else []) + (["voice"] if voice_names else []), "archive": metadata(bundle)}
    outputs = {f"{pack_id}.pack.json": bundle}
    for key, supported, extension in [("art_preview", art, ".png"), ("voice_preview", voice_names, ".wav")]:
        if key in identity:
            name = identity[key]
            require(safe_name(name) and name in supported, f"{key} must name a referenced asset")
            outputs[pack_id + extension] = files[name]
            entry[key] = metadata(files[name])
    return entry, outputs


def build(target):
    packs = sorted((ROOT / "packs").iterdir())
    require(len(packs) <= 256, "catalog exceeds 256 packs")
    entries = []
    if target:
        (target / "packs").mkdir(parents=True)
    for folder in packs:
        try:
            entry, assets = read_pack(folder)
        except (ValueError, OSError, TypeError, AttributeError, struct.error) as error:
            raise SystemExit(f"{folder.name}: {error}") from error
        entries.append(entry)
        if target:
            for filename, data in assets.items():
                (target / "packs" / filename).write_bytes(data)
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("check")
    builder = actions.add_parser("build")
    builder.add_argument("output", type=Path)
    builder.add_argument("entries", type=Path)
    index = actions.add_parser("index")
    index.add_argument("entries", type=Path)
    index.add_argument("source_revision")
    index.add_argument("asset_revision")
    index.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.action == "check":
        print(f"Validated {len(build(None))} companion packs")
    elif args.action == "build":
        args.entries.write_bytes(json_bytes(build(args.output)))
    else:
        require(REVISION.fullmatch(args.source_revision) and REVISION.fullmatch(args.asset_revision), "invalid revision")
        data = json_bytes({"format": 1, "source_revision": args.source_revision,
                           "asset_revision": args.asset_revision, "packs": json.loads(args.entries.read_bytes())})
        require(len(data) <= 256 * 1024, "catalog exceeds 256 KiB")
        args.output.write_bytes(data)


if __name__ == "__main__":
    main()
