#!/bin/bash

# MiniMax Translation 系统初始化脚本
# 作者: Claude Code
# 功能: 一键初始化整个翻译系统

set -e  # 遇到错误时停止执行

echo "🚀 MiniMax Translation 系统初始化脚本"
echo "=================================="
echo ""

# 检查Python和pip是否存在
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python 3.10+"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm 未安装，请先安装Node.js 16+"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 1. 安装Python依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

# 2. 安装前端依赖
echo "📦 安装前端依赖..."
cd frontend
npm install
cd ..

# 3. 系统初始化
echo "⚙️  初始化系统..."
python manage.py init_system

echo ""
echo "🎉 系统初始化完成！"
echo ""
echo "🔧 启动命令:"
echo "   后端: python manage.py runserver 0.0.0.0:5172"
echo "   前端: cd frontend && npm run dev"
echo ""
echo "🌐 访问地址:"
echo "   前端应用: http://localhost:5173/"
echo "   管理后台: http://localhost:5172/admin/"
echo "   默认账号: admin / admin123"
echo ""
echo "✨ 享受使用 MiniMax Translation！"