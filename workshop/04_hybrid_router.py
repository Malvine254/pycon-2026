# %% [markdown]
# # Module 4 - The hybrid router
# Rules (see `src/pycord/router.py`), in order:
# 1. Personal data -> **local only**, never falls back to the cloud
# 2. Cloud unreachable -> local
# 3. No local runtime -> cloud
# 4. Complex task -> cloud
# 5. Everything else -> local (free and private)
# If the chosen model fails, the router falls back to the other one (except for rule 1).

# %%
from dataclasses import replace

from pycord.config import Settings
from pycord.providers import get_cloud_provider, get_local_provider
from pycord.router import HybridRouter

settings = Settings.from_env()
router = HybridRouter(get_local_provider(settings), get_cloud_provider(settings))

prompts = [
    "Habari yako?",
    "Compare Django and FastAPI for building an M-Pesa payments API, step by step.",
    "My number is 0712345678, remind me to pay rent.",
]
for prompt in prompts:
    decision = router.decide(prompt)
    print(f"{decision.target:>5} | {decision.reason} | {prompt}")

# %%
for prompt in prompts[:2]:
    result = router.ask(prompt)
    print(result.summary(), "-", result.route_reason)
    print(result.text.strip()[:300], "\n")

# %% [markdown]
# ## Simulate a network outage
# Point the cloud provider at an unreachable host - the router keeps working locally.

# %%
offline_cloud = get_cloud_provider(replace(settings, foundry_endpoint="https://offline.invalid"))
offline_router = HybridRouter(get_local_provider(settings), offline_cloud)
result = offline_router.ask("Compare Python and JavaScript in three bullet points.")
print(result.summary(), "-", result.route_reason)

# %% [markdown]
# ## Exercises
# 1. Add a rule: questions written in Swahili go to the cloud for better quality.
#    Hint: check for words like "nini", "gani", "jinsi" in `HybridRouter.decide`.
# 2. Add a daily budget: once total `cost_kes` passes KES 50, route everything locally.
