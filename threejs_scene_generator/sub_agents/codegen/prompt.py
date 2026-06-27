import pathlib

from google.adk.skills import load_skill_from_dir

_skill = load_skill_from_dir(
    pathlib.Path(__file__).parent.parent.parent / "skills" / "threejs-codegen"
)
CODEGEN_PROMPT = _skill.instructions
