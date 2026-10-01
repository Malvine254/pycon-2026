import json

from pycord.agent import Agent, convert_currency
from pycord.config import DOCS_DIR
from pycord.rag import BM25Retriever, Chunk, build_rag_messages, load_documents


def test_bm25_ranks_relevant_chunk_first():
    chunks = [
        Chunk("a.md", "Plant maize at the start of the long rains."),
        Chunk("b.md", "Never share your M-Pesa PIN."),
    ]
    hits = BM25Retriever(chunks).search("when to plant maize")
    assert hits[0][0].source == "a.md"


def test_no_match_returns_empty():
    assert BM25Retriever([Chunk("a.md", "maize")]).search("blockchain") == []


def test_workshop_docs_load_and_search():
    retriever = BM25Retriever(load_documents(DOCS_DIR))
    assert retriever.chunks
    assert retriever.search("M-Pesa PIN")[0][0].source == "mpesa_safety.md"


def test_rag_messages_contain_citations():
    messages = build_rag_messages("q", [(Chunk("a.md", "text"), 1.0)])
    assert "[1] (a.md)" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "q"}


def test_convert_currency():
    assert convert_currency(1, "usd", "kes")["amount"] == 129.0
    assert "error" in convert_currency(1, "XYZ", "KES")


def test_agent_rejects_unknown_tool_and_bad_args():
    agent = Agent(provider=None)  # provider is not called in this test
    assert "error" in json.loads(agent.call_tool("delete_everything", "{}"))
    assert "error" in json.loads(agent.call_tool("convert_currency", "not json"))
    assert "search_docs" not in agent.functions
