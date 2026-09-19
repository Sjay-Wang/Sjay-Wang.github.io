"""Fetch Google Scholar statistics through SerpApi for the website badge."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


def fetch_author(scholar_id: str, api_key: str) -> dict[str, Any]:
    query = urlencode(
        {
            "engine": "google_scholar_author",
            "author_id": scholar_id,
            "hl": "en",
            "api_key": api_key,
        }
    )
    request = Request(
        f"{SERPAPI_ENDPOINT}?{query}",
        headers={"User-Agent": "Sjay-Wang.github.io citation updater"},
    )

    try:
        with urlopen(request, timeout=60) as response:
            result: dict[str, Any] = json.load(response)
    except HTTPError as error:
        try:
            details = json.loads(error.read().decode("utf-8")).get("error", "")
        except (UnicodeDecodeError, json.JSONDecodeError):
            details = ""
        message = f"SerpApi request failed with HTTP {error.code}"
        if details:
            message += f": {details}"
        raise RuntimeError(message) from None
    except URLError as error:
        raise RuntimeError(f"Could not connect to SerpApi: {error.reason}") from None

    if result.get("error"):
        raise RuntimeError(f"SerpApi request failed: {result['error']}")

    status = result.get("search_metadata", {}).get("status")
    if status != "Success":
        raise RuntimeError(f"SerpApi returned unexpected status: {status!r}")

    return result


def get_total_citations(result: dict[str, Any]) -> int:
    for row in result.get("cited_by", {}).get("table", []):
        citations = row.get("citations")
        if citations and "all" in citations:
            try:
                return int(str(citations["all"]).replace(",", ""))
            except (TypeError, ValueError):
                break
    raise RuntimeError("SerpApi did not return a valid total citation count")


def main() -> None:
    scholar_id = os.environ["GOOGLE_SCHOLAR_ID"]
    api_key = os.environ["SERPAPI_KEY"]
    result = fetch_author(scholar_id, api_key)
    cited_by = get_total_citations(result)

    author = {
        "source": "SERPAPI_GOOGLE_SCHOLAR_AUTHOR",
        "scholar_id": scholar_id,
        "name": result.get("author", {}).get("name"),
        "citedby": cited_by,
        "cited_by": result.get("cited_by", {}),
        "publications": result.get("articles", []),
        "updated": datetime.now(timezone.utc).isoformat(),
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
