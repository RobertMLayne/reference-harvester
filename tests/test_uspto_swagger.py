from __future__ import annotations

# pyright: reportMissingImports=false
# pylint: disable=import-error,wrong-import-position
# ruff: noqa: SLF001
import hashlib
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import requests

from reference_harvester.providers import (  # type: ignore[import]
    base as providers_base,
)

ProviderContext = providers_base.ProviderContext

# Load provider module explicitly
PROVIDER_MODULE = "reference_harvester.providers.uspto.provider"
provider_mod = importlib.import_module(PROVIDER_MODULE)


def _bare_provider():
    # Bypass __init__ to avoid side effects
    cls = getattr(provider_mod, "USPTOProvider")
    return cls.__new__(cls)


def test_refresh_inventory_uses_packaged_swagger(tmp_path: Path):
    prov = provider_mod.USPTOProvider()
    ctx = ProviderContext(name="uspto", out_dir=tmp_path / "out")

    prov.refresh_inventory(ctx)

    base_dir = (
        ctx.out_dir / "raw" / "harvester" / provider_mod.USPTO_PROVIDER_ID
    )
    artifacts_dir = base_dir / "artifacts"
    coverage_files = sorted(artifacts_dir.glob("coverage*.json"))
    endpoints_files = sorted(artifacts_dir.glob("swagger_endpoints*.json"))

    assert coverage_files, "coverage files were not written"
    assert endpoints_files, "endpoints files were not written"

    rows = json.loads(coverage_files[0].read_text(encoding="utf-8"))
    assert rows and len(rows) > 0
    first = rows[0]
    for key in ("host", "path", "method", "summary"):
        assert key in first


def test_api_sampling_no_coverage_yields_empty_manifest(tmp_path: Path):
    prov = _bare_provider()
    sampler = getattr(
        prov,
        "_sample_api_endpoints",
    )  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    settings = provider_mod.USPTOSettings(user_agent="ua-test")
    out_root = tmp_path / "out"

    sampler(
        out_root=out_root,
        settings=settings,
        sample_limit=5,
        throttle_seconds=0.0,
    )

    manifest = (
        out_root
        / "raw"
        / "harvester"
        / provider_mod.USPTO_PROVIDER_ID
        / "api_samples"
        / "manifest.json"
    )

    assert manifest.exists()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload == []


def test_fetch_swagger_specs_handles_request_failure(
    monkeypatch,
    tmp_path: Path,
):
    prov = _bare_provider()

    def fake_get(
        url: str,
        headers: dict | None = None,
        timeout: int | None = None,
    ) -> None:
        raise requests.RequestException("boom")

    monkeypatch.setattr(requests, "get", fake_get)

    fetch_specs = getattr(
        prov,
        "_fetch_swagger_specs",
    )  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    settings = provider_mod.USPTOSettings(user_agent="test-agent")
    results = fetch_specs(
        swagger_urls=["https://example.test/swagger.json"],
        artifacts_dir=tmp_path,
        settings=settings,
    )

    assert results == []
    assert list(tmp_path.iterdir()) == []


def test_fetch_swagger_specs_rejects_bad_json(monkeypatch, tmp_path: Path):
    prov = _bare_provider()

    class FakeResp:
        def __init__(self) -> None:
            self.status_code = 200
            self.content = b"{}"

        def json(self):
            raise ValueError("not json")

    monkeypatch.setattr(requests, "get", lambda *_, **__: FakeResp())

    fetch_specs = getattr(
        prov,
        "_fetch_swagger_specs",
    )  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    settings = provider_mod.USPTOSettings(user_agent="test-agent")
    results = fetch_specs(
        swagger_urls=["https://example.test/swagger.json"],
        artifacts_dir=tmp_path,
        settings=settings,
    )

    assert results == []


