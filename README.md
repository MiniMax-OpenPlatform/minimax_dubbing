# MiniMax Translation

A Vue 3 + Django translation management system with inline editing capabilities and AI-powered features.

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
python manage.py migrate

# 4. Start both servers (in separate terminals)
python manage.py runserver 0.0.0.0:5172 &
cd frontend && npm run dev
```

**That's it! 🎉**
- Frontend: http://localhost:5173/ (本地访问) 或 http://YOUR_IP:5173/ (外部访问)
- Backend: http://localhost:5172/api/ (本地访问) 或 http://YOUR_IP:5172/api/ (外部访问)

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
python manage.py migrate

# Create admin user (optional)
python manage.py createsuperuser
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

#### 5. Start Development Servers
```bash
# Terminal 1: Backend
python manage.py runserver 0.0.0.0:5172

# Terminal 2: Frontend
cd frontend && npm run dev
```

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
python manage.py test
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
python manage.py collectstatic

# Run with gunicorn
gunicorn backend.wsgi:application
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