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
        result = provider.ask(question)
        print(f"  {result.summary()}\n    {result.text.strip()[:200]}")

# %% [markdown]
# ## Exercise: add your own provider
# Any OpenAI-compatible endpoint can become a provider. Fill in the skeleton below
# (for example LM Studio on `http://localhost:1234/v1`).

# %%
import os
import urllib.request

from openai import OpenAI

from pycord.providers import Provider


class MyProvider(Provider):
    name = "my-provider"
    is_local = True

    def __init__(self, model: str) -> None:
        super().__init__(model)
        self.base_url = os.getenv("MY_PROVIDER_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("MY_PROVIDER_API_KEY", "not-needed")

    def _build_client(self) -> OpenAI:
        if not self.base_url:
            raise RuntimeError("Set MY_PROVIDER_BASE_URL before using MyProvider.")
        return OpenAI(base_url=self.base_url, api_key=self.api_key)

    def is_available(self) -> bool:
        if not self.base_url:
            return False
        try:
            with urllib.request.urlopen(f"{self.base_url}/models", timeout=1.5) as response:
                return response.status == 200
        except OSError:
            return False


# Set MY_PROVIDER_BASE_URL and MY_PROVIDER_API_KEY in the environment before using this optional provider.
# print(MyProvider("your-model-name").ask("Habari?").summary())
