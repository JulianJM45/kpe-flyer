"""Gemeinsame Testhilfen für die KPE Flyer-Testsuite."""

from __future__ import annotations

import base64
import io
import struct
import zlib


def make_png(width: int = 8, height: int = 8) -> bytes:
    """Erzeugt minimal gültige PNG-Daten (schwarz), ohne externe Bibliothek.

    Genug real für den Renderer (decodiert durch Pillow / Typst) und schnell
    genug, um sie in beliebiger Menge im Test zu verwenden.
    """
    raw = bytearray()
    row = b"\x00" + b"\x00" * (width * 3)
    for _ in range(height):
        raw += row

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(
        ">IIBBBBB", width, height, 8, 2, 0, 0, 0  # 8-bit RGB
    )
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    return base64.b64encode(png).decode("ascii")
