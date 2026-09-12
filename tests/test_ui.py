"""Integrationstests für die FastHTML-App (Server-Simulation über TestClient).

Testen die Endpunkte /, /preview und /download so, wie ein Browser sie erreichen
würde – inkl. Multipart-Foto-Uploads. Benutzt den TestClient aus httpx, ohne
einen echten Server zu starten.
"""

from __future__ import annotations

import base64

import pytest
from conftest import make_png
from starlette.testclient import TestClient

# Import löst die App-Erzeugung in main.py aus (serve() nur unter __main__).
from main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def has_typst():
    import shutil

    if shutil.which("typst") is None:
        pytest.skip("`typst` nicht im PATH – nur mit installiertem Typst lauffähig")


DATA = {
    "stamm": "München",
    "plz": "81739 München",
    "address": "Maximilian-Kolbe-Allee 18",
    "grouptime": "Freitag, 16.00-18.00 Uhr",
    "sfm": "Vroni Spörl",
    "mail": "stammstjakobus@gmail.com",
    "phone": "01577774472",
    "geschlecht": "weiblich",
    "instagram": "@muenchen",
}


# --- Startseite -------------------------------------------------------------

def test_index_returns_200():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Flyer Generator" in resp.text
    # Formularfelder müssen vorhanden sein (diese existieren im UI).
    for name in ("stamm", "plz", "grouptime", "sfm"):
        assert f'name="{name}"' in resp.text


def test_index_has_photo_inputs():
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'name="woelflingo"' in resp.text
    assert 'name="pfadi"' in resp.text
    assert 'name="raider"' in resp.text


# --- Vorschau (Preview) -----------------------------------------------------

def test_preview_no_upload_both_pages(has_typst):
    """Vorschau ohne Upload rendert beide Seiten als PNG."""
    resp = client.post("/preview", data=DATA)
    assert resp.status_code == 200
    body = resp.content
    # Zwei Seiten => zwei inline-PNG-Daten.
    assert body.count(b"data:image/png;base64,") == 2


def test_preview_single_page_upload(has_typst):
    """Vorschau mit Foto-Upload auf Seite 1 rendert nur die Innenseite."""
    png = base64.b64decode(make_png(32, 32))
    files = {"woelflingo": ("test_woelf.png", png, "image/png")}
    payload = dict(DATA); payload["pages"] = "1"
    resp = client.post("/preview", data=payload, files=files)
    assert resp.status_code == 200
    assert resp.content.count(b"data:image/png;base64,") == 1


def test_preview_invalid_metadata_returns_error(has_typst):
    """Ein ungültiges Foto (keines) löst beim Rendern eine Fehlerseite aus."""
    payload = dict(DATA)
    files = {"pfadi": ("broken.png", b"not a real image", "image/png")}
    resp = client.post("/preview", data=payload, files=files)
    assert resp.status_code == 200  # error_page ist ein gültiges HTML-Page
    assert "Fehler" in resp.text


# --- Download ---------------------------------------------------------------

def test_download_returns_pdf(has_typst):
    """Der Download liefert ein gültiges PDF mit Download-Header."""
    resp = client.post("/download", data=DATA)
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"
    assert "application/pdf" in resp.headers["content-type"]
    assert resp.headers["content-disposition"].startswith("attachment")
    assert "kpe-flyer-" in resp.headers["content-disposition"]


def test_download_with_photo_override(has_typst):
    """Download mit Foto-Upload rendert PDF ohne Fehler."""
    png = base64.b64decode(make_png(32, 32))
    files = {"pfadi": ("pfadi.png", png, "image/png")}
    resp = client.post("/download", data=DATA, files=files)
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"


def test_download_filename_sanitized(has_typst):
    """Der Dateiname wird aus dem Stamm-Namen abgeleitet und ASCII-sicher gemacht."""
    payload = dict(DATA); payload["stamm"] = "Mün/chen 2024"
    resp = client.post("/download", data=payload)
    assert resp.status_code == 200
    # Non-ASCII-Zeinen (Umlaut) werden verworfen, der Rest bleibt ASCII-sicher.
    assert "kpe-flyer-Mn-chen-2024.pdf" in resp.headers["content-disposition"]


def test_download_header_is_ascii_safe(has_typst):
    """Der Content-Disposition-Header ist UTF-8-decodierbar (kein Umlaut-Crash)."""
    payload = dict(DATA); payload["stamm"] = "München/Ätz 2024"
    resp = client.post("/download", data=payload)
    assert resp.status_code == 200
    # Löst die Testsuite nicht mehr mit UnicodeDecodeError ab.
    _ = resp.headers["content-disposition"]
