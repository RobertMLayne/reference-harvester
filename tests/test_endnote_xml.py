from __future__ import annotations

import xml.etree.ElementTree as ET

from reference_harvester.endnote_xml import patch_reference_types_table

_TEMPLATE = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<RefTypes version=\"22\">
  <RefType name=\"Generic\">
    <Fields>
      <Field id=\"25\">Custom 1</Field>
      <Field id=\"26\">Custom 2</Field>
      <Field id=\"27\">Custom 3</Field>
    </Fields>
  </RefType>
  <RefType name=\"Unused 1\">
    <Fields>
      <Field id=\"25\">Custom 1</Field>
    </Fields>
  </RefType>
</RefTypes>
"""


def _find_ref_type(root: ET.Element, name: str) -> ET.Element:
    for node in root.findall("./RefType"):
        if node.get("name") == name:
            return node
    raise AssertionError(f"Missing RefType {name!r}")


def test_patch_reference_types_table_renames_and_copies_fields():
    xml_text = patch_reference_types_table(
        _TEMPLATE,
        type_name="USPTO",
        base_type_name="Generic",
        target_slot_name="Unused 1",
        field_label_overrides=None,
    )

    root = ET.fromstring(xml_text)
    target = _find_ref_type(root, "USPTO")
    fields_el = target.find("./Fields")
    assert fields_el is not None
    fields = [
        (f.get("id"), (f.text or "").strip()) for f in fields_el.findall("./Field")
    ]

    # The target slot should now have the same fields as Generic.
    assert fields == [
        ("25", "Custom 1"),
        ("26", "Custom 2"),
        ("27", "Custom 3"),
    ]


def test_patch_reference_types_table_overrides_by_id_and_label():
    xml_text = patch_reference_types_table(
        _TEMPLATE,
        type_name="USPTO",
        base_type_name="Generic",
        target_slot_name="Unused 1",
        field_label_overrides={
            "id:25": "Application Number",
            "Custom 2": "Trial Number",
        },
    )

    root = ET.fromstring(xml_text)
    target = _find_ref_type(root, "USPTO")
    fields_el = target.find("./Fields")
    assert fields_el is not None

    by_id = {f.get("id"): (f.text or "").strip() for f in fields_el.findall("./Field")}

    assert by_id["25"] == "Application Number"
    assert by_id["26"] == "Trial Number"
    assert by_id["27"] == "Custom 3"
