# service status slack webhook

this app receives status incident events from slack and logs a clean incident summary to stdout.

the goal is an event-driven flow for service status updates from providers like openai and claude.

## why this exists

- openai status updates are available through an rss feed that a slack channel can subscribe to.
- a slack app forwards channel events to this webhook.
- the webhook reads the incident url, fetches provider json, parses the latest status update, and prints a normalized log line.
- logs are visible in local terminal output and deployment logs on platforms like render or vercel.

## request flow

1. slack sends an event callback to `POST /webhook`.
2. the app extracts the incident url from the event blocks.
3. the url is normalized through an adapter registry (`adapters/registry.py`).
4. the app fetches the incident payload with `httpx`.
5. a provider parser (`openai` or `claude`) maps the payload into:
   - provider
   - product
   - status text
   - timestamp
6. the app prints a formatted incident message to stdout.

the same endpoint also supports slack url verification and returns the challenge response.

## endpoints

- `GET /` simple info message.
- `GET /health` health json response.
- `HEAD /health` health check for platform probes.
- `POST /webhook` slack event callback endpoint.

## project structure

- `main.py` fastapi app, webhook endpoint, url verification, stdout logging.
- `adapters/registry.py` provider registry, url normalization, common output formatting.
- `adapters/openai_status.py` openai status url mapping + parser.
- `adapters/claude_status.py` claude status url mapping + parser.
- `test.sh` replays saved webhook payloads from `webhook_events_direct.log`.
- `Dockerfile` container build and uvicorn startup.
- `render.yaml` render service settings and health check path.

## local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

app runs on `http://localhost:8000` by default.

## replay webhook payloads for testing

save one raw slack webhook json per line in `webhook_events_direct.log`, then run:

```bash
bash test.sh
```

`test.sh` posts each line to `http://localhost:8000/webhook` with concurrent workers.

## docker run

```bash
docker build -t service-status-slack-webhook .
docker run --rm -p 8000:8000 service-status-slack-webhook
```

## deployment notes

- docker runtime is configured in `render.yaml`.
- health checks use `/health`.
- incident summaries are emitted to stdout, so platform logs are the primary output sink.
