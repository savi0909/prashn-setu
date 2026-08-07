"""Write the OpenAPI document to the repository root.

`openapi.json` is the contract the generated TypeScript client is built from
(§16.1: ``frontend/src/api/`` is generated, never hand-edited). It is committed
so a schema change shows up as a reviewable diff, and CI re-runs this script and
fails when the working tree differs — a route change that forgets to regenerate
is caught in the PR, not by the frontend at runtime.
"""

import json
import sys
from pathlib import Path

from app.config import REPO_ROOT
from app.main import create_app

OUTPUT_PATH = REPO_ROOT / "openapi.json"


def dump(path: Path = OUTPUT_PATH) -> Path:
    schema = create_app().openapi()
    # sort_keys so the diff reflects real schema changes, not dict ordering.
    # newline="\n" because the default translates to CRLF on Windows: the file
    # would then differ by line ending alone between a Windows developer and
    # Linux CI, and the drift check would fail for whoever ran it second.
    path.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


if __name__ == "__main__":
    written = dump()
    print(f"wrote {written}", file=sys.stderr)
