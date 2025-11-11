# Docker 部署指南 (Docker Deployment Guide)

本文档说明如何使用 Docker 部署 MiniMax Dubbing 系统。

---

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细说明](#详细说明)
- [数据持久化](#数据持久化)
- [常见问题](#常见问题)
- [生产环境部署建议](#生产环境部署建议)

---

## 🖥️ 系统要求

### 硬件要求
- **CPU**: 4核心或以上（推荐8核心）
- **内存**: 8GB RAM 或以上（推荐16GB）
- **存储**: 20GB 可用空间（用于 Docker 镜像和数据）

### 软件要求
- **Docker**: 20.10 或更高版本
- **Docker Compose**: 2.0 或更高版本（可选，但推荐）
- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+) / macOS / Windows with WSL2

### 网络要求
如果在企业网络环境中，需要配置代理：
```bash
export proxy="http://pac-internal.xaminim.com:3129"
export https_proxy=$proxy
export http_proxy=$proxy
export ftp_proxy=$proxy
export no_proxy="localhost,127.0.0.1,*.xaminim.com,10.0.0.0/8"
```

---

## 🚀 快速开始

### 方法一：使用 Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/MiniMax-OpenPlatform/minimax_dubbing.git
cd minimax_dubbing

# 2. 创建数据目录
mkdir -p data/media data/db data/logs

# 3. 构建并启动容器
docker-compose up -d --build

# 4. 查看日志
docker-compose logs -f

# 5. 访问系统
# - 前端: http://localhost:5173
# - 后端 API: http://localhost:5172
# - 管理后台: http://localhost:5172/admin/
```

### 方法二：使用 Docker 命令

```bash
# 1. 构建镜像
docker build -t minimax_dubbing:latest .

# 2. 创建数据目录
mkdir -p data/media data/db data/logs

# 3. 运行容器
docker run -d \
  --name minimax_dubbing \
  -p 5172:5172 \
  -p 5173:5173 \
  -v $(pwd)/data/media:/app/media \
  -v $(pwd)/data/db:/app \
  -v $(pwd)/data/logs:/app/logs \
  -e PYTHONUNBUFFERED=1 \
  -e DEBUG=False \
  --restart unless-stopped \
  minimax_dubbing:latest

# 4. 查看日志
docker logs -f minimax_dubbing
```

---

## 📖 详细说明

### Docker 镜像构建过程

Docker 镜像使用多阶段构建，包含以下步骤：

#### Stage 1: 构建前端
- 基础镜像：`node:18-alpine`
- 安装 Node.js 依赖
- 构建 Vue 3 前端应用
- 生成静态文件到 `frontend/dist/`

#### Stage 2: 下载 AI 模型
- 基础镜像：`python:3.10-slim`
- 安装 PyTorch 和相关库
- 预下载 AI 模型（Demucs + FaceNet，约420MB）
- 缓存模型到 `/root/.cache/torch/`

#### Stage 3: 最终运行镜像
- 基础镜像：`python:3.10-slim`
- 安装系统依赖：FFmpeg, OpenCV, Nginx, Supervisor, Cron
- 复制前端构建产物和 AI 模型缓存
- 安装 Python 后端依赖
- 配置 Nginx、Supervisor 和 Cron
- 设置启动脚本

### 容器内服务架构

单个 Docker 容器内运行多个服务（通过 Supervisor 管理）：

1. **Gunicorn** (端口 5172)
   - Django 后端应用
   - 4 个 worker 进程
   - 超时时间 600 秒（支持长时间操作）

2. **Nginx** (端口 5173)
   - 提供前端静态文件服务
   - 代理 API 请求到 Gunicorn
   - 支持大文件上传（最大500MB）

3. **Cron**
   - 定时任务服务
   - 每天凌晨3点执行数据清理（如果启用）

### 启动流程

容器启动时，`docker-entrypoint.sh` 脚本会执行以下操作：

1. 检查数据库文件是否存在
2. 运行数据库迁移 (`python manage.py migrate`)
3. 收集静态文件 (`python manage.py collectstatic`)
4. 初始化系统和管理员账号 (`python manage.py init_system`)
5. 安装 Cron 任务 (`python manage.py crontab add`)
6. 创建必要的目录
7. 启动 Supervisor 管理所有服务

---

## 💾 数据持久化

### 挂载卷说明

为了保证数据不会在容器重启或删除时丢失，需要挂载以下目录：

#### 1. 媒体文件目录 (`/app/media`)
- **用途**: 存储上传的视频、音频、字幕等文件
- **建议挂载**: `./data/media:/app/media`
- **预估大小**: 取决于使用量，建议预留 50GB+

#### 2. 数据库目录 (`/app/db.sqlite3`)
- **用途**: SQLite 数据库文件
- **建议挂载**: `./data/db:/app`
- **预估大小**: 通常 < 1GB

#### 3. 日志目录 (`/app/logs`)
- **用途**: 应用日志文件
- **建议挂载**: `./data/logs:/app/logs`
- **预估大小**: < 500MB（会自动轮转）

#### 4. AI 模型缓存 (`/root/.cache/torch`)
- **用途**: 缓存 AI 模型（Demucs + FaceNet）
- **建议**: 使用 Docker 命名卷
- **大小**: 约 420MB（固定）

### 数据备份

```bash
# 备份数据库
docker exec minimax_dubbing sqlite3 /app/db.sqlite3 ".backup /app/backup_$(date +%Y%m%d).db"
docker cp minimax_dubbing:/app/backup_$(date +%Y%m%d).db ./backups/

# 备份媒体文件
tar -czf media_backup_$(date +%Y%m%d).tar.gz data/media/

# 或使用 Docker 卷备份
docker run --rm \
  -v minimax_dubbing_model_cache:/source \
  -v $(pwd)/backups:/backup \
  alpine tar -czf /backup/model_cache_backup.tar.gz -C /source .
```

---

## 🔧 常见问题

### Q1: 构建镜像时网络超时？

**原因**: 下载依赖或 AI 模型时网络不稳定

**解决方法**:
```bash
# 配置代理（如果在企业网络）
export proxy="http://pac-internal.xaminim.com:3129"
export https_proxy=$proxy http_proxy=$proxy ftp_proxy=$proxy

# 增加构建超时时间
docker build --network=host -t minimax_dubbing:latest .
```

### Q2: 容器启动后无法访问？

**检查清单**:
```bash
# 1. 检查容器状态
docker ps -a | grep minimax_dubbing

# 2. 查看容器日志
docker logs minimax_dubbing

# 3. 检查端口占用
netstat -tuln | grep -E "5172|5173"

# 4. 进入容器检查服务
docker exec -it minimax_dubbing bash
supervisorctl status
curl http://localhost:5172/api/auth/test-auth/
```

### Q3: AI 模型下载失败？

**症状**: 首次使用人声分离或说话人识别时失败

**解决方法**:
```bash
# 方法1: 重新构建镜像时下载
docker-compose build --no-cache

# 方法2: 进入容器手动下载
docker exec -it minimax_dubbing python download_models.py --demucs --facenet

# 方法3: 从其他服务器复制模型缓存
# 在源服务器：
tar -czf models_cache.tar.gz -C /root/.cache/torch .

# 在目标服务器：
docker cp models_cache.tar.gz minimax_dubbing:/tmp/
docker exec -it minimax_dubbing tar -xzf /tmp/models_cache.tar.gz -C /root/.cache/torch/
```

### Q4: 数据库迁移失败？

**错误示例**: `django.db.utils.OperationalError: no such table`

**解决方法**:
```bash
# 进入容器
docker exec -it minimax_dubbing bash

# 重新运行迁移
python manage.py migrate --noinput

# 检查迁移状态
python manage.py showmigrations

# 重新初始化系统
python manage.py init_system
```

### Q5: 如何修改管理员密码？

**方法1: 使用 init_admin 命令**
```bash
docker exec -it minimax_dubbing python manage.py init_admin --force --username admin --password your_new_password
```

**方法2: 使用 Django shell**
```bash
docker exec -it minimax_dubbing python manage.py shell

# 在 shell 中执行：
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> admin = User.objects.get(username='admin')
>>> admin.set_password('your_new_password')
>>> admin.save()
>>> exit()
```

### Q6: 如何更新到最新版本？

```bash
# 1. 停止容器
docker-compose down

# 2. 备份数据（重要！）
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# 3. 拉取最新代码
git pull origin main

# 4. 重新构建镜像
docker-compose build --no-cache

# 5. 启动新容器
docker-compose up -d

# 6. 查看日志确认
docker-compose logs -f
```

### Q7: 容器内存不足？

**症状**: AI 模型加载失败，OOM 错误

**解决方法**:
```bash
# 增加 Docker 容器内存限制
docker-compose down
# 编辑 docker-compose.yml，调整 deploy.resources.limits.memory
docker-compose up -d
```

---

## 🔒 生产环境部署建议

### 1. 安全配置

#### 修改默认密码
```bash
# 首次部署后立即修改 admin 密码
docker exec -it minimax_dubbing python manage.py init_admin --force --password STRONG_PASSWORD
```

#### 关闭 DEBUG 模式
在 `docker-compose.yml` 中设置：
```yaml
environment:
  - DEBUG=False
  - ALLOWED_HOSTS=your-domain.com,your-ip
```

#### 配置防火墙
```bash
# 仅允许必要端口
ufw allow 5172/tcp
ufw allow 5173/tcp
ufw enable
```

### 2. 性能优化

#### 调整 Gunicorn Worker 数量
编辑 `docker/supervisord.conf`：
```ini
[program:gunicorn]
command=gunicorn backend.wsgi:application --bind 0.0.0.0:5172 --workers 8 --threads 4 --timeout 600
```
建议 workers = (CPU 核心数 × 2) + 1

#### 启用 Nginx 缓存
编辑 `docker/nginx.conf`，添加：
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m inactive=60m;
proxy_cache_key "$scheme$request_method$host$request_uri";
```

### 3. 监控和日志

#### 查看实时日志
```bash
# 所有服务日志
docker-compose logs -f

# 仅后端日志
docker exec minimax_dubbing tail -f /app/logs/gunicorn.log

# 仅 Nginx 日志
docker exec minimax_dubbing tail -f /var/log/nginx/access.log
```

#### 日志轮转
日志文件会自动轮转（最大50MB，保留10个备份）

#### 健康检查
```bash
# 检查容器健康状态
docker inspect --format='{{.State.Health.Status}}' minimax_dubbing

# 手动健康检查
curl http://localhost:5172/api/auth/test-auth/
```

### 4. 定期维护

#### 数据清理策略
访问管理后台 (http://localhost:5172/admin/)，配置自动清理策略：
- 项目清理天数：根据实际需求调整
- 用户清理天数：根据实际需求调整

#### 定期备份
建议设置 cron 任务自动备份：
```bash
# 每天凌晨4点备份
0 4 * * * tar -czf /backups/minimax_dubbing_$(date +\%Y\%m\%d).tar.gz /path/to/data/
```

#### 监控磁盘空间
```bash
# 检查数据目录大小
du -sh data/media data/db data/logs

# 检查 Docker 磁盘使用
docker system df
```

### 5. 高可用性部署

如需高可用性，建议：
1. 使用外部数据库（PostgreSQL）替代 SQLite
2. 使用对象存储（如 MinIO, AWS S3）存储媒体文件
3. 使用 Nginx 负载均衡器分发请求到多个后端实例
4. 使用 Redis 作为缓存和 Celery broker

---

## 📊 资源使用统计

### 镜像大小
- **最终镜像**: 约 4.5 - 5GB
  - 基础镜像: ~1GB
  - 系统依赖: ~800MB
  - Python 依赖: ~3GB
  - Node.js 依赖: ~500MB
  - AI 模型缓存: ~420MB

### 运行时资源
- **内存使用**: 空闲 2-3GB，处理视频时 4-6GB
- **CPU 使用**: 空闲 < 5%，AI 处理时 50-100%
- **磁盘 I/O**: 视频处理时较高

---

## 🆘 技术支持

如遇到问题：
1. 查看容器日志: `docker logs minimax_dubbing`
2. 查看应用日志: `docker exec minimax_dubbing cat /app/logs/gunicorn.log`
3. 提交 Issue: https://github.com/MiniMax-OpenPlatform/minimax_dubbing/issues

---

**Built with Docker** | Last Updated: 2025-01-11
