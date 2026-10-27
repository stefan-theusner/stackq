from pathlib import Path

from stackq.config import raw_data_dir
from stackq.model import MetaMarkdownPair


def get_meta_markdown_pairs() -> list[MetaMarkdownPair]:
    data_dir = raw_data_dir()

    def get_file_pair(file) -> MetaMarkdownPair:
        path = Path(file)
        pair = MetaMarkdownPair(
            meta=path.with_suffix(".json"),
            content=path.with_suffix(".md"),
        )
        return pair

    folder_path = Path(data_dir)
    file_pairs = [get_file_pair(file) for file in folder_path.rglob("*.json") if file.is_file()]

    return file_pairs
