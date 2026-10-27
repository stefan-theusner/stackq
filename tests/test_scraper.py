from stackq import scraper
from stackq.config import DOCS_BASE_URL
from stackq.model import MetaMarkdownPair, get_meta_markdown_pairs

SITEMAP = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{DOCS_BASE_URL}/</loc></url>
  <url><loc>{DOCS_BASE_URL}/stackit/</loc></url>
  <url><lastmod>2026-01-01</lastmod><loc>{DOCS_BASE_URL}/stackit/ske/create/</loc></url>
  <url><loc>{DOCS_BASE_URL}/de/stackit/ske/create/</loc></url>
</urlset>"""


def test_parse_sitemap_filters_and_finds_loc_anywhere():
    assert scraper.parse_sitemap(SITEMAP) == [f"{DOCS_BASE_URL}/stackit/ske/create/"]


def test_url_to_file_name_uses_full_path():
    a = scraper.url_to_file_name(f"{DOCS_BASE_URL}/stackit/ske/overview/")
    b = scraper.url_to_file_name(f"{DOCS_BASE_URL}/stackit/dns/overview/")
    assert a == "ske-overview"
    assert a != b
    # with or without trailing slash gives the same name
    assert scraper.url_to_file_name(f"{DOCS_BASE_URL}/stackit/ske/overview") == a


def test_html_to_markdown_fallback_and_removes_script_text():
    html = (
        "<html><head><title>SKE: Intro</title></head><body>"
        "<main><h1>Hello</h1><script>var secret = 1;</script><nav>Menu</nav></main>"
        "</body></html>"
    )
    title, markdown = scraper.html_to_markdown(html)
    assert title == "Hello"  # <h1> wins over <title>
    assert "# Hello" in markdown
    assert "secret" not in markdown
    assert "Menu" not in markdown


def test_html_to_markdown_without_main_uses_whole_page():
    _, markdown = scraper.html_to_markdown("<html><body><p>Just text</p></body></html>")
    assert "Just text" in markdown


def test_title_falls_back_to_title_tag_without_suffix():
    title, _ = scraper.html_to_markdown("<title>ALB Ingress | Docs</title><main>x</main>")
    assert title == "ALB Ingress"


def test_html_to_markdown_keeps_expressive_code_lines_and_indent():
    # trimmed copy of how Starlight / Expressive Code renders a YAML block
    html = (
        '<main><div class="sl-markdown-content"><div class="expressive-code"><figure>'
        '<pre data-language="yaml"><code>'
        '<div class="ec-line"><div class="code">metadata:</div></div>'
        '<div class="ec-line"><div class="code"><span class="indent">  </span>'
        "name: stackit-alb</div></div>"
        '</code></pre><div class="copy"><button>Copy to clipboard</button></div>'
        "</figure></div></div></main>"
    )
    _, markdown = scraper.html_to_markdown(html)
    assert "metadata:\n  name: stackit-alb" in markdown
    assert "Copy to clipboard" not in markdown


def test_strip_front_matter():
    text = '---\ntitle: "A: B"\nsource: https://x/\n---\n\n# Body\n\n---\nmore'
    assert MetaMarkdownPair.strip_front_matter(text) == "\n# Body\n\n---\nmore"
    # no front matter -> unchanged
    assert MetaMarkdownPair.strip_front_matter("# Body") == "# Body"


META_JSON = '{"url": "u", "category": "c", "title": "t", "md": "m.md"}'
FRONT_MATTER = '---\ntitle: "T"\nsource: u\n---\n\nbody'


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_page_paths_keep_dots_in_names(tmp_path):
    notes = f"{DOCS_BASE_URL}/stackit/ske/release-notes"
    md_30, json_30 = scraper.page_paths(f"{notes}/v1.30/", tmp_path)
    md_31, json_31 = scraper.page_paths(f"{notes}/v1.31/", tmp_path)
    assert md_30.name == "ske-release-notes-v1.30.md"
    assert json_30.name == "ske-release-notes-v1.30.json"
    assert md_30 != md_31 and json_30 != json_31


def test_meta_markdown_pairs_with_dotted_name(monkeypatch, tmp_path):
    monkeypatch.setenv("STACKQ_DATA_DIR", str(tmp_path))
    write(tmp_path / "stackit" / "x-v1.30.json", META_JSON)
    write(tmp_path / "stackit" / "x-v1.30.md", FRONT_MATTER)
    [pair] = get_meta_markdown_pairs()
    assert pair.meta == tmp_path / "stackit" / "x-v1.30.json"
    assert pair.content == tmp_path / "stackit" / "x-v1.30.md"


def test_category_two_letter_is_not_a_locale():
    assert scraper.scrape_category_from_url(f"{DOCS_BASE_URL}/ai/model-serving/") == "ai"
    assert scraper.scrape_category_from_url(f"{DOCS_BASE_URL}/de/stackit/ske/") == "stackit"


def test_scrape_all_limit_and_counts(monkeypatch, tmp_path):
    scraped = []

    def fake_scrape_page(url, data_dir):
        scraped.append(url)
        return None if url == "u2" else object()  # u2 "fails"

    monkeypatch.setenv("STACKQ_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(scraper, "get_page_urls", lambda: ["u1", "u2"])
    monkeypatch.setattr(scraper, "scrape_page", fake_scrape_page)
    monkeypatch.setattr(scraper.time, "sleep", lambda _: None)
    assert scraper.scrape_all(limit=0) == (0, 0)
    assert scraped == []
    assert scraper.scrape_all(limit=1) == (1, 0)
    assert scraped == ["u1"]
    assert scraper.scrape_all() == (1, 1)
