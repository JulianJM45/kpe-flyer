from pathlib import Path

from fasthtml.common import *
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from app.render import render_pdf, render_png
from app.ui import error_page, index_page

app, rt = fast_app(pico=True, hdrs=(Style(Path("static/style.css").read_text()),))

print("🚀 FlyerMaker läuft auf http://localhost:8000", flush=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


@rt("/")
def get():
    return index_page()


def _parse(d):
    """Formular-Felder in die render-Funktionen übergeben."""
    return (
        d.get("stamm", ""), d.get("plz", ""), d.get("address", ""),
        d.get("grouptime", ""), d.get("sfm", ""), d.get("mail", ""),
        d.get("phone", ""), "wichtel" in d, "two_weeks" in d,
        d.get("geschlecht", "weiblich") == "weiblich",
        d.get("instagram", ""),
    )


@rt("/preview")
async def post(request: Request):
    d = await request.form()
    try:
        pngs = render_png(*_parse(d))
    except Exception as exc:
        return error_page(str(exc))

    # PNGs inline auf der Seite einbetten (Base64), damit kein separater
    # Tab aufgeht und keine temporären Dateien im Spiel sind.
    parts = []
    for i, png in enumerate(pngs):
        import base64
        data = base64.b64encode(png).decode("ascii")
        parts.append(
            f'<img src="data:image/png;base64,{data}" alt="Flyer Seite {i + 1}" loading="lazy"/>'
        )
    return HTMLResponse("\n".join(parts))


@rt("/download")
async def post(request: Request):
    d = await request.form()
    try:
        pdf = render_pdf(*_parse(d))
    except Exception as exc:
        return error_page(str(exc))

    name = "".join(c if c.isalnum() else "-" for c in d.get("stamm", "")).strip("-") or "stamm"
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="kpe-flyer-{name}.pdf"'},
    )


serve()
