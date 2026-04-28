from __future__ import annotations

from dataclasses import dataclass, field


DEFAULT_USER_TOOLS = frozenset(
    {
        "pubmed_search",
        "gene_db_search",
        "personal_lib_search",
        "rag_search",
        "design_crispr_experiment",
        "read_tool",
        "write_tool",
        "execute_shell",
    }
)


@dataclass(frozen=True)
class ToolPolicy:
    """Explicit tool availability contract for Agent runtime wiring."""

    default_tools: frozenset[str] = DEFAULT_USER_TOOLS
    disabled_tools: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def default_user(cls) -> "ToolPolicy":
        return cls()

    def with_disabled(self, tools: set[str] | frozenset[str]) -> "ToolPolicy":
        return ToolPolicy(
            default_tools=self.default_tools,
            disabled_tools=frozenset(tools),
        )

    def enabled_tools(self) -> frozenset[str]:
        return self.default_tools - self.disabled_tools
