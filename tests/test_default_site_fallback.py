""""""
# 3rd-Party Imports
import httpx
import pytest
from fastapi.testclient import TestClient

# Local Imports
from reverse_proxy_server.app import app
from reverse_proxy_server.api.utils import force_decodable_accept_encoding

_UPSTREAM_MARKER = b"UPSTREAM-MARKER-asdf123"


class _FakeUpstreamClient:
    """Stand-in for app.state.http_client that records every forwarded
    request instead of hitting the real ShotGrid server."""

    def __init__(self):
        self.calls = []

    async def request(self, *, method, url, headers=None, content=None):
        self.calls.append({"method": method, "url": url})
        return httpx.Response(
            status_code=200,
            content=_UPSTREAM_MARKER,
            headers={"content-type": "text/plain"},
        )

    async def aclose(self):
        pass


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        app.state.http_client = _FakeUpstreamClient()
        yield test_client


def test_welcome_route_is_not_swallowed_by_fallback(client):
    response = client.get("/")
    assert response.json() == {"message": "Welcome to the Reverse Proxy Server!"}
    assert app.state.http_client.calls == []


def test_production_tracker_prefix_takes_precedence_over_fallback(client):
    response = client.get("/production-tracker/some/path")
    assert response.content == _UPSTREAM_MARKER
    assert app.state.http_client.calls[-1]["url"] == (
        "https://basilic.shotgrid.autodesk.com/some/path"
    )


def test_forge_auth_endpoint_is_forwarded(client):
    response = client.post("/forge/init_authentication")
    assert response.content == _UPSTREAM_MARKER
    assert app.state.http_client.calls[-1]["url"] == (
        "https://basilic.shotgrid.autodesk.com/forge/init_authentication"
    )


def test_unrecognized_root_absolute_path_also_forwards_by_default(client):
    response = client.get("/some/never/seen/prefix")
    assert response.content == _UPSTREAM_MARKER
    assert app.state.http_client.calls[-1]["url"] == (
        "https://basilic.shotgrid.autodesk.com/some/never/seen/prefix"
    )


def test_force_decodable_accept_encoding_overrides_browser_codecs():
    # A real Chrome request advertises br/zstd, which httpx silently fails to
    # decode (no exception) when the optional brotli/zstandard packages
    # aren't installed, corrupting the forwarded body. gzip/deflate are
    # always decodable via stdlib zlib.
    headers = force_decodable_accept_encoding(
        {"Accept-Encoding": "gzip, deflate, br, zstd", "X-Foo": "bar"}
    )
    assert headers["accept-encoding"] == "gzip, deflate"
    assert "Accept-Encoding" not in headers
    assert headers["X-Foo"] == "bar"
