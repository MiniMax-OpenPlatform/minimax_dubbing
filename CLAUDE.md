# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# minimax_dubbing

A Vue 3 + Django AI-powered video dubbing system with multi-modal speaker recognition, automatic subtitle generation (ASR), voice separation, translation, and text-to-speech synthesis.

## 🚀 Development Commands

### ⚡ Quick Setup (一键初始化)
```bash
# 快速初始化整个系统
./init.sh

# 或者手动初始化
python manage.py init_system

# 或者更细粒度的控制
python manage.py init_admin --username admin --password admin123
```

### Backend (Django)
```bash
# Install dependencies
pip install -r requirements.txt

# Database operations
python manage.py migrate                        # Apply all migrations (REQUIRED!)
python manage.py makemigrations                 # Create new migrations
python manage.py showmigrations                 # Show migration status

# System initialization
python manage.py init_system                    # Complete system init (creates admin)
python manage.py init_admin                     # Create admin user only
python manage.py init_admin --force             # Force recreate admin user

# Fix incomplete user registrations (missing UserConfig)
python fix_incomplete_users.py

# Development server
python manage.py runserver 0.0.0.0:5172

# Testing
python manage.py test
python manage.py test app_name                  # Test specific app
python manage.py test app_name.tests.TestClassName  # Test specific class
python manage.py test --verbosity=2             # Verbose test output

# Database shell and inspection
python manage.py shell                          # Django shell
python manage.py dbshell                        # Database SQL shell

# Check configuration validity
python check_config.py
```

### Frontend (Vue 3 + Vite)
```bash
# Install dependencies
cd frontend && npm install

# Development server
npm run dev  # Runs on port 5173

# Build for production
npm run build

# Type checking
vue-tsc -b

# Preview production build
npm run preview
```

### Required Dual Server Setup
**Critical**: Both backend (port 5172) and frontend (port 5173) must run simultaneously for the application to work.

```bash
# Terminal 1 - Backend
python manage.py runserver 0.0.0.0:5172

# Terminal 2 - Frontend
cd frontend && npm run dev
```

## 🏗️ Architecture Overview

### Technology Stack
- **Frontend**: Vue 3 + TypeScript + Element Plus + Vite + Pinia
- **Backend**: Django 5.2.6 + Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI Integration**:
  - MiniMax API - Translation and TTS
  - Qwen-VL (DashScope) - Visual-language model for speaker naming
  - Qwen LLM (DashScope) - Speaker-subtitle assignment
  - Alibaba Cloud NLS - ASR (Automatic Speech Recognition)
- **Computer Vision**: FaceNet + MTCNN (face detection) + DBSCAN (clustering)
- **Audio Processing**: Demucs (vocal separation), PyDub, librosa, FFmpeg

### Application Structure
```
/
├── backend/                    # Django settings and core configuration
├── authentication/             # Custom user auth with API key system
│   ├── management/commands/    # init_system, init_admin commands
│   └── models.py               # User and UserConfig models
├── projects/                   # Project management (main entity)
├── segments/                   # Translation segments with timestamps
├── speakers/                   # Speaker recognition and diarization (NEW)
│   └── models.py               # SpeakerRecognitionTask, Speaker models
├── services/                   # Business logic and AI integrations
│   ├── algorithms/             # Timestamp alignment algorithms
│   ├── business/               # Core business services
│   ├── clients/                # External API clients (MiniMax)
│   ├── parsers/                # SRT/subtitle file parsers
│   ├── asr/                    # ASR (Automatic Speech Recognition) (NEW)
│   ├── audio_separator/        # Demucs vocal separation (NEW)
│   └── speaker_diarization/    # Multi-modal speaker pipeline (NEW)
│       ├── face_detector.py    # FaceNet + MTCNN face detection
│       ├── clusterer.py        # DBSCAN face clustering
│       ├── vlm_naming.py       # Qwen-VL speaker profile generation
│       ├── llm_assignment.py   # Qwen LLM subtitle-speaker assignment
│       └── pipeline.py         # End-to-end orchestration
├── system_monitor/             # Background task monitoring
├── logs/                       # Centralized logging system
├── voices/                     # Voice management for TTS
├── voice_cloning/              # Voice cloning features
└── frontend/src/
    ├── components/
    │   ├── editor/             # Inline editing components
    │   ├── audio/              # Audio playback and visualization
    │   ├── project/            # Project management UI
    │   ├── voice/              # Voice/speaker management
    │   └── speakers/           # Speaker recognition UI (NEW)
    ├── composables/            # Vue 3 composition functions
    │   ├── useInlineEditor.ts  # Core editing logic with debounced saves
    │   ├── useSegmentSelection.ts  # Multi-select operations
    │   ├── useSegmentValidation.ts # Real-time validation
    │   ├── useSegmentBatch.ts  # Batch operations (translate/TTS)
    │   └── useBatchProgress.ts # Real-time progress tracking (NEW)
    ├── stores/                 # Pinia state management
    └── utils/                  # Shared utilities
```

