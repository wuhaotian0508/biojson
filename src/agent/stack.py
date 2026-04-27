from app.agent_stack import LegacyAgentStack, _legacy_defaults, build_legacy_agent_stack

# Compatibility facade for old agent.stack imports. The canonical implementation
# lives in app.agent_stack and still loads defaults through Settings.from_env.

__all__ = ["LegacyAgentStack", "_legacy_defaults", "build_legacy_agent_stack"]
