"""Integrationstests für die FastHTML-HTTP-API."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_index_returns_200(client):
    r = await client.get("/")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_index_content_type_html(client):
    r = await client.get("/")
    assert "text/html" in r.headers["content-type"]


@pytest.mark.asyncio
async def test_index_has_form(client):
    r = await client.get("/")
    assert b"<form" in r.content.lower()


@pytest.mark.asyncio
async def test_render_returns_pdf(client):
    r = await client.post(
        "/render",
        data={
            "stamm": "Teststamm",
            "plz": "12345 Teststadt",
            "address": "Musterstraße 1",
            "grouptime": "Freitag, 16.00-18.00 Uhr",
            "sfm": "Erika Muster",
            "mail": "test@example.com",
            "phone": "01234567890",
            "geschlecht": "weiblich",
        },
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_render_filename_uses_stamm(client):
    r = await client.post(
        "/render",
        data={
            "stamm": "München",
            "plz": "80000 München",
            "address": "Teststr. 1",
            "grouptime": "Montag",
            "sfm": "Test",
            "mail": "a@b.de",
            "phone": "0",
            "geschlecht": "weiblich",
        },
    )
    assert r.status_code == 200
    cd = r.headers.get("content-disposition", "")
    assert "M-nchen" in cd or "München" in cd or "nchen" in cd


@pytest.mark.asyncio
async def test_render_with_checkboxes(client):
    r = await client.post(
        "/render",
        data={
            "stamm": "Checkbox-Stamm",
            "plz": "11111 Test",
            "address": "Irgendwo 5",
            "grouptime": "Dienstag, 18-20 Uhr",
            "sfm": "Hans",
            "mail": "h@h.de",
            "phone": "0",
            "geschlecht": "männlich",
            "wichtel": "on",
            "two_weeks": "on",
            "instagram": "@test_stamm",
        },
    )
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_render_missing_fields_still_responds(client):
    """Auch bei leeren Pflichtfeldern gibt es eine Antwort (kein 500)."""
    r = await client.post("/render", data={})
    # Entweder PDF oder Fehlerseite – kein unbehandelter Server-Crash
    assert r.status_code in (200, 400, 422)


@pytest.mark.asyncio
async def test_static_files_served(client):
    r = await client.get("/static/style.css")
    assert r.status_code == 200
