import pathlib

from google.adk.skills import load_skill_from_dir

_skill = load_skill_from_dir(
    pathlib.Path(__file__).parent.parent.parent / "skills" / "vision-analyst"
)
VISION_PROMPT = _skill.instructions
