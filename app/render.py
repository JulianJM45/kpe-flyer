import shutil
import subprocess
import tempfile
from pathlib import Path

FLYER_DIR = Path(__file__).parent.parent / "flyer"


def render_pdf(
    stamm: str,
    plz: str,
    address: str,
    grouptime: str,
    sfm: str,
    mail: str,
    phone: str,
    wichtel: bool,
    stammesmeisterin: bool,
) -> bytes:
    """Compile the KPE Wickelfalz flyer with typst and return raw PDF bytes."""

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
        f'#let WICHTEL = {"true" if wichtel else "false"}\n'
        f'#let STAMMESMEISTERIN = {"true" if stammesmeisterin else "false"}\n'
    )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        flyer_tmp = tmp_path / "flyer"
        shutil.copytree(FLYER_DIR, flyer_tmp)
        (flyer_tmp / "metadata.typ").write_text(metadata, encoding="utf-8")

        out_pdf = tmp_path / "flyer.pdf"
        result = subprocess.run(
            [
                "typst",
                "compile",
                "--font-path",
                str(flyer_tmp / "fonts"),
                "flyper.typ",
                str(out_pdf),
            ],
            cwd=str(flyer_tmp),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr or result.stdout or "Typst konnte das PDF nicht rendern."
            )

        return out_pdf.read_bytes()
