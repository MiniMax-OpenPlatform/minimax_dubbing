#!/bin/bash
# Docker构建脚本 - 使用host网络模式解决网络访问问题

echo "开始构建 minimax-translation Docker镜像..."
echo "使用host网络模式以访问国内镜像源"

sudo docker build \
    --network host \
    -t minimax-translation:latest \
    .

if [ $? -eq 0 ]; then
    echo "✅ 构建成功！"
    echo "运行容器: sudo docker run -p 7860:7860 minimax-translation:latest"
else
    echo "❌ 构建失败"
    exit 1
fi
