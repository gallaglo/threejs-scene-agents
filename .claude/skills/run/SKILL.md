---
description: Launch the ADK web dev UI for local pipeline testing
---

# Run: threejs-scene-agents

Launch `adk web` in the background, verify it's up, then open the browser.

## Steps

1. Start the server in the background:
   ```bash
   uv run adk web &
   ```

2. Wait for it to be ready (watches for the uvicorn startup line):
   ```bash
   sleep 4 && curl -s http://127.0.0.1:8000 | head -c 1
   ```

3. Tell the user the server is running at **http://127.0.0.1:8000**.

4. Remind the user:
   - The pipeline is driven by session state, not conversational messages
   - To test text-only mode, set initial state: `{"prompt": "..."}`
   - To test image mode, set initial state: `{"image": "<base64>", "mime_type": "image/jpeg"}`
   - To stop the server: `kill $(lsof -ti:8000)`

## Notes

- Port: 8000 (uvicorn default)
- Sessions and artifacts are stored under `.adk/` in the project root
- Requires GCP ADC credentials: `gcloud auth application-default login`
