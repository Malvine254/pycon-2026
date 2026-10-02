# %% [markdown]
# # Module 4 - The hybrid router
# Rules (see `src/pycord/router.py`), in order:
# 1. Personal data -> **local only**, never falls back to the cloud
# 2. Cloud unreachable -> local
# 3. No local runtime -> cloud
# 4. Complex task -> cloud
# 5. Everything else -> local (free and private)
# If the chosen model fails, the router falls back to the other one (except for rule 1).
# No local model yet? Rule 3 sends everything to the cloud, and rule 1 refuses personal data.

# %%
from dataclasses import replace

from pycord.config import Settings
from pycord.labkit import LOCAL_SETUP_HINT
from pycord.providers import get_cloud_provider, get_local_provider
from pycord.router import HybridRouter

settings = Settings.from_env()
router = HybridRouter(get_local_provider(settings), get_cloud_provider(settings))
if not router.local.is_available():
    print(LOCAL_SETUP_HINT, "\n")

prompts = [
    "Habari yako?",
    "Compare Django and FastAPI for building an M-Pesa payments API, step by step.",
    "My number is 0712345678, remind me to pay rent.",
]
for prompt in prompts:
    try:
        decision = router.decide(prompt)
        print(f"{decision.target:>7} | {decision.reason} | {prompt}")
    except RuntimeError as exc:
        print(f"refused | {exc} | {prompt}")

# %%
for prompt in prompts[:2]:
    try:
        result = router.ask(prompt)
    except RuntimeError as exc:
        print("No model could answer:", exc)
        continue
    print(result.summary(), "-", result.route_reason)
    print(result.text.strip()[:300], "\n")

# %% [markdown]
# ## Simulate a network outage
# Point the cloud provider at an unreachable host - the router keeps working locally.
# Without a local model there is nothing left to answer, and the router says so clearly.

# %%
offline_cloud = get_cloud_provider(replace(settings, foundry_endpoint="https://offline.invalid"))
offline_router = HybridRouter(get_local_provider(settings), offline_cloud)
try:
    result = offline_router.ask("Compare Python and JavaScript in three bullet points.")
    print(result.summary(), "-", result.route_reason)
except RuntimeError as exc:
    print("Offline and no local model:", exc)
    print("This is exactly why the hybrid design needs a local model - install one to see it keep working.")

# %% [markdown]
# ## Exercises
# 1. Add a rule: questions written in Swahili go to the cloud for better quality.
#    Hint: check for words like "nini", "gani", "jinsi" in `HybridRouter.decide`.
# 2. Add a daily budget: once total `cost_kes` passes KES 50, route everything locally.
