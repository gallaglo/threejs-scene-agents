from google.adk.agents import LlmAgent

from ... import config
from .prompt import VALIDATOR_PROMPT
from .tools import set_validation_result

validator_agent = LlmAgent(
    name="validator_agent",
    model=config.MODEL,
    instruction=VALIDATOR_PROMPT,
    tools=[set_validation_result],
)