def test_fetch_swagger_specs_success_writes_meta(monkeypatch, tmp_path: Path):
    prov = _bare_provider()
    calls: list[tuple[str, dict | None, int | None]] = []

    class FakeResp:
        def __init__(self) -> None:
            self.status_code = 200
            self.content = b'{"foo": "bar"}'

        def json(self):
            return {}

    def fake_get(
        url: str,
        headers: dict | None = None,
        timeout: int | None = None,
    ) -> FakeResp:
        calls.append((url, headers, timeout))
        return FakeResp()

    monkeypatch.setattr(requests, "get", fake_get)

    fetch_specs = getattr(
        prov,
        "_fetch_swagger_specs",
    )  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    url = "https://example.test/swagger.json"
    settings = provider_mod.USPTOSettings(user_agent="ua-test")
    results = fetch_specs(
        swagger_urls=[url],
        artifacts_dir=tmp_path,
        settings=settings,
    )

    assert len(results) == 1
    name, out_path, spec = results[0]
    assert spec == {"_source_url": url}
    assert out_path.exists()

    meta_path = tmp_path / f"swagger_{name}.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["url"] == url
    assert meta["status_code"] == 200
    assert meta["sha256"] == hashlib.sha256(b'{"foo": "bar"}').hexdigest()
    assert meta_path.read_text(encoding="utf-8").endswith("\n")

    assert calls == [(url, {"User-Agent": "ua-test"}, 30)]


def test_launch_gui_uses_nicegui_stub(monkeypatch, tmp_path: Path):
    calls: list[str] = []

    class StubUI:
        def label(self, text: str) -> None:
            calls.append(text)

        def run(self) -> None:
            calls.append("run")

    stub_module = SimpleNamespace(ui=StubUI())
    monkeypatch.setitem(sys.modules, "nicegui", stub_module)

    app_mod = importlib.import_module("reference_harvester.gui.app")

    app_mod.launch_gui(tmp_path, options={"max_pages": 5})

    assert "run" in calls
    assert any(str(tmp_path) in str(val) for val in calls)
    assert any("max_pages" in str(val) for val in calls)


def test_write_coverage_matrix_emits_files(tmp_path: Path):
    prov = _bare_provider()
    endpoint = SimpleNamespace(
        path="/api/v1/datasets/foo",
        method="GET",
        summary="s",
        tags=["datasets"],
        operation_id="op1",
    )

    json_path = tmp_path / "cov.json"
    md_path = tmp_path / "cov.md"

    write_cov = getattr(
        prov,
        "_write_coverage_matrix",
    )  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    write_cov(
        endpoints=[endpoint],
        spec={"servers": [{"url": "https://api.data.uspto.gov"}]},
        json_path=json_path,
        md_path=md_path,
        source_name="test",
    )

    rows = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(rows) == 1
    assert rows[0]["host"] == "api.data.uspto.gov"
    assert rows[0]["implemented"] is True
    assert md_path.read_text(encoding="utf-8").startswith("# USPTO coverage")


def test_write_coverage_matrix_custom_columns(tmp_path: Path):
    prov = _bare_provider()
    endpoint = SimpleNamespace(
        path="/datasets/products",
        method="POST",
        summary="create dataset",
        tags=["datasets"],
        operation_id="createDataset",
    )

    json_path = tmp_path / "cov.json"
    md_path = tmp_path / "cov.md"

    write_cov = getattr(
        prov,
        "_write_coverage_matrix",
    )  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    write_cov(
        endpoints=[endpoint],
        spec={},
        json_path=json_path,
        md_path=md_path,
        source_name="custom",
        columns=["path", "method", "implemented", "summary"],
    )

    md_lines = md_path.read_text(encoding="utf-8").splitlines()
    assert "| path | method | implemented | summary |" in md_lines
    products_prefix = "| /datasets/products"
    data_rows = [line for line in md_lines if line.startswith(products_prefix)]
    assert data_rows
    prefix = "| /datasets/products | POST | yes | create dataset |"
    assert data_rows[0].startswith(prefix)


