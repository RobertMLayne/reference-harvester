from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from reference_harvester.models import ensure_parent
from reference_harvester.registry import FieldRegistry


def build_reference_type_table(
    registry: FieldRegistry, type_name: str = "ReferenceHarvester"
) -> str:
    """Return a minimal EndNote reference type table XML string.

    Canonical field names from the registry are emitted as field entries.
    Providers can extend this by mapping canonical fields to specific
    EndNote field identifiers before writing.
    """

    root = ET.Element("reference-types")
    ref_type = ET.SubElement(root, "type", {"name": type_name})
    fields_el = ET.SubElement(ref_type, "fields")

    for field in sorted(registry.fields.values(), key=lambda f: f.name):
        field_el = ET.SubElement(fields_el, "field", {"name": field.name})
        if field.description:
            desc = ET.SubElement(field_el, "description")
            desc.text = field.description

    return ET.tostring(root, encoding="unicode")


def write_reference_type_table(
    path: Path, registry: FieldRegistry, type_name: str = "ReferenceHarvester"
) -> None:
    xml_text = build_reference_type_table(registry, type_name)
    ensure_parent(path)
    path.write_text(xml_text, encoding="utf-8")


__all__ = ["build_reference_type_table", "write_reference_type_table"]
