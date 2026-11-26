"""Draw the original Desk Bot sprites as transparent 400 by 520 PNGs."""

import struct
import zlib
from pathlib import Path

WIDTH, HEIGHT = 400, 520


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def sprite(active):
    pixels = bytearray(WIDTH * HEIGHT * 4)

    def rect(x0, y0, x1, y1, color):
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            offset = (y * WIDTH + x0) * 4
            pixels[offset:offset + len(row)] = row

    ink = (37, 49, 73, 255)
    edge = (158, 186, 188, 255)
    soft = (228, 242, 232, 255)
    light = (255, 177, 104, 255) if active else (119, 232, 192, 255)
    rect(188, 76, 212, 145, ink)
    rect(176, 68, 224, 92, light)
    rect(56, 194, 90, 271, ink)
    rect(310, 194, 344, 271, ink)
    rect(82, 160, 318, 316, ink)
    rect(101, 140, 299, 336, ink)
    rect(100, 167, 300, 298, edge)
    rect(111, 154, 289, 320, soft)
    rect(122, 184, 278, 285, ink)
    rect(145, 216, 168, 240, light)
    rect(232, 216, 255, 240, light)
    rect(175, 253, 225, 261, light)
    rect(121, 331, 279, 409, ink)
    rect(139, 347, 261, 392, edge)
    rect(161, 362, 239, 372, light)
    rect(146, 407, 174, 437, ink)
    rect(226, 407, 254, 437, ink)
    rect(124, 431, 174, 447, ink)
    rect(226, 431, 276, 447, ink)
    raw = b"".join(b"\0" + pixels[y:y + WIDTH * 4] for y in range(0, len(pixels), WIDTH * 4))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    folder = Path(__file__).resolve().parents[1]
    (folder / "idle.png").write_bytes(sprite(False))
    (folder / "working.png").write_bytes(sprite(True))
