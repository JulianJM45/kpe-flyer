import io
import shutil
import subprocess
import tempfile
from copy import deepcopy
from pathlib import Path

from PIL import Image as PILImage

from app.session import PhotoSlot, Session

PREVIEW_PPI = 96   # used for interactive page-1 renders
FULL_PPI    = 96   # same for page-2 (rendered once, cached)

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
        elif fmt == "png1":
            # page 1 only, preview PPI
            out_pattern = str(tmp_path / "out-{p}.png")
            extra_args = ["--ppi", str(PREVIEW_PPI), "--pages", "1"]
        else:  # "png"
            out_pattern = str(tmp_path / "out-{p}.png")
            extra_args = ["--ppi", str(FULL_PPI)]

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


def render_pages(sess: Session) -> list[bytes]:
    """Render all pages as PNG (called once per session at preview start)."""
    result = _run_typst(sess, "png")
    assert isinstance(result, list)
    return result


def render_page1(sess: Session) -> bytes:
    """Render only page 1 as PNG at PREVIEW_PPI (fast, ~0.5 s)."""
    result = _run_typst(sess, "png1")
    assert isinstance(result, list)
    return result[0]


def render_page1_without_slot(sess: Session, slot_name: str) -> bytes:
    """
    Render page 1 with `slot_name` replaced by a solid background-colour
    image. The result is used as the PIL compositing base for that slot.
    """
    blank = _make_blank_png()
    tmp = deepcopy(sess)
    slot: PhotoSlot = getattr(tmp, slot_name)
    slot.photo_bytes = blank
    slot.photo_ext = ".png"
    slot.x = slot.y = 0.0
    slot.z = 1.0
    return render_page1(tmp)


def _make_blank_png() -> bytes:
    """2×2 pixel PNG filled with the page background colour (#F2F7FA)."""
    img = PILImage.new("RGB", (2, 2), (242, 247, 250))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def compile_pdf(sess: Session) -> bytes:
    result = _run_typst(sess, "pdf")
    assert isinstance(result, bytes)
    return result


# ── back-compat shims (used by legacy /render route) ─────────────────────────

render_svgs = render_pages
render_page1_svg = render_page1


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
