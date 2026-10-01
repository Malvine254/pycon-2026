# Lab 00 - Setup and environment check

> **Time:** 20 minutes · **Level:** Beginner · **Works offline:** after downloads

[Lab index](README.md) · [Next: Lab 01 →](01-hello-cloud.md)

## Goal

By the end of this lab you will have:

- [ ] Python 3.10+ and the project installed in a virtual environment
- [ ] A local model runtime (Foundry Local or Ollama) with a small model downloaded
- [ ] A Microsoft Foundry project with `gpt-5-mini` deployed
- [ ] A `.env` file, and a setup check that shows `[OK]`

> [!WARNING]
> Model downloads are 1-2 GB. **Do Steps 2 and 3 at home** before the workshop - conference Wi-Fi is shared by everyone.

---

## Step 1 - Install the basics

Install these if you don't have them:

| Tool | Check it works |
|---|---|
| Python 3.10 or newer | `python --version` (Windows may need `py --version`) |
| Git | `git --version` |
| VS Code + **Python** and **Jupyter** extensions | Open VS Code → Extensions |

> [!NOTE]
> You need at least **8 GB RAM**. A GPU or NPU is nice but not required.

## Step 2 - Install a local model runtime

Use **Foundry Local + Phi** for the workshop:

```powershell
# Windows
winget install Microsoft.FoundryLocal
```

```bash
# macOS
brew tap microsoft/foundrylocal
brew install foundrylocal
```

Then check the runtime, download the model, and test it:

```bash
foundry server status
foundry model download phi-3.5-mini
foundry model load phi-3.5-mini
```

Confirm the model is loaded before starting the Python app.

> [!TIP]
> Ollama is an optional alternative only. It is not required for the workshop labs.

> [!NOTE]
> Foundry Local has two CLI versions. If `foundry --help` lists `service` instead of `server`, use `foundry service status` and `foundry model run phi-3.5-mini`. The project supports both versions.

## Step 3 - Get the project and install it

<details open>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
git clone https://github.com/Malvine254/pycon-2026.git
cd pycon-2026
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

</details>

<details>
<summary><b>macOS / Linux</b></summary>

```bash
git clone https://github.com/Malvine254/pycon-2026.git
cd pycon-2026
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

</details>

> [!WARNING]
> PowerShell says *"running scripts is disabled"*? Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

## Step 4 - Add the provided Azure OpenAI settings

The facilitator provides the endpoint, API key, deployment name, and API version. No Azure resource creation is required for attendees.

Optional: facilitators or attendees using their own Azure account may create a resource and deployment at **https://ai.azure.com**.

## Step 5 - Configure `.env`

Open `.env` in VS Code and fill in:

```ini
FOUNDRY_ENDPOINT=https://<provided-resource>.openai.azure.com
FOUNDRY_API_KEY=<provided-key>
FOUNDRY_DEPLOYMENT=gpt-5-mini
FOUNDRY_API_VERSION=2025-08-07

LOCAL_RUNTIME=foundry-local      # or: ollama
LOCAL_MODEL=phi-3.5-mini
OLLAMA_MODEL=qwen2.5:1.5b       # optional Ollama path
```

For a personal Azure account, you may instead choose Entra ID:

| Option | How | When |
|---|---|---|
| **Entra ID (recommended)** | Install Azure CLI, run `az login`. Your account needs the **Cognitive Services OpenAI User** role on the Foundry resource. Leave `FOUNDRY_API_KEY` empty. | Your own Azure account |
| **API key** | Paste the key from the portal into `FOUNDRY_API_KEY`. | Shared workshop endpoint |

> [!CAUTION]
> Never commit `.env` or paste keys in chat. `.env` is already in `.gitignore`.

> [!TIP]
> For a shared workshop key, create a dedicated key, distribute it privately, and regenerate it in the Azure portal after the event.

## Step 6 - Run the setup check

```bash
python workshop/00_setup_check.py
```

Expected output:

```text
[OK] Python >= 3.10
[OK] .env file exists
[OK] FOUNDRY_ENDPOINT set
[OK] Cloud auth configured
[OK] Cloud reachable
[OK] Local runtime (foundry-local)
```

Then run the tests (no internet needed):

```bash
pytest
```

## Checkpoint

- [ ] Every line in the setup check shows `[OK]` (or you know which one you will fix)
- [ ] `pytest` ends with `passed`

> [!NOTE]
> Cloud lines failing is **okay for now** - Labs 02, 05 and 06 work fully offline.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` not found on Windows | Use `py -3.13 -m venv .venv`, or install Python from python.org and tick *Add to PATH* |
| `ModuleNotFoundError: pycord` | Activate `.venv` and run `pip install -e .` again |
| `Local runtime ... !!` | Open a **new** terminal after installing Foundry Local / Ollama, check `foundry --version` |
| `Cloud reachable !!` | Check `FOUNDRY_ENDPOINT` spelling and your internet connection |

---

[Lab index](README.md) · [Next: Lab 01 - Hello, cloud →](01-hello-cloud.md)
