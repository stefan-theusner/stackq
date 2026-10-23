import typer
from rich.console import Console

from stackq import __version__

app = typer.Typer(help="Ask questions about the STACKIT docs using local AI models.")
console = Console()


@app.command()
def scrape(limit: int = typer.Option(None, help="Only scrape the first N pages")):
    """Download the docs into data/raw/."""
    from stackq.scraper import scrape_all

    scrape_all(limit=limit)


@app.command()
def index():
    """Chunk, embed and store the scraped docs in PostgreSQL."""
    from stackq.rag import index_all

    index_all()


@app.command()
def ask(question: str):
    """Ask a question about the docs."""
    from stackq.rag import ask as rag_ask

    console.print(rag_ask(question))


@app.command()
def version():
    """Show the stackq version."""
    console.print(f"stackq {__version__}")


if __name__ == "__main__":
    app()