### Key Design Patterns

#### Backend Architecture
- **Django Apps**: Modular design with separate apps for authentication, projects, segments, services
- **Custom Authentication**: API key-based auth via `X-API-KEY` header
- **Service Layer**: Business logic separated into `services/` with algorithm and client abstractions
- **Nested REST Routes**: Projects contain segments via DRF nested routers

#### Frontend Architecture
- **Composition API**: All Vue 3 components use `<script setup>` with TypeScript
- **Composables Pattern**: Business logic extracted into reusable composables
- **Inline Editing**: Direct table editing with 800ms debounced auto-save
- **Batch Operations**: Progress-tracked bulk operations for translation and TTS

## 🔧 Core Features & Workflows

### Complete Dubbing Workflow
1. **Video Upload**: Upload video file to project
2. **Vocal Separation**: Extract vocal track using Demucs (removes background music)
3. **ASR Subtitle Generation**: Auto-generate SRT subtitles using Alibaba Cloud NLS
4. **Multi-Modal Speaker Recognition**:
   - Face detection and clustering (FaceNet + DBSCAN)
   - Speaker profiling via VLM (Qwen-VL generates name, role, gender, appearance)
   - Subtitle assignment via LLM (Qwen assigns each line to correct speaker)
5. **Voice Mapping**: Assign TTS voices to each speaker based on gender/role
6. **Batch Translation**: Translate all segments with vocabulary optimization
7. **TTS Generation**: Convert translated text to speech with timestamp alignment
8. **Audio Concatenation**: Merge segment audio into complete track
9. **Video Synthesis**: Combine translated audio with original video

### Key Business Logic
- **Multi-Modal Speaker Diarization**: 3-stage pipeline (face detection → VLM naming → LLM assignment)
- **Model Caching**: Demucs and FaceNet models cached locally (~420MB total) after first download
- **ASR Integration**: Alibaba Cloud NLS for automatic subtitle generation from audio
- **Vocal Separation**: Demucs htdemucs model separates vocals from background music
- **Timestamp Alignment**: Smart timestamp optimization for natural speech flow
- **Debounced Saves**: 800ms auto-save prevents excessive API calls
- **Progress Monitoring**: Real-time batch operation tracking via WebSocket-like polling
- **Voice Mapping**: Different TTS voices per speaker with gender-based defaults
- **Segment Validation**: Real-time field validation with error feedback
- **Video Synthesis**: FFmpeg-based video/audio merging with subtitle overlay

## 📝 Configuration & Environment

### Critical Settings
- **Frontend Port**: 5173 (fixed, do not change)
- **Backend Port**: 5172 (fixed, do not change)
- **CORS Configuration**: Allows all origins in DEBUG mode
- **Custom User Model**: `authentication.User` with group-based access
- **API Authentication**: `GroupIDKeyAuthentication` class
- **Time Zone**: Asia/Shanghai

### Environment Variables
```env
DEBUG=True
SECRET_KEY=django-insecure-key-for-dev
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# AI API Keys (configured per-user in UserConfig model)
MINIMAX_API_KEY=your-minimax-key
MINIMAX_GROUP_ID=your-minimax-group-id
DASHSCOPE_API_KEY=your-dashscope-key  # For Qwen-VL and Qwen LLM
ALIYUN_ACCESS_KEY_ID=your-aliyun-key   # For NLS ASR
ALIYUN_ACCESS_KEY_SECRET=your-secret
ALIYUN_APP_KEY=your-app-key
```

**Note**: API keys are stored in `authentication.UserConfig` model (per-user), not in .env file. Users configure keys via frontend settings page.

### API Configuration
- **Base URL**: `http://localhost:5172/api/`
- **Authentication**: Header `X-API-KEY: your-key`
- **Pagination**: 20 items per page
- **CORS**: Full cross-origin support enabled

## 🧪 Testing Strategy

### Backend Testing
```bash
# Run all tests
python manage.py test

# Test specific apps
python manage.py test authentication
python manage.py test projects
python manage.py test segments
python manage.py test services

# Test with verbose output
python manage.py test --verbosity=2
```

### Test Files Location
- `authentication/tests.py`
- `projects/tests.py`
- `segments/tests.py`
- `services/tests.py`
- `speakers/tests.py`
- `system_monitor/tests.py`
- `voices/tests.py`

### Frontend Testing
```bash
cd frontend
npm run test  # If test scripts are configured
```

## 🔧 AI Model Management

### Model Download and Caching
AI models are automatically cached after first use to avoid repeated downloads:

```bash
# Pre-download all models (recommended for deployment)
python download_models.py

# Download specific models
python download_models.py --demucs     # Demucs vocal separation (~320MB)
python download_models.py --facenet    # FaceNet face recognition (~100MB)

# Check cached models
python download_models.py --check
```

### Cache Locations
- **Demucs & FaceNet**: `~/.cache/torch/hub/checkpoints/`
- **Qwen Models**: Managed by DashScope SDK (cloud-based)
- **NLS ASR**: Cloud-based, no local caching needed

