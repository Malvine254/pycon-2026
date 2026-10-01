# Lab 02 - Hello, local with Phi (Foundry Local)

> **Time:** 15 minutes · **Level:** Beginner · **Works offline:** **Yes**

[← Lab 01](01-hello-cloud.md) · [Lab index](README.md) · [Next: Lab 03 →](03-unified-client.md)

## Goal

Run the **same prompt** as Lab 01 on a model that lives on your laptop - no internet, no cost per request, and your data never leaves the machine.

**File:** [`workshop/02_hello_local.py`](../workshop/02_hello_local.py) · **Code to read:** [`src/pycord/providers/local.py`](../src/pycord/providers/local.py)

> [!NOTE]
> Foundry Local exposes an **OpenAI-compatible API** on `localhost`. That means we use the *same* `openai` client as in Lab 01 - only the `base_url` changes.

---

## Step 1 - Choose and start a local runtime

### Option A: Foundry Local

Use this on Windows or macOS:

```powershell
foundry server status
foundry model list
foundry model download phi-3.5-mini
foundry model load phi-3.5-mini
```

Keep the Foundry Local server running while you complete this lab.

In `.env`:

```ini
LOCAL_RUNTIME=foundry-local
LOCAL_MODEL=phi-3.5-mini
```

### Optional alternative: Ollama

Use this on Windows, macOS, or Linux:

```bash
ollama pull qwen2.5:1.5b
ollama list
ollama run qwen2.5:1.5b "Habari?"
```

In `.env`:

```ini
LOCAL_RUNTIME=ollama
OLLAMA_MODEL=qwen2.5:1.5b
```

Restart the terminal, Python process, or notebook kernel after changing `.env`.

## Step 2 - Confirm the runtime is visible

In VS Code, click **Run Cell** above the first `# %%` block. This is Python code; do not paste it into PowerShell:

```python
from pycord.config import Settings
from pycord.providers import get_local_provider

local = get_local_provider(Settings.from_env())
print("Runtime available:", local.is_available())
```

Expected: `Runtime available: True`

If it prints `False`, finish Step 1, open a new terminal, and click **Run Cell** on the same Python cell again.

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
print("Base URL:", local.client.base_url)   # e.g. http://localhost:5273/v1/
print("Model id:", local.model)
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

**2.** Try a smaller model. Is it faster? Is the quality still "good enough"?

<details>
<summary>Solution</summary>

Foundry Local: keep `LOCAL_MODEL=phi-3.5-mini` and load Phi with `foundry model load phi-3.5-mini`.
Ollama: `ollama pull qwen2.5:0.5b` and set `OLLAMA_MODEL=qwen2.5:0.5b`.

Restart the Python cell / kernel so the new settings are loaded. Smaller models are faster and lighter on memory, but weaker at reasoning and Kiswahili.

</details>

## Troubleshooting

| Problem | Fix |
|---|---|
| `Runtime available: False` | Install Foundry Local / Ollama, then open a **new** terminal / restart VS Code |
| Very slow or laptop freezes | Close other apps, or use a smaller model (Exercise 2) |
| `ModuleNotFoundError: foundry_local` | Run `pip install -e .` - the project pins a compatible `foundry-local-sdk` |
| Ollama `connection refused` | Start the Ollama app, or run `ollama serve` |

---

[← Lab 01](01-hello-cloud.md) · [Lab index](README.md) · [Next: Lab 03 - One interface →](03-unified-client.md)
