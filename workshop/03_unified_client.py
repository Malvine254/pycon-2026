# %% [markdown]
# # Module 3 - One interface, many models
# `Provider` (see `src/pycord/providers/base.py`) hides the differences between cloud and local.
# Every provider has `.ask()`, `.chat()`, `.is_available()` and returns a `ChatResult`.

# %%
from pycord.config import Settings
from pycord.providers import get_cloud_provider, get_local_provider

settings = Settings.from_env()
providers = [get_local_provider(settings), get_cloud_provider(settings)]

questions = [
    "What is the capital city of Kenya?",
    "Translate 'Welcome to PyCon Kenya' into Swahili.",
    "Write a Python one-liner that sums the numbers 1 to 100.",
]

# %%
for question in questions:
    print(f"\nQ: {question}")
    for provider in providers:
        if not provider.is_available():
            print(f"  {provider.name}: not available, skipping")
            continue
        result = provider.ask(question, temperature=0)
        print(f"  {result.summary()}\n    {result.text.strip()[:200]}")

# %% [markdown]
# ## Exercise: add your own provider
# Any OpenAI-compatible endpoint can become a provider. Fill in the skeleton below
# (for example LM Studio on `http://localhost:1234/v1`).

# %%
from openai import OpenAI

from pycord.providers import Provider


class MyProvider(Provider):
    name = "my-provider"
    is_local = True

    def _build_client(self) -> OpenAI:
        return OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

    def is_available(self) -> bool:
        return False  # TODO: check whether the server is running


# print(MyProvider("your-model-name").ask("Habari?").summary())
