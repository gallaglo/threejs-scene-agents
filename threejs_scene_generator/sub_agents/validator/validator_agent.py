from google.adk.agents import LlmAgent
from google.genai.types import GenerateContentConfig, ThinkingConfig

from ... import config
from .prompt import VALIDATOR_PROMPT
from .tools import set_validation_result

validator_agent = LlmAgent(
    name="validator_agent",
    model=config.MODEL,
    instruction=VALIDATOR_PROMPT,
    tools=[set_validation_result],
    generate_content_config=GenerateContentConfig(
        thinking_config=ThinkingConfig(thinking_budget=0)
    ),
)
