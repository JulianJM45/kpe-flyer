from fasthtml.common import *

DEFAULTS = dict(
    stamm="München",
    plz="81739 München",
    address="Maximilian-Kolbe-Allee 18",
    grouptime="Freitag, 16.00-18.00 Uhr",
    sfm="Vroni Spörl",
    mail="stammstjakobus@gmail.com",
    phone="01577774472",
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


def fld(label, name, value="", type="text", placeholder=""):
    return Div(
        Label(label, fr=name),
        Input(type=type, name=name, id=name, value=value, placeholder=placeholder)
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
        card(
            "📍",
            "Stamm & Ort",
            Div(
                fld("Stamm", "stamm", DEFAULTS["stamm"]),
                fld("PLZ & Ort", "plz", DEFAULTS["plz"]),
                cls="field-grid",
            ),
            fld("Adresse", "address", DEFAULTS["address"]),
        ),
        card(
            "⏰",
            "Gruppenstunde",
            fld("Treffzeit", "grouptime", DEFAULTS["grouptime"]),
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
                fld("Name", "sfm", DEFAULTS["sfm"]),
                fld("Telefon", "phone", DEFAULTS["phone"], type="tel"),
                cls="field-grid",
            ),
            fld("E-Mail", "mail", DEFAULTS["mail"], type="email"),
            fld("Instagram (optional)", "instagram", "", type="text", placeholder="z.B. @kpe_muenchen"),
        ),
        card(
            "⚙️",
            "Optionen",
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
