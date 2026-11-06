#!/usr/bin/env python3
"""Package an explicitly reviewed file list, never the whole working tree."""
import argparse
import json
from pathlib import Path
import zipfile
from verify_release import ROOT, MANIFEST, inspect_files, release_metadata, reviewed_files, verify


def build(output, root=ROOT, refresh=False):
    output = Path(output)
    if output.exists():
        raise ValueError("output archive already exists")
    if refresh:
        files = inspect_files(root)
        manifest = {"schema": "DENG_RELEASE_MANIFEST_V1", **release_metadata(root), "files": files}
        (root / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = verify(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in reviewed_files(root):
            info = zipfile.ZipInfo("deng-cell-audit/" + name, date_time=(2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (root / name).read_bytes())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--refresh-manifest", action="store_true", help="only after reviewing edits and the explicit file list")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.out, refresh=args.refresh_manifest), indent=2))
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()

