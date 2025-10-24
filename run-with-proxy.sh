#!/bin/bash
# 带代理配置运行 Docker 容器

# 停止旧容器
sudo docker stop practical_edison 2>/dev/null || true
sudo docker rm practical_edison 2>/dev/null || true

# 使用代理运行新容器
sudo docker run -d \
  --name minimax-translation \
  -p 7860:7860 \
  -e http_proxy=http://pac-internal.xaminim.com:3129 \
  -e https_proxy=http://pac-internal.xaminim.com:3129 \
  -e HTTP_PROXY=http://pac-internal.xaminim.com:3129 \
  -e HTTPS_PROXY=http://pac-internal.xaminim.com:3129 \
  minimax-translation:latest

echo "容器已启动，查看日志："
echo "sudo docker logs -f minimax-translation"
