# KPE Flyer Generator

Web-App zum Anpassen und Rendern des KPE Wickelfalz-Flyers als PDF.

**Design:** Inspiriert von [kpe.de](https://www.kpe.de) mit offiziellen KPE-Farben (Blau & Gold) und Lilien-Logo.

## Voraussetzungen (lokal)

- Python ≥ 3.12 & [uv](https://docs.astral.sh/uv/)
- [Typst](https://typst.app/) (`typst --version` → 0.15.x)

## Lokal starten

```bash
# Abhängigkeiten installieren
uv sync

# App starten (http://localhost:5001)
uv run main.py
```

## Mit Docker starten

```bash
docker compose up --build
```

Die App läuft dann auf **http://localhost:5001**.

## Funktionsweise

1. **Pflichtfelder** ausfüllen (markiert mit *)
   - Stamm & Ort (Stamm, PLZ, Adresse)
   - Gruppenstunde (Treffzeit)
   - Kontakt (Name, Telefon, E-Mail)
   - Optionen (Stammesmeister/in, Wichtel)
2. **Optional:** Instagram-Handle angeben
3. „PDF generieren“ klicken
4. Typst rendert den Flyer und der Browser lädt das PDF automatisch herunter

**Hinweis:** Alle Felder (außer Instagram) sind Pflichtfelder. Das Formular kann nicht ohne vollständige Angaben abgeschickt werden.

## Dateistruktur

```
kpe-flyer/
├── app/
│   ├── main.py        # FastHTML-App (Routen, UI)
│   └── render.py      # Typst-Rendering-Logik
├── flyer/
│   ├── flyer.typ     # Typst-Template
│   ├── metadata.typ   # Default-Werte (werden zur Laufzeit überschrieben)
│   ├── fonts/         # League Spartan
│   └── pictures/      # Bilder & Icons
├── Dockerfile
└── docker-compose.yml
```
