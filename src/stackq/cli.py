import typer
from rich.console import Console

from stackq import __version__

app = typer.Typer(help="Ask questions about the STACKIT docs")
console = Console()

@app.command()
def scrape(limit: int = typer.Option(None, help="Only scrape the first N pages")):
    # Download the docs into data/raw/.
    from stackq.scraper import scrape_all
    _, failed = scrape_all(limit=limit)
    if failed:
        # non-zero exit code, so scripts/CI notice that pages are missing
        raise typer.Exit(code=1)

@app.command()
def index():
    # from stackq.rag import index_all
    from stackq.indexer import index_and_store
    _, failed = index_and_store()
    if failed:
        # non-zero exit code, so scripts/CI notice that pages are missing
        raise typer.Exit(code=1)

@app.command()
def ask(question: str):
    # Ask a question about the docs.
    from stackq.rag import ask as rag_ask
    answer = rag_ask(question)
    console.print(answer.content)

@app.command()
def evaluate(k: int = 10):
    # Evalute raq
    from stackq.evaluate import evaluate as rag_eval
    rag_eval(k=k)

@app.command()
def version():
    # Show the stackq version.
    console.print(f"stackq {__version__}")

if __name__ == "__main__":
    app()
