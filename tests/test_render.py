"""Testet die Rendering-Logik in app/render.py (ohne Server)."""

from __future__ import annotations

import base64

import pytest
from conftest import make_png

from app.render import (
    _metadata_text,
    _resolve_overrides,
    _thumbnail_bytes,
    render_pdf,
    render_png,
)

# Minimal gültige metadata, wie sie aus main._parse() hervorgeht.
META = dict(
    stamm="München",
    plz="81739 München",
    address="Maximilian-Kolbe-Allee 18",
    grouptime="Freitag, 16.00-18.00 Uhr",
    sfm="Vroni Spörl",
    mail="stammstjakobus@gmail.com",
    phone="01577774472",
    wichtel=False,
    two_weeks=False,
    stammesmeisterin=True,
    instagram="@muenchen",
)


@pytest.fixture(scope="module")
def has_typst():
    import shutil

    if shutil.which("typst") is None:
        pytest.skip("`typst` nicht im PATH – nur mit installiertem Typst lauffähig")


def test_thumbnail_bytes_roundtrip():
    """Ein gültiges PNG wird als JPEG-Thumb kodiert und bleibt decodierbar."""
    png = base64.b64decode(make_png(16, 16))
    thumb = _thumbnail_bytes(png)
    # Ergebnis ist ein JPEG -> Startbyte nach dem Header.
    assert thumb[:2] == b"\xff\xd8"


def test_thumbnail_bytes_passthrough_on_invalid():
    """Ungültige Bilddaten werden unverändert durchgereicht (kein Crash)."""
    data = b"not a picture at all"
    assert _thumbnail_bytes(data) == data


def test_resolve_overrides_low_quality_writes_thumbs(has_typst):
    """Bei low_quality=True werden Thumbs geschrieben, Namen enden auf _thumb.jpg."""
    import base64

    png = base64.b64decode(make_png())
    names, writes = _resolve_overrides(
        {"woelflingo": ("wolf.png", png)}, low_quality=True
    )
    assert names == {"woelflingo": "wolf_thumb.jpg"}
    stem, payload = writes["woelflingo"]
    assert stem == "wolf_thumb.jpg"
    assert payload[:2] == b"\xff\xd8"  # JPEG


def test_resolve_overrides_full_quality_keeps_original(has_typst):
    """Bei low_quality=False bleiben Originalname und -daten erhalten."""
    png = base64.b64decode(make_png())
    names, writes = _resolve_overrides(
        {"pfadi": ("wolf.png", png)}, low_quality=False
    )
    assert names == {"pfadi": "wolf.png"}
    stem, payload = writes["pfadi"]
    assert stem == "wolf.png"
    assert payload == png


def test_metadata_text_escapes_quotes():
    """Anführungszeichen in Werten werden für die metadata-Datei escaped."""
    text = _metadata_text(stamm='He"ller", Ort', plz="x", address="", grouptime="",
                          sfm="", mail="", phone="", instagram="", wichtel=True,
                          two_weeks=False, stammesmeisterin=False)
    assert 'STAMM = "He\\"ller\\", Ort"' in text
    assert "#let WICHTEL = true" in text
    assert "#let STAMMESMEISTERIN = false" in text


def test_render_png_all_pages(has_typst):
    """render_png rendert standardmäßig beide Seiten als PNG."""
    pngs = render_png(metadata_extra=META)
    assert len(pngs) == 2
    for p in pngs:
        assert p[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_png_single_page(has_typst):
    """render_png(pages="1") rendert nur die Innenseite."""
    pngs = render_png(metadata_extra=META, pages="1")
    assert len(pngs) == 1


def test_render_pdf_returns_valid_pdf(has_typst):
    """render_pdf liefert ein gültiges PDF zurück."""
    pdf = render_pdf(metadata_extra=META)
    assert pdf[:4] == b"%PDF"
    assert b"%%EOF" in pdf[-512:]


def test_render_png_with_photo_override_has_one_page(has_typst):
    """Ein Upload auf Seite 1 (pages="1") rendert genau eine Seite."""
    png = base64.b64decode(make_png(32, 32))
    pngs = render_png(metadata_extra=META, photo_overrides={"woelflingo": ("wolf.png", png)},
                      pages="1")
    assert len(pngs) == 1
