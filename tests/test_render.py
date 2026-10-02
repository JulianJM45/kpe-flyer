"""Tests für app.render.render_pdf (Python-Wrapper um typst)."""
import pytest

from app.render import render_pdf


DEFAULTS = dict(
    stamm="Teststadt",
    plz="12345 Teststadt",
    address="Musterstraße 1",
    grouptime="Samstag, 14.00-16.00 Uhr",
    sfm="Max Mustermann",
    mail="test@example.com",
    phone="0123456789",
    wichtel=False,
    two_weeks=False,
    stammesmeisterin=False,
    instagram="",
)


def _render(**overrides) -> bytes:
    kw = {**DEFAULTS, **overrides}
    return render_pdf(**kw)


def test_render_returns_pdf():
    pdf = _render()
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 10_000


def test_render_wichtel():
    pdf = _render(wichtel=True)
    assert pdf[:4] == b"%PDF"


def test_render_two_weeks():
    pdf = _render(two_weeks=True)
    assert pdf[:4] == b"%PDF"


def test_render_stammesmeisterin():
    pdf = _render(stammesmeisterin=True)
    assert pdf[:4] == b"%PDF"


def test_render_with_instagram():
    pdf = _render(instagram="@kpe_test")
    assert pdf[:4] == b"%PDF"


def test_render_all_flags():
    pdf = _render(wichtel=True, two_weeks=True, stammesmeisterin=True, instagram="@all")
    assert pdf[:4] == b"%PDF"


def test_render_escaping_backslash():
    """Backslashes im Input dürfen Typst nicht zum Absturz bringen."""
    pdf = _render(stamm=r"Test\Stamm")
    assert pdf[:4] == b"%PDF"


def test_render_escaping_quotes():
    """Anführungszeichen im Input dürfen Typst nicht brechen."""
    pdf = _render(sfm='Anna "die Beste" Müller')
    assert pdf[:4] == b"%PDF"


def test_render_empty_instagram_strips_whitespace():
    """Leerzeichen-only Instagram wird als leer behandelt – kein Absturz."""
    pdf = _render(instagram="   ")
    assert pdf[:4] == b"%PDF"
