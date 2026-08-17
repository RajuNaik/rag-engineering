from typing import Any

import requests

from .models import Document


def load_json_api(url: str, timeout: int = 30, **request_kwargs: Any) -> Document:
    """Call a JSON REST endpoint and preserve the response as JSON text."""
    response = requests.get(url, timeout=timeout, **request_kwargs)
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as exc:
        raise ValueError("API response is not valid JSON") from exc

    import json

    content = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    return Document(
        content=content,
        metadata={
            "source_type": "rest_api",
            "source": url,
            "url": url,
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type", ""),
        },
        id=url,
    )
