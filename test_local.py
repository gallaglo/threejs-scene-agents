import argparse
import asyncio
import base64
from pathlib import Path

from google.genai.types import Content, Part

from threejs_scene_generator.agent import root_agent


async def run_turn(
    session_service,
    runner,
    initial_state: dict,
    label: str,
) -> dict:
    session = await session_service.create_session(
        app_name="test",
        user_id="local",
        state=initial_state,
    )

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    async for event in runner.run_async(
        user_id="local",
        session_id=session.id,
        new_message=Content(role="user", parts=[Part(text="start")]),
    ):
        print(event)

    final = await session_service.get_session(
        app_name="test", user_id="local", session_id=session.id
    )
    print(f"\n--- {label} — Three.js code ---")
    print(final.state.get("threejs_code", "NOT GENERATED"))
    print(f"\nScore: {final.state.get('validation_score')}")
    print(f"Feedback: {final.state.get('validation_feedback')}")
    return final.state


async def test(image_path: str | None, prompt: str, second_prompt: str | None) -> None:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="test",
        session_service=session_service,
    )

    initial_state: dict = {"prompt": prompt}
    if image_path:
        image_bytes = Path(image_path).read_bytes()
        initial_state["image"] = base64.b64encode(image_bytes).decode()
        initial_state["mime_type"] = "image/jpeg"

    state = await run_turn(session_service, runner, initial_state, "Turn 1 — new scene")

    if second_prompt:
        turn2_state: dict = {
            "prompt": second_prompt,
            "threejs_code": state.get("threejs_code", ""),
            "scene_description": state.get("scene_description", ""),
        }
        await run_turn(session_service, runner, turn2_state, "Turn 2 — modification")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Three.js scene generator pipeline locally.")
    parser.add_argument("--image", help="Path to input image file")
    parser.add_argument("--prompt", default="", help="Text prompt for scene generation")
    parser.add_argument("--second-prompt", default="", help="Modification prompt for turn 2 (tests multi-turn path)")
    args = parser.parse_args()

    if not args.image and not args.prompt:
        parser.error("At least one of --image or --prompt is required")

    asyncio.run(test(args.image, args.prompt, args.second_prompt or None))
