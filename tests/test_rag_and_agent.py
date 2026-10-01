import json
from types import SimpleNamespace

import pytest

from pycord.agent import Agent, convert_currency
from pycord.config import DOCS_DIR
from pycord.documents import DocumentError, extract_text, safe_name
from pycord.rag import BM25Retriever, Chunk, build_rag_messages, chunk_text, load_documents


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


@pytest.mark.parametrize(("is_local", "expect_phone"), [(True, True), (False, False)])
def test_search_docs_redacts_for_cloud(is_local, expect_phone):
    retriever = BM25Retriever([Chunk("upload/n.md", "Wanjiku contract phone 0712345678")])
    agent = Agent(SimpleNamespace(is_local=is_local), retriever)
    text = agent.call_tool("search_docs", '{"query": "Wanjiku contract"}')
    assert ("0712345678" in text) is expect_phone


@pytest.mark.parametrize(("language", "expected"), [("sw", "Kiswahili"), ("en", "Always reply in English")])
def test_respond_forces_language(language, expected):
    captured = {}

    def complete(messages, **kwargs):
        captured["system"] = messages[0]["content"]
        message = SimpleNamespace(content="Sawa", tool_calls=None)
        return SimpleNamespace(usage=None, choices=[SimpleNamespace(message=message)])

    provider = SimpleNamespace(is_local=True, name="fake", model="m", complete=complete, cost_kes=lambda p, c: 0.0)
    reply = Agent(provider).respond("Hi", language=language)
    assert expected in captured["system"]
    assert captured["system"].startswith("You are Mela")
    assert reply.text == "Sawa"


def test_chunk_text_splits_long_paragraphs():
    chunks = chunk_text("a.pdf", "word " * 1000, max_chars=200)
    assert len(chunks) > 1
    assert all(len(c.text) <= 200 for c in chunks)


def test_retriever_add_and_remove():
    retriever = BM25Retriever([Chunk("a.md", "maize")])
    retriever.add([Chunk("b.md", "blockchain ledger")])
    assert retriever.search("blockchain")[0][0].source == "b.md"
    retriever.remove_source("b.md")
    assert retriever.search("blockchain") == []


def test_safe_name_and_extract_text():
    assert safe_name("../../etc/evil<x>.md") == "evil_x_.md"
    assert safe_name("..\\..\\win.txt") == "win.txt"
    assert extract_text("a.md", b"# Hello") == "# Hello"
    with pytest.raises(DocumentError):
        extract_text("a.exe", b"MZ")
    with pytest.raises(DocumentError):
        extract_text("a.txt", b"   ")
