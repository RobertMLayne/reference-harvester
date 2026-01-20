from __future__ import annotations

# pyright: reportMissingImports=false
# pyright: reportMissingTypeStubs=false
# pylint: disable=import-error,wrong-import-position
import importlib
from dataclasses import dataclass
from pathlib import Path

import pytest
import requests  # type: ignore[import-untyped]

PROVIDER_MODULE = "reference_harvester.providers.uspto.provider"
provider_mod = importlib.import_module(PROVIDER_MODULE)


@dataclass
class FakeResponse:
    url: str
    status_code: int
    content: bytes
    headers: dict[str, str]

    @property
    def ok(self) -> bool:
        return 200 <= int(self.status_code) < 400

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="ignore")


def _bare_provider():
    cls = getattr(provider_mod, "USPTOProvider")
    return cls.__new__(cls)


def test_harvest_additional_subdomains_writes_manifest(
    monkeypatch,
    tmp_path: Path,
):
    prov = _bare_provider()

    seed = "https://developer.uspto.gov/api-catalog/"

    html = (
        "<html><body>"
        "<a href='https://developer.uspto.gov/api-catalog/page2'>Next</a>"
        "<a href='https://developer.uspto.gov/robots.txt'>Robots</a>"
        "</body></html>"
    ).encode("utf-8")

    def fake_get(url: str, **_kwargs):  # noqa: ANN001
        if url.endswith("/robots.txt"):
            return FakeResponse(
                url=url,
                status_code=200,
                content=b"User-agent: *\nDisallow:\n",
                headers={"Content-Type": "text/plain"},
            )
        if url == seed:
            return FakeResponse(
                url=url,
                status_code=200,
                content=html,
                headers={"Content-Type": "text/html"},
            )
        # Any other fetch returns a small HTML payload; the crawler should
        # still record it if it chooses to fetch it.
        return FakeResponse(
            url=url,
            status_code=200,
            content=b"<html></html>",
            headers={"Content-Type": "text/html"},
        )

    monkeypatch.setattr(requests, "get", fake_get)

    harvester = getattr(
        prov,
        "_harvest_additional_subdomains",
    )

    settings = provider_mod.USPTOSettings(
        user_agent="ua-test",
        http_timeout=1.0,
        max_retries=1,
        backoff_factor=0.0,
        throttle_seconds=0.0,
    )

    out_root = tmp_path / "out" / "uspto"
    harvester(
        out_root=out_root,
        settings=settings,
        max_pages=1,
        max_attachments=0,
        extra_seeds=[seed],
        allow_hosts={"developer.uspto.gov"},
        deny_hosts=None,
        throttle_seconds=0.0,
        max_depth=0,
        since=None,
    )

    manifest_path = out_root / "manifest.json"
    assert manifest_path.exists()

    payload = manifest_path.read_text(encoding="utf-8")
    assert "api-catalog" in payload


@pytest.mark.parametrize(
    "allow_hosts,expect_in_scope",
    [
        ({"developer.uspto.gov"}, True),
        ({"example.com"}, False),
    ],
)
def test_harvest_additional_subdomains_respects_allow_hosts(
    monkeypatch,
    tmp_path: Path,
    allow_hosts: set[str],
    expect_in_scope: bool,
):
    prov = _bare_provider()

    seed = "https://developer.uspto.gov/api-catalog/"

    def fake_get(url: str, **_kwargs):  # noqa: ANN001
        if url.endswith("/robots.txt"):
            return FakeResponse(
                url=url,
                status_code=200,
                content=b"User-agent: *\nDisallow:\n",
                headers={"Content-Type": "text/plain"},
            )
        return FakeResponse(
            url=url,
            status_code=200,
            content=b"<html></html>",
            headers={"Content-Type": "text/html"},
        )

    monkeypatch.setattr(requests, "get", fake_get)

    harvester = getattr(prov, "_harvest_additional_subdomains")
    settings = provider_mod.USPTOSettings(user_agent="ua-test", max_retries=1)

    out_root = tmp_path / "out" / "uspto"
    harvester(
        out_root=out_root,
        settings=settings,
        max_pages=1,
        max_attachments=0,
        extra_seeds=[seed],
        allow_hosts=allow_hosts,
        deny_hosts=None,
        throttle_seconds=0.0,
        max_depth=0,
        since=None,
    )

    payload = (out_root / "manifest.json").read_text(encoding="utf-8")
    assert ("developer.uspto.gov" in payload) is expect_in_scope
