import json
import re
from dataclasses import dataclass
from pathlib import Path

import markdown
from markdownify import markdownify
from ollama import Message


class ChatMessage(Message):
    pass

@dataclass(frozen=True)
class MetaData:
    url: str
    category: str
    title: str
    md: str

@dataclass(frozen=True)
class MetaMarkdownPair:
    meta: Path
    content: Path

    @staticmethod
    def clean_markdown(text: str) -> str:
        html = markdown.markdown(text, extensions=["fenced_code", "tables"])
        md = markdownify(
            html,
            heading_style="ATX",     # "# Heading" instead of underlined headings
            bullets="-",             # one bullet style
            strip=["img"],           # drop images (remove if you want to keep them)
        )
        md = re.sub(r"\n{3,}", "\n\n", md)   # markdownify leaves extra blank lines
        # FAQ accordions put headings inside list items ("- ## Topic", "  ### Question");
        # the header splitter only sees headings at the start of a line
        md = re.sub(r"^[ \t]*(?:[-*+][ \t]+)?(#{1,6} )", r"\1", md, flags=re.MULTILINE)
        return md.strip()

    def read_meta(self) -> MetaData:
        with open(self.meta, 'r', encoding="utf-8") as f:
            return  MetaData(**json.load(f))

    @staticmethod
    def strip_front_matter(text: str) -> str:
        # the scraper starts each .md with "---\ntitle: ...\nsource: ...\n---"; that data is
        # already in the .json, and embedding it would put title/URL into the first chunk
        return re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)

    def read_content(self):
        text = self.content.read_text(encoding="utf-8")
        return self.clean_markdown(self.strip_front_matter(text))