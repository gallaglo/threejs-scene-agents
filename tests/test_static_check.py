from unittest.mock import MagicMock

import pytest

from threejs_scene_generator.agent import _static_validation_check

_VALID_CODE = """
function init() {
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    let animId;

    function animate() {
        animId = requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }
    animate();

    return function dispose() {
        cancelAnimationFrame(animId);
        renderer.dispose();
    };
}
"""


def _ctx(code, iteration=0):
    ctx = MagicMock()
    ctx.state = {"threejs_code": code, "iteration": iteration}
    return ctx


def test_valid_code_passes():
    ctx = _ctx(_VALID_CODE)
    assert _static_validation_check(ctx) == "pass"


def test_missing_init_fails():
    ctx = _ctx("const scene = new THREE.Scene();")
    assert _static_validation_check(ctx) == "fail"
    assert "init" in ctx.state["refinement_targets"]


def test_import_statement_fails():
    ctx = _ctx("import * as THREE from 'three';\n" + _VALID_CODE)
    assert _static_validation_check(ctx) == "fail"
    assert "import" in ctx.state["refinement_targets"].lower()


def test_export_statement_fails():
    ctx = _ctx(_VALID_CODE + "\nexport default init;")
    assert _static_validation_check(ctx) == "fail"
    assert "import" in ctx.state["refinement_targets"].lower() or "export" in ctx.state["refinement_targets"].lower()


def test_missing_renderer_dispose_fails():
    ctx = _ctx(_VALID_CODE.replace("renderer.dispose();", ""))
    assert _static_validation_check(ctx) == "fail"
    assert "renderer.dispose()" in ctx.state["refinement_targets"]


def test_missing_cancel_animation_frame_fails():
    ctx = _ctx(_VALID_CODE.replace("cancelAnimationFrame(animId);", ""))
    assert _static_validation_check(ctx) == "fail"
    assert "cancelAnimationFrame" in ctx.state["refinement_targets"]


def test_banned_api_fails():
    ctx = _ctx(_VALID_CODE + "\nconst geo = new THREE.CapsuleGeometry();")
    assert _static_validation_check(ctx) == "fail"
    assert "CapsuleGeometry" in ctx.state["refinement_targets"]


def test_multiple_failures_all_collected():
    # Code with no init, import statement, and banned API
    ctx = _ctx("import * as THREE from 'three';\nconst x = new THREE.WebGPURenderer();")
    assert _static_validation_check(ctx) == "fail"
    # Expected failures: WebGPURenderer, no init, import statement, missing dispose, missing cancelAnimationFrame, missing render, missing requestAnimationFrame
    targets = ctx.state["refinement_targets"].split("\n")
    assert len(targets) == 7


def test_const_arrow_init_passes():
    code = _VALID_CODE.replace("function init()", "const init = () =>")
    ctx = _ctx(code)
    assert _static_validation_check(ctx) == "pass"


def test_state_side_effects_on_fail():
    ctx = _ctx("const x = 1;")
    _static_validation_check(ctx)
    assert ctx.state["richness_feedback"] == ""
    assert ctx.state["animation_feedback"] == ""
    # Ensure it's stored as a formatted string, not a list
    assert isinstance(ctx.state["refinement_targets"], str)
    assert "1. " in ctx.state["refinement_targets"]


def test_iteration_limit_exceeded():
    ctx = _ctx("const x = 1;", iteration=3)
    assert _static_validation_check(ctx) == "done"
    assert ctx.state["validation_score"] == 0
    assert "Max iterations reached" in ctx.state["validation_feedback"]
    assert "1. " in ctx.state["refinement_targets"]


def test_parameters_usage_fails():
    ctx = _ctx(_VALID_CODE + "\nconst width = geometry.parameters.width;")
    assert _static_validation_check(ctx) == "fail"
    assert "parameters" in ctx.state["refinement_targets"]


def test_uninitialized_array_fails():
    ctx = _ctx(_VALID_CODE + "\nvar queue;\nqueue.shift();")
    assert _static_validation_check(ctx) == "fail"
    assert "queue" in ctx.state["refinement_targets"]


def test_initialized_array_passes():
    ctx = _ctx(_VALID_CODE + "\nconst queue = [];\nqueue.shift();")
    assert _static_validation_check(ctx) == "pass"


def test_parameter_array_passes():
    ctx = _ctx(_VALID_CODE + "\nfunction helper(arr) {\n  arr.push(1);\n}")
    assert _static_validation_check(ctx) == "pass"


def test_missing_renderer_render_fails():
    ctx = _ctx(_VALID_CODE.replace("renderer.render(scene, camera);", ""))
    assert _static_validation_check(ctx) == "fail"
    assert "renderer.render" in ctx.state["refinement_targets"]


def test_missing_request_animation_frame_fails():
    ctx = _ctx(_VALID_CODE.replace("animId = requestAnimationFrame(animate);", ""))
    assert _static_validation_check(ctx) == "fail"
    assert "requestAnimationFrame" in ctx.state["refinement_targets"]
