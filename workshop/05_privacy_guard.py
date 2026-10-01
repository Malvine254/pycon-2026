# %% [markdown]
# # Module 5 - Privacy guard
# Kenya's Data Protection Act (2019) makes personal data handling a legal concern.
# `src/pycord/privacy.py` detects Kenyan phone numbers, KRA PINs, M-Pesa codes,
# ID numbers and emails so the router can keep them on the device.

# %%
from pycord.privacy import contains_pii, detect_pii, redact

samples = [
    "QFT3XYZ12A Confirmed. Ksh1,500.00 sent to JOHN 0712345678",
    "My KRA PIN is A012345678Z and my ID number 12345678",
    "Email wanjiku@example.co.ke about the meetup",
    "How do I plant maize during the long rains?",
]
for text in samples:
    print(contains_pii(text), [(m.kind, m.value) for m in detect_pii(text)])

# %% [markdown]
# ## Pattern 1: keep it local
# The router sends anything with personal data to the local model and never falls back.

# %%
from pycord.config import Settings
from pycord.providers import get_cloud_provider, get_local_provider
from pycord.router import HybridRouter

settings = Settings.from_env()
router = HybridRouter(get_local_provider(settings), get_cloud_provider(settings))
result = router.ask(f"Explain this M-Pesa message in simple words: {samples[0]}")
print(result.summary(), "-", result.route_reason)
print(result.text)

# %% [markdown]
# ## Pattern 2: redact, then use the cloud
# When you need the bigger model, strip the personal data first.

# %%
safe_text = redact(samples[0])
print(safe_text)
cloud = get_cloud_provider(settings)
print(cloud.ask(f"Explain this M-Pesa message in simple words: {safe_text}").text)

# %% [markdown]
# ## Exercises
# 1. Add a pattern for Kenyan number plates such as `KDA 123A` to `PATTERNS`.
#    Hint: `r"\bK[A-Z]{2}\s?\d{3}[A-Z]\b"`
# 2. Add a test for it in `tests/test_privacy.py` and run `pytest`.
