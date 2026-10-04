import asyncio
import mimetypes
from pathlib import Path

from fasthtml.common import *
from starlette.datastructures import UploadFile
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from app.compose import COMPOSITORS
from app.render import (
    compile_pdf,
    render_page1,
    render_page1_without_slot,
    render_pages,
    render_pdf,
)
from app.session import PhotoSlot, apply_move, create_session, get_session
from app.ui import error_page, index_page, page1_preview, preview_page

app, rt = fast_app(pico=True, hdrs=(Style(Path("static/style.css").read_text()),))

print("🚀 FlyerMaker läuft auf http://localhost:8000", flush=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Main form ─────────────────────────────────────────────────────────────────

@rt("/", methods="get")
def index():
    return index_page()


# ── Legacy /render endpoint (direct PDF, no preview) ────────────────────────

@rt("/render", methods="post")
async def render(request: Request):
    d = await request.form()
    try:
        pdf = render_pdf(
            str(d.get("stamm", "")), str(d.get("plz", "")), str(d.get("address", "")),
            str(d.get("grouptime", "")), str(d.get("sfm", "")), str(d.get("mail", "")),
            str(d.get("phone", "")), "wichtel" in d, "two_weeks" in d,
            str(d.get("geschlecht", "weiblich")) == "weiblich",
            str(d.get("instagram", "")),
        )
    except Exception as exc:  # noqa: BLE001 – HTTP-Grenze: jeder Fehler wird als error_page zurückgegeben
        return error_page(str(exc))
    import unicodedata
    stamm = str(d.get("stamm", ""))
    normalized = unicodedata.normalize("NFKD", stamm).encode("ascii", "ignore").decode()
    name = "".join(c if c.isalnum() else "-" for c in normalized).strip("-") or "stamm"
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="kpe-flyer-{name}.pdf"'},
    )


# ── Preview: initial render ───────────────────────────────────────────────────

@rt("/preview", methods="post")
async def preview(request: Request):
    form = await request.form()
    sid = create_session(dict(form))
    sess = get_session(sid)
    assert sess is not None
    try:
        pages = await asyncio.to_thread(render_pages, sess)
        sess.svg_page1 = pages[0]
        sess.svg_page2 = pages[1] if len(pages) > 1 else b""
        sess.svg_version = 0
    except Exception as exc:  # noqa: BLE001 – HTTP-Grenze: jeder Fehler wird als error_page zurückgegeben
        return error_page(str(exc))
    return preview_page(sid, sess)


# ── SVG file serving ──────────────────────────────────────────────────────────

@rt("/svg/{sid}/{page}/{ver}", methods="get")
def svg(sid: str, page: int, ver: int):
    sess = get_session(sid)
    if not sess:
        return Response("Session nicht gefunden", status_code=404)
    svg = sess.svg_page1 if page == 1 else sess.svg_page2
    if not svg:
        return Response("SVG nicht vorhanden", status_code=404)
    return Response(svg, media_type="image/png", headers={"Cache-Control": "no-store"})


# ── Photo upload ──────────────────────────────────────────────────────────────

_PHOTO_SLOTS = {"wolf", "pfadi", "raider"}
_EXT_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@rt("/preview/{sid}/photo/{slot_name}", methods="post")
async def upload_photo(request: Request, sid: str, slot_name: str):
    if slot_name not in _PHOTO_SLOTS:
        return Response("Ungültiger Slot", status_code=400)
    sess = get_session(sid)
    if not sess:
        return Response("Session abgelaufen", status_code=404)

    form = await request.form()
    uploaded = form.get("photo")
    if not isinstance(uploaded, UploadFile):
        return page1_preview(sid, sess)

    photo_bytes = await uploaded.read()
    if not photo_bytes:
        return page1_preview(sid, sess)

    ct = uploaded.content_type or "image/jpeg"
    ext = _EXT_MAP.get(ct) or (mimetypes.guess_extension(ct) or ".jpg")

    slot: PhotoSlot = getattr(sess, slot_name)
    slot.photo_bytes = photo_bytes
    slot.photo_ext = ext
    slot.x = slot.y = 0.0  # reset position on new upload

    try:
        # Render page 1 WITH photo  +  blank base for PIL, concurrently
        page1_png, base_png = await asyncio.gather(
            asyncio.to_thread(render_page1, sess),
            asyncio.to_thread(render_page1_without_slot, sess, slot_name),
        )
        sess.svg_page1 = page1_png
        sess.page1_bases[slot_name] = base_png
        sess.svg_version += 1
    except Exception as exc:  # noqa: BLE001 – HTTP-Grenze: jeder Fehler wird als error_page zurückgegeben
        return error_page(str(exc))

    return page1_preview(sid, sess)


# ── Photo position / zoom ─────────────────────────────────────────────────────

@rt("/preview/{sid}/move/{slot_name}", methods="post")
async def move_photo(request: Request, sid: str, slot_name: str):
    if slot_name not in _PHOTO_SLOTS:
        return Response("Ungültiger Slot", status_code=400)
    sess = get_session(sid)
    if not sess:
        return Response("Session abgelaufen", status_code=404)

    form = await request.form()
    direction = str(form.get("dir", ""))
    slot: PhotoSlot = getattr(sess, slot_name)
    apply_move(slot, direction)

    base = sess.page1_bases.get(slot_name)
    if slot.photo_bytes and base:
        # Fast path: PIL composite, no typst (~50 ms)
        try:
            compositor = COMPOSITORS[slot_name]
            sess.svg_page1 = await asyncio.to_thread(
                compositor, base, slot.photo_bytes, slot.x, slot.y, slot.z
            )
            sess.svg_version += 1
        except Exception as exc:  # noqa: BLE001 – HTTP-Grenze: jeder Fehler wird als error_page zurückgegeben
            return error_page(str(exc))
    else:
        # Slow path: typst re-render (~480 ms)
        try:
            sess.svg_page1 = await asyncio.to_thread(render_page1, sess)
            sess.svg_version += 1
        except Exception as exc:  # noqa: BLE001 – HTTP-Grenze: jeder Fehler wird als error_page zurückgegeben
            return error_page(str(exc))

    return page1_preview(sid, sess)


# ── PDF download ──────────────────────────────────────────────────────────────

@rt("/download/{sid}", methods="post")
async def download(sid: str):
    sess = get_session(sid)
    if not sess:
        return error_page("Session abgelaufen. Bitte Vorschau neu laden.")
    try:
        pdf = compile_pdf(sess)
    except Exception as exc:  # noqa: BLE001 – HTTP-Grenze: jeder Fehler wird als error_page zurückgegeben
        return error_page(str(exc))

    stamm = sess.form_data.get("stamm", "stamm")
    import unicodedata
    normalized = unicodedata.normalize("NFKD", stamm).encode("ascii", "ignore").decode()
    name = "".join(c if c.isalnum() else "-" for c in normalized).strip("-") or "stamm"
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="kpe-flyer-{name}.pdf"'},
    )


serve()
