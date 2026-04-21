import asyncio
from core.harness import check_path
from tools.base import BaseTool


class Writetool(BaseTool):
    name = 'write_tool'
    description = 'write 文件'

    @property
    def schema(self):
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                "description": "write 文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要写的文件的完整路径",
                        },
                        "content": {
                            "type": "string",
                            "description": "要写的内容",
                        }
                    },
                    "required": ["file_path", "content"],
                },
            },
        }

    @property
    def timeout(self):
        return 60

    async def execute(self, file_path, content, timeout=None, user_id=None, **_):
        timeout = timeout or self.timeout
        check_path(file_path, write=True, user_id=user_id)
        with open(file_path, 'w') as f:
            f.write(content)
        return content


if __name__ == '__main__':
    writetool = Writetool()
    tools = [writetool.schema]
    result = asyncio.run(writetool.execute(file_path='/data/haotianwu/simple-agent/my-skill-try/111.txt', content='111111'))
    print(result)
