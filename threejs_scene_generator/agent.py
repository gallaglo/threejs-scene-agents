from google.adk.agents import LoopAgent, SequentialAgent

from .sub_agents.codegen import codegen_agent
from .sub_agents.refinement import refinement_agent
from .sub_agents.validator import validator_agent
from .sub_agents.vision import vision_agent

refine_loop = LoopAgent(
    name="refine_loop",
    max_iterations=3,
    sub_agents=[validator_agent, refinement_agent],
)

root_agent = SequentialAgent(
    name="scene_pipeline",
    sub_agents=[vision_agent, codegen_agent, refine_loop],
)
