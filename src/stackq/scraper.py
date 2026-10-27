import json
import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from stackq import __version__
from stackq.config import DOCS_BASE_URL, raw_data_dir
from stackq.model import MetaData

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
REQUEST_DELAY_SECONDS = 1.0
USER_AGENT = f"stackq/{__version__}"
# one Session reuses the TLS connection across requests
SESSION = requests.Session()
SESSION.headers["User-Agent"] = USER_AGENT
# Explicit list, so a two-letter category like /ai/ is not mistaken for a locale
LOCALES = ("de",)


def fetch(url: str, timeout: float = 10) -> requests.Response:
    response = SESSION.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def get_page_urls() -> list[str]:
    sitemap = fetch(f"{DOCS_BASE_URL}/sitemap-0.xml", timeout=30)
    return parse_sitemap(sitemap.text)


def parse_sitemap(xml_text: str) -> list[str]:
    root = ET.fromstring(xml_text)
    urls = [loc.text.strip() for loc in root.iter(f"{SITEMAP_NS}loc") if loc.text]
    return [u for u in urls if should_scrape(u)]


def should_scrape(page_url: str) -> bool:
    category = scrape_category_from_url(page_url)
    return (
        page_url != f"{DOCS_BASE_URL}/"
        and page_url != f"{DOCS_BASE_URL}/{category}/"
        and "/de/" not in page_url
    )


def scrape_category_from_url(page_url: str) -> str | None:
    locales = "|".join(LOCALES)
    pattern = re.compile(rf"^{re.escape(DOCS_BASE_URL)}/(?:(?:{locales})/)?([^/]+)")
    match = pattern.match(page_url)
    return match.group(1) if match else None


def url_to_file_name(page_url: str) -> str:
    """/<locale>/<category>/a/b/ -> a-b; the whole path keeps same-slug pages apart."""
    parts = urlparse(page_url).path.strip("/").split("/")
    if parts[0] in LOCALES:
        parts = parts[1:]
    return "-".join(parts[1:]) or "index"


def page_paths(page_url: str, data_dir: Path) -> tuple[Path, Path]:
    category = scrape_category_from_url(page_url) or "uncategorized"
    folder = data_dir / category
    name = url_to_file_name(page_url)
    # not with_suffix(): it would turn "v1.30" into "v1.md"
    return folder / f"{name}.md", folder / f"{name}.json"


def html_to_markdown(html: str | bytes) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    title = soup.find("title")
    if title:
        title_text = title.get_text(strip=True).removesuffix(" | Docs")
    elif h1:
        title_text = h1.get_text(strip=True)
    else:
        title_text = ""
    main_content = soup.select_one("main .sl-markdown-content")
    if not main_content:
        print(" Class sl-markdown-content not found.")
        main_content = soup.find(["main", "article"]) or soup

    # decompose() drops the element with its text; markdownify's strip=[...] keeps the text
    for el in main_content.select("script, style, nav, .sl-anchor-link, .expressive-code .copy"):
        el.decompose()

    # Expressive Code wraps each code line in a div, which markdownify turns into paragraphs
    for pre in main_content.select("pre"):
        lines = pre.select(".ec-line")
        if lines:
            code = "\n".join(line.get_text() for line in lines)
            pre.clear()
            pre.append(code)

    return title_text, md(str(main_content), heading_style="ATX")


def scrape_page(page_url: str, data_dir: Path) -> MetaData | None:
    print(f"About to scrape: {page_url}")
    category = scrape_category_from_url(page_url) or "uncategorized"
    content_path, metadata_path = page_paths(page_url, data_dir)

    try:
        os.makedirs(content_path.parent, exist_ok=True)

        response = fetch(page_url)
        title_text, markdown_text = html_to_markdown(response.content)

        meta_data = MetaData(
            url=page_url,
            category=category,
            title=title_text,
            md=content_path.name,
        )
        # .md before .json: the indexer keys on *.json, so a .json means the page is complete.
        # json.dumps quotes the title, so ":" or "#" can't break the YAML.
        md_content = (
            f"---\ntitle: {json.dumps(title_text, ensure_ascii=False)}\n"
            f"source: {page_url}\n---\n\n{markdown_text}"
        )
        with open(content_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(asdict(meta_data), f, ensure_ascii=False, indent=4)

        print(f"Page scraped: {metadata_path}")
        return meta_data

    except (requests.RequestException, OSError) as e:
        print(f"Could not scrape url {page_url}: {e}")
        return None


def scrape_all(limit: int | None = None) -> tuple[int, int]:
    # Return (ok, failed) page counts.
    data_dir = raw_data_dir()
    page_urls = get_page_urls()

    if limit is not None:
        page_urls = page_urls[:limit]
    print(f"About to scrape {len(page_urls)} pages")
    ok = failed = 0
    for i, page_url in enumerate(page_urls):
        if i > 0:
            time.sleep(REQUEST_DELAY_SECONDS)
        if scrape_page(page_url, data_dir) is None:
            failed += 1
        else:
            ok += 1
    print(f"Done: {ok} pages scraped, {failed} failed")
    return ok, failed


if __name__ == "__main__":
    scrape_all()
