# MiniMax Translation

> 🚀 基于Vue 3 + Django的AI视频翻译管理系统

一个专业的视频翻译管理平台，集成MiniMax AI API，支持批量翻译、TTS语音合成、在线编辑等功能。

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Vue](https://img.shields.io/badge/Vue-3.0+-green)
![Django](https://img.shields.io/badge/Django-5.2+-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## ✨ Features

### Core Translation System
- **📹 Video & Audio Support**: Upload and process video/audio files for translation
- **📝 SRT Import/Export**: Import SRT subtitle files and export translated versions
- **🔄 Inline Editing**: Direct table editing with auto-save and validation
- **🎯 Smart Segmentation**: Automatic text segmentation with time alignment

### AI-Powered Features
- **🤖 Batch Translation**: AI-powered bulk translation with progress tracking
- **🎙️ Text-to-Speech (TTS)**: Generate natural speech from translated text
- **👥 Auto Speaker Assignment**: LLM-based automatic speaker detection and assignment
- **⚡ Real-time Progress**: Live progress monitoring for batch operations

### Advanced Audio Processing
- **🎵 Audio Concatenation**: Merge individual segment audio into complete tracks
- **⏱️ Timestamp Alignment**: Smart timestamp optimization for natural speech
- **🎛️ Audio Preview**: Integrated media player with waveform visualization
- **🔊 Voice Mapping**: Configure different voices for different speakers

### System Management
- **📊 Task Monitoring**: Real-time monitoring of background tasks
- **⚙️ Configurable Settings**: Admin interface for system configuration
- **🔒 API Authentication**: Secure API key-based authentication
- **📱 Responsive Design**: Modern Vue 3 interface with Element Plus

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Vue 3 + TypeScript + Element Plus + Vite
- **Backend**: Django 5.2.6 + Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI Integration**: MiniMax API for translation and TTS

### Project Structure
```
minimax_translation/
├── backend/                    # Django settings and configuration
├── projects/                   # Project management app
├── segments/                   # Segment management app
├── authentication/             # Auth system
├── system_monitor/             # Task monitoring and system config
├── services/                   # Business logic and AI integrations
│   ├── algorithms/             # Timestamp alignment algorithms
│   ├── business/               # Business logic services
│   ├── clients/                # External API clients
│   └── parsers/                # File format parsers
├── frontend/                   # Vue 3 application
│   ├── src/
│   │   ├── components/         # Vue components
│   │   ├── composables/        # Vue 3 composition functions
│   │   ├── utils/              # Utility functions
│   │   └── stores/             # Pinia state management
└── api_example/                # API usage examples
```

## 🚀 Quick Start

### ⚡ Super Quick Setup (2 minutes)

```bash
# 1. Clone and setup
git clone https://github.com/backearth1/minimax_translation.git
cd minimax_translation

# 2. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 3. Setup database
python3 manage.py migrate
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