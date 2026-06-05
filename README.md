# threejs-scene-agents

A multi-agent pipeline that converts a photo, a text description, or both into a working [Three.js](https://threejs.org/) r128 scene. Deployed to [Agent Runtime](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview).

## Pipeline

```text
VisionAgent → CodeGenAgent → LoopAgent(ValidatorAgent, RefinementAgent)
```

1. **VisionAgent** — analyzes the photo, text description, or both and outputs a structured scene description (geometry, materials, lighting, animation, background)
2. **CodeGenAgent** — generates Three.js r128 code from the description
3. **ValidatorAgent** — scores the code 0–100 and calls a tool to either exit the loop (score ≥ 80) or continue
4. **RefinementAgent** — fixes the code based on validator feedback; loop runs up to 3 iterations

The calling service reads `threejs_code` and `validation_score` from the final session state, surfaced via SSE events during `streamQuery`.

## Setup

```bash
# Install dependencies
uv sync

# Copy and fill in environment variables
cp .env.example .env
```

Required in `.env`:

| Variable | Description |
| --- | --- |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `STAGING_BUCKET` | GCS bucket for deployment staging (e.g. `gs://my-project-staging`) |
| `GOOGLE_CLOUD_LOCATION` | Region for model API calls (e.g. `us-central1`) |
| `AGENT_ENGINE_LOCATION` | Region for Agent Runtime deployment (e.g. `us-west1`) |

## Local testing

```bash
# Authenticate with GCP
gcloud auth application-default login

# Run the pipeline against an image, a text prompt, or both
uv run python test_local.py --image path/to/photo.jpg
uv run python test_local.py --prompt "a glowing red sphere floating in space"
uv run python test_local.py --image path/to/photo.jpg --prompt "make it look futuristic"
```

Or use the ADK dev UI:

```bash
uv run adk web
```

## Deployment

```bash
uv run python deploy.py
```

On first run, copy the printed `AGENT_ENGINE_RESOURCE_NAME` and set it in `.env` (and as a GitHub secret). Subsequent runs will update the existing deployment instead of creating a new one.

### CI/CD

The GitHub Actions workflow in `.github/workflows/deploy.yml` automatically deploys to Agent Runtime on push to `main` when files under `threejs_scene_generator/` change.

Required GitHub secrets:

| Secret | Description |
| --- | --- |
| `GCP_PROJECT_ID` | GCP project ID |
| `WIF_PROVIDER` | Workload Identity Federation provider |
| `WIF_SERVICE_ACCOUNT` | Service account email |
| `STAGING_BUCKET` | GCS bucket for deployment staging |
| `AGENT_ENGINE_RESOURCE_NAME` | Set after first deploy to trigger updates |

## Tech stack

- [Google ADK](https://google.github.io/adk-docs/) — agent framework
- [Agent Runtime](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview) — managed deployment
- `gemini-2.5-pro` — vision agent (multimodal)
- `gemini-2.5-flash` — codegen, validator, refinement agents
- [uv](https://docs.astral.sh/uv/) — package manager

## License

MIT
