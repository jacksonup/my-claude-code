"""CLI 入口 — 只做参数解析和分发，不承载 agent loop 逻辑。"""

import asyncio
import sys

import click

MIN_PYTHON = (3, 10)


def _check_python() -> tuple[bool, str]:
    v = sys.version_info[:2]
    ok = v >= MIN_PYTHON
    msg = f"Python {v[0]}.{v[1]} (需要 >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]})"
    return ok, msg


def _check_imports() -> list[tuple[str, bool, str]]:
    results = []
    for pkg in ("click", "httpx", "pydantic", "rich"):
        try:
            __import__(pkg)
            results.append((pkg, True, "OK"))
        except ImportError as e:
            results.append((pkg, False, str(e)))
    return results


@click.group()
@click.version_option(version="0.1.0", prog_name="my-claude")
def main():
    """my-claude — Python 版终端编码助手"""


@main.command()
def doctor():
    """检查运行环境。"""
    ok, msg = _check_python()
    status = "✓" if ok else "✗"
    click.echo(f"  {status} Python: {msg}")

    for pkg, passed, detail in _check_imports():
        status = "✓" if passed else "✗"
        click.echo(f"  {status} {pkg}: {detail}")

    if not ok:
        sys.exit(1)


@main.command()
@click.option("--model", default=None, help="模型名（mock 为离线模式）")
@click.option("--prompt", "-p", default="Hello", help="用户输入")
def chat(model: str | None, prompt: str):
    """单轮对话 — 验证模型链路。"""
    from my_claude_code.runtime.app import create_model, run_chat

    adapter = create_model(model)
    click.echo(f"[model: {adapter.model_name}]")

    text = asyncio.run(run_chat(adapter, prompt))
    click.echo(text)
