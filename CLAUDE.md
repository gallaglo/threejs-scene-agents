# CLAUDE.md

## Commands

```
# Install dependencies
uv sync

# Run pipeline locally (image, prompt, or both)
uv run python test_local.py --image path/to/photo.jpg
uv run python test_local.py --prompt "a glowing red sphere floating in space"
uv run python test_local.py --image path/to/photo.jpg --prompt "make it look futuristic"

# Deploy to Agent Runtime (creates on first run, updates when AGENT_ENGINE_RESOURCE_NAME is set)
uv run python deploy.py
# Update AGENT_ENGINE_RESOURCE_NAME in .env with the printed resource name on first deploy

# Alternatively, deploy via ADK CLI (always creates a new resource)
# Move .adk/ out first — it's 16MB of local session state that bloats the payload
mv threejs_scene_generator/.adk /tmp/adk_backup
uv run adk deploy agent_engine \
  --project $GOOGLE_CLOUD_PROJECT \
  --region $AGENT_ENGINE_LOCATION \
  --display_name "threejs-scene-generator" \
  --adk_app app \
  --env_file .env \
  threejs_scene_generator/
mv /tmp/adk_backup threejs_scene_generator/.adk
```

## Architecture

Multi-agent pipeline deployed to Agent Runtime via AdkApp, exposing :streamQuery
(NDJSON streaming).

Agents are defined in threejs_scene_generator/ using Google ADK (google-adk).
System prompts live in each sub-agent's folder as prompt.txt — edit prompts
there, not inline in agent definitions.

Pipeline: VisionAgent → CodeGenAgent → LoopAgent(ValidatorAgent, RefinementAgent)

Package structure:
  threejs_scene_generator/
    __init__.py           sets env vars, exposes root_agent
    agent.py              pipeline wiring (root_agent); name="scene_pipeline"
    config.py             model/env config
    sub_agents/
      vision/             VisionAgent — analyses photo, outputs scene_description
      codegen/            CodeGenAgent — generates Three.js code
      validator/          ValidatorAgent — scores code, exits loop via tool
      refinement/         RefinementAgent — fixes failing sections

Session state keys flow between agents. The only output the calling service
(personal-website) reads is threejs_code and validation_score from the final
session state, surfaced via NDJSON events from :streamQuery.

## Git workflow

Always create a feature branch for changes — never commit or push directly to main.

## Deployment

Use `uv run python deploy.py` (or let the GitHub Actions workflow do it). On
first run it creates a new resource; on subsequent runs it updates the existing
one when AGENT_ENGINE_RESOURCE_NAME is set. Update AGENT_ENGINE_RESOURCE_NAME in
.env and as a Cloud Run env var on the personal-website service after the first
deploy.

Do not mix deploy.py and `adk deploy agent_engine` on the same resource — they
use different deployment specs (package_spec vs deployment_source) and the API
will reject updates that switch between them. Stick with deploy.py.

`adk deploy agent_engine` always creates a new resource (never updates) and has a
known gotcha: threejs_scene_generator/.adk/ is a 16MB local session database
(from `adk web`) that must be excluded before deploying or the 8MB API limit is
exceeded.
