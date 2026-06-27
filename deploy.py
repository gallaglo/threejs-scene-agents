import os
import tomllib

import vertexai
from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.agent_engines import AdkApp

from threejs_scene_generator.agent import root_agent

load_dotenv()

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
AGENT_ENGINE_LOCATION = os.environ.get("AGENT_ENGINE_LOCATION", "us-west1")
STAGING_BUCKET = os.environ["STAGING_BUCKET"]

vertexai.init(project=PROJECT, location=AGENT_ENGINE_LOCATION, staging_bucket=STAGING_BUCKET)

adk_app = AdkApp(agent=root_agent)

with open("pyproject.toml", "rb") as f:
    REQUIREMENTS = tomllib.load(f)["project"]["dependencies"]
EXTRA_PACKAGES = ["threejs_scene_generator/"]

existing = os.environ.get("AGENT_ENGINE_RESOURCE_NAME")

if existing:
    engine = agent_engines.AgentEngine(resource_name=existing)
    engine.update(
        agent_engine=adk_app,
        requirements=REQUIREMENTS,
        extra_packages=EXTRA_PACKAGES,
    )
    print("\nUpdated existing deployment.")
else:
    engine = agent_engines.AgentEngine.create(
        agent_engine=adk_app,
        requirements=REQUIREMENTS,
        extra_packages=EXTRA_PACKAGES,
        display_name="threejs-scene-generator",
        description="Photo-to-Three.js multi-agent pipeline",
    )
    print("\nDeployed successfully.")

print(f"AGENT_ENGINE_RESOURCE_NAME={engine.resource_name}")
print("\nSet this as a Cloud Run env var on personal-website.")
