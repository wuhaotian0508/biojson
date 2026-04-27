from __future__ import annotations


def test_crispr_tool_preview_and_confirmed_execution():
    import asyncio
    import inspect

    from agent.tools.crispr import CrisprTool
    import agent.tools.crispr as crispr_module

    assert "from skills" not in inspect.getsource(crispr_module)
    assert "import skills" not in inspect.getsource(crispr_module)

    class FakePipeline:
        def __init__(self):
            self.cleaned = False

        def run_all_from_genes(self, genes):
            yield {"type": "progress", "step": 1, "total": 1, "msg": "done"}
            yield {"type": "result", "sops": {"ACC1": "SOP text"}}

        def cleanup(self):
            self.cleaned = True

    tool = CrisprTool(pipeline_factory=FakePipeline)
    preview = asyncio.run(
        tool.execute(genes=[{"gene": "GmFAD2", "species": "Glycine max"}])
    )
    assert "GmFAD2" in preview
    assert "请确认是否继续" in preview

    result = asyncio.run(
        tool.execute(
            genes=[{"gene": "GmFAD2", "species": "Glycine max"}],
            confirmed=True,
        )
    )
    assert "成功为 1 个基因生成了实验方案" in result
    assert "SOP text" in result
