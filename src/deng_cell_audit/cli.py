import argparse
import json
import sys
from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog="deng-cell-audit", description="DENG Cell Audit: offline cell-evidence audit tools")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="run entirely synthetic examples")
    demo.add_argument("--out", required=True, help="new output directory")
    replay_parser = sub.add_parser("replay", help="read local H5AD files fixed by a contract")
    replay_parser.add_argument("--contract", required=True)
    replay_parser.add_argument("--out", required=True, help="new output directory")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            from .demo import run_demo
            result = run_demo(args.out)
        else:
            from .replay import replay
            result = replay(args.contract, args.out)
        print(json.dumps({"status": "COMPLETED", "fingerprint_rows": result["fingerprint_rows"],
                          "panel_context_rows": result["panel_context_rows"], "model_use": "HOLD"}))
        return 0
    except (ValueError, OSError, KeyError, TypeError, ImportError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 2

