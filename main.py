from pathlib import Path

from fasthtml.common import *
from starlette.responses import Response

from app.render import render_pdf
from app.ui import error_page, index_page

app, rt = fast_app(pico=True, hdrs=(Style(Path("static/style.css").read_text()),))


@rt("/")
def get():
    return index_page()


@rt("/render")
async def post(request: Request):
    d = await request.form()
    try:
        pdf = render_pdf(
            d.get("stamm", ""), d.get("plz", ""), d.get("address", ""),
            d.get("grouptime", ""), d.get("sfm", ""), d.get("mail", ""),
            d.get("phone", ""), "wichtel" in d,
        )
    except Exception as exc:
        return error_page(str(exc))

    name = "".join(c if c.isalnum() else "-" for c in d.get("stamm", "")).strip("-") or "stamm"
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="kpe-flyer-{name}.pdf"'},
    )


serve()
