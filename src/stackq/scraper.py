"""Stage 1: fetch doc pages and save them as JSON."""

from rich.console import Console

console = Console()


def get_page_urls() -> list[str]:
    """Return all doc page URLs (hint: start with /sitemap.xml)."""
    # TODO: fetch the sitemap with requests, parse <loc> entries with BeautifulSoup
    raise NotImplementedError


def scrape_page(url: str) -> dict:
    """Return {'url', 'title', 'text'} for a single page."""
    # TODO: fetch the page, extract the main content, skip nav/footer
    raise NotImplementedError


def scrape_all(limit: int | None = None) -> None:
    """Scrape every page and write it to data/raw/. Be polite: sleep between requests."""
    # TODO
    raise NotImplementedError
