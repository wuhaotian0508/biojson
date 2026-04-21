"""
Toolregistry — 工具注册中心

管理所有 RAG 搜索工具的注册、查找和执行分发。
支持 BaseTool 类型校验和自动发现。
"""
from __future__ import annotations

import importlib
import inspect
import logging
from pathlib import Path

from tools.base import BaseTool

logger = logging.getLogger(__name__)

# 自动发现时跳过的模块（不含可注册工具，或需要手动配置）
_SKIP_MODULES = {"__init__", "base", "registry", "reranker"}


class Toolregistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """注册一个 tool（必须继承 BaseTool）"""
        if not isinstance(tool, BaseTool):
            raise TypeError(
                f"工具 {tool!r} 未继承 BaseTool，请先迁移。"
                f"期望 BaseTool 子类，实际为 {type(tool).__name__}"
            )
        if tool.name in self._tools:
            logger.warning("工具 %r 重复注册，覆盖旧实例", tool.name)
        self._tools[tool.name] = tool
        logger.debug("已注册工具: %s (%s)", tool.name, type(tool).__name__)

    def get(self, name: str) -> BaseTool | None:
        """按名称获取 tool，不存在返回 None"""
        return self._tools.get(name)

    def list_all(self) -> list[dict]:
        """返回所有 tool 的 name + description，供前端展示"""
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]

    @property
    def tool_names(self) -> set[str]:
        """返回所有已注册工具名称集合"""
        return set(self._tools.keys())

    @property
    def get_definitions(self) -> list[dict]:
        """所有 tool 的 OpenAI function calling schema 列表"""
        return [t.schema for t in self._tools.values()]

    async def execute(self, name: str, **params):
        """按名称分发执行（async）"""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"未知工具: {name}")
        return await tool.execute(**params)

    def auto_discover(
        self,
        tools_dir: str | Path | None = None,
        skip: set[str] | None = None,
    ) -> list[str]:
        """扫描 tools/ 目录，自动导入并注册所有无参构造的 BaseTool 子类。

        需要构造器参数的工具（GeneDBSearchTool 等）不会被自动注册，
        应手动实例化后调用 register()。

        返回成功自动注册的工具名列表。
        """
        if tools_dir is None:
            tools_dir = Path(__file__).parent
        else:
            tools_dir = Path(tools_dir)

        skip_names = skip or _SKIP_MODULES
        registered: list[str] = []

        for py_file in sorted(tools_dir.glob("*.py")):
            mod_name = py_file.stem
            if mod_name in skip_names:
                continue

            try:
                module = importlib.import_module(f"tools.{mod_name}")
            except Exception as e:
                logger.warning("自动发现: 导入 tools.%s 失败: %s", mod_name, e)
                continue

            for _attr_name, cls in inspect.getmembers(module, inspect.isclass):
                # 必须是 BaseTool 子类（非 BaseTool 本身），且定义在当前模块
                if (
                    cls is BaseTool
                    or not issubclass(cls, BaseTool)
                    or cls.__module__ != module.__name__
                ):
                    continue
                # 已注册则跳过
                if hasattr(cls, "name") and cls.name in self._tools:
                    continue
                # 尝试无参实例化
                try:
                    sig = inspect.signature(cls.__init__)
                    # 除 self 外是否都有默认值
                    params_needed = [
                        p for name, p in sig.parameters.items()
                        if name != "self"
                        and p.default is inspect.Parameter.empty
                        and p.kind not in (
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        )
                    ]
                    if params_needed:
                        logger.debug(
                            "自动发现: %s 需要构造参数 %s，跳过",
                            cls.__name__,
                            [p.name for p in params_needed],
                        )
                        continue
                    instance = cls()
                    self.register(instance)
                    registered.append(instance.name)
                except Exception as e:
                    logger.warning("自动发现: 实例化 %s 失败: %s", cls.__name__, e)

        if registered:
            logger.info("自动发现注册了 %d 个工具: %s", len(registered), registered)
        return registered

    def __repr__(self):
        return f"Toolregistry(tools={list(self._tools.keys())})"
