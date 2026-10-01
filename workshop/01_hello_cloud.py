# %% [markdown]
# # Module 1 - Hello, cloud (Microsoft Foundry)
# Call a model deployed in Microsoft Foundry with the `openai` SDK.
# Auth: Entra ID via `az login` (recommended) or `FOUNDRY_API_KEY` in `.env`.

# %%
from pycord.config import Settings
from pycord.providers import get_cloud_provider

settings = Settings.from_env()
cloud = get_cloud_provider(settings)
print("Endpoint:  ", settings.foundry_endpoint)
print("Deployment:", settings.foundry_deployment)

# %%
result = cloud.ask(
    "In two sentences, why should a Kenyan Python developer learn about AI?",
    system="You are a friendly Kenyan tech mentor.",
)
print(result.text)
print(result.summary())

# %% [markdown]
# ## Under the hood
# `cloud.ask(...)` is a thin wrapper around the raw SDK call below.

# %%
response = cloud.client.chat.completions.create(
    model=settings.foundry_deployment,
    messages=[{"role": "user", "content": "Say 'Habari PyCon Kenya!' and nothing else."}],
)
print(response.choices[0].message.content)
print(response.usage)

# %% [markdown]
# ## Exercises
# 1. Pass `temperature=0` and then `temperature=1` to `cloud.ask` and compare answers.
# 2. Ask the same question in Swahili. How good is the reply?
# 3. Using `result.cost_kes`, how many requests like this fit in a KES 100 budget?
