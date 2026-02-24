# service-status-slack-webhook

FastAPI webhook receiver for Slack/Statuspage events.

## Run locally with Docker

Build:

```bash
docker build -t service-status-slack-webhook .
```

Run:

```bash
docker run --rm -p 8000:8000 -e PORT=8000 service-status-slack-webhook
```

Verify:

```bash
curl -i http://localhost:8000/health
curl -i http://localhost:8000/
```

Send a webhook test payload:

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event": {
      "channel_type": "channel",
      "type": "message",
      "text": "Status: operational\nEverything is healthy",
      "username": "Slack"
    }
  }'
```

Then check:

```bash
curl http://localhost:8000/
```

## Deploy on Render (Docker)

This repository includes `render.yaml` for an infrastructure-as-code deployment.

1. Push this repo to GitHub.
2. In Render, create a new Web Service from the repo.
3. Render detects `render.yaml` and Docker runtime automatically.
4. Deploy.

After deploy, test:

```bash
curl -i https://<your-service>.onrender.com/health
curl -i https://<your-service>.onrender.com/
```

Webhook URL for integrations:

```text
https://<your-service>.onrender.com/webhook
```

No `:8000` is needed in the public URL. Render handles external routing and forwards to the container port via the `PORT` environment variable.

## Notes

- `incident.log` and `webhook_events_direct.log` are stored in container filesystem.
- On Render free instances, services can sleep and local files may reset after restart/redeploy.
