from unittest.mock import MagicMock

import pytest

from threejs_scene_generator.agent import _static_check

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


def _ctx(code):
    ctx = MagicMock()
    ctx.state = {"threejs_code": code}
    return ctx


def test_valid_code_passes():
    ctx = _ctx(_VALID_CODE)
    assert _static_check(ctx) is None


def test_missing_init_fails():
    ctx = _ctx("const scene = new THREE.Scene();")
    assert _static_check(ctx) == "fail"
    assert any("init" in t for t in ctx.state["refinement_targets"])


def test_import_statement_fails():
    ctx = _ctx("import * as THREE from 'three';\n" + _VALID_CODE)
    assert _static_check(ctx) == "fail"
    assert any("import" in t.lower() for t in ctx.state["refinement_targets"])


def test_export_statement_fails():
    ctx = _ctx(_VALID_CODE + "\nexport default init;")
    assert _static_check(ctx) == "fail"
    assert any("import" in t.lower() or "export" in t.lower() for t in ctx.state["refinement_targets"])


def test_missing_renderer_dispose_fails():
    ctx = _ctx(_VALID_CODE.replace("renderer.dispose();", ""))
    assert _static_check(ctx) == "fail"
    assert any("renderer.dispose()" in t for t in ctx.state["refinement_targets"])


def test_missing_cancel_animation_frame_fails():
    ctx = _ctx(_VALID_CODE.replace("cancelAnimationFrame(animId);", ""))
    assert _static_check(ctx) == "fail"
    assert any("cancelAnimationFrame" in t for t in ctx.state["refinement_targets"])


def test_multiple_failures_all_collected():
    # Code with no init, import statement, missing both cleanup calls
    ctx = _ctx("import * as THREE from 'three';\nconst x = 1;")
    assert _static_check(ctx) == "fail"
    assert len(ctx.state["refinement_targets"]) == 4


def test_const_arrow_init_passes():
    code = _VALID_CODE.replace("function init()", "const init = () =>")
    ctx = _ctx(code)
    assert _static_check(ctx) is None


def test_state_side_effects_on_fail():
    ctx = _ctx("const x = 1;")
    _static_check(ctx)
    assert ctx.state["richness_feedback"] == ""
    assert ctx.state["animation_feedback"] == ""
    assert isinstance(ctx.state["refinement_targets"], list)
