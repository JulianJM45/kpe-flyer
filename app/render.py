import os
import shutil
import subprocess
import tempfile
from pathlib import Path

FLYER_DIR = Path(__file__).parent.parent / "flyer"


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _metadata_text(
    *,
    stamm, plz, address, grouptime, sfm, mail, phone, instagram,
    wichtel, two_weeks, stammesmeisterin,
    photo_overrides: dict[str, str] | None = None,
    photo_transforms: dict[str, tuple[float, float, float]] | None = None,
) -> str:
    """Liefert den Inhalt von metadata.typ.

    `photo_overrides` mappt pictures-Schlessel ("woelflinge", "pfadi", "raider")
    auf den Dateinamen eines hochgeladenen Fotos. Leerer Wert => Originalfoto aus
    dem Template. Die Foto-Override-Zeilen stehen ganz oben, damit die statischen
    Werte unten (die denselben Namen haben könnten) nicht überschrieben werden.

    `photo_transforms` mappt denselben Schlüssen auf (x-mm, y-mm, zoom)
    für Verschiebung/Zoom des jeweiligen Fotos. Fehlt ein Wert => 0 mm / 1.0.
    """

    overrides = {
        "WOELFLINGE_PHOTO": (photo_overrides or {}).get("woelflingo", ""),
        "PFADI_PHOTO": (photo_overrides or {}).get("pfadi", ""),
        "RAADER_PHOTO": (photo_overrides or {}).get("raider", ""),
    }

    def _tf(slot: str) -> tuple[str, str, str]:
        v = (photo_transforms or {}).get(slot)
        if not v:
            return '0mm', '0mm', '1.0'
        x, y, z = v
        # X/Y als Länge mit-mm-Einheit (Wert wird von Typst geparst),
        # ZOOM als unskalierte Zahl ohne Anführungszeichen.
        return f'{x:g}mm', f'{y:g}mm', f'{z}'

    wx, wy, wz = _tf("woelflingo")
    px, py, pz = _tf("pfadi")
    rx, ry, rz = _tf("raider")

    return (
        f'#let WOELFLINGE_PHOTO = "{_esc(overrides["WOELFLINGE_PHOTO"])}"\n'
        f'#let PFADI_PHOTO = "{_esc(overrides["PFADI_PHOTO"])}"\n'
        f'#let RAADER_PHOTO = "{_esc(overrides["RAADER_PHOTO"])}"\n'
        f'#let WOELFLINGE_X = {_esc(wx)}\n'
        f'#let WOELFLINGE_Y = {_esc(wy)}\n'
        f'#let WOELFLINGE_ZOOM = {wz}\n'
        f'#let PFADI_X = {_esc(px)}\n'
        f'#let PFADI_Y = {_esc(py)}\n'
        f'#let PFADI_ZOOM = {pz}\n'
        f'#let RAIDER_X = {_esc(rx)}\n'
        f'#let RAIDER_Y = {_esc(ry)}\n'
        f'#let RAIDER_ZOOM = {rz}\n'
        "\n"
        f'#let STAMM = "{_esc(stamm)}"\n'
        f'#let PLZ = "{_esc(plz)}"\n'
        f'#let ADDRESS = "{_esc(address)}"\n'
        f'#let GROUPTIME = "{_esc(grouptime)}"\n'
        f'#let SFM = "{_esc(sfm)}"\n'
        f'#let MAIL = "{_esc(mail)}"\n'
        f'#let PHONE = "{_esc(phone)}"\n'
        f'#let INSTAGRAM = "{_esc(instagram.strip())}"\n'
        "#let WICHTEL = " + ("true" if wichtel else "false") + "\n"
        "#let twoWEEKS = " + ("true" if two_weeks else "false") + "\n"
        "#let STAMMESMEISTERIN = " + ("true" if stammesmeisterin else "false") + "\n"
    )


