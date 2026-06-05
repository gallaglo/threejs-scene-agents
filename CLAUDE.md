# CLAUDE.md

## Commands

```
# Install dependencies
uv sync

# Run pipeline locally (image, prompt, or both)
uv run python test_local.py --image path/to/photo.jpg
uv run python test_local.py --prompt "a glowing red sphere floating in space"
uv run python test_local.py --image path/to/photo.jpg --prompt "make it look futuristic"

# Deploy or update Agent Engine
uv run python deploy.py
```

## Architecture

Multi-agent pipeline deployed to Vertex AI Agent Engine. No web server.
No runtime traffic. Invoked once per deployment via deploy.py.

Agents are defined in threejs_scene_generator/ using Google ADK (google-adk).
System prompts live in each sub-agent's folder as prompt.txt — edit prompts
there, not inline in agent definitions.

Pipeline: VisionAgent → CodeGenAgent → LoopAgent(ValidatorAgent, RefinementAgent)

Package structure:
  threejs_scene_generator/
    __init__.py           sets env vars, exposes root_agent
    agent.py              pipeline wiring (root_agent)
    config.py             model/env config
    sub_agents/
      vision/             VisionAgent — analyses photo, outputs scene_description
      codegen/            CodeGenAgent — generates Three.js code
      validator/          ValidatorAgent — scores code, exits loop via tool
      refinement/         RefinementAgent — fixes failing sections

Session state keys flow between agents. The only output the calling service
(personal-website) reads is threejs_code and validation_score from the final
session state, surfaced via SSE events that Agent Engine emits during streamQuery.

## Deployment

Run deploy.py once. Copy the printed AGENT_ENGINE_RESOURCE_NAME and set it
as a Cloud Run env var on the personal-website service.

To update after changing agent code or prompts, re-run deploy.py — it will
update the existing engine rather than creating a new one if
AGENT_ENGINE_RESOURCE_NAME is set in .env.
