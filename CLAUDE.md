# minimax_translation

A Vue 3 + Django translation management system with inline editing capabilities.

## 🚀 项目启动指南

### ⚡ 快速启动 (2分钟)

```bash
# 1. 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. 初始化数据库
python manage.py migrate

# 3. 启动服务 (两个终端)
python manage.py runserver 0.0.0.0:5172
cd frontend && npm run dev
```

**访问地址**:
- 前端: `http://localhost:5173/` (本地) 或 `http://YOUR_IP:5173/` (外部)
- 后端: `http://localhost:5172/` (本地) 或 `http://YOUR_IP:5172/` (外部)

> 💡 外部访问：将 YOUR_IP 替换为实际IP地址

### 环境要求
- Python 3.10+
- Node.js 16+
- npm 或 yarn

### 详细启动步骤

<details>
<summary>展开查看详细步骤</summary>

#### 1. 启动后端 Django 服务器

```bash
# 在项目根目录
cd /home/Devin/minimax_translation

# 启动Django开发服务器
python3 manage.py runserver 0.0.0.0:5172
```

**后端地址**: `http://localhost:5172/` (本地) 或 `http://YOUR_IP:5172/` (外部)

#### 2. 启动前端 Vue 应用

```bash
# 在新的终端窗口
cd /home/Devin/minimax_translation/frontend

# 启动前端开发服务器
npm run dev
```

**前端地址**: `http://localhost:5173/` (本地) 或 `http://YOUR_IP:5173/` (外部)

</details>

### 3. 查看实时日志

Django服务器的实时日志会显示在运行后端的终端中，包括：
- API请求详情
- 用户认证状态
- 数据库操作
- 错误信息

## 🏗️ 项目架构

### 技术栈
- **前端**: Vue 3 + TypeScript + Element Plus + Vite
- **后端**: Django 5.2.6 + Django REST Framework
- **数据库**: SQLite (开发环境)

### 前端架构
```
frontend/src/
├── components/
│   ├── editor/              # 编辑器组件
│   │   ├── InlineEditTable.vue      # 行内编辑表格
│   │   ├── SegmentInlineEditor.vue  # 段落编辑器容器
│   │   └── EditorToolbar.vue        # 编辑工具栏
│   ├── audio/               # 音频组件
│   ├── project/             # 项目组件
│   └── ...
├── composables/             # Vue 3 组合式函数
│   ├── useInlineEditor.ts   # 主编辑逻辑
│   ├── useSegmentSelection.ts  # 选择管理
│   ├── useSegmentValidation.ts # 验证系统
│   └── useSegmentBatch.ts   # 批量操作
└── utils/                   # 工具函数
```

### 后端架构
```
项目根目录/
├── projects/                # 项目管理应用
├── segments/                # 段落管理应用
├── authentication/          # 认证系统
├── logs/                    # 日志系统
└── backend/                 # Django设置
```

## ✨ 核心功能

### 前端编辑器 (已优化)
- ✅ **行内编辑**: 直接在表格中编辑，无需弹窗
- ✅ **防抖自动保存**: 800ms延迟自动保存
- ✅ **实时验证**: 字段验证和错误提示
- ✅ **批量操作**: 翻译、TTS、属性更新
- ✅ **进度监控**: 批量操作进度显示
- ✅ **键盘快捷键**: Ctrl+Enter保存等

### API 端点
- `/api/projects/` - 项目管理
- `/api/projects/{id}/segments/` - 段落管理
- `/api/auth/test-auth/` - 认证测试

## 🔧 开发规范

### Vue 3 组合式API
- 使用 TypeScript 进行类型安全
- 组件职责单一，避免巨石文件
- 使用 composables 抽离业务逻辑

### Django 开发
- RESTful API 设计
- 认证基于 API Key
- CORS 配置支持前端跨域

## 📝 配置信息

- **前端端口**: 5173 (固定)
- **后端端口**: 5172 (固定)
- **API Base URL**: `http://10.11.17.19:5172/api/`
- **CORS**: 已配置允许前端域名
- 前端固定使用5173端口，不要改变