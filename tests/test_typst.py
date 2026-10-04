"""Tests für den Typst-Render-Schritt – standalone und via Python."""
import shutil
import subprocess
import tempfile
from pathlib import Path

FLYER_DIR = Path(__file__).parent.parent / "flyer"


def _compile(metadata_content: str, timeout: int = 30) -> bytes:
    """Schreibt metadata.typ, ruft typst compile auf und gibt PDF-Bytes zurück."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        flyer_tmp = tmp_path / "flyer"
        shutil.copytree(FLYER_DIR, flyer_tmp)
        (flyer_tmp / "metadata.typ").write_text(metadata_content, encoding="utf-8")
        (flyer_tmp / "custom").mkdir(exist_ok=True)

        out_pdf = tmp_path / "flyer.pdf"
        result = subprocess.run(
            [
                "typst",
                "compile",
                "--font-path",
                str(flyer_tmp / "fonts"),
                "flyer.typ",
                str(out_pdf),
            ],
            cwd=str(flyer_tmp),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        assert result.returncode == 0, (
            f"typst compile fehlgeschlagen:\n{result.stderr or result.stdout}"
        )
        return out_pdf.read_bytes()


DEFAULT_META = """\
#let STAMM = "Teststadt"
#let PLZ = "12345 Teststadt"
#let ADDRESS = "Musterstraße 1"
#let GROUPTIME = "Samstag, 14.00-16.00 Uhr"
#let SFM = "Max Mustermann"
#let MAIL = "test@example.com"
#let PHONE = "0123456789"
#let INSTAGRAM = ""
#let WICHTEL = false
#let twoWEEKS = false
#let STAMMESMEISTERIN = false
#let WOLF_PHOTO = "pictures/Wölflinge.jpeg"
#let WOLF_X = 0mm
#let WOLF_Y = 0mm
#let WOLF_Z = 1
#let PFADI_PHOTO = "pictures/Pfadfinder.png"
#let PFX = 0mm
#let PFY = 0mm
#let PFZ = 1
#let RAIDER_PHOTO = "pictures/Raider2.jpg"
#let RAX = -62mm
#let RAY = 2mm
#let RAZ = 1.1
"""


def test_typst_available():
    """typst muss im PATH vorhanden sein."""
    assert shutil.which("typst") is not None, "typst nicht im PATH"


def test_standalone_default():
    """Flyer rendert mit Default-metadata.typ (Repo-Stand) fehlerfrei."""
    original_meta = (FLYER_DIR / "metadata.typ").read_text(encoding="utf-8")
    pdf = _compile(original_meta)
    assert pdf[:4] == b"%PDF", "Ausgabe ist kein PDF"


def test_standalone_minimal():
    """Flyer rendert mit minimalen Test-Daten."""
    pdf = _compile(DEFAULT_META)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 10_000, "PDF verdächtig klein"


def test_standalone_wichtel_true():
    """Wichtel-Flag = true muss fehlerlos rendern."""
    meta = DEFAULT_META.replace("#let WICHTEL = false", "#let WICHTEL = true")
    pdf = _compile(meta)
    assert pdf[:4] == b"%PDF"


def test_standalone_two_weeks_true():
    """twoWEEKS = true muss fehlerlos rendern."""
    meta = DEFAULT_META.replace("#let twoWEEKS = false", "#let twoWEEKS = true")
    pdf = _compile(meta)
    assert pdf[:4] == b"%PDF"


def test_standalone_stammesmeisterin():
    """STAMMESMEISTERIN = true (weibliche Form) muss fehlerlos rendern."""
    meta = DEFAULT_META.replace(
        "#let STAMMESMEISTERIN = false", "#let STAMMESMEISTERIN = true"
    )
    pdf = _compile(meta)
    assert pdf[:4] == b"%PDF"


def test_standalone_with_instagram():
    """Optionales Instagram-Feld befüllt muss fehlerlos rendern."""
    meta = DEFAULT_META.replace('#let INSTAGRAM = ""', '#let INSTAGRAM = "@kpe_test"')
    pdf = _compile(meta)
    assert pdf[:4] == b"%PDF"


def test_standalone_special_chars():
    """Sonderzeichen in Feldern dürfen den Typst-Compile nicht brechen."""
    meta = DEFAULT_META.replace(
        '#let STAMM = "Teststadt"',
        r'#let STAMM = "St. Ä-ö-ü-Test & Co."',
    )
    pdf = _compile(meta)
    assert pdf[:4] == b"%PDF"


def test_standalone_all_flags():
    """Alle Flags gleichzeitig aktiv."""
    meta = (
        DEFAULT_META
        .replace("#let WICHTEL = false", "#let WICHTEL = true")
        .replace("#let twoWEEKS = false", "#let twoWEEKS = true")
        .replace("#let STAMMESMEISTERIN = false", "#let STAMMESMEISTERIN = true")
        .replace('#let INSTAGRAM = ""', '#let INSTAGRAM = "@kpe_all"')
    )
    pdf = _compile(meta)
    assert pdf[:4] == b"%PDF"
