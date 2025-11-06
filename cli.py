#!/usr/bin/env python3
"""
A股数据分析系统 CLI 工具
"""
import typer
import sys
from pathlib import Path
from typing import Optional
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from stock_analyzer.services import DatabaseService, DataFetcher, SchedulerService
from stock_analyzer.tools import StockTools
from stock_analyzer.api.llm_handler import LLMHandler
from stock_analyzer.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer(help="A股数据分析系统")


@app.command()
def server(
    host: str = typer.Option(None, help="服务器地址"),
    port: int = typer.Option(None, help="服务器端口"),
    reload: bool = typer.Option(False, help="开发模式（自动重载）")
):
    """
    启动服务端（包含数据更新和API服务）
    """
    from stock_analyzer.api import start_server

    typer.echo("🚀 正在启动服务端...")
    start_server(host=host, port=port, reload=reload)


@app.command()
def client():
    """
    启动客户端（交互式对话）
    """
    typer.echo("💬 正在启动客户端...")
    typer.echo("正在连接到 LLM...")

    try:
        # 初始化服务
        db_service = DatabaseService()
        stock_tools = StockTools(db_service)
        llm_handler = LLMHandler(stock_tools)

        typer.echo(f"✅ 已连接到 {config.llm.provider} ({config.llm.model})")
        typer.echo("输入 'quit' 或 'exit' 退出\n")

        # 对话历史
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的A股股票分析助手。你可以帮助用户查询股票信息、分析市场数据。"
                          "当用户询问股票相关问题时，你应该使用提供的工具函数来获取准确的数据。"
            }
        ]

        while True:
            try:
                # 获取用户输入
                user_input = typer.prompt("\n你", default="")

                if user_input.lower() in ['quit', 'exit', 'q']:
                    typer.echo("👋 再见！")
                    break

                if not user_input.strip():
                    continue

                # 添加用户消息
                messages.append({"role": "user", "content": user_input})

                # 调用 LLM
                typer.echo("\n🤖 助手: ", nl=False)
                response = llm_handler.chat(messages)

                # 显示响应
                if response.get("content"):
                    typer.echo(response["content"])
                    # 添加助手响应到历史
                    messages.append({"role": "assistant", "content": response["content"]})
                else:
                    typer.echo("抱歉，我无法回答这个问题。")

            except KeyboardInterrupt:
                typer.echo("\n\n👋 再见！")
                break
            except Exception as e:
                typer.echo(f"\n❌ 错误: {e}", err=True)

    except Exception as e:
        typer.echo(f"❌ 启动失败: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def update(
    type: str = typer.Argument("all", help="更新类型: all(全部), stocks(股票信息), daily(每日数据)"),
    codes: Optional[str] = typer.Option(None, help="指定股票代码（逗号分隔），仅用于daily类型")
):
    """
    手动更新数据
    """
    typer.echo(f"📥 开始更新数据 (类型: {type})...")

    try:
        db_service = DatabaseService()
        scheduler = SchedulerService(db_service)

        if type == "all":
            scheduler.daily_update_job()
        elif type == "stocks":
            scheduler.update_all_stocks()
        elif type == "daily":
            stock_codes = codes.split(",") if codes else None
            scheduler.update_daily_data(stock_codes)
        else:
            typer.echo(f"❌ 无效的更新类型: {type}", err=True)
            raise typer.Exit(1)

        typer.echo("✅ 更新完成！")

    except Exception as e:
        typer.echo(f"❌ 更新失败: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def stats():
    """
    查看数据库统计信息
    """
    try:
        db_service = DatabaseService()

        stock_count = db_service.get_stock_count()
        daily_count = db_service.get_daily_data_count()
        latest_date = db_service.get_latest_trade_date()

        typer.echo("\n📊 数据库统计信息")
        typer.echo("=" * 40)
        typer.echo(f"股票总数: {stock_count}")
        typer.echo(f"历史数据记录数: {daily_count}")
        typer.echo(f"最新交易日期: {latest_date if latest_date else '无'}")
        typer.echo("=" * 40 + "\n")

    except Exception as e:
        typer.echo(f"❌ 查询失败: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def search(keyword: str):
    """
    搜索股票
    """
    try:
        db_service = DatabaseService()
        stocks = db_service.search_stocks(keyword, limit=20)

        if not stocks:
            typer.echo(f"❌ 未找到包含 '{keyword}' 的股票")
            return

        typer.echo(f"\n🔍 搜索结果 (关键词: {keyword})")
        typer.echo("=" * 80)
        typer.echo(f"{'代码':<10} {'名称':<15} {'行业':<15} {'市盈率':<10} {'市值(亿)':<12}")
        typer.echo("-" * 80)

        for stock in stocks:
            pe = f"{stock.pe_ratio:.2f}" if stock.pe_ratio else "N/A"
            cap = f"{stock.total_market_cap:.2f}" if stock.total_market_cap else "N/A"
            industry = stock.industry[:12] + "..." if stock.industry and len(stock.industry) > 12 else (stock.industry or "N/A")

            typer.echo(f"{stock.code:<10} {stock.name:<15} {industry:<15} {pe:<10} {cap:<12}")

        typer.echo("=" * 80 + "\n")

    except Exception as e:
        typer.echo(f"❌ 搜索失败: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def init_config():
    """
    初始化配置文件
    """
    import shutil

    config_file = Path("config.yaml")
    example_file = Path("config.yaml.example")

    if config_file.exists():
        overwrite = typer.confirm("配置文件已存在，是否覆盖？")
        if not overwrite:
            typer.echo("❌ 取消操作")
            return

    if example_file.exists():
        shutil.copy(example_file, config_file)
        typer.echo(f"✅ 已创建配置文件: {config_file}")
        typer.echo("⚠️  请编辑配置文件，填入您的 API key 等信息")
    else:
        typer.echo("❌ 未找到配置模板文件", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
