from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Every probe runs outside the checkout with an extracted built wheel first
# on sys.path. This prevents the source-tree template and pytest's conftest
# import setup from hiding missing runtime package data.
PROBE = """
import importlib.metadata
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

wheel_root, mode, output = map(Path, sys.argv[1:])
sys.path.insert(0, str(wheel_root))
from reference_harvester import endnote_xml
from reference_harvester.registry import load_registry

module = Path(endnote_xml.__file__).resolve()
assert module.is_relative_to(wheel_root.resolve()), module
registry_path = module.parent / 'registry' / 'uspto_fields.yaml'
registry = load_registry(registry_path)

def verify_table(text):
    root = ET.fromstring(text)
    nodes = root.findall('./RefType') + root.findall('./RefTypeX')
    target = next(node for node in nodes
                  if node.get('name') == 'PackagedProbe')
    assert target.find('./Fields/Field') is not None

mode = str(mode)
if mode == 'template':
    template = endnote_xml._default_template_path()
    assert template.is_relative_to(wheel_root.resolve()), template
    root = ET.parse(template).getroot()
    assert root.findall('./RefType') or root.findall('./RefTypeX')
elif mode == 'build':
    verify_table(endnote_xml.build_reference_type_table(
        registry, default_type='PackagedProbe'))
elif mode == 'write':
    endnote_xml.write_reference_type_table(
        output, registry, type_name='PackagedProbe')
    verify_table(output.read_text(encoding='utf-8'))
elif mode == 'cli':
    distribution = importlib.metadata.distribution('reference-harvester')
    entry = next(ep for ep in distribution.entry_points
                 if ep.group == 'console_scripts'
                 and ep.name == 'reference-harvester')
    assert entry.value == 'reference_harvester.cli.app:run'
    sys.argv = ['reference-harvester', 'endnote-xml',
                '--out-path', str(output), '--type-name', 'PackagedProbe']
    try:
        entry.load()()
    except SystemExit as error:
        assert error.code in (None, 0), error.code
    verify_table(output.read_text(encoding='utf-8'))
else:
    raise AssertionError(mode)
"""


@pytest.fixture(scope="module")
def packaged_wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    # A fresh source copy avoids stale egg-info/SOURCES.txt entries and keeps
    # build products outside both the checkout and the runtime probe's cwd.
    temporary = tmp_path_factory.mktemp("endnote-package-data")
    project = temporary / "project"
    project.mkdir()
    for name in ("pyproject.toml", "README.md"):
        shutil.copyfile(ROOT / name, project / name)
    shutil.copytree(
        ROOT / "src",
        project / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"),
    )
    wheels = temporary / "wheels"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(wheels),
            str(project),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    built = list(wheels.glob("*.whl"))
    assert len(built) == 1
    installed = temporary / "installed"
    with zipfile.ZipFile(built[0]) as wheel:
        wheel.extractall(installed)
    return installed


@pytest.mark.parametrize("mode", ["template", "build", "write", "cli"])
def test_built_wheel_default_endnote_template(
    packaged_wheel: Path,
    tmp_path: Path,
    mode: str,
) -> None:
    output = tmp_path / "result.xml"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            PROBE,
            str(packaged_wheel),
            mode,
            str(output),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
