#!/usr/bin/env python3
"""
项目验证脚本 - 检查项目配置和依赖
"""
import sys
from pathlib import Path

def check_dependencies():
    """检查依赖包"""
    print("📦 检查依赖包...")

    required = {
        'akshare': 'A股数据获取',
        'sqlalchemy': '数据库ORM',
        'pandas': '数据处理',
        'pyyaml': '配置文件',
        'fastapi': 'API服务',
        'uvicorn': 'ASGI服务器',
        'pydantic': '数据验证',
        'typer': 'CLI工具'
    }

    missing = []
    for package, description in required.items():
        try:
            __import__(package)
            print(f"  ✅ {package:15s} - {description}")
        except ImportError:
            print(f"  ❌ {package:15s} - {description} (未安装)")
            missing.append(package)

    if missing:
        print(f"\n⚠️  缺少 {len(missing)} 个依赖包")
        print("请运行: pip install -r requirements.txt")
        return False

    print("\n✅ 所有依赖包已安装")
    return True


def check_config():
    """检查配置文件"""
    print("\n📝 检查配置文件...")

    config_file = Path("config.yaml")
    example_file = Path("config.yaml.example")

    if not config_file.exists():
        if example_file.exists():
            print("  ⚠️  config.yaml 不存在")
            print(f"  💡 请复制 {example_file} 为 config.yaml")
            return False
        else:
            print("  ❌ 未找到配置文件模板")
            return False

    print("  ✅ config.yaml 存在")

    try:
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 检查必要配置
        if not config.get('llm', {}).get('api_key'):
            print("  ⚠️  未配置 llm.api_key")
            return False

        print("  ✅ 配置文件格式正确")
        return True

    except Exception as e:
        print(f"  ❌ 配置文件解析失败: {e}")
        return False


def check_structure():
    """检查项目结构"""
    print("\n📁 检查项目结构...")

    required_dirs = [
        'stock_analyzer',
        'stock_analyzer/models',
        'stock_analyzer/services',
        'stock_analyzer/tools',
        'stock_analyzer/api',
        'stock_analyzer/web'
    ]

    required_files = [
        'cli.py',
        'requirements.txt',
        'README.md',
        'config.yaml.example',
        'stock_analyzer/__init__.py',
        'stock_analyzer/config.py',
        'stock_analyzer/models/stock.py',
        'stock_analyzer/services/database.py',
        'stock_analyzer/services/data_fetcher.py',
        'stock_analyzer/services/scheduler.py',
        'stock_analyzer/tools/stock_tools.py',
        'stock_analyzer/api/server.py',
        'stock_analyzer/api/llm_handler.py',
        'stock_analyzer/web/index.html'
    ]

    all_ok = True

    for dir_path in required_dirs:
        if Path(dir_path).is_dir():
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ (缺失)")
            all_ok = False

    for file_path in required_files:
        if Path(file_path).is_file():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (缺失)")
            all_ok = False

    if all_ok:
        print("\n✅ 项目结构完整")
    else:
        print("\n⚠️  项目结构不完整")

    return all_ok


def test_import():
    """测试模块导入"""
    print("\n🔍 测试模块导入...")

    try:
        # 添加项目路径
        sys.path.insert(0, str(Path(__file__).parent))

        from stock_analyzer.config import config
        print("  ✅ stock_analyzer.config")

        from stock_analyzer.models import Stock, StockDaily
        print("  ✅ stock_analyzer.models")

        from stock_analyzer.services import DatabaseService, DataFetcher
        print("  ✅ stock_analyzer.services")

        from stock_analyzer.tools import StockTools
        print("  ✅ stock_analyzer.tools")

        print("\n✅ 模块导入成功")
        return True

    except Exception as e:
        print(f"\n❌ 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("A股数据分析系统 - 项目验证")
    print("=" * 60)

    results = []

    # 检查项目结构
    results.append(("项目结构", check_structure()))

    # 检查依赖
    results.append(("依赖包", check_dependencies()))

    # 检查配置
    results.append(("配置文件", check_config()))

    # 测试导入
    results.append(("模块导入", test_import()))

    # 总结
    print("\n" + "=" * 60)
    print("验证结果总结:")
    print("=" * 60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s} {status}")

    all_passed = all(result for _, result in results)

    print("=" * 60)
    if all_passed:
        print("🎉 所有检查通过！项目已准备就绪。")
        print("\n快速开始:")
        print("  1. 编辑 config.yaml 配置文件")
        print("  2. 运行 python cli.py update all 更新数据")
        print("  3. 运行 python cli.py server 启动服务")
        print("  4. 运行 python cli.py client 启动客户端")
    else:
        print("⚠️  部分检查未通过，请根据上述提示修复问题。")
        sys.exit(1)


if __name__ == "__main__":
    main()