def _run_compile(
    tmp_path: Path,
    out_template: str,
    *,
    metadata_text: str,
    photo_overrides: dict[str, tuple[str, bytes]] | None = None,
    dpi: int = 150,
    pages: str | None = None,
) -> list[bytes]:
    """Mit Typst kompilieren und alle ausgegebenen Dateien als Bytes zurückgeben.

    `out_template` ist relativ zu tmp_path; bei PNG-Export enthält er die
    Seitenplatzhalter {p}/{0p}. `pages` begrenzt den Export optional auf eine
    Seite (Live-Tausch einzelner Photos).
    """

    flyer_tmp = tmp_path / "flyer"
    shutil.copytree(FLYER_DIR, flyer_tmp)
    (flyer_tmp / "metadata.typ").write_text(metadata_text, encoding="utf-8")

    # Hochgeladene Photos in das pictures-Verzeichnis kopieren.
    if photo_overrides:
        pic_dir = flyer_tmp / "pictures"
        for _key, (_filename, data) in photo_overrides.items():
            (pic_dir / _filename).write_bytes(data)

    out_path = tmp_path / out_template
    # In Container-/Server-Umgebungen schlägt die Sandbox von Typst mit
    # „cannot preserve mount namespace" fehl. Wir schalten sie hier ab.
    env = os.environ.copy()
    env["TYPST__SANDBOX"] = "0"
    # --ppi (PNG-Auflösung) und --pages stehen VOR den Positional-Argumenten.
    dpi_flag = (["--ppi", str(dpi)] if out_path.name.endswith(".png") else [])
    pages_flag = (["--pages", pages] if pages else [])
    result = subprocess.run(
        ["typst", "compile", "--font-path", str(flyer_tmp / "fonts"), *dpi_flag, *pages_flag, "flyer.typ", str(out_path)],
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

    # Bei PDF existiert genau eine Datei; bei PNG eine pro Seite. Für den Glob wird
    # der PNG-Platzhalter {p}/{0p} durch '*' ersetzt, bei PDF bleibt der echte Name.
    glob_name = out_path.name.replace("{p}", "*").replace("{0p}", "*")
    files = sorted(tmp_path.glob(glob_name))
    if not files:
        raise RuntimeError("Typst hat keine Ausgabe erzeugt.")
    return [p.read_bytes() for p in files]


def render_pdf(
    *,
    metadata_extra: dict,
    photo_overrides: dict[str, tuple[str, bytes]] | None = None,
    photo_transforms: dict[str, tuple[float, float, float]] | None = None,
) -> bytes:
    """Compile the KPE Wickelfalz flyer with typst and return raw PDF bytes."""

    with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
        tmp_path = Path(tmp)
        metadata_text = _metadata_text(
            **metadata_extra, photo_overrides=None, photo_transforms=photo_transforms
        )
        files = _run_compile(
            tmp_path, "flyer.pdf", metadata_text=metadata_text,
            photo_overrides=photo_overrides,
        )
    return files[0]


def render_png(
    *,
    metadata_extra: dict,
    photo_overrides: dict[str, tuple[str, bytes]] | None = None,
    photo_transforms: dict[str, tuple[float, float, float]] | None = None,
    dpi: int = 150,
    pages: str | None = None,
) -> list[bytes]:
    """Compile the flyer with typst and return raw PNG bytes.

    `pages` begrenzt den Export auf eine Seite (z.B. "1" für die Innenseite);
    ohne Wert werden beide Seiten exportiert.
    """

    with tempfile.TemporaryDirectory(dir=Path.home()) as tmp:
        out_template = "page{p}.png"
        # Namen der hochgeladenen Photos in die metadata-Override-Zeilen schreiben,
        # damit picture_or() diese statt der Originalfotos verwendet.
        override_names = {k: v[0] for k, v in (photo_overrides or {}).items()}
        metadata_text = _metadata_text(
            **metadata_extra,
            photo_overrides=override_names,
            photo_transforms=photo_transforms,
        )
        return _run_compile(
            Path(tmp),
            out_template,
            metadata_text=metadata_text,
            photo_overrides=photo_overrides,
            dpi=dpi,
            pages=pages,
        )
