"""Export the generated OpenAPI spec to a JSON file (WBS 1.2.4).

Usage:
    python -m scripts.export_openapi [output_path]

Publishes the API contract so the frontend can integrate against it (WBS 1.5.1)
and so the spec can be checked into docs / served by tooling.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.main import create_app


def build_spec() -> dict:
    return create_app().openapi()


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("openapi.json")
    output.write_text(json.dumps(build_spec(), indent=2), encoding="utf-8")
    print(f"Wrote OpenAPI spec to {output}")


if __name__ == "__main__":
    main()
