import argparse
import asyncio
import base64
from pathlib import Path

from threejs_scene_generator.agent import root_agent


async def test(image_path: str | None, prompt: str) -> None:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    initial_state: dict = {"prompt": prompt}
    if image_path:
        image_bytes = Path(image_path).read_bytes()
        initial_state["image"] = base64.b64encode(image_bytes).decode()
        initial_state["mime_type"] = "image/jpeg"

    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="test",
        session_service=session_service,
    )
    session = await session_service.create_session(
        app_name="test",
        user_id="local",
        state=initial_state,
    )

    async for event in runner.run_async(
        user_id="local",
        session_id=session.id,
        new_message=None,
    ):
        print(event)

    final = await session_service.get_session(
        app_name="test", user_id="local", session_id=session.id
    )
    print("\n--- Final Three.js code ---")
    print(final.state.get("threejs_code", "NOT GENERATED"))
    print(f"\nScore: {final.state.get('validation_score')}")
    print(f"Feedback: {final.state.get('validation_feedback')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Three.js scene generator pipeline locally.")
    parser.add_argument("--image", help="Path to input image file")
    parser.add_argument("--prompt", default="", help="Text prompt for scene generation")
    args = parser.parse_args()

    if not args.image and not args.prompt:
        parser.error("At least one of --image or --prompt is required")

    asyncio.run(test(args.image, args.prompt))
