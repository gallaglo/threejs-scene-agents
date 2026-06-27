from google.adk.agents import LlmAgent

from ... import config
from .prompt import REFINEMENT_PROMPT

refinement_agent = LlmAgent(
    name="refinement_agent",
    model=config.MODEL,
    instruction=REFINEMENT_PROMPT,
    output_key="threejs_code",
)
