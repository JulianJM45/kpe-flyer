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
    document.getElementById('flyerForm').addEventListener('submit', function () {
        var btn = document.getElementById('submitBtn');
        btn.disabled = true;
        btn.textContent = '⏳  Wird generiert …';
        setTimeout(function () {
            btn.disabled = false;
            btn.textContent = '📄  PDF generieren';
        }, 20000);
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
            Button("📄  PDF generieren", type="submit", id="submitBtn"),
            cls="submit-section",
        ),
        _SUBMIT_JS,
        method="post",
        action="/render",
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
