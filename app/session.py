import time
import uuid
from dataclasses import dataclass, field

_STEP_XY = 5.0   # mm per arrow click
_STEP_Z  = 0.05  # zoom step per click


@dataclass
class PhotoSlot:
    photo_bytes: bytes | None = None
    photo_ext: str = ".jpg"
    x: float = 0.0   # mm offset
    y: float = 0.0   # mm offset
    z: float = 1.0   # zoom multiplier


@dataclass
class Session:
    form_data: dict
    wolf:   PhotoSlot = field(default_factory=PhotoSlot)
    pfadi:  PhotoSlot = field(default_factory=PhotoSlot)
    raider: PhotoSlot = field(default_factory=lambda: PhotoSlot(x=62.0, y=2.0, z=1.1))
    svg_page1: bytes | None = None
    svg_page2: bytes | None = None
    svg_version: int = 0
    # base images for PIL compositing (page 1 with that slot blanked)
    page1_bases: dict[str, bytes] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


_store: dict[str, Session] = {}


def create_session(form_data: dict) -> str:
    _cleanup()
    sid = str(uuid.uuid4())
    _store[sid] = Session(form_data=dict(form_data))
    return sid


def get_session(sid: str) -> Session | None:
    return _store.get(sid)


def apply_move(slot: PhotoSlot, direction: str) -> None:
    match direction:
        case "up":       slot.y += _STEP_XY
        case "down":     slot.y -= _STEP_XY
        case "left":     slot.x += _STEP_XY
        case "right":    slot.x -= _STEP_XY
        case "zoom_in":  slot.z = round(slot.z + _STEP_Z, 4)
        case "zoom_out": slot.z = max(0.1, round(slot.z - _STEP_Z, 4))


def _cleanup() -> None:
    cutoff = time.time() - 3600
    stale = [k for k, v in _store.items() if v.created_at < cutoff]
    for k in stale:
        del _store[k]
