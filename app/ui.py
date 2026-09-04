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


def fld(label, name, value="", type="text"):
    return Div(Label(label, fr=name), Input(type=type, name=name, id=name, value=value))


def card(icon, title, *content):
    return Article(Header(H3(f"{icon}  {title}")), *content)


def index_page():
    form = Form(
        card("📍", "Stamm & Ort",
            Div(fld("Stamm", "stamm", DEFAULTS["stamm"]),
                fld("PLZ & Ort", "plz", DEFAULTS["plz"]), cls="field-grid"),
            fld("Adresse", "address", DEFAULTS["address"]),
        ),
        card("⏰", "Gruppenstunde",
            fld("Treffzeit", "grouptime", DEFAULTS["grouptime"]),
        ),
        card("👤", "Kontakt",
            Div(fld("Stammesmeisterin / -meister", "sfm", DEFAULTS["sfm"]),
                fld("Telefon", "phone", DEFAULTS["phone"], type="tel"), cls="field-grid"),
            fld("E-Mail", "mail", DEFAULTS["mail"], type="email"),
        ),
        card("⚙️", "Optionen",
            Label(
                Input(type="checkbox", name="wichtel", id="wichtel"),
                Div(Strong("Wichtel-Stufe anzeigen"),
                    Small("Zeigt den Wichtel-Bereich (ab 4 Jahren) im Flyer"),
                    cls="toggle-text"),
                cls="toggle-label",
            ),
        ),
        Div(Button("📄  PDF generieren", type="submit", id="submitBtn"), cls="submit-row"),
        _SUBMIT_JS,
        method="post", action="/render", id="flyerForm",
    )

    return (
        Title("KPE Flyer Generator"),
        Main(
            Div(Div("KPE", cls="badge"), H1("Flyer Generator"),
                P("Passe die Daten an und lade den personalisierten Flyer als PDF herunter."),
                cls="hero"),
            form,
            P("Powered by Typst · KPE-Flyer Template", cls="footnote"),
            cls="container",
        ),
    )


def error_page(msg: str):
    return (
        Title("Fehler – KPE Flyer Generator"),
        Main(
            Div(H3("⚠️ Fehler beim Rendern"), Pre(msg), cls="error-box"),
            A("← Zurück zum Formular", href="/"),
            cls="container",
        ),
    )
