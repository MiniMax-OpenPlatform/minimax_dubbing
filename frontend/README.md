# MiniMax Translation Frontend

Vue 3 + TypeScript + Element Plus frontend for the MiniMax Translation system.

## 🚀 Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Type-safe JavaScript
- **Element Plus** - Vue 3 UI library
- **Vite** - Fast build tool and dev server
- **Pinia** - State management
- **Axios** - HTTP client

## 📦 Dependencies

### Core Dependencies
- `vue` - Vue 3 framework
- `element-plus` - UI component library
- `@element-plus/icons-vue` - Icon components
- `axios` - HTTP requests
- `pinia` - State management

### Development Dependencies
- `@vitejs/plugin-vue` - Vue plugin for Vite
- `typescript` - TypeScript compiler
- `vue-tsc` - TypeScript compiler for Vue
- `vite` - Build tool

## 🏗️ Project Structure

```
src/
├── components/
│   ├── audio/              # Audio player components
│   ├── editor/             # Text editor components
│   ├── project/            # Project management components
│   └── common/             # Shared components
├── composables/            # Vue 3 composition functions
│   ├── useInlineEditor.ts  # Inline editing logic
│   ├── useBatchProgress.ts # Batch operation progress
│   ├── useAudioOperations.ts # Audio handling
│   └── useProjectData.ts   # Project data management
├── utils/
│   ├── api.ts              # API client
│   ├── auth.ts             # Authentication
│   └── logger.ts           # Logging utilities
├── stores/                 # Pinia stores
└── types/                  # TypeScript type definitions
```

## 🚀 Development

### Prerequisites
- Node.js 16+
- npm or yarn

### Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development Server
The development server runs on `http://localhost:5173/` (本地访问) 或 `http://YOUR_IP:5173/` (外部访问) and connects to the Django backend at `http://localhost:5172/`.

> 💡 外部访问时请将 YOUR_IP 替换为实际IP地址

## 🎯 Key Features

### Vue 3 Composition API
- Modern composition-based architecture
- TypeScript integration for type safety
- Reactive state management with Pinia

### Component Architecture
- **Modular Design**: Reusable, single-responsibility components
- **Type Safety**: Full TypeScript integration
- **Responsive**: Mobile-friendly design

### Real-time Features
- **Live Progress**: Real-time batch operation monitoring
- **Auto-save**: Automatic saving with debouncing
- **Instant Updates**: Reactive UI updates

## 🔧 Configuration

### API Configuration
The API base URL is configured in `src/utils/api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:5172/api/'
```

### Build Configuration
Vite configuration is in `vite.config.ts`:
```typescript
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173
  }
})
```

## 📱 Components

### Core Components
- **ProjectList**: Project management interface
- **ProjectDetail**: Individual project view
- **InlineEditTable**: Editable data table
- **MediaPreview**: Audio/video player
- **BatchProgressBar**: Progress monitoring

### Composables
- **useInlineEditor**: Manages inline editing state
- **useBatchProgress**: Tracks batch operation progress
- **useAudioOperations**: Handles audio playback and operations
- **useProjectData**: Manages project data fetching

## 🎨 Styling

### Element Plus Theme
- Consistent design system
- Built-in accessibility features
- Responsive grid system

### Custom Styles
- Component-scoped CSS
- CSS variables for theming
- Mobile-responsive design

## 🚀 Production Build

```bash
# Build for production
npm run build

# Analyze bundle
npm run build -- --analyze
```

The build outputs to `dist/` directory with optimized assets.

## 🧪 Development Guidelines

### Code Style
- Use Composition API over Options API
- Prefer `<script setup>` syntax
- Use TypeScript for type safety
- Follow Vue 3 best practices

### Component Guidelines
- Single responsibility principle
- Props and emits with TypeScript
- Reactive refs over reactive objects
- Use composables for reusable logic

### State Management
- Use Pinia for global state
- Local component state for UI state
- Composables for shared logic

## 🔍 Debugging

### Vue DevTools
Install Vue DevTools browser extension for debugging:
- Component inspection
- State monitoring
- Performance profiling

### Console Logging
Structured logging with custom logger:
```typescript
import { logger } from '@/utils/logger'
logger.info('Operation completed', { data })
```

## 📚 Learn More

- [Vue 3 Documentation](https://vuejs.org/)
- [Element Plus Documentation](https://element-plus.org/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Vite Documentation](https://vitejs.dev/)

---

**Part of the MiniMax Translation System**