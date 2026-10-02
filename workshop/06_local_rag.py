# %% [markdown]
# # Module 6 - Local RAG (answers from your own documents)
# Retrieval-Augmented Generation: search our documents, then let the model answer from them.
# We use BM25 keyword search - pure Python, works offline, nothing to download.

# %%
from pycord.config import DOCS_DIR, Settings
from pycord.labkit import local_or_cloud
from pycord.rag import BM25Retriever, build_rag_messages, load_documents

chunks = load_documents(DOCS_DIR)
retriever = BM25Retriever(chunks)
print(f"Loaded {len(chunks)} chunks from {DOCS_DIR}")

# %%
for chunk, score in retriever.search("fertiliser for maize at planting"):
    print(f"{score:.2f}  {chunk.source}: {chunk.text[:80]!r}")

# %%
# Uses the local model when installed, otherwise the cloud model so you can follow along.
model = local_or_cloud(Settings.from_env())


def ask_docs(question: str) -> None:
    hits = retriever.search(question)
    result = model.chat(build_rag_messages(question, hits))
    print(f"Q: {question}\n{result.text.strip()}\n{result.summary()}\n")


ask_docs("When should I plant maize?")
ask_docs("Someone says they sent me money by mistake. What should I do?")
ask_docs("Nifanye nini nikipokea ujumbe wa ulaghai?")

# %% [markdown]
# ## Exercises
# 1. Add your own `.md` file to `data/docs/` (e.g. your county's services or your meetup FAQ)
#    and ask questions about it.
# 2. Ask something that is NOT in the documents. Does the model admit it doesn't know?
# 3. Swap `local` for the cloud provider and compare answers.
