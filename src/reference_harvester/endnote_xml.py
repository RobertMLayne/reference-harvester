from __future__ import annotations

import copy
from pathlib import Path
from xml.etree import ElementTree as ET

from reference_harvester.registry import FieldRegistry


class EndNoteRefTypesError(RuntimeError):
    pass


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _default_template_path() -> Path:
    """Best-effort default for a RefTypes/RefTypeTable export.

    We intentionally do not try to read from the user's EndNote preferences
    folder automatically; importing/exporting reference type tables is a
    global setting for the EndNote desktop user account.
    """

    candidates = [
        Path.cwd() / "endnote_reference_type_table.xml",
        Path(__file__).resolve().parents[2] / "endnote_reference_type_table.xml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise EndNoteRefTypesError(
        "EndNote RefTypes template not found. Provide template_path=... or "
        "place endnote_reference_type_table.xml in the project root."
    )


def _iter_ref_type_nodes(root: ET.Element) -> list[ET.Element]:
    # EndNote exports include both RefType and RefTypeX nodes.
    nodes: list[ET.Element] = []
    nodes.extend(root.findall("./RefType"))
    nodes.extend(root.findall("./RefTypeX"))
    return nodes


def _find_ref_type_by_name(root: ET.Element, name: str) -> ET.Element | None:
    for node in _iter_ref_type_nodes(root):
        if node.get("name") == name:
            return node
    return None


def _apply_field_label_overrides(
    fields_el: ET.Element, overrides: dict[str, str]
) -> None:
    # Overrides can be keyed by:
    # - existing label text (e.g., "Custom 1")
    # - field id (e.g., "25" or "id:25")
    # Prefer field-id matching for robustness across localization/user edits.
    by_label: dict[str, ET.Element] = {}
    by_id: dict[str, ET.Element] = {}
    for field in fields_el.findall("./Field"):
        field_id = field.get("id")
        if field_id:
            by_id[field_id.strip()] = field
        if field.text is None:
            continue
        by_label[field.text.strip()] = field

    for old_label, new_label in overrides.items():
        key = old_label.strip()
        if key.lower().startswith("id:"):
            key = key.split(":", 1)[1].strip()

        node = by_id.get(key)
        if node is None:
            node = by_label.get(old_label)
        if node is not None:
            node.text = new_label


def patch_reference_types_table(
    template_xml: str,
    *,
    type_name: str,
    base_type_name: str = "Generic",
    target_slot_name: str = "Unused 1",
    field_label_overrides: dict[str, str] | None = None,
) -> str:
    """Patch an exported EndNote Reference Types Table XML.

    Strategy: reuse an existing template export (for schema correctness), then
    repurpose one of the "Unused" reference types (default: "Unused 1") by
    copying the field layout from a base type (default: "Generic") and
    optionally relabeling fields (e.g., Custom 1..8).

    This stays within EndNote's hard limits by not adding new types.
    """

    try:
        root = ET.fromstring(template_xml)
    except ET.ParseError as exc:
        msg = f"Invalid RefTypes XML template: {exc}"
        raise EndNoteRefTypesError(msg) from exc

    if root.tag != "RefTypes":
        raise EndNoteRefTypesError(
            f"Unexpected root element {root.tag!r}; expected 'RefTypes'"
        )

    base = _find_ref_type_by_name(root, base_type_name)
    if base is None:
        raise EndNoteRefTypesError(
            f"Base reference type {base_type_name!r} not found in template"
        )
    base_fields = base.find("./Fields")
    if base_fields is None:
        raise EndNoteRefTypesError(
            f"Base reference type {base_type_name!r} is missing <Fields>"
        )

    target = _find_ref_type_by_name(root, target_slot_name)
    if target is None:
        raise EndNoteRefTypesError(
            f"Target slot {target_slot_name!r} not found in template"
        )

    target.set("name", type_name)

    target_fields = target.find("./Fields")
    if target_fields is None:
        target_fields = ET.SubElement(target, "Fields")
    target_fields.clear()
    for field in base_fields.findall("./Field"):
        target_fields.append(copy.deepcopy(field))

    if field_label_overrides:
        _apply_field_label_overrides(target_fields, field_label_overrides)

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode")


def build_reference_type_table(
    registry: FieldRegistry,
    type_fields: dict[str, list[str]] | None = None,
    default_type: str = "ReferenceHarvester",
) -> str:
    """Return an EndNote Reference Types Table XML string.

    This patches an exported EndNote Reference Types Table XML template
    (RefTypeTable export), producing an importable file.

    Notes:
    - EndNote has hard limits on number of types/fields; this reuses an
      "Unused" slot rather than attempting to create unlimited custom types.
    - registry/type_fields are currently only used to decide the output type
      name; field mapping is handled via relabeling of existing slots.
    """

    _ = registry
    type_name = default_type
    if type_fields:
        # Preserve previous CLI behavior where the caller provided a single
        # entry {type_name: [...]}.
        type_name = next(iter(type_fields.keys()))

    template_path = _default_template_path()
    template_xml = template_path.read_text(encoding="utf-8")
    return patch_reference_types_table(
        template_xml,
        type_name=type_name,
        field_label_overrides=None,
    )


def write_reference_type_table(
    path: Path,
    registry: FieldRegistry,
    type_fields: dict[str, list[str]] | None = None,
    default_type: str = "ReferenceHarvester",
    *,
    type_name: str | None = None,
    template_path: Path | None = None,
    base_type_name: str = "Generic",
    target_slot_name: str = "Unused 1",
    field_label_overrides: dict[str, str] | None = None,
) -> None:
    _ = registry

    # Back-compat: allow (type_fields/default_type) or explicit type_name.
    effective_type_name = type_name
    if effective_type_name is None:
        effective_type_name = default_type
        if type_fields:
            effective_type_name = next(iter(type_fields.keys()))

    tpl_path = template_path or _default_template_path()
    template_xml = tpl_path.read_text(encoding="utf-8")
    xml_text = patch_reference_types_table(
        template_xml,
        type_name=effective_type_name,
        base_type_name=base_type_name,
        target_slot_name=target_slot_name,
        field_label_overrides=field_label_overrides,
    )
    _ensure_parent(path)
    path.write_text(xml_text, encoding="utf-8")


__all__ = [
    "EndNoteRefTypesError",
    "build_reference_type_table",
    "patch_reference_types_table",
    "write_reference_type_table",
]
