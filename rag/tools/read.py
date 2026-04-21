import asyncio
from core.harness import check_path
from tools.base import BaseTool


class Readtool(BaseTool):
    name = 'read_tool'
    description = 'read 文件'

    @property
    def schema(self):
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                "description": "read 文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要读的文件的完整路径",
                        }
                    },
                    "required": ["file_path"],
                },
            },
        }

    @property
    def timeout(self):
        return 60

    async def execute(self, file_path, timeout=None, user_id=None, **_):
        timeout = timeout or self.timeout
        check_path(file_path, user_id=user_id)
        with open(file_path) as f:
            content = f.read()
        return content


if __name__ == '__main__':
    readtool = Readtool()
    tools = [readtool.schema]
    result = asyncio.run(readtool.execute(file_path='/data/haotianwu/simple-agent/my-skill-try/skills/deep-think/skill.md'))
    print(result)
