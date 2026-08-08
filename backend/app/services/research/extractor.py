import html
import logging
import re
from typing import Dict, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 SignalForge/1.0"
}


def fetch_html(client: httpx.Client, url: str) -> Optional[str]:
    """Fetch raw HTML content from network with timeout and error handling."""
    if not url or not url.startswith("http"):
        return None

    try:
        response = client.get(url, follow_redirects=True)
        if response.status_code == 200:
            return response.text
        logger.warning(f"Failed to fetch research source {url}: status {response.status_code}")
        return None
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.warning(f"Network error fetching research source {url}: {exc}")
        return None
    except Exception as exc:
        logger.error(f"Unexpected error fetching research source {url}: {exc}")
        return None


def extract_page_content(html_text: str, url: str) -> Dict[str, str]:
    """
    Extract title, cleaned body text content, and domain source name from raw HTML.
    Strips script, style, header, footer, nav tags and HTML elements.
    """
    domain = urlparse(url).netloc.replace("www.", "") or "Web Source"

    if not html_text or not html_text.strip():
        return {
            "title": domain,
            "content": "",
            "source_name": domain,
        }

    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    if title_match:
        raw_title = title_match.group(1)
        title = html.unescape(re.sub(r"<[^>]+>", " ", raw_title)).strip()
        title = " ".join(title.split())
    else:
        title = domain

    # Remove non-content tags (script, style, header, footer, nav, noscript)
    cleaned = re.sub(
        r"<(script|style|header|footer|nav|noscript|svg)[^>]*>.*?</\1>",
        " ",
        html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Remove all HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)

    # Unescape HTML entities
    cleaned = html.unescape(cleaned)

    # Normalize whitespace
    content = " ".join(cleaned.split()).strip()

    return {
        "title": title if title else domain,
        "content": content,
        "source_name": domain,
    }
