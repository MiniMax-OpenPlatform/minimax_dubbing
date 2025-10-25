# MiniMax Dubbing - AI智能配音系统

[English](./README_EN.md) | 简体中文

> 🎙️ 基于Vue 3 + Django的AI智能配音系统

一个专业的视频配音与翻译平台，集成MiniMax AI API，支持批量翻译、AI语音合成、智能配音等功能。

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Vue](https://img.shields.io/badge/Vue-3.0+-green)
![Django](https://img.shields.io/badge/Django-5.2+-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## 🤖 核心AI能力

### 1️⃣ 丰富音色库与高拟真语音克隆

**传统方式**：配音演员录制成本高，音色选择受限，无法快速迭代。

**AI增值**：MiniMax TTS提供40种语言，数百个高质量预设音色，涵盖不同年龄、性别、情感风格。支持语速、音调、情感强度等细粒度参数调节。更支持语音克隆技术，仅需少量音频样本即可生成高度拟真的定制音色，让每个角色都拥有独特声音特征，实现真人级配音效果。

### 2️⃣ AI翻译与专业词汇优化

**传统方式**：使用通用翻译工具，专业术语翻译不准确，需反复修改。

**AI增值**：集成MiniMax LLM翻译，支持自定义专业词汇表（如人名、地名、专有名词的固定译法）。AI会在翻译时严格遵循词汇表规则，确保术语统一且符合行业标准。支持主流语种语言互译，覆盖全球主流市场，大幅减少人工校对工作量。

### 3️⃣ TTS智能时间戳对齐

**传统方式**：配音时长与原字幕时间轴不匹配，需手动逐句调整时间戳。

**AI增值**：内置智能对齐算法，根据TTS生成的音频时长自动优化字幕时间轴。算法会智能延长或缩短时间戳，保持语句间的自然停顿，确保配音与画面完美同步，省去99%的手动调时工作。

### 4️⃣ AI智能说话人识别（多模态技术）

**传统方式**：手动逐条标注每句对话的说话人，耗时且易出错。

**AI增值**：采用**人脸检测 + VLM命名 + LLM分配**的三阶段智能识别技术：
1. **人脸检测与聚类**：使用FaceNet和DBSCAN算法从视频中检测并聚类人脸
2. **VLM智能命名**：利用Qwen-VL多模态模型分析人脸图像和对话内容，为每个说话人生成姓名、角色、性别、外貌特征和性格分析
3. **LLM精准分配**：使用大语言模型根据对话上下文将字幕精准分配给对应说话人

一键自动完成，将几小时的标注工作缩短至几分钟，识别结果包含说话人档案、代表图片和详细分析，准确率高且支持人工矫正。

---

## ✨ 功能特性

### 核心翻译系统
- **📹 视频音频支持**：上传和处理视频/音频文件进行翻译配音
- **📝 SRT导入导出**：导入SRT字幕文件并导出翻译后的版本
- **🔄 内联编辑**：表格直接编辑，支持自动保存和实时验证
- **🎯 智能分段**：自动文本分段，精确时间轴对齐

### AI驱动功能
- **🤖 批量翻译**：AI批量翻译，实时进度追踪
- **🎙️ 语音合成(TTS)**：将翻译文本转换为自然流畅的语音
- **👥 智能说话人识别**：人脸检测+VLM命名+LLM分配的多模态识别系统
- **🎭 说话人档案**：自动生成说话人姓名、角色、外貌、性格分析
- **⚡ 实时进度**：批量操作的实时进度监控，错误信息固定显示

### 高级音频处理
- **🎵 音频拼接**：将分段音频合并为完整音轨
- **⏱️ 时间戳对齐**：智能优化配音时间戳，确保自然流畅
- **🎛️ 音频预览**：集成媒体播放器和波形可视化
- **🔊 音色映射**：为不同说话人配置不同的音色

### 系统管理
- **📊 任务监控**：后台任务实时监控
- **⚙️ 可配置设置**：管理后台界面进行系统配置
- **🔒 API认证**：安全的API密钥认证机制
- **📱 响应式设计**：基于Vue 3和Element Plus的现代化界面

## 🏗️ 技术架构

### 技术栈
- **前端**: Vue 3 + TypeScript + Element Plus + Vite
- **后端**: Django 5.2.6 + Django REST Framework
- **数据库**: SQLite (开发环境) / PostgreSQL (生产环境)
- **AI集成**:
  - MiniMax API - 翻译和TTS
  - Qwen-VL (DashScope) - 视觉语言模型说话人命名
  - Qwen LLM - 说话人字幕分配
- **计算机视觉**: FaceNet + MTCNN (人脸检测) + DBSCAN (聚类)

### 项目结构
```
minimax_translation/
├── backend/                    # Django配置和核心设置
├── projects/                   # 项目管理应用
├── segments/                   # 片段管理应用
├── authentication/             # 认证系统
├── speakers/                   # 说话人识别系统 (NEW)
├── system_monitor/             # 任务监控和系统配置
├── services/                   # 业务逻辑和AI集成
│   ├── algorithms/             # 时间戳对齐算法
│   ├── business/               # 业务逻辑服务
│   ├── clients/                # 外部API客户端
│   ├── parsers/                # 文件格式解析器
│   └── speaker_diarization/    # 说话人识别pipeline (NEW)
│       ├── face_detector.py    # 人脸检测
│       ├── clusterer.py        # 人脸聚类
│       ├── vlm_naming.py       # VLM说话人命名
│       ├── llm_assignment.py   # LLM字幕分配
│       └── pipeline.py         # 完整流程编排
├── frontend/                   # Vue 3应用
│   ├── src/
│   │   ├── components/         # Vue组件
│   │   ├── composables/        # Vue 3组合式函数
│   │   ├── utils/              # 工具函数
│   │   └── stores/             # Pinia状态管理
└── api_example/                # API使用示例
```

## 🚀 快速开始

### 📦 推荐：使用虚拟环境安装（3分钟）

使用虚拟环境可以隔离项目依赖，避免与系统Python包冲突：

```bash
# 1. 克隆仓库
git clone https://github.com/MiniMax-OpenPlatform/minimax_dubbing.git
cd minimax_dubbing

# 2. 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# Windows系统使用: venv\Scripts\activate

# 3. 安装后端依赖
pip install -r requirements.txt

# 4. 安装前端依赖
cd frontend && npm install && cd ..

# 5. 初始化数据库和管理员账号（必须执行！）
python3 manage.py migrate       # 创建数据库表结构
python3 manage.py init_system   # 创建管理员账号（admin/admin123）
```

> ⚠️ **重要提示**: `migrate` 命令必须执行，否则会导致数据库字段缺失，保存配置时出现 500 错误！

### ⚡ 或者：直接安装（2分钟）

如果不想使用虚拟环境，可以直接安装：

```bash
# 1. 克隆仓库
git clone https://github.com/MiniMax-OpenPlatform/minimax_dubbing.git
cd minimax_dubbing

# 2. 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 3. 初始化数据库和管理员账号（必须执行！）
python3 manage.py migrate       # 创建数据库表结构
python3 manage.py init_system   # 创建管理员账号（admin/admin123）
```

> ⚠️ **重要提示**: `migrate` 命令必须执行，否则会导致数据库字段缺失，保存配置时出现 500 错误！

### 🚀 启动服务

> 💡 **注意**: 如果使用虚拟环境，启动前需先激活虚拟环境: `source venv/bin/activate`

#### 方法1: 两个终端窗口 (推荐)

**终端1 - 启动后端服务:**
```bash
# 如果使用虚拟环境，先激活
source venv/bin/activate  # Linux/Mac，Windows使用 venv\Scripts\activate

cd minimax_translation
python3 manage.py runserver 0.0.0.0:5172
```

**终端2 - 启动前端服务:**
```bash
cd minimax_translation/frontend
npm run dev
```

#### 方法2: 单个终端 (后台运行)

如果只有一个终端，可以将后端放到后台运行：

```bash
# 如果使用虚拟环境，先激活
source venv/bin/activate  # Linux/Mac，Windows使用 venv\Scripts\activate

cd minimax_translation

# 1. 后台启动后端服务
nohup python3 manage.py runserver 0.0.0.0:5172 > backend.log 2>&1 &

# 2. 启动前端服务
cd frontend && npm run dev
```

**停止后台服务:**
```bash
# 查找并停止后端服务
pkill -f "python3 manage.py runserver"
```

#### 方法3: Screen 会话 (生产环境推荐)

使用screen可以防止SSH断开导致的服务停止：

```bash
# 安装screen (如果没有)
sudo apt install screen  # Ubuntu/Debian

# 启动后端会话
screen -S backend
# 如果使用虚拟环境，先激活
source venv/bin/activate  # Linux/Mac
cd minimax_translation
python3 manage.py runserver 0.0.0.0:5172
# 按 Ctrl+A 然后按 D 退出screen

# 启动前端会话
screen -S frontend
cd minimax_translation/frontend
npm run dev
# 按 Ctrl+A 然后按 D 退出screen

# 查看所有会话
screen -ls

# 重新连接会话
screen -r backend   # 连接后端
screen -r frontend  # 连接前端

# 停止会话
screen -S backend -X quit
screen -S frontend -X quit
```

**访问地址 🎉**
- **前端应用**: http://localhost:5173/ (本地) 或 http://YOUR_IP:5173/ (外部)
- **后端API**: http://localhost:5172/api/ (本地) 或 http://YOUR_IP:5172/api/ (外部)

> ⚠️ **重要**: 必须同时运行两个服务才能正常访问！前端在5173端口，后端在5172端口。

### 📋 Prerequisites
- Python 3.10+
- Node.js 16+
- npm

### 💾 模型缓存说明

系统使用的AI模型会自动缓存到本地，**不需要每次都重新下载**：

#### Demucs 人声分离模型
- **首次使用**: 自动下载 htdemucs 模型（约 320MB）
- **缓存位置**: `~/.cache/torch/hub/checkpoints/`
- **后续使用**: 直接使用缓存的模型，无需重新下载
- **团队共享**: 可以将缓存目录打包分享给团队成员，避免重复下载

#### FaceNet 人脸识别模型
- **首次使用**: 自动下载预训练模型（约 100MB）
- **缓存位置**: `~/.cache/torch/hub/checkpoints/`
- **后续使用**: 自动使用本地缓存

#### 手动预下载模型（推荐）

为了避免首次使用时等待，可以使用提供的脚本预先下载所有模型：

```bash
# 下载所有模型
python download_models.py

# 或者只下载特定模型
python download_models.py --demucs     # 只下载Demucs
python download_models.py --facenet    # 只下载FaceNet

# 检查已缓存的模型
python download_models.py --check
```

#### 快速部署技巧
如果需要在多台机器上部署，可以：
```bash
# 方法1: 使用下载脚本预下载（推荐）
python download_models.py

# 方法2: 在已有缓存的机器上打包分享
tar -czf models_cache.tar.gz ~/.cache/torch/
# 在新机器上解压
tar -xzf models_cache.tar.gz -C ~/
```

这样可以避免每台机器都重新下载模型，节省时间和带宽。

### 🔧 Detailed Setup

<details>
<summary>Click for step-by-step instructions</summary>

#### 1. Clone Repository
```bash
git clone https://github.com/backearth1/minimax_translation.git
cd minimax_translation
```

#### 2. Backend Setup
```bash
# (推荐) 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac，Windows使用 venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Setup database
python3 manage.py migrate

# Initialize system (creates admin user automatically)
python3 manage.py init_system
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

#### 4. Environment Configuration (Optional)
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
nano .env
```

#### 5. Start Development Servers (需要两个终端)

**终端1 - 后端服务:**
```bash
# 如果使用虚拟环境，先激活
source venv/bin/activate  # Linux/Mac，Windows使用 venv\Scripts\activate

cd minimax_translation
python3 manage.py runserver 0.0.0.0:5172
```

**终端2 - 前端服务:**
```bash
cd minimax_translation/frontend
npm run dev
```

> 💡 **提示**: 两个服务必须同时运行！前端服务在5173端口，后端服务在5172端口。

</details>

### 🌐 Access Points
- **Frontend**: http://localhost:5173/ (本地) 或 http://YOUR_IP:5173/ (外部)
- **Backend API**: http://localhost:5172/api/ (本地) 或 http://YOUR_IP:5172/api/ (外部)
- **Admin Panel**: http://localhost:5172/admin/ (本地) 或 http://YOUR_IP:5172/admin/ (外部)

> 💡 **外部访问说明**: 将 `YOUR_IP` 替换为你的实际IP地址（如 192.168.1.100）

## 📖 Usage

### Basic Workflow

1. **Create Project**: Upload video file and SRT file (or use ASR to generate subtitles)
2. **Auto Speaker Recognition**: AI automatically detects faces, names speakers, and assigns dialogues
3. **Configure Voices**: Review and adjust speaker-to-voice mappings in project settings
4. **Batch Translate**: Translate all segments using AI
5. **Generate TTS**: Create audio for translated text with aligned timestamps
6. **Preview & Export**: Preview concatenated audio and export results

### Key Features Guide

#### Auto Speaker Recognition (New Multi-Modal AI)
- **Face Detection & Clustering**: Uses FaceNet and DBSCAN to identify unique faces in video
- **VLM Intelligent Naming**: Qwen-VL analyzes face images and dialogue to generate speaker profiles (name, role, gender, appearance, personality)
- **LLM Subtitle Assignment**: Uses large language model to assign each subtitle to the correct speaker based on context
- **Auto Voice Mapping**: Automatically creates speaker-to-voice mappings based on gender and role
- **Result Review**: View speaker profiles with representative images and detailed analysis

#### Batch Operations
- **Translation**: Bulk translate all segments with progress tracking
- **TTS**: Generate audio for all translated segments
- **Real-time Monitoring**: Live progress updates with detailed status

#### Audio Management
- **Concatenation**: Merge segment audio into complete track
- **Preview**: Integrated media player with waveform visualization
- **Export**: Download final audio files

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,10.11.17.19
```

### MiniMax API Setup
Configure your MiniMax API credentials in the Django admin panel or directly in the code.

## 🔧 API Reference

### Authentication
All API requests require authentication via API key:
```bash
curl -H "X-API-KEY: your-api-key" http://localhost:5172/api/projects/
```

### Key Endpoints
- `GET /api/projects/` - List projects
- `POST /api/projects/upload_srt/` - Upload SRT file
- `POST /api/projects/{id}/upload_video/` - Upload video file
- `POST /api/projects/{id}/separate_vocals/` - Separate vocals from video
- `POST /api/projects/{id}/asr_recognize/` - Auto-generate subtitles using ASR
- `POST /speakers/tasks/` - Start speaker recognition task
- `GET /speakers/tasks/{task_id}/progress/` - Get speaker recognition progress
- `POST /api/projects/{id}/batch_translate/` - Start batch translation
- `POST /api/projects/{id}/batch_tts/` - Start batch TTS
- `POST /api/projects/{id}/concatenate_audio/` - Concatenate audio
- `POST /api/projects/{id}/synthesize_video/` - Synthesize final video with translated audio

## 🧪 Testing

### Backend Tests
```bash
python3 manage.py test
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## 🔧 故障排查 (Troubleshooting)

### 问题1: 注册时返回 400 错误 / 保存配置时 500 错误

**错误现象**:
```
POST http://your-ip:5172/api/auth/register/ 400 (Bad Request)
PATCH http://your-ip:5172/api/auth/config/ 500 (Internal Server Error)
```

**原因**: 数据库迁移未执行，缺少必要的字段

**错误日志**:
```
ERROR: table authentication_userconfig has no column named aliyun_access_key_id
ERROR: no such column: authentication_userconfig.dashscope_api_key
```

**解决方法**:
```bash
# 1. 拉取最新代码（包含所有迁移文件）
git pull origin main

# 2. 激活虚拟环境（如果使用）
source venv/bin/activate

# 3. 运行数据库迁移（关键步骤！）
python3 manage.py migrate

# 4. 重启后端服务
pkill -f "python3 manage.py runserver"
python3 manage.py runserver 0.0.0.0:5172
```

**验证迁移是否成功**:
```bash
python3 manage.py showmigrations authentication
# 应该看到所有迁移都有 [X] 标记，包括：
# [X] 0004_userconfig_dashscope_api_key
# [X] 0005_userconfig_aliyun_access_key_id_and_more
```

**如果之前注册失败但能登录（用户已创建但缺少配置）**:
```bash
# 运行修复脚本，为已存在的用户创建配置
python3 fix_incomplete_users.py
```

这个脚本会：
- 检查所有用户，找出没有配置的用户
- 自动为这些用户创建配置
- 验证修复结果

**可能原因2**: 旧版本代码中 MiniMax API Key 配置问题（已修复）

如果使用的是旧版本代码，请拉取最新代码：
```bash
git pull origin main
# 重启后端服务
pkill -f "python3 manage.py runserver"
python3 manage.py runserver 0.0.0.0:5172
```

> 💡 **已修复**: 最新版本已将 MiniMax API Key 默认值内置到 settings.py，无需配置环境变量即可使用

### 问题2: 首次使用人声分离或说话人识别时等待很久

**原因**: 正在下载 AI 模型（Demucs 320MB + FaceNet 100MB）

**解决方法**:
```bash
# 使用脚本预先下载所有模型
python download_models.py

# 或者从其他机器复制模型缓存
tar -czf models_cache.tar.gz ~/.cache/torch/
# 传输到新机器后解压
tar -xzf models_cache.tar.gz -C ~/
```

### 问题3: 前端无法连接后端 API

**检查清单**:
1. 确认后端服务正在运行: `ps aux | grep "python3 manage.py runserver"`
2. 确认端口正确: 后端 5172，前端 5173
3. 检查防火墙规则（如果在远程服务器）
4. 查看后端日志: `tail -f backend.log`（如果使用 nohup）

### 问题4: 虚拟环境激活失败

**Linux/Mac**:
```bash
source venv/bin/activate
```

**Windows**:
```bash
venv\Scripts\activate
```

如果提示权限错误，Windows 需要：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题5: npm install 失败

**解决方法**:
```bash
# 清除 npm 缓存
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

## 📦 Production Deployment

### Backend
```bash
# Install production dependencies
pip install -r requirements.txt

# Collect static files
python3 manage.py collectstatic

# Run with gunicorn
gunicorn backend.wsgi:application
```

### 🔄 Background Service (Persistent Running)

#### For Development (Terminal Closes, Service Continues):
```bash
# Backend - Using nohup
nohup python3 manage.py runserver 0.0.0.0:5172 > backend.log 2>&1 &

# Frontend - Using nohup
cd frontend
nohup npm run dev > frontend.log 2>&1 &

# Check running processes
ps aux | grep python3
ps aux | grep node

# Stop services
pkill -f "python3 manage.py runserver"
pkill -f "npm run dev"
```

#### For Production (Using systemd):
```bash
# 1. Create backend service file
sudo nano /etc/systemd/system/minimax-backend.service

# Content:
[Unit]
Description=MiniMax Translation Backend
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/minimax_translation
ExecStart=/usr/bin/python3 manage.py runserver 0.0.0.0:5172
Restart=always

[Install]
WantedBy=multi-user.target

# 2. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable minimax-backend
sudo systemctl start minimax-backend

# 3. Check status
sudo systemctl status minimax-backend
```

#### Alternative: Using screen/tmux:
```bash
# Using screen
screen -S minimax-backend
python3 manage.py runserver 0.0.0.0:5172
# Press Ctrl+A then D to detach

screen -S minimax-frontend
cd frontend && npm run dev
# Press Ctrl+A then D to detach

# List running screens
screen -ls

# Reattach to screen
screen -r minimax-backend
```

### Frontend
```bash
cd frontend
npm run build
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **MiniMax API** for AI translation and TTS capabilities
- **Vue 3** and **Element Plus** for the modern frontend
- **Django REST Framework** for the robust backend API
- **FFmpeg** for audio processing capabilities

## 📞 技术支持与交流

### 💬 加入微信技术交流群

欢迎扫码加入我们的微信技术交流群，与开发者和用户一起讨论：

<div align="center">
  <img src="./20251023-162139.jpg" alt="微信技术交流群" width="300"/>
  <p><i>扫码加入微信群，交流AI配音技术</i></p>
</div>

### 其他支持方式

- 在 GitHub 仓库创建 Issue 反馈问题
- 查看项目文档
- 参考 `/api_example` 中的API使用示例

---

**Built with ❤️ using Vue 3, Django, and AI-powered technologies**