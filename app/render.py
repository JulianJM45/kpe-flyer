import shutil
import subprocess
import tempfile
from pathlib import Path

from app.session import PhotoSlot, Session

FLYER_DIR = Path(__file__).parent.parent / "flyer"

_DEFAULT_PHOTOS = {
    "wolf":   "pictures/W\u00f6lflinge.jpeg",
    "pfadi":  "pictures/Pfadfinder.png",
    "raider": "pictures/Raider2.jpg",
}


def _fmt(v: float) -> str:
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _build_metadata(sess: Session) -> str:
    d = sess.form_data

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    def photo_path(slot: PhotoSlot, name: str) -> str:
        return f"custom/{name}{slot.photo_ext}" if slot.photo_bytes else _DEFAULT_PHOTOS[name]

    return (
        f'#let STAMM = "{esc(d.get("stamm", ""))}"\n'
        f'#let PLZ = "{esc(d.get("plz", ""))}"\n'
        f'#let ADDRESS = "{esc(d.get("address", ""))}"\n'
        f'#let GROUPTIME = "{esc(d.get("grouptime", ""))}"\n'
        f'#let SFM = "{esc(d.get("sfm", ""))}"\n'
        f'#let MAIL = "{esc(d.get("mail", ""))}"\n'
        f'#let PHONE = "{esc(d.get("phone", ""))}"\n'
        f'#let INSTAGRAM = "{esc(d.get("instagram", "").strip())}"\n'
        f'#let WICHTEL = {"true" if "wichtel" in d else "false"}\n'
        f'#let twoWEEKS = {"true" if "two_weeks" in d else "false"}\n'
        f'#let STAMMESMEISTERIN = {"true" if d.get("geschlecht", "weiblich") == "weiblich" else "false"}\n'
        f'#let WOLF_PHOTO = "{photo_path(sess.wolf, "wolf")}"\n'
        f'#let WOLF_X = {_fmt(sess.wolf.x)}mm\n'
        f'#let WOLF_Y = {_fmt(sess.wolf.y)}mm\n'
        f'#let WOLF_Z = {_fmt(sess.wolf.z)}\n'
        f'#let PFADI_PHOTO = "{photo_path(sess.pfadi, "pfadi")}"\n'
        f'#let PFX = {_fmt(sess.pfadi.x)}mm\n'
        f'#let PFY = {_fmt(sess.pfadi.y)}mm\n'
        f'#let PFZ = {_fmt(sess.pfadi.z)}\n'
        f'#let RAIDER_PHOTO = "{photo_path(sess.raider, "raider")}"\n'
        f'#let RAX = {_fmt(sess.raider.x)}mm\n'
        f'#let RAY = {_fmt(sess.raider.y)}mm\n'
        f'#let RAZ = {_fmt(sess.raider.z)}\n'
    )


def _run_typst(sess: Session, fmt: str) -> list[bytes] | bytes:
    metadata = _build_metadata(sess)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        flyer_tmp = tmp_path / "flyer"
        shutil.copytree(FLYER_DIR, flyer_tmp)
        (flyer_tmp / "metadata.typ").write_text(metadata, encoding="utf-8")

        custom_dir = flyer_tmp / "custom"
        custom_dir.mkdir()
        for slot, name in [(sess.wolf, "wolf"), (sess.pfadi, "pfadi"), (sess.raider, "raider")]:
            if slot.photo_bytes:
                (custom_dir / f"{name}{slot.photo_ext}").write_bytes(slot.photo_bytes)

        if fmt == "pdf":
            out_pattern = str(tmp_path / "out.pdf")
            extra_args: list[str] = []
        else:
            out_pattern = str(tmp_path / "out-{p}.png")
            extra_args = ["--ppi", "144"]

        result = subprocess.run(
            ["typst", "compile", "--font-path", str(flyer_tmp / "fonts"), *extra_args, "flyer.typ", out_pattern],
            cwd=str(flyer_tmp),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "Typst konnte das Dokument nicht rendern.")

        if fmt == "pdf":
            return (tmp_path / "out.pdf").read_bytes()

        pages: list[bytes] = []
        for i in range(1, 20):
            f = tmp_path / f"out-{i}.png"
            if not f.exists():
                break
            pages.append(f.read_bytes())
        return pages


def render_svgs(sess: Session) -> list[bytes]:
    result = _run_typst(sess, "svg")
    assert isinstance(result, list)
    return result


def render_page1_svg(sess: Session) -> bytes:
    return render_svgs(sess)[0]


def compile_pdf(sess: Session) -> bytes:
    result = _run_typst(sess, "pdf")
    assert isinstance(result, bytes)
    return result


# ── Legacy helper (keep old route working) ───────────────────────────────────

def render_pdf(
    stamm: str, plz: str, address: str, grouptime: str,
    sfm: str, mail: str, phone: str,
    wichtel: bool, two_weeks: bool, stammesmeisterin: bool,
    instagram: str = "",
) -> bytes:
    from app.session import Session
    fd: dict = {
        "stamm": stamm, "plz": plz, "address": address, "grouptime": grouptime,
        "sfm": sfm, "mail": mail, "phone": phone, "instagram": instagram,
        "geschlecht": "weiblich" if stammesmeisterin else "männlich",
    }
    if wichtel:
        fd["wichtel"] = "on"
    if two_weeks:
        fd["two_weeks"] = "on"
    sess = Session(form_data=fd)
    return compile_pdf(sess)
