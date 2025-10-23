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

### 4️⃣ AI智能说话人识别

**传统方式**：手动逐条标注每句对话的说话人，耗时且易出错。

**AI增值**：利用MiniMax大语言模型分析对话上下文，自动识别并命名说话人角色，还能根据剧情为角色生成合适的名称。一键自动分配，将几小时的标注工作缩短至几分钟，同时支持人工矫正，准确率正在不断迭代提升，敬请期待。

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
- **👥 自动说话人分配**：基于LLM的智能角色识别与分配
- **⚡ 实时进度**：批量操作的实时进度监控

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
- **AI集成**: MiniMax API 用于翻译和TTS

### 项目结构
```
minimax_translation/
├── backend/                    # Django配置和核心设置
├── projects/                   # 项目管理应用
├── segments/                   # 片段管理应用
├── authentication/             # 认证系统
├── system_monitor/             # 任务监控和系统配置
├── services/                   # 业务逻辑和AI集成
│   ├── algorithms/             # 时间戳对齐算法
│   ├── business/               # 业务逻辑服务
│   ├── clients/                # 外部API客户端
│   └── parsers/                # 文件格式解析器
├── frontend/                   # Vue 3应用
│   ├── src/
│   │   ├── components/         # Vue组件
│   │   ├── composables/        # Vue 3组合式函数
│   │   ├── utils/              # 工具函数
│   │   └── stores/             # Pinia状态管理
└── api_example/                # API使用示例
```

## 🚀 快速开始

### ⚡ 超快速安装（2分钟）

```bash
# 1. 克隆仓库
git clone https://github.com/MiniMax-OpenPlatform/minimax_dubbing.git
cd minimax_dubbing

# 2. 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 3. 初始化数据库和管理员账号
python3 manage.py migrate
python3 manage.py init_system
```

### 🚀 启动服务

#### 方法1: 两个终端窗口 (推荐)

**终端1 - 启动后端服务:**
```bash
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
# Install Python dependencies
pip install -r requirements.txt

# Setup database
python3 manage.py migrate

# Create admin user (optional)
python3 manage.py createsuperuser
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

1. **Create Project**: Upload SRT file or create empty project
2. **Configure Voices**: Set up speaker-to-voice mappings in project settings
3. **Auto Assign Speakers**: Use AI to automatically detect and assign speakers
4. **Batch Translate**: Translate all segments using AI
5. **Generate TTS**: Create audio for translated text
6. **Preview & Export**: Preview concatenated audio and export results

### Key Features Guide

#### Auto Speaker Assignment
- Analyzes dialogue content using LLM
- Automatically assigns speakers based on conversation context
- Requires at least 2 speakers configured in project settings

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
- `POST /api/projects/{id}/batch_translate/` - Start batch translation
- `POST /api/projects/{id}/batch_tts/` - Start batch TTS
- `POST /api/projects/{id}/auto_assign_speakers/` - Auto assign speakers
- `POST /api/projects/{id}/concatenate_audio/` - Concatenate audio

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

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review API examples in `/api_example`

---

**Built with ❤️ using Vue 3, Django, and AI-powered technologies**