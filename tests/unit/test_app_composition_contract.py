from __future__ import annotations


def test_agent_stack_composition_root_lives_under_app_namespace():
    from agent.stack import build_legacy_agent_stack as legacy_build
    from app.agent_stack import build_legacy_agent_stack

    assert build_legacy_agent_stack is legacy_build
