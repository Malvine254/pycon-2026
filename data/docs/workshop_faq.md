# Pycord Workshop FAQ

## What is Pycord?

Pycord is the hands-on project for the PyCon Kenya 2026 workshop "Building a hybrid AI system with Python and local models". It combines cloud models from Microsoft Foundry with small models running on your own laptop.

## Why hybrid?

Local models are free per request, work offline and keep personal data on your device. Cloud models are bigger and better at complex tasks. A hybrid router picks the right one for each request.

## What can Mela help with?

Mela is a general assistant with a small Kenyan workshop knowledge base. It can explain the sample maize-farming notes, give M-Pesa safety reminders, answer workshop questions, search uploaded documents, convert sample currencies, and report Nairobi time.

When the local model is selected, BM25 retrieval adds the most relevant document passages to the prompt. When the cloud model is selected, the agent can call the allow-listed `search_docs` tool. Mela should answer from retrieved context when it is relevant and say when it does not have enough information.

Uploaded documents stay in memory. Personal data is kept on the local path and is redacted before document results are sent to a cloud model.

For unrelated questions, Mela should answer briefly without inventing facts. It does not access bank accounts, send messages, make transactions, or replace official agricultural, financial, or medical advice.

## How is personal data protected?

In Auto mode, Kenyan personal data is routed to the local model when one is available. If no local model is available, Mela refuses the request instead of sending it to the cloud. Uploaded documents stay in memory, and personal data is redacted before cloud document context is used.

## What if the Wi-Fi is slow?

Most modules work fully offline once the local model is downloaded. Facilitators have USB drives with the model files and Python packages.

## Which laptop do I need?

Any laptop with at least 8 GB of RAM can run the small local models used in the workshop, such as phi-3.5-mini or qwen2.5-0.5b. A GPU or NPU is optional.
