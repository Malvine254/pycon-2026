# %% [markdown]
# # Module 0 - Setup check
# Run cell by cell in VS Code ("Run Cell") or as a script: `python workshop/00_setup_check.py`.
# Every line should say OK. Being offline is fine - most modules work locally.

# %%
import shutil
import sys

from pycord.config import PROJECT_ROOT, Settings
from pycord.providers import get_cloud_provider, get_local_provider

settings = Settings.from_env()


def check(label: str, ok: bool, hint: str = "") -> None:
    print(f"[{'OK' if ok else '!!'}] {label}" + ("" if ok else f"  -> {hint}"))


check("Python >= 3.10", sys.version_info >= (3, 10), "Install Python 3.10 or newer")
check(".env file exists", (PROJECT_ROOT / ".env").exists(), "Copy .env.example to .env")
check("FOUNDRY_ENDPOINT set", bool(settings.foundry_endpoint), "Set FOUNDRY_ENDPOINT in .env")
check(
    "Cloud auth configured",
    bool(settings.foundry_api_key) or shutil.which("az") is not None,
    "Set FOUNDRY_API_KEY to the key from the facilitators (own Azure account: run `az login`)",
)
check("Cloud reachable", get_cloud_provider(settings).is_available(), "Offline? Modules 2, 5 and 6 still work")

local = get_local_provider(settings)
endpoint = local.endpoint()
print(f"     Phi endpoint: {endpoint or 'not found'}" + (" (from LOCAL_ENDPOINT)" if settings.local_endpoint else " (from `foundry server status`)"))
check(
    f"Local runtime ({local.name})",
    local.is_available(),
    "Optional for now - labs fall back to the cloud model. Install Foundry Local and load Phi (labs/00-setup.md)",
)
