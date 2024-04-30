from __future__ import annotations
from pathlib import Path
from flask.testing import FlaskClient
import pytest
from showmark.app import create_app

DATA_DIR = Path(__file__).with_name("data")
FILES_DIR = DATA_DIR / "files"


@pytest.fixture
def client(tmp_path: Path) -> FlaskClient:
    p = tmp_path / "unreadable.md"
    p.write_text("You can't see this!\n", encoding="utf-8")
    p.chmod(0)
    search_path = f"{FILES_DIR}:{tmp_path}"
    app = create_app(TESTING=True, SHOWMARK_SEARCH_PATH=search_path)
    return app.test_client()


def test_nop(client: FlaskClient) -> None:
    rv = client.get("/")
    assert rv.status_code == 200


def test_render_md(client: FlaskClient) -> None:
    rv = client.get("/", query_string={"file": "hello.md", "action": "View"})
    assert rv.status_code == 200
    assert "Hello, Markdown World!" in rv.text


def test_render_rst(client: FlaskClient) -> None:
    rv = client.get("/", query_string={"file": "hello.rst", "action": "View"})
    assert rv.status_code == 200
    assert "Hello, reStructuredText World!" in rv.text


def test_not_exists(client: FlaskClient) -> None:
    rv = client.get("/", query_string={"file": "dne.rst", "action": "View"})
    assert rv.status_code == 200
    assert "No such file" in rv.text


def test_bad_ext(client: FlaskClient) -> None:
    rv = client.get("/", query_string={"file": "hello.txt", "action": "View"})
    assert rv.status_code == 200
    assert "Unsupported/invalid markup file extension" in rv.text


def test_unreadable(client: FlaskClient) -> None:
    rv = client.get("/", query_string={"file": "unreadable.md", "action": "View"})
    assert rv.status_code == 200
    assert "Error Reading File" in rv.text


def test_not_utf8(client: FlaskClient) -> None:
    rv = client.get("/", query_string={"file": "not-utf8.rst", "action": "View"})
    assert rv.status_code == 200
    assert "Error Reading File" in rv.text


def test_invalid(client: FlaskClient) -> None:
    rv = client.get("/", query_string={"file": "invalid.rst", "action": "View"})
    assert rv.status_code == 200
    assert "Error Rendering File" in rv.text


def test_listall(client: FlaskClient) -> None:
    rv = client.get("/", query_string={"file": "hello.md", "action": "List All"})
    assert rv.status_code == 200
    assert "files/hello.md" in rv.text
