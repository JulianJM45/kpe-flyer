# KPE Flyer Generator

Web-App zum Anpassen und Rendern des KPE Wickelfalz-Flyers als PDF.

## Voraussetzungen (lokal)

- Python ≥ 3.12 & [uv](https://docs.astral.sh/uv/)
- [Typst](https://typst.app/) (`typst --version` → 0.15.x)

## Lokal starten

```bash
# Abhängigkeiten installieren
uv sync

# App starten (http://localhost:5001)
python -m app.main
```

## Mit Docker starten

```bash
docker compose up --build
```

Die App läuft dann auf **http://localhost:5001**.

## Funktionsweise

1. Felder im Browser ausfüllen (Stamm, Adresse, Kontakt, …)
2. „PDF generieren" klicken
3. Typst rendert den Flyer und der Browser lädt das PDF automatisch herunter

## Dateistruktur

```
kpe-flyer/
├── app/
│   ├── main.py        # FastHTML-App (Routen, UI)
│   └── render.py      # Typst-Rendering-Logik
├── flyer/
│   ├── flyper.typ     # Typst-Template
│   ├── metadata.typ   # Default-Werte (werden zur Laufzeit überschrieben)
│   ├── fonts/         # League Spartan
│   └── pictures/      # Bilder & Icons
├── Dockerfile
└── docker-compose.yml
```