### Deployment Tip
For multi-server deployment, cache models on one server then distribute:
```bash
# On source server
tar -czf models_cache.tar.gz ~/.cache/torch/

# On target servers
tar -xzf models_cache.tar.gz -C ~/
```

## 🔍 Development Guidelines

### Vue 3 Best Practices
- Use TypeScript for all components and composables
- Prefer `<script setup>` syntax with Composition API
- Extract business logic into composables for reusability
- Use Pinia for state management
- Follow Element Plus component patterns

### Django Best Practices
- RESTful API design with DRF
- Custom authentication via API keys
- Modular app structure
- Service layer pattern for business logic
- Comprehensive logging configuration

### File Editing Conventions
- **Vue Components**: Use `<script setup lang="ts">` with TypeScript
- **Django Models**: Follow existing field naming conventions
- **API Endpoints**: Use DRF ViewSets with proper serializers
- **Composables**: Export typed functions with clear interfaces

## 🚨 Important Notes

1. **Never change ports**: Frontend 5173, Backend 5172 - hardcoded in configurations
2. **Always run both servers** - frontend depends on backend API
3. **Database migrations required** - Run `python manage.py migrate` before first use (critical!)
4. **Model downloads** - First use of vocal separation or speaker recognition downloads ~420MB
5. **Use existing authentication patterns** - API key via headers (`X-API-KEY`)
6. **Follow existing component structure** - especially in `frontend/src/components/`
7. **Maintain timestamp precision** - critical for audio synchronization
8. **Respect debounce patterns** - 800ms auto-save prevents API rate limiting
9. **Test batch operations thoroughly** - they involve external AI APIs with costs
10. **API keys per-user** - Stored in UserConfig model, not environment variables
11. **FFmpeg required** - Must be installed for video synthesis and audio processing

## 🔐 Security Considerations

- **API Keys**: Stored per-user in UserConfig model (database), not in .env or settings.py
- **CORS**: Configured for development (allow all origins when DEBUG=True)
- **Authentication**: Custom `GroupIDKeyAuthentication` via `X-API-KEY` header
- **No sensitive data in frontend** - All API keys managed server-side
- **External API proxy** - All AI API calls (MiniMax, DashScope, NLS) go through backend

## 📊 Key API Endpoints

### Project Management
- `POST /api/projects/upload_srt/` - Upload SRT file
- `POST /api/projects/{id}/upload_video/` - Upload video file
- `GET /api/projects/{id}/segments/` - Get project segments

### Audio Processing
- `POST /api/projects/{id}/separate_vocals/` - Demucs vocal separation
- `POST /api/projects/{id}/concatenate_audio/` - Merge segment audio
- `POST /api/projects/{id}/synthesize_video/` - Final video synthesis

### ASR (Automatic Speech Recognition)
- `POST /api/projects/{id}/asr_recognize/` - Generate subtitles from audio
- `GET /api/projects/{id}/asr_recognize/` - Check ASR task status

### Speaker Recognition (Multi-Modal AI)
- `POST /api/speakers/tasks/` - Start speaker diarization task
- `GET /api/speakers/tasks/{task_id}/progress/` - Real-time progress polling
- `GET /api/speakers/tasks/{task_id}/` - Get recognition results
- `POST /api/projects/{id}/apply_speakers/` - Apply speaker assignments to segments

### Translation & TTS
- `POST /api/projects/{id}/batch_translate/` - Batch translate segments
- `POST /api/projects/{id}/batch_tts/` - Batch TTS generation
- `GET /api/projects/{id}/batch_translate/` - Check translation progress
- `GET /api/projects/{id}/batch_tts/` - Check TTS progress

## 🔧 Common Troubleshooting

### Problem: 400/500 Errors on User Registration or Saving Config
**Cause**: Missing database migrations for UserConfig fields
**Solution**:
```bash
# Pull latest code with migrations
git pull origin main

# Apply migrations (critical step!)
python manage.py migrate

# Verify all migrations applied
python manage.py showmigrations authentication

# If users exist without config
python fix_incomplete_users.py
```

### Problem: First Vocal Separation or Speaker Recognition Takes Forever
**Cause**: Downloading AI models (~420MB)
**Solution**:
```bash
# Pre-download models
python download_models.py

# Or copy from another server
tar -czf models_cache.tar.gz ~/.cache/torch/
# Transfer and extract on target server
```

### Problem: Frontend Can't Connect to Backend
**Check**:
1. Backend running on 5172: `ps aux | grep "runserver"`
2. Frontend running on 5173: `ps aux | grep "npm"`
3. CORS settings allow your IP
4. Check backend logs for errors

### Problem: ASR or Speaker Recognition Fails
**Cause**: Missing API keys in UserConfig
**Solution**: Configure keys via frontend Settings page or Django admin

---

This codebase implements a sophisticated AI-powered video dubbing system with multi-modal speaker recognition, automatic subtitle generation, vocal separation, translation optimization, and comprehensive audio/video processing capabilities.