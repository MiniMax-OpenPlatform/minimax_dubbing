# MiniMax Dubbing - AI智能配音系统

[English](./README_EN.md) | 简体中文

> 🎙️ AI智能配音翻译

本方案试图用AI完成说话人自动识别，时间戳自动对齐，自动翻译优化等，提升视频翻译的效率。

## 🌐 在线体验

**立即体验:** [https://solution.minimaxi.com/dubbing/](https://solution.minimaxi.com/dubbing/)

无需部署，在线试用完整功能！

![Python](https://img.shields.io/badge/Python-3.10.12-blue)
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
- **AI集成**: MiniMax API - 翻译和TTS
- **计算机视觉**: FaceNet + MTCNN (人脸检测) + DBSCAN (聚类)

## 🚀 快速开始

### 🐳 Docker部署（一键启动）

使用Docker可以一键部署整个系统，无需手动安装依赖，适合生产环境和快速体验。

#### 方式1：使用Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/MiniMax-OpenPlatform/minimax_dubbing.git
cd minimax_dubbing

# 2. 创建数据目录
mkdir -p data/media data/db data/logs

# 3. 构建并启动容器
docker-compose up -d --build

# 4. 查看日志
docker-compose logs -f
```

#### 方式2：使用Docker命令

```bash
# 1. 构建镜像
docker build -t minimax_dubbing:latest .

# 2. 运行容器
docker run -d \
  --name minimax_dubbing \
  -p 5173:5173 \
  -v $(pwd)/data/media:/app/media \
  -v $(pwd)/data/db:/app \
  -v $(pwd)/data/logs:/app/logs \
  --restart unless-stopped \
  minimax_dubbing:latest

# 3. 查看容器日志
docker logs -f minimax_dubbing
```

#### 访问系统

- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:5172/api/
- **管理后台**: http://localhost:5172/admin/
- **默认管理员**: 用户名 `admin`，密码 `admin123`

> 💡 **提示**: 首次登录后请及时修改管理员密码

#### 容器管理

```bash
# 停止容器
docker-compose down
# 或
docker stop minimax_dubbing

# 重启容器
docker-compose restart
# 或
docker restart minimax_dubbing

# 查看容器状态
docker-compose ps
# 或
docker ps
```

## 📖 使用说明

### 基本工作流程

1. **创建项目**: 上传视频文件和SRT字幕（或使用ASR自动生成字幕）
2. **人声分离**: 分离人声和背景音乐
3. **说话人识别**: AI自动检测人脸、命名说话人并分配对话
4. **配置音色**: 查看并调整说话人音色映射
5. **批量翻译**: AI批量翻译所有段落
6. **生成TTS**: 为翻译文本生成语音，自动对齐时间戳
7. **拼接音频**: 合并段落音频为完整音轨
8. **合成视频**: 生成带翻译音频的最终视频

### 关键功能

#### 智能说话人识别
- **人脸检测与聚类**：使用FaceNet和DBSCAN识别视频中的独特人脸
- **VLM智能命名**：Qwen-VL分析人脸图像和对话生成说话人档案（姓名、角色、性别、外貌、性格）
- **LLM字幕分配**：使用大语言模型根据上下文将每句字幕分配给正确的说话人
- **自动音色映射**：根据性别和角色自动创建说话人与音色的映射
- **结果审核**：查看说话人档案、代表图片和详细分析

#### 批量操作
- **批量翻译**：一键翻译所有段落，实时进度追踪
- **批量TTS**：为所有翻译文本生成语音
- **实时监控**：查看详细的进度状态和错误信息

#### 音频管理
- **音频拼接**：将段落音频合并为完整音轨
- **预览播放**：集成媒体播放器和波形可视化
- **导出下载**：下载最终音频和视频文件

## ⚙️ 配置说明

### API密钥配置

登录系统后，在"账户设置"页面配置以下API密钥：

- **MiniMax API**: 用于翻译和TTS语音合成
- **阿里云NLS**: 用于ASR语音识别（可选）

> 💡 在 [MiniMax开放平台](https://platform.minimaxi.com/) 注册获取API凭证

### 管理后台配置

访问 http://localhost:5172/admin/ 进行系统配置：

- **数据清理策略**：配置自动清理不活跃项目和用户的策略（默认关闭）
- **并发参数**：调整API并发请求数
- **任务监控**：查看后台任务执行状态

## 🔧 常见问题

### Q: 如何访问管理后台？

**A**: 访问 http://localhost:5172/admin/，使用默认账号 `admin` / `admin123` 登录。首次登录后请及时修改密码。

### Q: 批量TTS失败怎么办？

**A**: 确保已完成以下步骤：
- 所有段落都有译文
- 已在"项目配置"中配置音色映射
- 在"账户设置"中配置了正确的MiniMax API密钥

### Q: ASR识别不准确？

**A**: 建议：
- 确保人声分离质量良好
- 检查项目源语言设置是否正确
- 可以手动编辑识别结果

### Q: 如何调整TTS语速？

**A**: 系统会自动根据原字幕时长调整语速。可以在项目配置中设置最大语速限制（默认1.3倍）。

### Q: 视频合成时音量如何调整？

**A**: 点击"合成视频"时可设置：
- 翻译音频音量：默认1.0（100%）
- 背景音音量：默认0.3（30%）

### Q: 数据会被自动清理吗？

**A**: 系统支持自动清理功能，但**默认关闭**。可在管理后台的"系统配置"中启用和配置清理策略。

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📝 开源协议

本项目采用 MIT 协议开源 - 详见 LICENSE 文件

## 🙏 致谢

- **MiniMax API** - AI翻译和TTS能力
- **Vue 3** 和 **Element Plus** - 现代化前端框架
- **Django REST Framework** - 强大的后端API框架
- **FFmpeg** - 音视频处理能力

## 📞 技术支持与交流

### 💬 加入微信技术交流群

欢迎扫码加入我们的微信技术交流群，共同探索视频翻译的技术边界：

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
