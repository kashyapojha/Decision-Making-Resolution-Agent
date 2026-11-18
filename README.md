# Decision-Making Resolution Agent

A Python agentic tool loop that resolves damaged-order requests by:

1. Looking up an order.
2. Checking replacement inventory.
3. Refunding when a replacement is unavailable.
4. Dispatching a customer notification.

## Run the demo

```powershell
py -m resolution_agent.cli "My headphones in ORD-1002 arrived damaged"
```

The demo uses an offline deterministic provider, so no API key is required.

## Run with an OpenAI-compatible provider

Set `OPENAI_API_KEY`, optionally set `OPENAI_MODEL` and `OPENAI_BASE_URL`, then run:

```powershell
py -m resolution_agent.cli --provider openai "My headphones in ORD-1002 arrived damaged"
```

## Test

```powershell
py -m unittest discover -s tests -v
```
