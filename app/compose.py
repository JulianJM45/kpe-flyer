"""
PIL-based photo compositing for page 1 preview.

Bypasses typst entirely for position/zoom updates. Uses a pre-rendered
"base" image (page 1 with that slot blanked) and composites the custom
photo on top with the correct polygon mask.

Coordinate convention  (matches typst's tiling offset semantics):
    img_origin_mm = (place_x - offset_x,  place_y - offset_y)

where offset_x/y are the slot's x/y fields (in mm) and place_* is the
absolute placement of the polygon on the A4 page (top-left = 0,0).

Preview PPI is defined in render.py  (PREVIEW_PPI = 96).
Page: 297 mm × 210 mm.
"""

from __future__ import annotations

import io

from PIL import Image, ImageDraw

PREVIEW_PPI: int = 96
MM: float = PREVIEW_PPI / 25.4  # pixels per mm
PAGE_W_MM: float = 297.0
PAGE_H_MM: float = 210.0
BG_COLOR: tuple[int, int, int] = (242, 247, 250)  # #F2F7FA


# ── helpers ───────────────────────────────────────────────────────────────────

def _px(mm: float) -> int:
    return round(mm * MM)


def _load(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def _to_png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def _composite(
    base: Image.Image,
    photo_bytes: bytes,
    poly_mm: list[tuple[float, float]],
    img_x_mm: float,
    img_y_mm: float,
    img_w_px: int | None = None,
    img_h_px: int | None = None,
) -> Image.Image:
    """
    Scale photo to (img_w_px, img_h_px) – supply exactly one, the other is
    derived from the aspect ratio – position it at (img_x_mm, img_y_mm) and
    paste it onto a copy of `base` masked by `poly_mm` (page mm coords).
    """
    page_w, page_h = base.size

    photo = _load(photo_bytes)
    ow, oh = photo.size
    if img_w_px is not None:
        img_h_px = round(oh * img_w_px / ow)
    else:
        assert img_h_px is not None
        img_w_px = round(ow * img_h_px / oh)

    photo = photo.resize((img_w_px, img_h_px), Image.LANCZOS)

    # Polygon mask in page pixels
    mask = Image.new("L", (page_w, page_h), 0)
    ImageDraw.Draw(mask).polygon(
        [(_px(x), _px(y)) for x, y in poly_mm], fill=255
    )

    # Full-page layer with photo at its position
    layer = Image.new("RGB", (page_w, page_h), BG_COLOR)
    ix, iy = _px(img_x_mm), _px(img_y_mm)

    src_x = max(0, -ix)
    src_y = max(0, -iy)
    dst_x = max(0, ix)
    dst_y = max(0, iy)
    w_copy = min(img_w_px - src_x, page_w - dst_x)
    h_copy = min(img_h_px - src_y, page_h - dst_y)
    if w_copy > 0 and h_copy > 0:
        layer.paste(
            photo.crop((src_x, src_y, src_x + w_copy, src_y + h_copy)),
            (dst_x, dst_y),
        )

    result = base.copy()
    result.paste(layer, (0, 0), mask)
    return result


# ── per-slot compositors ──────────────────────────────────────────────────────

def composite_wolf(
    base_png: bytes, photo: bytes, x: float, y: float, z: float
) -> bytes:
    """wolf slot: diamond polygon, width-scaled image."""
    w = 145.0  # 14.5 cm → mm
    place_x, place_y = 25.0, -23.0  # 2.5 cm, -2.3 cm → mm
    poly = [
        (place_x + w / 2, place_y + 0),
        (place_x + w,     place_y + w / 2),
        (place_x + w / 2, place_y + w),
        (place_x + 0,     place_y + w / 2),
    ]
    return _to_png(
        _composite(
            _load(base_png), photo, poly,
            img_x_mm=place_x - x,
            img_y_mm=place_y - y,
            img_w_px=_px(w * z),
        )
    )


def composite_pfadi(
    base_png: bytes, photo: bytes, x: float, y: float, z: float
) -> bytes:
    """pfadi slot: hexagon-like polygon, bottom-left placed, width-scaled."""
    w, h = 120.0, 84.0  # 12 cm, 8.4 cm → mm
    place_x = 99.0          # 9.9 cm
    place_y = PAGE_H_MM - h  # bottom+left: polygon top at 210-84=126 mm
    poly = [
        (place_x + 0,    place_y + 12.0),
        (place_x + 12.0, place_y + 0),
        (place_x + 90.0, place_y + 0),
        (place_x + w,    place_y + h / 2),
        (place_x + 90.0, place_y + h),
        (place_x + 0,    place_y + h),
    ]
    return _to_png(
        _composite(
            _load(base_png), photo, poly,
            img_x_mm=place_x - x,
            img_y_mm=place_y - y,
            img_w_px=_px(w * z),
        )
    )


def composite_raider(
    base_png: bytes, photo: bytes, x: float, y: float, z: float
) -> bytes:
    """raider slot: triangle at top-right, height-scaled image."""
    w, h = 130.0, 140.0  # 13 cm, 14 cm → mm
    place_x = PAGE_W_MM - w  # top+right: 297-130 = 167 mm
    place_y = 0.0
    poly = [
        (place_x + 0,    place_y + 75.0),
        (place_x + 75.0, place_y + 0),
        (place_x + w,    place_y + 0),
        (place_x + w,    place_y + h),
        (place_x + 48.0, place_y + h),
    ]
    return _to_png(
        _composite(
            _load(base_png), photo, poly,
            img_x_mm=place_x - x,
            img_y_mm=place_y - y,
            img_h_px=_px(h * z),  # raider scales by height
        )
    )


COMPOSITORS = {
    "wolf":   composite_wolf,
    "pfadi":  composite_pfadi,
    "raider": composite_raider,
}
