"""Web scraping and URL utilities."""

from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup


def fetch(url: str, timeout=20) -> tuple[str, list[str]]:
    """Fetch a URL and extract text content and links.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds (default: 20)

    Returns:
        Tuple of (text_content, links)
        - text_content: Extracted text (max 20,000 chars)
        - links: List of absolute URLs found on page (max 60 links)
    """
    r = httpx.get(url, timeout=timeout, follow_redirects=True)
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    links = [a.get("href") for a in soup.find_all("a", href=True)]
    links = [urljoin(url, h) for h in links if h]
    return text[:20000], links[:60]


def same_origin(root: str, u: str) -> bool:
    """Check if two URLs have the same origin (domain).

    Args:
        root: Root URL
        u: URL to check

    Returns:
        True if URLs have the same netloc (domain), False otherwise
    """
    return urlparse(root).netloc == urlparse(u).netloc
