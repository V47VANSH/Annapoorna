# Annapoorna backend

FastAPI backend. See the [main README](../README.md) for setup.

```bash
cp .env.example .env
uv sync --extra ml
uv run python check_setup.py   # checks the services in .env
uv run uvicorn main:app --reload
```

API docs: http://localhost:8000/docs

Other commands:

```bash
uv run python predict.py leaf.jpg --top 3   # run the disease model on images
uv run python sattelite_report.py           # satellite report for the demo farm
uv run earthengine authenticate             # Earth Engine login
uv run pytest tests -q
```

Notes:

- The models (CNN, Whisper), Earth Engine and the LLM client are loaded on first
  use, so the server starts quickly and one missing service doesn't stop the
  others from working.
- With `ALLOW_KEYLESS_FALLBACKS=true` (default), missing services fall back to
  Open-Meteo, the in-memory store or the offline advice.
- `OFFLINE_MODE=true` turns off all network calls, the tests use it.
- Chat history is kept per user in memory.
