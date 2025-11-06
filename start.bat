@echo off
chcp 65001 >nul
echo 🚀 A股数据分析系统快速启动脚本
echo ==================================
echo.

REM 检查配置文件
if not exist "config.yaml" (
    echo ⚠️  未找到配置文件，正在创建...
    if exist "config.yaml.example" (
        copy config.yaml.example config.yaml >nul
        echo ✅ 已创建 config.yaml，请编辑该文件并填入您的配置信息
        echo.
        echo 重要提示：
        echo 1. 填写 llm.api_key ^(必须^)
        echo 2. 根据需要选择 llm.provider ^(openai/anthropic/ollama^)
        echo 3. 数据库默认使用 SQLite，无需额外配置
        echo.
        pause
    ) else (
        echo ❌ 未找到 config.yaml.example 文件
        pause
        exit /b 1
    )
)

echo.
echo 请选择启动模式：
echo 1. 服务端模式 ^(提供API服务和Web界面^)
echo 2. 客户端模式 ^(命令行对话^)
echo 3. 更新数据
echo 4. 查看统计
echo.

set /p choice="请输入选项 (1-4): "

if "%choice%"=="1" (
    echo 🌐 启动服务端...
    echo API文档: http://localhost:8000/docs
    echo Web界面: 在浏览器打开 stock_analyzer/web/index.html
    python cli.py server
) else if "%choice%"=="2" (
    echo 💬 启动客户端...
    python cli.py client
) else if "%choice%"=="3" (
    echo 📥 更新数据...
    echo 注意：首次更新可能需要较长时间
    python cli.py update all
) else if "%choice%"=="4" (
    echo 📊 查看统计...
    python cli.py stats
) else (
    echo ❌ 无效选项
    pause
    exit /b 1
)

pause
