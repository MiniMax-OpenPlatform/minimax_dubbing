# MiniMax Dubbing - AI-Powered Dubbing System

English | [简体中文](./README.md)

> 🎙️ AI-Powered Dubbing System Based on Vue 3 + Django

A professional video dubbing and translation platform integrated with MiniMax AI API, supporting batch translation, AI voice synthesis, and intelligent dubbing.

## 🌐 Try It Online

**Live Demo:** [https://solution.minimaxi.com/dubbing/](https://solution.minimaxi.com/dubbing/)

No deployment needed - try all features online now!

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Vue](https://img.shields.io/badge/Vue-3.0+-green)
![Django](https://img.shields.io/badge/Django-5.2+-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## 🤖 Core AI Capabilities

### 1️⃣ Rich Voice Library & High-Fidelity Voice Cloning

**Traditional Approach**: High cost of voice actor recording, limited voice options, unable to iterate quickly.

**AI Value**: MiniMax TTS provides 40 languages and hundreds of high-quality preset voices covering different ages, genders, and emotional styles. Supports fine-grained parameter adjustment for speech rate, pitch, and emotional intensity. Also supports voice cloning technology - generate highly realistic custom voices with only a few audio samples, giving each character unique voice characteristics for human-level dubbing quality.

### 2️⃣ AI Translation with Professional Vocabulary Optimization

**Traditional Approach**: Generic translation tools produce inaccurate professional terminology, requiring extensive manual revision.

**AI Value**: Integrated with MiniMax LLM translation, supports custom vocabulary lists (such as names, place names, and fixed translations for proper nouns). AI strictly follows vocabulary rules during translation, ensuring consistent terminology that meets industry standards. Supports translation between mainstream languages, covering global mainstream markets, significantly reducing manual proofreading workload.

### 3️⃣ TTS Intelligent Timestamp Alignment

**Traditional Approach**: Dubbing duration doesn't match original subtitle timeline, requiring manual timestamp adjustment for each line.

**AI Value**: Built-in intelligent alignment algorithm automatically optimizes subtitle timeline based on TTS-generated audio duration. The algorithm intelligently extends or shortens timestamps while maintaining natural pauses between sentences, ensuring perfect synchronization between dubbing and video, eliminating 99% of manual timing work.

### 4️⃣ AI Intelligent Speaker Recognition

**Traditional Approach**: Manually labeling speakers for each dialogue line is time-consuming and error-prone.

**AI Value**: Utilizes MiniMax Large Language Model to analyze dialogue context, automatically identifying and naming speaker roles, and can generate appropriate character names based on the plot. One-click automatic assignment reduces hours of annotation work to just minutes, with support for manual correction. Accuracy is continuously improving through iterations - stay tuned!

---

## ✨ Features

### Core Translation System
- **📹 Video & Audio Support**: Upload and process video/audio files for dubbing
- **📝 SRT Import/Export**: Import SRT subtitle files and export translated versions
- **🔄 Inline Editing**: Direct table editing with auto-save and real-time validation
- **🎯 Smart Segmentation**: Automatic text segmentation with precise timeline alignment

### AI-Powered Features
- **🤖 Batch Translation**: AI-powered bulk translation with real-time progress tracking
- **🎙️ Text-to-Speech (TTS)**: Convert translated text to natural, fluent speech
- **👥 Auto Speaker Assignment**: LLM-based intelligent character recognition and assignment
- **⚡ Real-time Progress**: Live progress monitoring for batch operations

### Advanced Audio Processing
- **🎵 Audio Concatenation**: Merge segment audio into complete tracks
- **⏱️ Timestamp Alignment**: Smart optimization of dubbing timestamps for natural flow
- **🎛️ Audio Preview**: Integrated media player with waveform visualization
- **🔊 Voice Mapping**: Configure different voices for different speakers

### System Management
- **📊 Task Monitoring**: Real-time background task monitoring
- **⚙️ Configurable Settings**: Admin interface for system configuration
- **🔒 API Authentication**: Secure API key-based authentication
- **📱 Responsive Design**: Modern interface built with Vue 3 and Element Plus

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Vue 3 + TypeScript + Element Plus + Vite
- **Backend**: Django 5.2.6 + Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI Integration**: MiniMax API for translation and TTS
- **Computer Vision**: FaceNet + MTCNN (face detection) + DBSCAN (clustering)

## 🚀 Quick Start

### 🐳 Docker Deployment (One-Click Setup)

Use Docker to deploy the entire system with one command, no manual dependency installation required.

#### Method 1: Docker Compose (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/MiniMax-OpenPlatform/minimax_dubbing.git
cd minimax_dubbing

# 2. Create data directories
mkdir -p data/media data/db data/logs

# 3. Build and start containers
docker-compose up -d --build

# 4. View logs
docker-compose logs -f
```

#### Method 2: Docker Command

```bash
# 1. Build image
docker build -t minimax_dubbing:latest .

# 2. Run container
docker run -d \
  --name minimax_dubbing \
  -p 5173:5173 \
  -v $(pwd)/data/media:/app/media \
  -v $(pwd)/data/db:/app \
  -v $(pwd)/data/logs:/app/logs \
  --restart unless-stopped \
  minimax_dubbing:latest

# 3. View container logs
docker logs -f minimax_dubbing
```

#### Access System

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5172/api/
- **Admin Panel**: http://localhost:5172/admin/
- **Default Admin**: Username `admin`, Password `admin123`

> 💡 **Tip**: Change the admin password after first login

#### Container Management

```bash
# Stop container
docker-compose down
# or
docker stop minimax_dubbing

# Restart container
docker-compose restart
# or
docker restart minimax_dubbing

# Check container status
docker-compose ps
# or
docker ps
```

## 📖 Usage

### Basic Workflow

1. **Create Project**: Upload SRT file or create empty project
2. **Vocal Separation**: Separate vocals from background music
3. **Speaker Recognition**: AI automatically detects and assigns speakers
4. **Configure Voices**: Set up speaker-to-voice mappings in project settings
5. **Batch Translate**: Translate all segments using AI
6. **Generate TTS**: Create audio for translated text with timestamp alignment
7. **Concatenate Audio**: Merge segment audio into complete track
8. **Synthesize Video**: Generate final video with translated audio

### Key Features Guide

#### Auto Speaker Recognition
- **Face Detection & Clustering**: Uses FaceNet and DBSCAN to identify unique faces
- **VLM Speaker Profiling**: Qwen-VL analyzes faces and generates speaker profiles
- **LLM Subtitle Assignment**: Large language model assigns subtitles to speakers
- **Auto Voice Mapping**: Automatically creates voice mappings based on gender/role
- **Result Review**: View speaker profiles with images and detailed analysis

#### Batch Operations
- **Translation**: Bulk translate all segments with progress tracking
- **TTS**: Generate audio for all translated segments
- **Real-time Monitoring**: Live progress updates with detailed status

#### Audio Management
- **Concatenation**: Merge segment audio into complete track
- **Preview**: Integrated media player with waveform visualization
- **Export**: Download final audio files

## ⚙️ Configuration

### API Key Setup

After logging in, configure API keys in the "User Settings" page:

- **MiniMax API**: For translation and TTS
- **Alibaba Cloud NLS**: For ASR speech recognition (optional)

> 💡 Register at [MiniMax Open Platform](https://platform.minimaxi.com/) to get API credentials

### Admin Configuration

Access http://localhost:5172/admin/ for system configuration:

- **Data Cleanup Policy**: Configure automatic cleanup of inactive projects/users (disabled by default)
- **Concurrency Parameters**: Adjust API concurrent request limits
- **Task Monitoring**: View background task execution status

## 🔧 FAQ

### Q: How to access the admin panel?

**A**: Visit http://localhost:5172/admin/ and login with default credentials `admin` / `admin123`. Change password after first login.

### Q: Batch TTS fails?

**A**: Ensure:
- All segments have translations
- Voice mapping is configured in project settings
- MiniMax API key is configured in user settings

### Q: ASR recognition is inaccurate?

**A**: Suggestions:
- Ensure good vocal separation quality
- Check project source language setting is correct
- Manually edit recognition results

### Q: How to adjust TTS speech rate?

**A**: System automatically adjusts speech rate based on original subtitle duration. You can set max speed limit in project config (default 1.3x).

### Q: How to adjust volume during video synthesis?

**A**: When clicking "Synthesize Video", you can set:
- Translated audio volume: default 1.0 (100%)
- Background music volume: default 0.3 (30%)

### Q: Will data be automatically cleaned up?

**A**: System supports automatic cleanup, but it's **disabled by default**. You can enable and configure cleanup policy in admin "System Config".

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

## 📞 Support & Community

### 💬 Join WeChat Technical Discussion Group

Scan the QR code to join our WeChat technical discussion group and connect with developers and users:

<div align="center">
  <img src="./20251023-162139.jpg" alt="WeChat Technical Group" width="300"/>
  <p><i>Scan to join WeChat group for AI dubbing technology discussions</i></p>
</div>

### Other Support Channels

- Create an issue in the GitHub repository
- Check the project documentation
- Review API examples in `/api_example`

---

**Built with ❤️ using Vue 3, Django, and AI-powered technologies**
