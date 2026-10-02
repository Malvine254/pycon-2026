# Lab 02 - Hello, local with Phi (Foundry Local)

> **Time:** 15 minutes · **Level:** Beginner · **Works offline:** **Yes**

[← Lab 01](01-hello-cloud.md) · [Lab index](README.md) · [Next: Lab 03 →](03-unified-client.md)

## Goal

Run the **same prompt** as Lab 01 on a model that lives on your laptop - no internet, no cost per request, and your data never leaves the machine.

**File:** [`workshop/02_hello_local.py`](../workshop/02_hello_local.py) · **Code to read:** [`src/pycord/providers/local.py`](../src/pycord/providers/local.py)

> [!NOTE]
> Foundry Local exposes an **OpenAI-compatible API** on `localhost`. That means we use the *same* `openai` client as in Lab 01 - only the `base_url` changes.

---

## Step 1 - Make sure Phi is running

If you completed [Lab 00, Step 2](00-setup.md#step-2---install-and-start-the-local-model), you are ready. Quick reminder:

```powershell
foundry server start
foundry model load phi-3.5-mini
foundry server status        # shows Ready and the port (Web URLs)
```

Keep the server running while you complete this lab.

In `.env`:

```ini
LOCAL_MODEL=phi-3.5-mini
```

Restart the terminal, Python process, or notebook kernel after changing `.env`.

## Step 2 - Confirm the runtime is visible

In VS Code, click **Run Cell** above the first `# %%` block. This is Python code; do not paste it into PowerShell:

```python
from pycord.config import Settings
from pycord.labkit import local_or_cloud

model = local_or_cloud(Settings.from_env())
print(f"Using: {model.name} (local: {model.is_local})")
```

Expected: `Using: foundry-local (local: True)`

> [!TIP]
> **Phi not installed yet?** The cell prints install instructions and continues with the cloud model
> (`Using: foundry (local: False)`), so you can keep up with the session. Finish Step 1 later, open a new
> terminal, and click **Run Cell** again to switch to the local model.

## Step 3 - Ask the same question as Lab 01

Click **Run Cell** above the second `# %%` block. This is Python code; do not paste it into PowerShell.

> [!IMPORTANT]
> The **first** call is slow: the model is loaded from disk into memory. Calls after that are much faster.

```text
[foundry-local | Phi-3.5-mini-instruct-generic-cpu | 6.84s | 31+64 tokens | KES 0.0000]
```

Notice **KES 0.0000** - local calls are free.

## Step 4 - See where the request went

Click **Run Cell** above the third `# %%` block. This is Python code; do not paste it into PowerShell:

```python
print("Base URL:", model.client.base_url)   # e.g. http://localhost:5273/v1/
print("Model id:", model.model)
```

## Step 5 - Run the offline test

1. Finish downloading the model while online.
2. Turn off your Wi-Fi.
3. Return to VS Code and click **Run Cell** on the second `# %%` block again.
4. Confirm that it still works, then turn Wi-Fi back on.

## Checkpoint

- [ ] You got an answer from the local model
- [ ] It worked with Wi-Fi off
- [ ] You compared its speed and quality with Lab 01

## Exercises

**1.** Fill in this table for the same prompt:

| | Cloud (Lab 01) | Local (Lab 02) |
|---|---|---|
| Latency | | |
| Cost (KES) | | |
| Quality (1-5) | | |
| Works offline? | | |

**2.** Try another Phi model. Is it faster? Is the quality better?

<details>
<summary>Solution</summary>

See which Phi models Foundry Local offers, then pick one (for example `phi-4-mini`):

```powershell
foundry model list
```

Restart the Python cell / kernel after changing `.env` so the new settings are loaded. Bigger Phi models usually answer better (including in Kiswahili) but need more memory and are slower.

## Change the local model

To switch Phi models:

1. Check the available model names:

	```powershell
	foundry model list
	```

2. Set the selected Phi alias in `.env`:

	```ini
	LOCAL_MODEL=phi-4-mini
	```

3. Download and load that same alias:

	```powershell
	foundry model download phi-4-mini
	foundry model load phi-4-mini
	```

4. Restart the Python cell or the app. The provider checks that the selected alias is actually loaded; if it is missing, the lab skips the local provider instead of crashing.

</details>

## Troubleshooting

| Problem | Fix |
|---|---|
| `Using: foundry (local: False)` | Phi is not running - the lab used the cloud instead. Follow [Lab 00, Step 2](00-setup.md#step-2---install-and-start-the-local-model), then open a **new** terminal / restart VS Code |
| Very slow or laptop freezes | Close other apps (browsers, Teams) and run `foundry model load phi-3.5-mini` again |

---

[← Lab 01](01-hello-cloud.md) · [Lab index](README.md) · [Next: Lab 03 - One interface →](03-unified-client.md)
