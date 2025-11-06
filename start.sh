#!/bin/bash

echo "🚀 A股数据分析系统快速启动脚本"
echo "=================================="
echo ""

# 检查配置文件
if [ ! -f "config.yaml" ]; then
    echo "⚠️  未找到配置文件，正在创建..."
    if [ -f "config.yaml.example" ]; then
        cp config.yaml.example config.yaml
        echo "✅ 已创建 config.yaml，请编辑该文件并填入您的配置信息"
        echo ""
        echo "重要提示："
        echo "1. 填写 llm.api_key (必须)"
        echo "2. 根据需要选择 llm.provider (openai/anthropic/ollama)"
        echo "3. 数据库默认使用 SQLite，无需额外配置"
        echo ""
        read -p "配置完成后按回车继续..."
    else
        echo "❌ 未找到 config.yaml.example 文件"
        exit 1
    fi
fi

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import akshare" 2>/dev/null; then
    echo "⚠️  依赖未安装，正在安装..."
    pip install -r requirements.txt
fi

echo ""
echo "请选择启动模式："
echo "1. 服务端模式 (提供API服务和Web界面)"
echo "2. 客户端模式 (命令行对话)"
echo "3. 更新数据"
echo "4. 查看统计"
echo ""

read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo "🌐 启动服务端..."
        echo "API文档: http://localhost:8000/docs"
        echo "Web界面: 在浏览器打开 stock_analyzer/web/index.html"
        python3 cli.py server
        ;;
    2)
        echo "💬 启动客户端..."
        python3 cli.py client
        ;;
    3)
        echo "📥 更新数据..."
        echo "注意：首次更新可能需要较长时间"
        python3 cli.py update all
        ;;
    4)
        echo "📊 查看统计..."
        python3 cli.py stats
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
