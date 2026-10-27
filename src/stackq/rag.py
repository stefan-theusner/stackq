import toons
from ollama import ChatResponse, Client
from psycopg.rows import dict_row

from stackq.config import CHAT_MODEL, EMBED_MODEL, OLLAMA_HOST
from stackq.db import connect, search
from stackq.model import ChatMessage

client = Client(host=OLLAMA_HOST)

SYS_MESSAGES: list[ChatMessage] = [
    ChatMessage(
        role="system", 
        content="Answer the question using ONLY the context below. If the answer is not in the context, say you don't know. Cite the source URLs."
        )
]

def embed(text: str) -> list[float]:
    return client.embed(model=EMBED_MODEL, input=f"search_query: {text}")["embeddings"][0]

def retrieve(conn, question: str, k: int = 10) -> list[dict]:
    return search(conn, embed(question), k).fetchall()

def retrieve_context(question: str) -> list[ChatMessage]:
    with connect() as conn:
        return [ChatMessage(role="user", content=toons.dumps(row)) for row in retrieve(conn, question)]

def chat(messages: list[ChatMessage]):
    chat_response: ChatResponse = client.chat(model=CHAT_MODEL, messages=messages, options={"num_ctx": 8192})
    response_message = chat_response.message
    # build history
    messages.append(ChatMessage(role="assistant", content=response_message.content))
    return chat_response.message

def ask(question: str) -> str:
    context_messages = retrieve_context(question)
    # build the message chain
    messages = SYS_MESSAGES + [ChatMessage(role="user", content=f"Question: {question}")] + context_messages
    # prepare chat
    return chat(messages)

if __name__ == "__main__":
    answer = ask("How can i setup a DNS environment?")
    print(answer.content)