def test_refresh_inventory_with_stubbed_inventory(monkeypatch, tmp_path: Path):
    def stub_import(module_path: str):
        if module_path == "harvester.providers.uspto.inventory":
            return SimpleNamespace(
                extract_endpoints=lambda spec: [
                    SimpleNamespace(path="/datasets/products", method="GET")
                ],
                write_inventory_json=lambda p, endpoints: p.write_text(
                    json.dumps(
                        [
                            {"path": e.path, "method": e.method}
                            for e in endpoints
                        ]
                    ),
                    encoding="utf-8",
                ),
                write_inventory_md=lambda p, endpoints: p.write_text(
                    "# md", encoding="utf-8"
                ),
                load_openapi=lambda p: {
                    "servers": [{"url": "https://data.uspto.gov"}],
                    "paths": {"/datasets/products": {"get": {}}},
                },
            )
        if module_path == "harvester.providers.uspto.constants":
            return SimpleNamespace(USPTO_PROVIDER_ID="uspto")
        if module_path == "harvester.core.storage":

            class StubStorePaths:
                def __init__(self, out_root: Path):
                    self.out_root = out_root

                def artifacts_root(self, provider_id: str) -> Path:
                    path = self.out_root / provider_id / "artifacts"
                    path.mkdir(parents=True, exist_ok=True)
                    return path

            return SimpleNamespace(StorePaths=StubStorePaths)
        return SimpleNamespace()

    monkeypatch.setattr(provider_mod, "_import_harvester_module", stub_import)
    monkeypatch.setattr(
        provider_mod,
        "_ensure_harvester_on_path",
        lambda: tmp_path,
    )

    prov = provider_mod.USPTOProvider.__new__(provider_mod.USPTOProvider)
    prov.registry_path = tmp_path / "registry.yaml"
    monkeypatch.setattr(
        prov,
        "_fetch_swagger_specs",
        lambda **_: [
            (
                "live",
                tmp_path / "spec.json",
                {"servers": [{"url": "https://data.uspto.gov"}]},
            )
        ],
    )

    ctx = ProviderContext(
        name="uspto",
        out_dir=tmp_path,
        options={"endpoints_md_columns": ["path", "method", "tags"]},
    )
    prov.refresh_inventory(ctx)

    artifacts = tmp_path / "raw" / "harvester" / "uspto" / "artifacts"
    assert (artifacts / "swagger_endpoints.json").exists()
    assert (artifacts / "swagger_endpoints.md").exists()
    assert (artifacts / "coverage.json").exists()
    assert (artifacts / "coverage.md").exists()
    assert (artifacts / "swagger.json").exists()

    coverage_rows = json.loads(
        (artifacts / "coverage.json").read_text(encoding="utf-8")
    )
    assert coverage_rows[0]["path"] == "/datasets/products"
    assert coverage_rows[0]["host"] == "data.uspto.gov"

    coverage_text = (artifacts / "coverage.md").read_text(encoding="utf-8")
    md_lines = coverage_text.splitlines()
    assert any("/datasets/products" in line for line in md_lines)
    assert any("| Method | Path | Host |" == line for line in md_lines)
    data_rows = [line for line in md_lines if line.startswith("| GET | ")]
    assert data_rows
    row = data_rows[0]
    assert "| GET | /datasets/products | data.uspto.gov | yes |" in row
    assert "| s | datasets |" in row or row.endswith("| s | datasets |")

    endpoints_written = json.loads(
        (artifacts / "swagger_endpoints.json").read_text(encoding="utf-8")
    )
    assert endpoints_written[0]["path"] == "/datasets/products"
    md_text = (artifacts / "swagger_endpoints.md").read_text(encoding="utf-8")
    md_endpoints = md_text.splitlines()
    assert any("/datasets/products" in line for line in md_endpoints)
    assert md_endpoints[0] == "| path | method | tags |"
    assert md_endpoints[1] == "| --- | --- | --- |"
    assert "| /datasets/products | GET | |" in md_endpoints[2]
