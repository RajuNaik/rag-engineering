from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .models import Document


def load_web_page(url: str, timeout: int = 30) -> Document:
    """Fetch a web page and return its HTML as source content.

    Parsing/cleaning HTML is intentionally a later stage. Keeping the raw HTML
    here makes the ingestion boundary explicit.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL must start with http:// or https://")

    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "rag-engineering/0.1"},
    )
    response.raise_for_status()

    # Verify that the content is HTML when the server provides a content type.
    content_type = response.headers.get("content-type", "")
    if content_type and "html" not in content_type.lower():
        raise ValueError(f"Expected HTML but received: {content_type}")

    title = BeautifulSoup(response.text, "html.parser").title
    return Document(
        content=response.text,
        metadata={
            "source_type": "web",
            "source": url,
            "url": url,
            "domain": parsed.netloc,
            "title": title.get_text(strip=True) if title else None,
            "status_code": response.status_code,
            "content_type": content_type,
        },
        id=url,
    )
