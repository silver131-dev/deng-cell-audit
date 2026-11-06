import importlib.util
import json
from pathlib import Path
import sys
import zipfile
import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
spec = importlib.util.spec_from_file_location("verify_release", TOOLS / "verify_release.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
sys.modules["verify_release"] = verify
spec2 = importlib.util.spec_from_file_location("build_release", TOOLS / "build_release.py")
builder = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(builder)


def fixture_root(tmp_path):
    root = tmp_path / "repo"; root.mkdir()
    (root / "README.md").write_text("Synthetic example only.\n")
    (root / "LICENSE").write_text((TOOLS.parent / "LICENSE").read_text())
    (root / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\nlicense = "MIT"\nlicense-files = ["LICENSE"]\n')
    (root / "release-files.txt").write_text("LICENSE\nREADME.md\npyproject.toml\nrelease-files.txt\nrelease_manifest.json\n")
    (root / "release_manifest.json").write_text("{}")
    return root


def test_release_only_contains_reviewed_files_and_detects_tamper(tmp_path):
    root = fixture_root(tmp_path)
    # Unlisted private work is never selected for publication.
    (root / "excluded.bin").write_bytes(bytes([1, 2, 3]))
    out = tmp_path / "candidate.zip"
    assert builder.build(out, root, refresh=True)["status"] == "PASS"
    with zipfile.ZipFile(out) as z:
        assert sorted(z.namelist()) == ["deng-cell-audit/" + name for name in ["LICENSE", "README.md", "pyproject.toml", "release-files.txt", "release_manifest.json"]]
        manifest = json.loads(z.read("deng-cell-audit/release_manifest.json"))
        assert manifest["version"] == "1.2.3" and manifest["license"] == "MIT"
    (root / "README.md").write_text("Changed after review")
    with pytest.raises(ValueError, match="manifest"): verify.verify(root)


@pytest.mark.parametrize("content", ["lib" + "file_" + "a"*32, "gh" + "p_" + "z"*40, "/wo" + "rkspace/private/file", "A"*301])
def test_selected_sensitive_text_is_rejected(content):
    with pytest.raises(ValueError): verify.inspect_text("example.txt", content.encode())


def test_release_rejects_unsafe_paths_and_data_files(tmp_path):
    root = fixture_root(tmp_path)
    for bad in ["../escape.txt", "counts.h5ad"]:
        (root / "release-files.txt").write_text(bad + "\nrelease-files.txt\nrelease_manifest.json\n")
        with pytest.raises(ValueError): verify.reviewed_files(root)


def test_release_does_not_overwrite_existing_archive(tmp_path):
    root = fixture_root(tmp_path);out = tmp_path / "candidate.zip";out.write_bytes(b"keep")
    with pytest.raises(ValueError): builder.build(out, root, refresh=True)
    assert out.read_bytes() == b"keep"


def test_release_rejects_false_license_metadata(tmp_path):
    root = fixture_root(tmp_path)
    builder.build(tmp_path / "candidate.zip", root, refresh=True)
    manifest_path = root / "release_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["license"] = "Apache-2.0"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="package metadata"):
        verify.verify(root)


def test_release_rejects_omitted_license_notice(tmp_path):
    root = fixture_root(tmp_path)
    (root / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\nlicense = "MIT"\nlicense-files = ["LICENSE", "NOTICE.txt"]\n')
    (root / "NOTICE.txt").write_text("Additional notice\n")
    with pytest.raises(ValueError, match="explicitly selected"):
        builder.build(tmp_path / "candidate.zip", root, refresh=True)

