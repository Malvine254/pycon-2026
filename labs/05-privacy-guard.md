# Lab 05 - Privacy guard for Kenyan data

> **Time:** 20 minutes · **Level:** Intermediate · **Works offline:** **Yes**

[← Lab 04](04-hybrid-router.md) · [Lab index](README.md) · [Next: Lab 06 →](06-local-rag.md)

## Goal

Detect Kenyan personal data, keep it on the device, and learn two privacy patterns: **keep it local** and **redact, then use the cloud**.

**File:** [`workshop/05_privacy_guard.py`](../workshop/05_privacy_guard.py) · **Code to read:** [`src/pycord/privacy.py`](../src/pycord/privacy.py)

## Before you start

In a terminal with `(.venv)` active, load local Phi:

```powershell
foundry server start
foundry model load phi-3.5-mini
```

No FastAPI server is needed for this lab. The cloud comparison is optional and uses the facilitator-provided `.env` settings.

> [!IMPORTANT]
> Kenya's **Data Protection Act (2019)** regulates how personal data is processed and transferred. Sending customer data to a cloud API is a design decision, not an accident.

## What we detect

| Kind | Example | Pattern idea |
|---|---|---|
| `phone_ke` | `0712345678`, `+254 712 345 678` | `07..`/`01..` or `+254` and 9 digits |
| `mpesa_code` | `QFT3XYZ12A` | 10 capital letters/digits with both letters and digits |
| `kra_pin` | `A012345678Z` | `A`/`P` + 9 digits + letter |
| `national_id` | `ID number 12345678` | 7-8 digits **after** the word "ID" |
| `email` | `wanjiku@example.co.ke` | standard email shape |

> [!NOTE]
> National ID numbers are just 7-8 digits, which would match prices and counts. Requiring the word "ID" nearby avoids false alarms - a good example of trading recall for precision.

---

## Step 1 - Detect personal data

In VS Code, click **Run Cell** above the first `# %%` block. This is Python code; do not paste it into PowerShell:

```text
True [('mpesa_code', 'QFT3XYZ12A'), ('phone_ke', '0712345678')]
True [('kra_pin', 'A012345678Z'), ('national_id', 'ID number 12345678')]
True [('email', 'wanjiku@example.co.ke')]
False []
```

## Step 2 - Pattern 1: keep it local

Click **Run Cell** above the second `# %%` block. The router sees personal data and answers locally:

```text
[foundry-local | ...] - personal data detected - keeping it on this device
```

> [!WARNING]
> If the local model **fails**, the router raises an error instead of falling back to the cloud. Failing safely is better than leaking data.

## Step 3 - Pattern 2: redact, then use the cloud

Click **Run Cell** above the third `# %%` block:

```text
[MPESA_CODE] Confirmed. Ksh1,500.00 sent to JOHN [PHONE_KE]
```

The cloud model can still explain the message - without ever seeing the real code or number.

> [!TIP]
> Mela uses Pattern 2 automatically: when the agent searches your uploaded documents for a **cloud** model, the results are redacted first (see `_search_docs` in [`agent.py`](../src/pycord/agent.py)).

## Checkpoint

- [ ] You can list the 5 kinds of personal data we detect
- [ ] You know when to use "keep it local" vs "redact, then cloud"

## Exercises

**1.** Add a pattern for Kenyan **number plates**, like `KDA 123A`.

<details>
<summary>Solution</summary>

In `src/pycord/privacy.py`, add to `PATTERNS`:

```python
    "vehicle_plate": re.compile(r"\bK[A-Z]{2}\s?\d{3}[A-Z]\b"),
```

</details>

**2.** Add a test for it and run `pytest tests/test_privacy.py -v`.

<details>
<summary>Solution</summary>

Add a line to the `parametrize` list in `test_detects_kenyan_pii`:

```python
        ("Car KDA 123A is parked outside", "vehicle_plate"),
```

</details>

**3.** Discussion: what personal data might we **miss**? (Hint: names, addresses, Kiswahili phrasing like *"namba yangu ni sifuri saba..."*.)

---

[← Lab 04](04-hybrid-router.md) · [Lab index](README.md) · [Next: Lab 06 - Local RAG →](06-local-rag.md)
