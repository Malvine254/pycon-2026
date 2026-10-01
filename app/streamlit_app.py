"""Mela chat UI. Run with: streamlit run app/streamlit_app.py"""
import streamlit as st

from pycord.config import DOCS_DIR, Settings
from pycord.privacy import contains_pii
from pycord.providers import get_cloud_provider, get_local_provider
from pycord.rag import BM25Retriever, build_rag_messages, load_documents
from pycord.router import HybridRouter

st.set_page_config(page_title="Mela - Pycord")


@st.cache_resource
def load_stack():
    settings = Settings.from_env()
    local = get_local_provider(settings)
    cloud = get_cloud_provider(settings)
    return local, cloud, HybridRouter(local, cloud), BM25Retriever(load_documents(DOCS_DIR))


local, cloud, router, retriever = load_stack()

st.title("Mela")
st.caption("Pycord - hybrid AI with Microsoft Foundry and local models - PyCon Kenya 2026")

with st.sidebar:
    mode = st.radio("Route", ["Auto (hybrid)", "Local only", "Cloud only"])
    use_rag = st.toggle("Answer from workshop documents (RAG)", value=False)
    st.write(f"Local `{local.name}`: {'ready' if local.is_available() else 'not found'}")
    st.write(f"Cloud `{cloud.name}`: {'reachable' if cloud.is_available() else 'offline'}")
    if st.button("Clear chat"):
        st.session_state.history = []

if "history" not in st.session_state:
    st.session_state.history = []

for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
        if turn.get("meta"):
            st.caption(turn["meta"])

if prompt := st.chat_input("Uliza swali... / Ask a question..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if use_rag:
        messages = build_rag_messages(prompt, retriever.search(prompt))
    else:
        messages = [{"role": t["role"], "content": t["content"]} for t in st.session_state.history]

    target = {"Auto (hybrid)": router, "Local only": local, "Cloud only": cloud}[mode]
    with st.chat_message("assistant"):
        if mode == "Cloud only" and contains_pii(prompt):
            st.warning("This message contains personal data and will be sent to the cloud.")
        try:
            with st.spinner("Thinking..."):
                result = target.chat(messages)
            meta = result.summary() + (f" - {result.route_reason}" if result.route_reason else "")
            st.markdown(result.text)
            st.caption(meta)
            st.session_state.history.append({"role": "assistant", "content": result.text, "meta": meta})
        except Exception as exc:
            st.error(f"{type(exc).__name__}: {exc}")
