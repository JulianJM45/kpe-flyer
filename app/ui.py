from fasthtml.common import *

from app.session import PhotoSlot, Session

PLACEHOLDERS = dict(
    stamm="z.B. München",
    plz="z.B. 81739 München",
    address="z.B. Maximilian-Kolbe-Allee 18",
    grouptime="z.B. Freitag, 16.00-18.00 Uhr",
    sfm="z.B. Vroni Spörl",
    mail="z.B. stammstjakobus@gmail.com",
    phone="z.B. 01577774472",
)

_SUBMIT_JS = Script("""
    document.getElementById('flyerForm').addEventListener('submit', function (e) {
        var btn = document.getElementById('previewBtn');
        btn.disabled = true;
        btn.textContent = '⏳  Vorschau wird geladen …';
    });
""")


def fld(label, name, placeholder="", type="text", required=True):
    return Div(
        Label(label, fr=name),
        Input(type=type, name=name, id=name, placeholder=placeholder, required=required)
    )


def card(icon, title, *content):
    return Article(Header(H3(icon, " ", title)), Div(*content))


def kpe_header():
    return Header(
        Div(
            Div(
                Img(src="/static/logo.svg", alt="KPE Logo"),
                cls="kpe-logo-container",
            ),
            Div(
                H1("Flyer Generator"),
                P("Katholische Pfadfinderschaft Europas"),
                cls="kpe-title",
            ),
            cls="container",
        ),
        cls="kpe-header",
    )


def kpe_footer():
    return Footer(
        Div(
            Div(
                Img(src="/static/logo.svg", alt="KPE Logo", cls="kpe-footer-logo"),
                Div(
                    "Katholische Pfadfinderschaft Europas · ",
                    A("www.kpe.de", href="https://www.kpe.de", target="_blank"),
                ),
                Div("Powered by Typst"),
                cls="kpe-footer-content",
            ),
            cls="container",
        ),
        cls="kpe-footer",
    )


def index_page():
    form = Form(
        P(
            Small("Felder mit ", Strong("*", style="color: #d02825;"), " sind Pflichtfelder"),
            style="text-align: center; color: var(--kpe-text-muted); margin-bottom: 1.5rem;"
        ),
        card(
            "📍",
            "Stamm & Ort",
            Div(
                fld("Stamm", "stamm", PLACEHOLDERS["stamm"]),
                fld("PLZ & Ort", "plz", PLACEHOLDERS["plz"]),
                cls="field-grid",
            ),
            fld("Adresse", "address", PLACEHOLDERS["address"]),
        ),
        card(
            "⏰",
            "Gruppenstunde",
            fld("Treffzeit", "grouptime", PLACEHOLDERS["grouptime"]),
            Div(
                Label(
                    Input(type="checkbox", name="two_weeks", id="two_weeks"),
                    Div(
                        Strong("alle zwei Wochen"),
                        cls="toggle-text",
                    ),
                ),
                cls="toggle-row",
            ),
        ),
        card(
            " ",
            "Wichtel",
            Div(
                Label(
                    Input(type="checkbox", name="wichtel", id="wichtel"),
                    Div(
                        Strong("Wichtel-Stufe anzeigen"),
                        Small("Zeigt den Wichtel-Bereich (ab 4 Jahren) im Flyer an"),
                        cls="toggle-text",
                    ),
                ),
                cls="toggle-row",
            ),
        ),
        card(
            "👤",
            "Kontakt",
            Div(
                Label(
                    Input(type="radio", name="geschlecht", value="weiblich", checked=True, id="sm-w"),
                    "Stammesmeisterin",
                ),
                Label(
                    Input(type="radio", name="geschlecht", value="männlich", id="sm-m"),
                    "Stammesmeister",
                ),
                cls="radio-group",
            ),
            Div(
                fld("Name", "sfm", PLACEHOLDERS["sfm"]),
                fld("Telefon", "phone", PLACEHOLDERS["phone"], type="tel"),
                cls="field-grid",
            ),
            fld("E-Mail", "mail", PLACEHOLDERS["mail"], type="email"),
            fld("Instagram (optional)", "instagram", "z.B. @kpe_muenchen", type="text", required=False),
        ),
        Div(
            Button("👁  Vorschau", type="submit", id="previewBtn"),
            cls="submit-section",
        ),
        _SUBMIT_JS,
        method="post",
        action="/preview",
        id="flyerForm",
        enctype="multipart/form-data",
    )

    return (
        Title("KPE Flyer Generator"),
        kpe_header(),
        Main(Div(form, cls="kpe-content"), cls="container"),
        kpe_footer(),
    )


# ── Photo overlay controls ────────────────────────────────────────────────────

def _upload_form(sid: str, slot_name: str, label: str = "📷 Eigenes Foto"):
    return Form(
        Label(
            label,
            Input(
                type="file",
                name="photo",
                accept="image/*",
                style="display:none",
                onchange="this.form.requestSubmit()",
            ),
            cls="liquid-btn upload-label",
        ),
        hx_post=f"/preview/{sid}/photo/{slot_name}",
        hx_target="#page1-preview",
        hx_swap="outerHTML",
        hx_encoding="multipart/form-data",
    )


