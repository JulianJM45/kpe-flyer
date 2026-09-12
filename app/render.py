import os
import shutil
import subprocess
import tempfile
from pathlib import Path

FLYER_DIR = Path(__file__).parent.parent / "flyer"


def _compile(
    stamm: str,
    plz: str,
    address: str,
    grouptime: str,
    sfm: str,
    mail: str,
    phone: str,
    wichtel: bool,
    two_weeks: bool,
    stammesmeisterin: bool,
    instagram: str,
    out_template: Path,
    dpi: int = 150,
) -> list[bytes]:
    """metadata.typ schreiben, mit Typst kompilieren und alle ausgegebenen
    Dateien als Bytes zurückgeben.

    `out_template` enthält bei PNG-Export die Seitenplatzhalter {p}/{0p}
    (z.B. `tmp_path / "page{p}.png"`). Bei PDF ist es eine normale Datei.
    """

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    metadata = (
        f'#let STAMM = "{esc(stamm)}"\n'
        f'#let PLZ = "{esc(plz)}"\n'
        f'#let ADDRESS = "{esc(address)}"\n'
        f'#let GROUPTIME = "{esc(grouptime)}"\n'
        f'#let SFM = "{esc(sfm)}"\n'
        f'#let MAIL = "{esc(mail)}"\n'
        f'#let PHONE = "{esc(phone)}"\n'
        f'#let INSTAGRAM = "{esc(instagram.strip())}"\n'
        f'#let WICHTEL = {"true" if wichtel else "false"}\n'
        f'#let twoWEEKS = {"true" if two_weeks else "false"}\n'
        f'#let STAMMESMEISTERIN = {"true" if stammesmeisterin else "false"}\n'
    )

    with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
        tmp_path = Path(tmp)
        flyer_tmp = tmp_path / "flyer"
        shutil.copytree(FLYER_DIR, flyer_tmp)
        (flyer_tmp / "metadata.typ").write_text(metadata, encoding="utf-8")

        # out_template ist RELATIV zu tmp_path (z.B. "page{p}.png"), damit die
        # Ausgabe im selben temp-Verzeichnis wie der Flyer landet.
        out_path = tmp_path / out_template
        # In Container-/Server-Umgebungen schlägt die Sandbox von Typst mit
        # „cannot preserve mount namespace" fehl. Wir schalten sie hier ab.
        env = os.environ.copy()
        env["TYPST__SANDBOX"] = "0"
        # Bei PDF ist kein --ppi nötig; bei PNG wird die Auflösung über --ppi
        # gesteuert. Die Option muss VOR den Positional-Argumenten stehen.
        dpi_flag = (["--ppi", str(dpi)] if out_path.name.endswith(".png") else [])
        result = subprocess.run(
            ["typst", "compile", "--font-path", str(flyer_tmp / "fonts"), *dpi_flag, "flyer.typ", str(out_path)],
            cwd=str(flyer_tmp),
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr or result.stdout or "Typst konnte die Ausgabe nicht rendern."
            )

        # Bei PDF existiert genau eine Datei; bei PNG eine pro Seite. Für den
        # Glob wird der PNG-Platzhalter {p}/{0p} durch '*' ersetzt, bei PDF
        # bleibt der echte Dateiname unverändert.
        glob_name = out_path.name.replace("{p}", "*").replace("{0p}", "*")
        files = sorted(tmp_path.glob(glob_name))
        if not files:
            raise RuntimeError("Typst hat keine Ausgabe erzeugt.")
        return [p.read_bytes() for p in files]


def render_pdf(
    stamm: str,
    plz: str,
    address: str,
    grouptime: str,
    sfm: str,
    mail: str,
    phone: str,
    wichtel: bool,
    two_weeks: bool,
    stammesmeisterin: bool,
    instagram: str = "",
) -> bytes:
    """Compile the KPE Wickelfalz flyer with typst and return raw PDF bytes."""

    return _compile(
        stamm, plz, address, grouptime, sfm, mail, phone,
        wichtel, two_weeks, stammesmeisterin, instagram,
        "flyer.pdf",
    )[0]


def render_png(
    stamm: str,
    plz: str,
    address: str,
    grouptime: str,
    sfm: str,
    mail: str,
    phone: str,
    wichtel: bool,
    two_weeks: bool,
    stammesmeisterin: bool,
    instagram: str = "",
    dpi: int = 150,
) -> list[bytes]:
    """Compile the flyer with typst and return raw PNG bytes for every page.

    Die PNGs eignen sich zur Einbettung im Browser (z.B. unter dem
    Vorschau-Button). `dpi` steuert die Ausgabeauflösung.
    """

    return _compile(
        stamm, plz, address, grouptime, sfm, mail, phone,
        wichtel, two_weeks, stammesmeisterin, instagram,
        "page{p}.png",
        dpi=dpi,
    )
