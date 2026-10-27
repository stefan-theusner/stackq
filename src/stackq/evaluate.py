import json
from pathlib import Path

from stackq.db import connect
from stackq.rag import retrieve


def evaluate(path: str = "evals/retrieval.json", k: int = 10):
    cases = json.loads(Path(path).read_text())
    hits = 0
    with connect() as conn:
        for case in cases:
            urls = {row["url"] for row in retrieve(conn, case["question"], k)}
            hit = not urls.isdisjoint(case["urls"])
            hits += hit
            print(f"{'✓' if hit else '✗'} {case['question']}")
            if not hit:
                for url in sorted(urls):
                    print(f"    {url}")
    print(f"hit rate @{k}: {hits}/{len(cases)} = {hits / len(cases):.0%}")


if __name__ == "__main__":
    evaluate()