def _move_btn(sid: str, slot_name: str, direction: str, label: str, extra_cls: str = ""):
    return Button(
        label,
        hx_post=f"/preview/{sid}/move/{slot_name}",
        hx_vals=f'{{"dir":"{direction}"}}',
        hx_target="#page1-preview",
        hx_swap="outerHTML",
        cls=f"liquid-btn arrow-btn {extra_cls}".strip(),
    )


def _photo_controls(sid: str, slot_name: str, slot: PhotoSlot) -> tuple:
    if not slot.photo_bytes:
        return (_upload_form(sid, slot_name),)

    return (
        Div(
            _move_btn(sid, slot_name, "up", "↑"),
            Div(
                _move_btn(sid, slot_name, "left", "←"),
                _move_btn(sid, slot_name, "zoom_in", "＋"),
                _move_btn(sid, slot_name, "zoom_out", "－"),
                _move_btn(sid, slot_name, "right", "→"),
                cls="move-row",
            ),
            _move_btn(sid, slot_name, "down", "↓"),
            cls="move-grid",
        ),
        _upload_form(sid, slot_name, "🔄"),
    )


# Photo pin positions as % of page SVG (297mm × 210mm landscape)
# Derived from typst polygon placement coordinates.
_PINS = {
    "wolf":   ("33%", "24%"),   # diamond centre
    "pfadi":  ("51%", "78%"),   # left-hexagon centre
    "raider": ("82%", "34%"),   # top-right triangle centre
}


def _photo_overlay(sid: str, sess: Session):
    pins = []
    for slot_name, (left, top) in _PINS.items():
        slot: PhotoSlot = getattr(sess, slot_name)
        controls = _photo_controls(sid, slot_name, slot)
        has_photo = bool(slot.photo_bytes)
        pins.append(
            Div(
                *controls,
                cls=f"photo-pin {'has-photo' if has_photo else ''}",
                style=f"left:{left};top:{top};",
                id=f"pin-{slot_name}",
            )
        )
    return Div(*pins, cls="photo-overlay")


def page1_preview(sid: str, sess: Session):
    ver = sess.svg_version
    return Div(
        Img(
            src=f"/svg/{sid}/1/{ver}",
            cls="page-svg",
            alt="Innenseite Vorschau",
        ),
        _photo_overlay(sid, sess),
        id="page1-preview",
        cls="page-wrapper",
    )


# ── Full preview page ─────────────────────────────────────────────────────────

def preview_page(sid: str, sess: Session):
    return (
        Title("Vorschau – KPE Flyer Generator"),
        kpe_header(),
        Main(
            Div(
                Div(
                    A("← Formular bearbeiten", href="/", cls="back-link"),
                    cls="preview-topbar",
                ),
                H2("Seite 1 – Innenseite", cls="page-label"),
                P(
                    "Klicke auf 📷, um ein eigenes Foto einzusetzen. "
                    "Mit den Pfeilen kannst du Ausschnitt und Zoom anpassen.",
                    cls="preview-hint",
                ),
                page1_preview(sid, sess),
                H2("Seite 2 – Außenseite", cls="page-label"),
                Div(
                    Img(
                        src=f"/svg/{sid}/2/0",
                        cls="page-svg",
                        alt="Außenseite Vorschau",
                    ),
                    cls="page-wrapper page-wrapper--static",
                ),
                Script("""
                    document.addEventListener('DOMContentLoaded', function() {
                        var form = document.querySelector('.download-bar form');
                        if (form) form.addEventListener('submit', function() {
                            var btn = document.getElementById('downloadBtn');
                            if (!btn) return;
                            btn.disabled = true;
                            btn.textContent = '⏳ Wird generiert …';
                            setTimeout(function() {
                                btn.disabled = false;
                                btn.textContent = '⬇ PDF herunterladen';
                            }, 30000);
                        });
                    });
                """),
                Div(
                    Form(
                        Button(
                            "⬇  PDF herunterladen",
                            type="submit",
                            id="downloadBtn",
                            cls="download-btn",
                        ),
                        method="post",
                        action=f"/download/{sid}",
                    ),
                    cls="download-bar",
                ),
                cls="preview-content container",
            ),
        ),
        kpe_footer(),
    )


def error_page(msg: str):
    return (
        Title("Fehler – KPE Flyer Generator"),
        kpe_header(),
        Main(
            Div(
                Div(
                    H3("⚠️ Fehler beim Rendern"),
                    Pre(msg),
                    cls="error-box",
                ),
                Div(
                    A("← Zurück zum Formular", href="/"),
                    cls="error-actions",
                ),
                cls="error-container",
            ),
            cls="container",
        ),
        kpe_footer(),
    )
