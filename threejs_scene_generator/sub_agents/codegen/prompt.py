CODEGEN_PROMPT = """
You are generating Three.js r128 JavaScript code. Rules that must never be broken:
1. No import or export statements of any kind.
2. No ES module syntax.
3. Define a function called init that accepts one argument: a canvas element.
4. init must return a dispose function that calls renderer.dispose() and cancels the animation frame.
5. THREE is available as a global variable — do not declare it.
6. Only use APIs that exist in Three.js r128. Do not use APIs introduced after r128.
Output only the JavaScript code. No markdown, no explanation.

Scene description to implement:
{scene_description}

The init(canvas) function must:
- Accept a raw HTMLCanvasElement
- Create a WebGLRenderer attached to that canvas
- Create a PerspectiveCamera and Scene
- Build all geometry, materials, and lights procedurally from the scene description
- Start a requestAnimationFrame animation loop matching the "animation" field
- Return a synchronous dispose() function that calls renderer.dispose() and cancels the animation frame via cancelAnimationFrame

The code must be executable as:
  new Function('THREE', 'canvas', code)(THREE, canvasElement)

Use the colors from the scene description for materials. Match the lighting type (warm/cool/dramatic/neutral) with appropriate light colors and intensities. Match the geometry type exactly. Implement the animation type exactly as specified.
"""
