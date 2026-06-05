import os

import vertexai
from dotenv import load_dotenv
from vertexai import agent_engines

from threejs_scene_generator.agent import root_agent

load_dotenv()

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
AGENT_ENGINE_LOCATION = os.environ.get("AGENT_ENGINE_LOCATION", "us-west1")
STAGING_BUCKET = os.environ["STAGING_BUCKET"]

vertexai.init(project=PROJECT, location=AGENT_ENGINE_LOCATION, staging_bucket=STAGING_BUCKET)

existing = os.environ.get("AGENT_ENGINE_RESOURCE_NAME")

if existing:
    engine = agent_engines.AgentEngine(resource_name=existing)
    engine.update(agent_engine=root_agent)
    print("\nUpdated existing deployment.")
else:
    engine = agent_engines.AgentEngine.create(
        agent_engine=root_agent,
        requirements=[
            "google-adk>=1.5.0",
            "google-cloud-aiplatform>=1.93.0",
        ],
        extra_packages=["threejs_scene_generator/"],
        display_name="threejs-scene-generator",
        description="Photo-to-Three.js multi-agent pipeline",
    )
    print("\nDeployed successfully.")

print(f"AGENT_ENGINE_RESOURCE_NAME={engine.resource_name}")
print("\nSet this as a Cloud Run env var on personal-website.")
