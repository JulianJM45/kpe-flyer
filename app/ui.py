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

# Externes Skript für Vorschau/Download + Live-Tausch der Photos.
# Die Foto-Chips liegen als Overlay über den Default-Fotos auf Seite 1 und tragen
# die Upload-/Zoom/Verschiebungs-Logik. Transform-Werte werden live an das
# Formular übergeben, damit sie bei Vorschau UND Download eingeflochten werden.
_SCRIPT = Script(src="/static/script.js")


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
        # Die Datei-Eingaben sind echte <input type="file">, nur per CSS versteckt:
        # So lässt sich die Dateiauswahl über den Overlay-Chip in der Vorschau
        # auslösen und das gewählte Foto wird mit dem nächsten POST gesendet.
        Input(type="file", name="woelflingo", id="woelflingo", accept="image/*",
              cls="photo-input-hidden"),
        Input(type="file", name="pfadi", id="pfadi", accept="image/*",
              cls="photo-input-hidden"),
        Input(type="file", name="raider", id="raider", accept="image/*",
              cls="photo-input-hidden"),
        # Versteckte Transform-Felder je Foto-Slot; Werte werden in der Vorschau
        # live verschoben/gezoomt und bei Vorschau UND Download mitgesendet.
        Input(type="hidden", name="tr-woelflingo-x", id="tr-woelflingo-x", value="0"),
        Input(type="hidden", name="tr-woelflingo-y", id="tr-woelflingo-y", value="0"),
        Input(type="hidden", name="tr-woelflingo-z", id="tr-woelflingo-z", value="1"),
        Input(type="hidden", name="tr-pfadi-x", id="tr-pfadi-x", value="0"),
        Input(type="hidden", name="tr-pfadi-y", id="tr-pfadi-y", value="0"),
        Input(type="hidden", name="tr-pfadi-z", id="tr-pfadi-z", value="1"),
        Input(type="hidden", name="tr-raider-x", id="tr-raider-x", value="0"),
        Input(type="hidden", name="tr-raider-y", id="tr-raider-y", value="0"),
        Input(type="hidden", name="tr-raider-z", id="tr-raider-z", value="1"),
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
        _SCRIPT,
        method="post",
        id="flyerForm",
    )

    return (
        Title("KPE Flyer Generator"),
        kpe_header(),
        Main(Div(form, cls="kpe-content"), cls="container",),
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
