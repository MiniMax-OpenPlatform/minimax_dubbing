# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# minimax_translation

A Vue 3 + Django translation management system with inline editing capabilities and AI-powered features for video/audio translation.

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
python manage.py migrate
python manage.py makemigrations

# System initialization
python manage.py init_system                    # 完整系统初始化
python manage.py init_admin                     # 仅创建管理员账号
python manage.py init_admin --force             # 强制重新创建管理员

# Development server
python manage.py runserver 0.0.0.0:5172

# Testing
python manage.py test
python manage.py test app_name  # Test specific app
python manage.py test app_name.tests.TestClassName  # Test specific class

# Database shell
python manage.py shell
python manage.py dbshell
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
- **AI Integration**: MiniMax API for translation and TTS

### Application Structure
```
/
├── backend/                    # Django settings and core configuration
├── authentication/             # Custom user auth with API key system
├── projects/                   # Project management (main entity)
├── segments/                   # Translation segments with timestamps
├── services/                   # Business logic and AI integrations
│   ├── algorithms/             # Timestamp alignment algorithms
│   ├── business/               # Core business services
│   ├── clients/                # External API clients (MiniMax)
│   └── parsers/                # SRT/subtitle file parsers
├── system_monitor/             # Background task monitoring
├── logs/                       # Centralized logging system
├── voices/                     # Voice management for TTS
├── voice_cloning/              # Voice cloning features
└── frontend/src/
    ├── components/
    │   ├── editor/             # Inline editing components
    │   ├── audio/              # Audio playback and visualization
    │   ├── project/            # Project management UI
    │   └── voice/              # Voice/speaker management
    ├── composables/            # Vue 3 composition functions
    │   ├── useInlineEditor.ts  # Core editing logic with debounced saves
    │   ├── useSegmentSelection.ts  # Multi-select operations
    │   ├── useSegmentValidation.ts # Real-time validation
    │   └── useSegmentBatch.ts  # Batch operations (translate/TTS)
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

### Translation Workflow
1. **Project Creation**: Upload SRT file or create empty project
2. **Speaker Configuration**: Map speakers to voice models
3. **Auto Speaker Assignment**: LLM-based speaker detection
4. **Batch Translation**: AI-powered bulk translation with progress tracking
5. **TTS Generation**: Convert translated text to speech
6. **Audio Concatenation**: Merge segment audio into complete tracks

### Key Business Logic
- **Timestamp Alignment**: Smart timestamp optimization for natural speech flow
- **Debounced Saves**: 800ms auto-save prevents excessive API calls
- **Progress Monitoring**: Real-time batch operation tracking
- **Voice Mapping**: Different TTS voices per speaker
- **Segment Validation**: Real-time field validation with error feedback

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
MINIMAX_API_KEY=your-api-key
MINIMAX_GROUP_ID=your-group-id
```

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
- `system_monitor/tests.py`
- `voices/tests.py`

### Frontend Testing
```bash
cd frontend
npm run test  # If test scripts are configured
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

1. **Never change frontend port from 5173** - hardcoded in configurations
2. **Always run both servers** - frontend depends on backend API
3. **Use existing authentication patterns** - API key via headers
4. **Follow existing component structure** - especially in `frontend/src/components/`
5. **Maintain timestamp precision** - critical for audio synchronization
6. **Respect debounce patterns** - prevent API rate limiting
7. **Test batch operations thoroughly** - they involve external AI APIs

## 🔐 Security Considerations

- API keys stored in Django settings (development only)
- CORS configured for development (allow all origins when DEBUG=True)
- Custom authentication middleware for API access
- No sensitive data in frontend code
- All external API calls go through backend proxy

This codebase implements a sophisticated translation management system with real-time editing, AI-powered batch operations, and comprehensive audio processing capabilities.