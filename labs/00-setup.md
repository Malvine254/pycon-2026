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

## Step 2 - Install and start the local model

We use **Foundry Local + Phi** (`phi-3.5-mini`). Foundry Local has two CLI generations, and the project supports both:

| | **New CLI** | **Legacy CLI** |
|---|---|---|
| Command group | `foundry server ...` | `foundry service ...` |
| Loads Phi for you? | No - you run `foundry model load` | Yes - the labs start the service and load Phi automatically |

> [!TIP]
> No time to install now? Skip to Step 3. Every lab falls back to the cloud model and tells you how to install Phi later.

### 2.1 Install Foundry Local

```powershell
# Windows
winget install Microsoft.FoundryLocal
```

```bash
# macOS
brew tap microsoft/foundrylocal
brew install foundrylocal
```

**Open a new terminal**, then check it is installed:

```powershell
foundry --version
```

> [!WARNING]
> `foundry : The term 'foundry' is not recognized` means the terminal was opened before the install. Close it and open a new one (or restart VS Code).

### 2.2 Find out which CLI you have

```powershell
foundry --help
```

- The list shows **`server`** → you have the **new CLI**. Use the left column below.
- The list shows **`service`** → you have the **legacy CLI**. Use the right column below.

### 2.3 Start, download and load Phi

| Step | New CLI | Legacy CLI |
|---|---|---|
| 1. Start the service | `foundry server start` | `foundry service start` |
| 2. Download Phi (once, ~2.2 GB - **do this at home**) | `foundry model download phi-3.5-mini` | `foundry model download phi-3.5-mini` |
| 3. Load Phi into memory | `foundry model load phi-3.5-mini` | Optional: `foundry model run phi-3.5-mini`, ask a question, type `/exit` |

> [!NOTE]
> Loading takes 10-60 seconds the first time. Keep the service running for the whole workshop.

### 2.4 Find the port Foundry Local is running on

The port is chosen when the service starts and **can change** after a restart, so never hard-code it - look it up:

| New CLI | Legacy CLI |
|---|---|
| `foundry server status` | `foundry service status` |
| Look for **`Web URLs  http://127.0.0.1:<port>`** and **`Ready`** | Look for **`running on http://127.0.0.1:<port>/openai/status`** |

Write the port down (for example `5273`).

<details>
<summary>Can't see the URL? Find the port from the process list (Windows)</summary>

```powershell
Get-NetTCPConnection -State Listen |
  Where-Object { (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName -match 'foundry|inference' } |
  Select-Object LocalAddress, LocalPort, OwningProcess
```

</details>

### 2.5 Check the port is open and Phi is loaded

Replace `5273` with your port.

<table>
<tr><th>Windows (PowerShell)</th><th>macOS</th></tr>
<tr><td>

```powershell
$port = 5273
Get-NetTCPConnection -LocalPort $port -State Listen
(Invoke-RestMethod "http://127.0.0.1:$port/v1/models").data.id
```

</td><td>

```bash
PORT=5273
nc -z 127.0.0.1 $PORT && echo "port open"
curl -s http://127.0.0.1:$PORT/v1/models
```

</td></tr>
</table>

**Expected:** the port is listening, and the model list contains an id with **`Phi-3.5-mini`** (for example `Phi-3.5-mini-instruct-generic-cpu`).

| You see | Meaning | Fix |
|---|---|---|
| Nothing listening on the port | Service is not running | Run 2.3 step 1 again, then 2.4 |
| Port open, but no `Phi-3.5-mini` in the list | Service runs, Phi not loaded | New CLI: `foundry model load phi-3.5-mini`. Legacy CLI: nothing to do - the labs load it |
| `unknown command 'server'` | You have the legacy CLI | Use the right-hand column |
| Laptop freezes / out of memory | Phi needs ~4 GB free RAM | Close other apps, or use Ollama with `qwen2.5:0.5b` (below) |

> [!IMPORTANT]
> The final check is the setup script in **Step 6**: `[OK] Local runtime (foundry-local)` means the Python code can reach Phi.

### Every time you restart your laptop

| New CLI | Legacy CLI |
|---|---|
| `foundry server start` then `foundry model load phi-3.5-mini` | `foundry service start` (the labs load Phi) |

<details>
<summary>Optional alternative: Ollama (Windows / macOS / Linux)</summary>

Install from ollama.com, then:

```bash
ollama pull qwen2.5:1.5b
ollama run qwen2.5:1.5b "Habari?"
```

Ollama always uses port **11434**. Check it:

```powershell
(Invoke-RestMethod http://127.0.0.1:11434/api/tags).models.name
```

In `.env` set `LOCAL_RUNTIME=ollama` and `OLLAMA_MODEL=qwen2.5:1.5b`.

</details>

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
>
> **No local model yet?** Also okay. `[!!] Local runtime` is optional: every lab falls back to the cloud
> model and prints how to install Phi. Install it when the Wi-Fi allows and re-run the lab to see the local version.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` not found on Windows | Use `py -3.13 -m venv .venv`, or install Python from python.org and tick *Add to PATH* |
| `ModuleNotFoundError: pycord` | Activate `.venv` and run `pip install -e .` again |
| `Local runtime ... !!` | Follow [Step 2.4-2.5](#24-find-the-port-foundry-local-is-running-on) to check the port and that Phi is loaded. Optional - labs fall back to the cloud |
| `Cloud reachable !!` | Check `FOUNDRY_ENDPOINT` spelling and your internet connection |

---

[Lab index](README.md) · [Next: Lab 01 - Hello, cloud →](01-hello-cloud.md)
