# %% [markdown]
# # Module 2 - Hello, local (Phi on Foundry Local)
# The same OpenAI-style API, but the model runs on your laptop: no internet, no cost per request.
#
# Before this module, in a terminal:
# - `foundry server start`, then `foundry model load phi-3.5-mini`
# - Full steps and port checks: labs/00-setup.md, Step 2
#
# No local model yet? The lab falls back to the cloud model so you can still follow along.

# %%
from pycord.config import Settings
from pycord.labkit import local_or_cloud

settings = Settings.from_env()
model = local_or_cloud(settings)
print(f"Using: {model.name} (local: {model.is_local})")

# %%
# The first local call may take a while: the model is loaded into memory.
result = model.ask(
    "In two sentences, why should a Kenyan Python developer learn about AI?",
    system="You are a friendly Kenyan tech mentor.",
)
print(result.text)
print(result.summary())

# %% [markdown]
# ## Under the hood
# Local runtimes expose an OpenAI-compatible endpoint, so we use the exact same client.

# %%
print("Base URL:", model.client.base_url)
print("Model id:", model.model)

# %% [markdown]
# ## Exercises
# 1. Turn off Wi-Fi and run the cell again. It still works!
# 2. Compare latency and quality with Module 1. When is "good enough" good enough?
# 3. Try another Phi model (`LOCAL_MODEL=phi-4-mini`, then `foundry model load phi-4-mini`) - how do speed and quality change?
