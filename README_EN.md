# MiniMax Dubbing - AI-Powered Dubbing System

English | [简体中文](./README.md)

> 🎙️ AI-Powered Dubbing System Based on Vue 3 + Django

A professional video dubbing and translation platform integrated with MiniMax AI API, supporting batch translation, AI voice synthesis, and intelligent dubbing.

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

### Project Structure
```
minimax_dubbing/
├── backend/                    # Django configuration and core settings
├── projects/                   # Project management app
├── segments/                   # Segment management app
├── authentication/             # Authentication system
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
# 1. Clone repository
git clone https://github.com/MiniMax-OpenPlatform/minimax_dubbing.git
cd minimax_dubbing

# 2. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 3. Initialize database and admin account
python3 manage.py migrate
python3 manage.py init_system
```

### 🚀 Start Services

#### Method 1: Two Terminal Windows (Recommended)

**Terminal 1 - Start Backend:**
```bash
cd minimax_dubbing
python3 manage.py runserver 0.0.0.0:5172
```

**Terminal 2 - Start Frontend:**
```bash
cd minimax_dubbing/frontend
npm run dev
```

#### Method 2: Single Terminal (Background Mode)

```bash
cd minimax_dubbing

# 1. Start backend in background
nohup python3 manage.py runserver 0.0.0.0:5172 > backend.log 2>&1 &

# 2. Start frontend
cd frontend && npm run dev
```

**Access Points 🎉**
- **Frontend**: http://localhost:5173/ (local) or http://YOUR_IP:5173/ (external)
- **Backend API**: http://localhost:5172/api/ (local) or http://YOUR_IP:5172/api/ (external)
- **Admin Panel**: http://localhost:5172/admin/

> ⚠️ **Important**: Both services must run simultaneously! Frontend on port 5173, backend on port 5172.

### 📋 Prerequisites
- Python 3.10+
- Node.js 16+
- FFmpeg

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
ALLOWED_HOSTS=localhost,127.0.0.1
```

### MiniMax API Setup
Register your account at [MiniMax Open Platform](https://platform.minimaxi.com/) to get your API credentials.

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
- Check the documentation
- Review API examples in `/api_example`

---

**Built with ❤️ using Vue 3, Django, and AI-powered technologies**
