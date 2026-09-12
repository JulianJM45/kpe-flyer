from fasthtml.common import *

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
    function setBusy(btn, busy) {
        if (!btn) return;
        var orig = btn.getAttribute('data-label') || (btn.textContent = btn.textContent, btn.getAttribute('data-label'));
        if (orig === null || orig === undefined) btn.setAttribute('data-label', btn.textContent);
        btn.disabled = busy;
        btn.textContent = busy ? '⏳  Wird generiert …' : btn.getAttribute('data-label');
    }

    function makeHandler(action) {
        return function (event) {
            event.preventDefault();

            var form = document.getElementById('flyerForm');
            var previewBox = document.getElementById('previewBox');
            previewBox.style.display = 'none';
            previewBox.innerHTML = '';

            var btn = action === 'preview'
                ? document.getElementById('previewBtn')
                : document.getElementById('downloadBtn');
            setBusy(btn, true);

            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/' + action);
            xhr.send(new FormData(form));

            xhr.onload = function () {
                setBusy(btn, false);
                if (action === 'preview') {
                    previewBox.innerHTML = xhr.responseText;
                    previewBox.style.display = 'block';
                }
                // Download-Response: Browser startet den Download automatisch.
            };
            xhr.onerror = function () {
                setBusy(btn, false);
                previewBox.innerHTML = '<p style=\"color:#d02825;\">Fehler beim Generieren. Bitte erneut versuchen.</p>';
                previewBox.style.display = 'block';
            };
        };
    }

    document.getElementById('previewBtn').addEventListener('click', makeHandler('preview'));
    document.getElementById('downloadBtn').addEventListener('click', makeHandler('download'));
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
            cls="kpe-footer",
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
                    "Stammesfeldmeister",
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
            Button("👁️  Vorschau", type="submit", id="previewBtn"),
            Button("💾  Herunterladen", type="submit", id="downloadBtn"),
            cls="submit-section",
        ),
        Div(
            P(
                "Vorschau erscheint hier (PNG).",
                style="text-align:center; color:var(--kpe-text-muted); font-size:0.9rem;",
            ),
            id="previewBox",
            style="margin-bottom: 3rem; text-align: center; display: none;",
        ),
        _SUBMIT_JS,
        method="post",
        id="flyerForm",
    )

    return (
        Title("KPE Flyer Generator"),
        kpe_header(),
        Main(Div(form, cls="kpe-content"), cls="container"),
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
