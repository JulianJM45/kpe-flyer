"""Testet das Typt-Template flyer.typ selbst.

Diese Tests kompilieren flyer.typ direkt mit der Typst-CLI (wie die App im
Produktionsbetrieb) und prüfen, dass das Template ohne Fehler aufgeht und
sowohl PDF als auch PNG-Ausgabe erzeugt. Damit wird sichergestellt, dass
syntax-change am Flyer nicht stillschingend den Build kaputtmachen.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

# Projekt-Wurzel (tests/ liegt unter dem Repo-Wurzelverzeichnis).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FLYER_DIR = PROJECT_ROOT / "flyer"


def _valid_metadata() -> str:
    """Liefert einen metadata.typ-Inhalt, der alle vom Template erwarteten #let definiert.

    Deckt sich mit den Variablen, die in flyer.typ über `metadata.*` bzw.
    `twoWEEKS` referenziert werden. Kommt ein Name nicht vor, schlägt das
    Typst-Kompilat fehl -> der Test fängt genau solche Flüchtigkeiten ab.
    """
    return "\n".join(
        [
            '#let WOELFLINGE_PHOTO = ""',
            '#let PFADI_PHOTO = ""',
            '#let RAADER_PHOTO = ""',
            "#let WOELFLINGE_X = 0mm",
            "#let WOELFLINGE_Y = 0mm",
            "#let WOELFLINGE_ZOOM = 1.0",
            "#let PFADI_X = 0mm",
            "#let PFADI_Y = 0mm",
            "#let PFADI_ZOOM = 1.0",
            "#let RAIDER_X = 0mm",
            "#let RAIDER_Y = 0mm",
            "#let RAIDER_ZOOM = 1.0",
            '#let STAMM = "München"',
            '#let PLZ = "81739 München"',
            '#let ADDRESS = "Maximilian-Kolbe-Allee 18"',
            '#let GROUPTIME = "Freitag, 16.00-18.00 Uhr"',
            '#let SFM = "Vroni Spörl"',
            '#let MAIL = "stammstjakobus@gmail.com"',
            '#let PHONE = "01577774472"',
            '#let INSTAGRAM = "@muenchen"',
            "#let WICHTEL = true",
            "#let twoWEEKS = true",
            "#let STAMMESMEISTERIN = true",
        ]
    )


def _write_metadata(tmp: Path) -> None:
    (tmp / "metadata.typ").write_text(_valid_metadata(), encoding="utf-8")


@pytest.fixture()
def has_typst():
    """Marker fixture: skips the test when Typst is not installed."""
    if shutil.which("typst") is None:
        pytest.skip("`typst` nicht im PATH – nur mit installiertem Typst lauffähig")


def _compile(flyer_tmp: Path, out_name: str, pages: str | None = None) -> list[bytes]:
    """Kompiliert flyer.typ in flyer_tmp und liefert alle Ausgabe-Bytes."""
    import os
    env = os.environ.copy()
    env["TYPST__SANDBOX"] = "0"
    cmd = ["typst", "compile", "--font-path", str(flyer_tmp / "fonts"),
           "flyer.typ", out_name]
    # --pages steht VOR dem Input-Pfad, aber NACH dem Subcommand `compile`
    # (CLI-Konvention der App); ein Platz vor `compile` ist ungültig.
    if pages:
        cmd[2:2] = ["--pages", pages]
    res = subprocess.run(
        cmd, cwd=str(flyer_tmp), capture_output=True, text=True, timeout=60, env=env,
    )
    if res.returncode != 0:
        pytest.fail(
            f"Typst-Fehlerrat (Exit {res.returncode}):\n{res.stderr or res.stdout}"
        )
    files = sorted((flyer_tmp / out_name).parent.glob(
        out_name.replace("{p}", "*").replace("{0p}", "*")
    ))
    return [f.read_bytes() for f in files]


def test_flyer_typ_compiles_pdf(has_typst):
    """flyer.typ kompiliert zu einem vollständigen PDF."""
    with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
        flyer_tmp = Path(tmp) / "flyer"
        shutil.copytree(FLYER_DIR, flyer_tmp)
        _write_metadata(flyer_tmp)
        pdfs = _compile(flyer_tmp, "flyer.pdf")

    assert len(pdfs) == 1
    assert pdfs[0][:4] == b"%PDF", "Ausgabe ist kein PDF"


def test_flyer_typ_compiles_png_all_pages(has_typst):
    """flyer.typ rendert beide Seiten als PNG."""
    with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
        flyer_tmp = Path(tmp) / "flyer"
        shutil.copytree(FLYER_DIR, flyer_tmp)
        _write_metadata(flyer_tmp)
        pngs = _compile(flyer_tmp, "page{p}.png")

    assert len(pngs) == 2, f"erwartet 2 Seiten, erhalten {len(pngs)}"


def test_flyer_typ_compiles_single_page(has_typst):
    """Mit --pages auf Seite 1 rendert nur die Innenseite."""
    with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
        flyer_tmp = Path(tmp) / "flyer"
        shutil.copytree(FLYER_DIR, flyer_tmp)
        _write_metadata(flyer_tmp)
        pngs = _compile(flyer_tmp, "page{p}.png", pages="1")

    assert len(pngs) == 1, f"erwartet 1 Seite, erhalten {len(pngs)}"
