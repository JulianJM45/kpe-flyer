import html
import json
from pathlib import Path

from fasthtml.common import *
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from app.render import render_pdf, render_png
from app.ui import error_page, index_page

PHOTO_SLOTS = ("woelflingo", "pfadi", "raider")

app, rt = fast_app(pico=True, hdrs=(Style(Path("static/style.css").read_text()),))

print("🚀 FlyerMaker läuft auf http://localhost:8000", flush=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


def _parse(d):
    """Formular-Felder in die render-Funktionen übergeben."""
    return dict(
        stamm=d.get("stamm", ""), plz=d.get("plz", ""), address=d.get("address", ""),
        grouptime=d.get("grouptime", ""), sfm=d.get("sfm", ""), mail=d.get("mail", ""),
        phone=d.get("phone", ""), wichtel="wichtel" in d, two_weeks="two_weeks" in d,
        stammesmeisterin=d.get("geschlecht", "weiblich") == "weiblich",
        instagram=d.get("instagram", ""),
    )


def _photo_overrides(d):
    """Hochgeladene Photos (als UploadFile) in den Override-Zuordnungen sammeln."""
    overrides = {}
    for slot in PHOTO_SLOTS:
        val = d.get(slot)
        if isinstance(val, UploadFile) and val.filename:
            overrides[slot] = (val.filename, val.file.read())
    return overrides or None


def _photo_transforms(d):
    """Live Zoom/Verschiebung je Foto-Slot aus dem Formular sammeln.

    Die Felder heißen tr-{slot}-x/-y/-z (Slot = Formular-ID, z.B. woelflingo) und
    werden vom Frontend gesetzt, wenn ein Bild in der Vorschau verschoben oder
    gezoomt wird. Der Schlüssel muss dem Slot-Namen entsprechen, den auch
    render.py (_metadata_text -> _tf) erwartet.
    """
    transforms = {}
    for slot in PHOTO_SLOTS:
        x = d.get(f"tr-{slot}-x")
        y = d.get(f"tr-{slot}-y")
        z = d.get(f"tr-{slot}-z")
        if any(v not in (None, "") for v in (x, y, z)):
            transforms[slot] = (float(x or 0), float(y or 0), float(z or 1))
    return transforms or None


# Positionen der drei Fotos auf Seite 1 (Innenseite, 297 x 210 mm), abgeleitet
# von den Platzierungen in flyer/flyer.typ. Werte sind als Prozente der
# Seitenbreite/-höhe angegeben und werden im Frontend als Overlay über das
# jeweilige Foto gelegt.
def page1_slot_boxes():
    W, H = 297.0, 210.0
    boxes = [
        # Wölflinge: Diamant @ dx=25mm dy=-23mm, 145 x 145 mm
        {"name": "woelflingo", "cx": 97.5 / W * 100, "cy": 100 / H * 100,
         "w": 145.0 / W * 100, "h": 145.0 / H * 100},
        # Pfadfinder: unten links @ dx=99mm, 120 x 84 mm
        {"name": "pfadi", "cx": (99 + 60) / W * 100, "cy": 210 / H * 100,
         "w": 120.0 / W * 100, "h": 84.0 / H * 100},
        # Raider: oben rechts verankert, 130 x 140 mm
        {"name": "raider", "cx": 260 / W * 100, "cy": 140 / H * 100,
         "w": 130.0 / W * 100, "h": 140.0 / H * 100},
    ]
    for b in boxes:
        b.update({k: round(v, 2) for k, v in b.items() if k != "name"})
    return boxes


def _render_images(pngs, pages):
    """PNG-Bytes als <div class="page-wrap"> umrandete inline <img> zurückgeben.

    Bei Seite 1 wird die Geometrie der drei Fotos als JSON in data-slots
    gespeichert, damit das Frontend über jedes Foto ein Overlay legen kann.
    """
    parts = []
    for i, png in enumerate(pngs):
        page = str(pages) if pages else str(i + 1)
        data = base64.b64encode(png).decode("ascii")
        slots_attr = ""
        if page == "1":
            attr = html.escape(json.dumps(page1_slot_boxes(), separators=(",", ":")))
            slots_attr = f' data-slots="{attr}"'
        parts.append(
            f'<div class="page-wrap" data-page="{page}"{slots_attr}>'
            f"<img src=\"data:image/png;base64,{data}\" data-page=\"{page}\" loading=\"lazy\"/></div>"
        )
    return "\n".join(parts)


@rt("/")
def get():
    return index_page()


@rt("/preview")
async def post(request: Request):
    d = await request.form()
    try:
        meta = _parse(d)
        overrides = _photo_overrides(d)
        transforms = _photo_transforms(d)
        pages = d.get("pages") or None  # "1" => nur Innenseite (Live-Tausch), None => beide Seiten
        pngs = render_png(metadata_extra=meta, photo_overrides=overrides,
                          photo_transforms=transforms, pages=pages)
    except Exception as exc:
        return error_page(str(exc))

    return HTMLResponse(_render_images(pngs, pages))


@rt("/download")
async def post(request: Request):
    d = await request.form()
    try:
        meta = _parse(d)
        overrides = _photo_overrides(d)
        transforms = _photo_transforms(d)
        pdf = render_pdf(metadata_extra=meta, photo_overrides=overrides,
                         photo_transforms=transforms)
    except Exception as exc:
        return error_page(str(exc))

    name = "".join(c if c.isalnum() else "-" for c in d.get("stamm", "")).strip("-") or "stamm"
    # Nicht-ASCII-Zeichen (z.B. Umlaute) aus dem Dateiname entfernen, damit der
    # Content-Disposition-Header niemals nicht-utf-8 Bytes enthält.
    safe_name = "".join(c for c in name if c.isascii()) or "stamm"
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="kpe-flyer-{safe_name}.pdf"'},
    )


if __name__ == "__main__":
    serve()
