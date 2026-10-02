# %% [markdown]
# # Module 7 - Agent with tools (stretch goal)
# The model decides which Python function to call; we run it and send back the result.
# Tool calling works best with the cloud model; local Phi answers text-only questions.

# %%
from pycord.agent import Agent
from pycord.config import DOCS_DIR, Settings
from pycord.providers import get_cloud_provider
from pycord.rag import BM25Retriever, load_documents

settings = Settings.from_env()
agent = Agent(get_cloud_provider(settings), retriever=BM25Retriever(load_documents(DOCS_DIR)))
print("Tools:", list(agent.functions))

# %%
for question in [
    "What time is it in Nairobi right now?",
    "How much is 250 USD in KES?",
    "Bei ya dola 100 ni shilingi ngapi za Kenya?",
    "What spacing should I use for maize, and what time is it now?",
]:
    print(f"\nQ: {question}")
    print("A:", agent.run(question))

# %% [markdown]
# ## Exercises
# 1. Add a tool `mpesa_fee(amount)` that returns a (made-up) transaction fee and register it
#    in `TOOLS` and `Agent.functions` in `src/pycord/agent.py`.
# 2. Try the agent with the local provider: `Agent(get_local_provider(settings))`.
