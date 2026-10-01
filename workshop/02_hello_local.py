# %% [markdown]
# # Module 2 - Hello, local (Foundry Local / Ollama)
# The same OpenAI-style API, but the model runs on your laptop: no internet, no cost per request.
#
# Before this module, in a terminal:
# - Foundry Local: `foundry model run phi-3.5-mini` (first run downloads the model)
# - Ollama: `ollama pull qwen2.5:1.5b` and set `LOCAL_RUNTIME=ollama` in `.env`

# %%
from pycord.config import Settings
from pycord.providers import get_local_provider

settings = Settings.from_env()
local = get_local_provider(settings)
print("Runtime available:", local.is_available())

# %%
# The first call may take a while: the model is loaded into memory.
result = local.ask(
    "In two sentences, why should a Kenyan Python developer learn about AI?",
    system="You are a friendly Kenyan tech mentor.",
)
print(result.text)
print(result.summary())

# %% [markdown]
# ## Under the hood
# Local runtimes expose an OpenAI-compatible endpoint, so we use the exact same client.

# %%
print("Base URL:", local.client.base_url)
print("Model id:", local.model)

# %% [markdown]
# ## Exercises
# 1. Turn off Wi-Fi and run the cell again. It still works!
# 2. Compare latency and quality with Module 1. When is "good enough" good enough?
# 3. Try a smaller model (`LOCAL_MODEL=qwen2.5-0.5b`) - faster, but how is the quality?
