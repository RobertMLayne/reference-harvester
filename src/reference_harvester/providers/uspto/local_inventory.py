from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List

import yaml


@dataclass
class Endpoint:
    path: str
    method: str
    summary: str | None = None
    tags: list[str] | None = None
    operation_id: str | None = None
    host: str | None = None


def load_openapi(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return yaml.safe_load(text)  # type: ignore[no-any-return]


def extract_endpoints(spec: dict[str, Any]) -> list[Endpoint]:
    endpoints: list[Endpoint] = []
    servers = spec.get("servers") or []
    host: str | None = None
    if servers and isinstance(servers[0], dict):
        raw = servers[0].get("url")
        if isinstance(raw, str):
            host = raw.replace("https://", "").replace("http://", "").strip("/")

    paths = spec.get("paths") or {}
    for raw_path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, meta in methods.items():
            if not isinstance(meta, dict):
                continue
            endpoints.append(
                Endpoint(
                    path=str(raw_path),
                    method=str(method).upper(),
                    summary=meta.get("summary"),
                    tags=list(meta.get("tags", []) or []),
                    operation_id=meta.get("operationId"),
                    host=host,
                )
            )
    return endpoints


def write_inventory_json(path: Path, endpoints: Iterable[Endpoint]) -> None:
    payload: List[dict[str, Any]] = []
    for ep in endpoints:
        payload.append(
            {
                "path": ep.path,
                "method": ep.method,
                "tags": ep.tags or [],
                "summary": ep.summary,
                "operation_id": ep.operation_id,
                "host": ep.host,
            }
        )
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_inventory_md(path: Path, endpoints: Iterable[Endpoint]) -> None:
    lines = ["| path | method | tags | summary |", "| --- | --- | --- | --- |"]
    for ep in endpoints:
        tags = ", ".join(ep.tags or [])
        summary = ep.summary or ""
        lines.append(f"| {ep.path} | {ep.method} | {tags} | {summary} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
