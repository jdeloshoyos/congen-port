"""Minimal PNG (RGBA) helpers, pure Python over stdlib ``zlib``.

The runtime loads PNGs via pyglet; these functions are used by the one-time
asset converter and by tests that verify the conversion is lossless.  The
encoder emits 8-bit true-colour RGBA (colour type 6) with filter type 0 on
every scanline; the decoder mirrors that exact format.
"""

from __future__ import annotations

import struct
import zlib

_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def encode_rgba_png(width: int, height: int, rgba: bytes) -> bytes:
    """Encode top-down RGBA bytes as a true-colour PNG (colour type 6)."""
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    stride = width * 4
    raw = bytearray((stride + 1) * height)
    for y in range(height):
        row = y * (stride + 1)
        raw[row] = 0  # filter type: None
        raw[row + 1:row + 1 + stride] = rgba[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return _PNG_SIG + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")


def decode_rgba_png(data: bytes) -> tuple[int, int, bytes]:
    """Decode the encoder's output back to (width, height, top-down RGBA)."""
    if data[:8] != _PNG_SIG:
        raise ValueError("not a PNG")
    pos = 8
    width = height = 0
    idat = b""
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", chunk[:10])
            if depth != 8 or color != 6:
                raise ValueError("expected 8-bit RGBA PNG")
        elif tag == b"IDAT":
            idat += chunk
        elif tag == b"IEND":
            break
        pos += 12 + length
    raw = zlib.decompress(idat)
    stride = width * 4
    if len(raw) != (stride + 1) * height:
        raise ValueError("unexpected scanline length")
    rgba = bytearray(stride * height)
    for y in range(height):
        row = y * (stride + 1)
        if raw[row] != 0:
            raise ValueError("unsupported filter type")
        rgba[y * stride:(y + 1) * stride] = raw[row + 1:row + 1 + stride]
    return width, height, bytes(rgba)


def pcx_to_rgba(indices: bytes, palette: bytes) -> bytes:
    """Bake a PCX's palette into RGBA; index 0 becomes fully transparent."""
    out = bytearray(len(indices) * 4)
    for i, idx in enumerate(indices):
        if idx == 0:
            continue  # alpha stays 0
        p = idx * 3
        j = i * 4
        out[j] = palette[p]
        out[j + 1] = palette[p + 1]
        out[j + 2] = palette[p + 2]
        out[j + 3] = 255
    return bytes(out)


def silhouette_rgba(indices: bytes) -> bytes:
    """White mask of non-transparent pixels (for the after-image)."""
    out = bytearray(len(indices) * 4)
    for i, idx in enumerate(indices):
        if idx != 0:
            j = i * 4
            out[j] = out[j + 1] = out[j + 2] = 255
            out[j + 3] = 255
    return bytes(out)


def nearest_scale(rgba: bytes, sw: int, sh: int, dw: int, dh: int) -> bytes:
    """Nearest-neighbour resize of top-down RGBA bytes (crisp pixel art)."""
    out = bytearray(dw * dh * 4)
    for dy in range(dh):
        srow = (dy * sh // dh) * sw * 4
        drow = dy * dw * 4
        for dx in range(dw):
            si = srow + (dx * sw // dw) * 4
            di = drow + dx * 4
            out[di:di + 4] = rgba[si:si + 4]
    return bytes(out)


def encode_ico(images: list[tuple[int, int, bytes]]) -> bytes:
    """Wrap RGBA images into a Windows ``.ico`` container.

    ``images`` is a list of ``(width, height, top_down_rgba)``; each is embedded
    as a PNG (supported by Windows Vista and later).  Sizes of 256 are stored
    as 0 in the directory, per the ICO spec.
    """
    pngs = [encode_rgba_png(w, h, rgba) for (w, h, rgba) in images]
    count = len(pngs)
    header = struct.pack("<HHH", 0, 1, count)
    entries = bytearray()
    offset = 6 + 16 * count
    for (w, h, _rgba), png in zip(images, pngs):
        entries += struct.pack(
            "<BBBBHHII",
            0 if w >= 256 else w,
            0 if h >= 256 else h,
            0, 0, 1, 32, len(png), offset,
        )
        offset += len(png)
    return header + bytes(entries) + b"".join(pngs)
