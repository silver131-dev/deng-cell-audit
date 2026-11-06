#!/usr/bin/env python3
"""Verify only reviewed release files. No network or data execution."""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "release_manifest.json"
PATTERNS = {
    "private_account_link": r"chatgpt[.]com/(?:library|space)",
    "private_file_id": r"libfile_[a-z0-9]{16,}",
    "personal_absolute_path": r"/(?:home|Users|workspace)/[^\s\"']+|[A-Za-z]:[\\/](?:Users|Documents)[\\/]",
    "access_token": r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}",
    "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "email_address": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "embedded_payload": r"[A-Za-z0-9+/]{300,}={0,2}",
}
ALLOWED_SUFFIXES = {".py", ".md", ".toml", ".txt", ".json", ".yml", ".yaml"}
ALLOWED_NAMES = {".gitignore", ".gitattributes", "MANIFEST.in", "LICENSE"}


def reviewed_files(root):
    lines = (root / "release-files.txt").read_text(encoding="utf-8").splitlines()
    if not lines or len(lines) != len(set(lines)):
        raise ValueError("empty or duplicate release file list")
    for name in lines:
        p = PurePosixPath(name)
        if not name or p.is_absolute() or ".." in p.parts or "\\" in name or p.as_posix() != name:
            raise ValueError("unsafe release path")
        if p.suffix not in ALLOWED_SUFFIXES and p.name not in ALLOWED_NAMES:
            raise ValueError("non-text or unapproved file type: " + name)
        full = root / name
        if full.is_symlink() or not full.is_file() or not full.resolve().is_relative_to(root.resolve()):
            raise ValueError("missing, external, or symlink release file: " + name)
        if any(part.is_symlink() for part in [full, *full.parents] if part != root.parent):
            raise ValueError("symlink component: " + name)
    required = {MANIFEST, "release-files.txt", "pyproject.toml", "LICENSE"}
    if not required.issubset(lines):
        raise ValueError("release list must include manifest, metadata, LICENSE, and itself")
    return lines


def release_metadata(root):
    selected = reviewed_files(root)
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    version, license_id = project.get("version"), project.get("license")
    if not isinstance(version, str) or not version.strip() or not isinstance(license_id, str) or not license_id.strip():
        raise ValueError("release requires an explicit version and SPDX license expression")
    license_files = project.get("license-files")
    if not isinstance(license_files, list) or "LICENSE" not in license_files or any(
        not isinstance(name, str) or name not in selected for name in license_files
    ):
        raise ValueError("license files must be explicitly selected for release")
    return {"version": version, "license": license_id, "license_decision": "SELECTED"}


def inspect_text(name, data):
    if len(data) > 200_000:
        raise ValueError("unexpectedly large release text: " + name)
    text = data.decode("utf-8")
    if "\x00" in text:
        raise ValueError("binary data in release text: " + name)
    for label, pattern in PATTERNS.items():
        if re.search(pattern, text):
            raise ValueError(label + " in " + name)
    if name.endswith(".py"):
        ast.parse(text, filename=name)
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def inspect_files(root):
    files = reviewed_files(root)
    return {name: inspect_text(name, (root / name).read_bytes()) for name in files if name != MANIFEST}


def verify(root=ROOT):
    actual = inspect_files(root)
    manifest_bytes = (root / MANIFEST).read_bytes()
    inspect_text(MANIFEST, manifest_bytes)
    expected = json.loads(manifest_bytes)
    if expected.get("schema") != "DENG_RELEASE_MANIFEST_V1" or expected.get("files") != actual:
        raise ValueError("release manifest differs from reviewed bytes")
    metadata = release_metadata(root)
    if any(expected.get(key) != value for key, value in metadata.items()):
        raise ValueError("release manifest license or version differs from package metadata")
    return {"status": "PASS", "release_files": len(actual) + 1,
            "scope": "Explicit allowlist, UTF-8 text, selected sensitive patterns, syntax, SHA-256",
            **metadata}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root), indent=2))
    except (ValueError, OSError, UnicodeError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()

