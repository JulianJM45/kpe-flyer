"""Tests für app.ui – HTML-Generierung ohne HTTP-Server."""
from app.ui import error_page, index_page


def _html(components) -> str:
    from fasthtml.common import to_xml
    if isinstance(components, tuple):
        return "".join(to_xml(c) for c in components)
    return to_xml(components)


def test_index_page_contains_form():
    html = _html(index_page())
    assert '<form' in html.lower()
    assert 'action="/render"' in html
    assert 'method="post"' in html


def test_index_page_has_all_fields():
    html = _html(index_page())
    for field in ("stamm", "plz", "address", "grouptime", "sfm", "mail", "phone"):
        assert f'name="{field}"' in html, f"Feld '{field}' fehlt im Formular"


def test_index_page_has_checkboxes():
    html = _html(index_page())
    assert 'name="wichtel"' in html
    assert 'name="two_weeks"' in html


def test_index_page_has_geschlecht_radio():
    html = _html(index_page())
    assert 'name="geschlecht"' in html
    assert 'value="weiblich"' in html


def test_index_page_has_submit_button():
    html = _html(index_page())
    assert 'type="submit"' in html


def test_index_page_title():
    html = _html(index_page())
    assert "KPE Flyer Generator" in html


def test_error_page_shows_message():
    html = _html(error_page("Typst ist abgestürzt"))
    assert "Typst ist abgestürzt" in html


def test_error_page_has_back_link():
    html = _html(error_page("irgendein Fehler"))
    assert 'href="/"' in html


def test_error_page_title():
    html = _html(error_page("x"))
    assert "Fehler" in html
