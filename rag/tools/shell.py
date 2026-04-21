import asyncio
from core.harness import check_command
from tools.base import BaseTool


class Shelltool(BaseTool):
    name = 'execute_shell'
    description = '执行 shell 命令'

    @property
    def schema(self):
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                "description": "执行 shell 命令",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "要执行的 shell 命令",
                        }
                    },
                    "required": ["command"],
                },
            },
        }

    @property
    def timeout(self):
        return 60

    async def execute(self, command, timeout=None, **_):
        timeout = timeout or self.timeout
        check_command(command)
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )

        output = stdout.decode()
        if stderr:
            output += f"\nSTDERR:\n{stderr.decode()}"
        output += f"\nExit code: {process.returncode}"
        return output


if __name__ == '__main__':
    shell = Shelltool()
    tools = [shell.schema]
    result = asyncio.run(shell.execute(command='ls -la'))
    print(result)
