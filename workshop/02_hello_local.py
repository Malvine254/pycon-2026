# %% [markdown]
# # Module 2 - Hello, local (Foundry Local / Ollama)
# The same OpenAI-style API, but the model runs on your laptop: no internet, no cost per request.
#
# Before this module, in a terminal:
# - Foundry Local: `foundry model download phi-3.5-mini`, then `foundry run phi-3.5-mini`
# - Ollama: `ollama pull qwen2.5:1.5b` and set `LOCAL_RUNTIME=ollama` in `.env`
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
# 3. Try a smaller model (`LOCAL_MODEL=qwen2.5-0.5b`) - faster, but how is the quality?
