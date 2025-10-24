# Docker 部署说明

## 快速启动

### 1. 构建镜像（离线构建）

```bash
sudo docker build --network host -t minimax-translation:latest .
```

**构建时间**: 约 10 秒（使用离线资源）
**镜像大小**: 261MB

### 2. 运行容器（带代理配置）

```bash
sudo docker run -d \
  --name minimax-translation \
  -p 7860:7860 \
  -e http_proxy=http://pac-internal.xaminim.com:3129 \
  -e https_proxy=http://pac-internal.xaminim.com:3129 \
  -e HTTP_PROXY=http://pac-internal.xaminim.com:3129 \
  -e HTTPS_PROXY=http://pac-internal.xaminim.com:3129 \
  -e NO_PROXY=localhost,127.0.0.1 \
  minimax-translation:latest
```

或者使用脚本：
```bash
./run-with-proxy.sh
```

### 3. 访问应用

- **前端**: http://your-server-ip:7860
- **管理后台**: http://your-server-ip:7860/admin/

### 4. 登录凭证

- **用户名**: `admin`
- **密码**: `admin123`
- **API密钥**: `admin_api_key_12345`

## 常用命令

### 查看日志
```bash
sudo docker logs -f minimax-translation
```

### 停止容器
```bash
sudo docker stop minimax-translation
```

### 重启容器
```bash
sudo docker restart minimax-translation
```

### 删除容器
```bash
sudo docker stop minimax-translation
sudo docker rm minimax-translation
```

### 进入容器
```bash
sudo docker exec -it minimax-translation bash
```

## 离线构建资源

项目使用完全离线的构建方式，所有依赖都预先下载到 `.docker-resources/` 目录：

- `ffmpeg`, `ffprobe` - 音频处理二进制文件
- `pip-packages/` - Python 依赖包
- `node_modules.tar.gz` - 前端依赖包

## 网络配置

容器需要通过代理访问外网（MiniMax API）：

- **代理地址**: http://pac-internal.xaminim.com:3129
- **作用**: 启用 AI 翻译和 TTS 功能

如果不配置代理：
- ✅ 基础功能正常（项目管理、文件上传、编辑）
- ❌ AI 功能无法使用（翻译、TTS）

## 故障排查

### 前端认证失败 (401)

清除浏览器缓存：
```javascript
// 在浏览器控制台执行
localStorage.clear()
sessionStorage.clear()
location.reload()
```

然后使用 `admin/admin123` 登录。

### AI 功能无法使用

检查代理配置：
```bash
sudo docker exec minimax-translation env | grep -i proxy
```

应该看到：
```
HTTP_PROXY=http://pac-internal.xaminim.com:3129
HTTPS_PROXY=http://pac-internal.xaminim.com:3129
```

### 验证网络连接

```bash
sudo docker exec minimax-translation python3 -c "
import requests
response = requests.get('https://api.minimaxi.com', timeout=10)
print(f'Status: {response.status_code}')
"
```

## 数据持久化

当前配置使用容器内本地存储。如需持久化数据，可以挂载卷：

```bash
sudo docker run -d \
  --name minimax-translation \
  -p 7860:7860 \
  -v /path/to/data:/app/db.sqlite3 \
  -v /path/to/media:/app/media \
  -e http_proxy=http://pac-internal.xaminim.com:3129 \
  -e https_proxy=http://pac-internal.xaminim.com:3129 \
  minimax-translation:latest
```

## 架构说明

- **后端**: Django + Gunicorn (2 workers)
- **前端**: Vue 3 (已打包到镜像内)
- **数据库**: SQLite
- **端口**: 7860
- **音频处理**: ffmpeg

## 更新部署

```bash
# 1. 停止并删除旧容器
sudo docker stop minimax-translation
sudo docker rm minimax-translation

# 2. 重新构建镜像
sudo docker build --network host -t minimax-translation:latest .

# 3. 启动新容器
./run-with-proxy.sh
```
