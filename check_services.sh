#!/bin/bash

echo "=========================================="
echo "服务状态检查"
echo "=========================================="

# 检查后端服务
echo ""
echo "1. Django 后端服务 (端口 5172)"
echo "----------------------------------------"
if ps aux | grep "python.*runserver.*5172" | grep -v grep > /dev/null; then
    echo "✓ Django 服务运行中"

    # 测试API响应
    if curl -s http://localhost:5172/admin/ > /dev/null 2>&1; then
        echo "✓ API 响应正常"
    else
        echo "✗ API 无响应"
    fi
else
    echo "✗ Django 服务未运行"
    echo ""
    echo "启动命令:"
    echo "  python manage.py runserver 0.0.0.0:5172"
fi

# 检查前端服务
echo ""
echo "2. Vue 前端服务 (端口 5173)"
echo "----------------------------------------"
if ps aux | grep "vite" | grep "5173\|minimax_translation" | grep -v grep > /dev/null; then
    echo "✓ Vue 开发服务器运行中"

    # 测试前端响应
    if curl -s http://localhost:5173/ | grep -q "id=\"app\""; then
        echo "✓ 前端页面响应正常"
    else
        echo "✗ 前端页面无响应"
    fi
else
    echo "✗ Vue 开发服务器未运行"
    echo ""
    echo "启动命令:"
    echo "  cd frontend && npm run dev"
fi

echo ""
echo "=========================================="
echo "访问地址"
echo "=========================================="
echo "前端: http://localhost:5173"
echo "后端: http://localhost:5172"
echo "管理后台: http://localhost:5172/admin/"
echo ""
