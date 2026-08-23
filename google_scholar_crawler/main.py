"""Fetch public Google Scholar statistics for the website citation badge."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scholarly import scholarly


def main() -> None:
    scholar_id = os.environ["GOOGLE_SCHOLAR_ID"]
    author: dict[str, Any] = scholarly.search_author_id(scholar_id)
    scholarly.fill(
        author,
        sections=["basics", "indices", "counts", "publications"],
    )

    cited_by = author.get("citedby")
    if not isinstance(cited_by, int):
        raise RuntimeError("Google Scholar did not return a valid citation count")

    author["updated"] = datetime.now(timezone.utc).isoformat()
    author["publications"] = {
        publication["author_pub_id"]: publication
        for publication in author.get("publications", [])
    }

    output_dir = Path(__file__).resolve().parent / "results"
    output_dir.mkdir(exist_ok=True)

    with (output_dir / "gs_data.json").open("w", encoding="utf-8") as output:
        json.dump(author, output, ensure_ascii=False, indent=2)

    badge_data = {
        "schemaVersion": 1,
        "label": "citations",
        "message": str(cited_by),
    }
    with (output_dir / "gs_data_shieldsio.json").open(
        "w", encoding="utf-8"
    ) as output:
        json.dump(badge_data, output, ensure_ascii=False)


if __name__ == "__main__":
    main()
