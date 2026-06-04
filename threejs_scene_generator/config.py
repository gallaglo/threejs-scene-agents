import os

# Vision agent gets its own model setting — image understanding benefits from
# Pro's stronger multimodal reasoning, while Flash is sufficient for the
# text-only codegen/validator/refinement agents.
VISION_MODEL = os.getenv("VISION_MODEL", "gemini-2.5-pro")
MODEL = os.getenv("GENAI_MODEL", "gemini-2.5-flash")
