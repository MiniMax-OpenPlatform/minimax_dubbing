<template>
  <div class="user-guide-container">
    <div class="guide-header">
      <h1>📖 MiniMax 翻译工具 - 使用说明</h1>
      <p class="subtitle">快速上手指南 - 从视频上传到翻译完成的完整工作流程</p>
    </div>

    <div class="guide-content">
      <!-- 快速开始 -->
      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><VideoCamera /></el-icon>
            <span>快速开始 - 完整工作流程</span>
          </div>
        </template>
        <div class="workflow-steps">
          <div class="workflow-step">
            <div class="step-number">1</div>
            <div class="step-content">
              <h4>上传视频和字幕</h4>
              <p><strong>方式一：上传视频 + SRT字幕文件</strong></p>
              <ul>
                <li>点击"项目管理" → "新建项目"</li>
                <li>选择源语言和目标语言</li>
                <li>上传原始视频文件（支持常见格式）</li>
                <li>上传SRT字幕文件（可选）</li>
              </ul>
              <p><strong>方式二：仅上传视频 + 使用ASR识别</strong></p>
              <ul>
                <li>上传视频后，点击"人声分离"提取人声</li>
                <li>点击"ASR识别"自动生成字幕</li>
                <li>系统自动识别语音并创建字幕段落</li>
              </ul>
            </div>
          </div>

          <div class="workflow-step">
            <div class="step-number">2</div>
            <div class="step-content">
              <h4>人声分离（必需）</h4>
              <ul>
                <li>点击工具栏"人声分离"按钮</li>
                <li>系统使用Demucs模型分离人声和背景音</li>
                <li>分离后得到：人声音频 + 背景音乐</li>
                <li>人声用于ASR识别，背景音用于后期合成</li>
              </ul>
            </div>
          </div>

          <div class="workflow-step">
            <div class="step-number">3</div>
            <div class="step-content">
              <h4>配置音色映射</h4>
              <ul>
                <li>点击"项目配置"设置不同说话人的音色</li>
                <li>为每个说话人（SPEAKER_00、SPEAKER_01等）选择合适的TTS音色</li>
                <li>可使用预设音色或自定义克隆音色</li>
              </ul>
            </div>
          </div>

          <div class="workflow-step">
            <div class="step-number">4</div>
            <div class="step-content">
              <h4>翻译字幕</h4>
              <p><strong>单条翻译：</strong></p>
              <ul>
                <li>直接在表格中双击译文列进行内联编辑</li>
                <li>或点击段落右侧"翻译"按钮单独翻译</li>
              </ul>
              <p><strong>批量翻译：</strong></p>
              <ul>
                <li>勾选需要翻译的段落（或不勾选=全部）</li>
                <li>点击工具栏"批量翻译"按钮</li>
                <li>系统使用MiniMax LLM自动翻译所有段落</li>
                <li>翻译过程中可查看实时进度</li>
              </ul>
            </div>
          </div>

          <div class="workflow-step">
            <div class="step-number">5</div>
            <div class="step-content">
              <h4>生成TTS语音</h4>
              <p><strong>单条TTS：</strong></p>
              <ul>
                <li>点击段落右侧"生成TTS"按钮</li>
              </ul>
              <p><strong>批量TTS：</strong></p>
              <ul>
                <li>勾选需要生成语音的段落</li>
                <li>点击工具栏"批量TTS"按钮</li>
                <li>系统根据音色映射为每个段落生成语音</li>
                <li>自动进行时间戳对齐和语速调整</li>
              </ul>
            </div>
          </div>

          <div class="workflow-step">
            <div class="step-number">6</div>
            <div class="step-content">
              <h4>拼接音频</h4>
              <ul>
                <li>所有段落TTS完成后，点击"拼接音频"</li>
                <li>系统将所有段落音频按时间轴合并</li>
                <li>生成完整的翻译音频文件</li>
                <li>可在预览区播放并查看波形图</li>
              </ul>
            </div>
          </div>

          <div class="workflow-step">
            <div class="step-number">7</div>
            <div class="step-content">
              <h4>合成最终视频</h4>
              <ul>
                <li>点击工具栏"合成视频"按钮</li>
                <li>系统自动完成以下步骤：</li>
                <li class="sub-step">① 混合翻译音频和背景音乐</li>
                <li class="sub-step">② 使用ffmpeg替换原视频的音轨</li>
                <li class="sub-step">③ 生成最终翻译视频</li>
                <li>在预览区可直接播放翻译视频</li>
              </ul>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 核心功能详解 -->
      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><Tools /></el-icon>
            <span>核心功能详解</span>
          </div>
        </template>

        <div class="feature-section">
          <h4>🎙️ ASR语音识别</h4>
          <ul>
            <li><strong>支持语言：</strong>中文、英语、日语、韩语、法语、德语、西班牙语等15+语言</li>
            <li><strong>自动语言检测：</strong>根据项目源语言配置自动选择识别语言</li>
            <li><strong>智能合并：</strong>自动合并过短的字幕片段，避免字幕过于离散</li>
            <li><strong>参数配置：</strong>可调整最小字幕时长(0.5s)和最大间隔(0.5s)</li>
          </ul>
        </div>

        <div class="feature-section">
          <h4>🎵 人声分离 (Demucs)</h4>
          <ul>
            <li><strong>四轨分离：</strong>人声、鼓、贝斯、其他乐器</li>
            <li><strong>高质量模型：</strong>使用htdemucs模型，分离效果优秀</li>
            <li><strong>智能降噪：</strong>自动应用降噪滤波器提升人声清晰度</li>
            <li><strong>背景保留：</strong>保留背景音乐用于后期合成</li>
          </ul>
        </div>

        <div class="feature-section">
          <h4>🗣️ TTS语音合成</h4>
          <ul>
            <li><strong>多音色支持：</strong>内置20+种预设音色，支持自定义克隆</li>
            <li><strong>智能对齐：</strong>自动调整语速匹配原字幕时长</li>
            <li><strong>情感控制：</strong>支持设置语音情感和语调</li>
            <li><strong>批量处理：</strong>支持批量生成并实时查看进度</li>
          </ul>
        </div>

        <div class="feature-section">
          <h4>✏️ 内联编辑</h4>
          <ul>
            <li><strong>即时编辑：</strong>双击单元格直接编辑原文、译文、说话人等</li>
            <li><strong>自动保存：</strong>800ms防抖自动保存，无需手动确认</li>
            <li><strong>实时验证：</strong>输入时实时检查格式和内容</li>
            <li><strong>快捷操作：</strong>支持Tab/Enter键快速切换单元格</li>
          </ul>
        </div>

        <div class="feature-section">
          <h4>🎬 视频合成</h4>
          <ul>
            <li><strong>音频混合：</strong>将翻译音频与背景音乐混合，可调节音量比例</li>
            <li><strong>音轨替换：</strong>使用ffmpeg替换原视频的音轨</li>
            <li><strong>格式支持：</strong>输出MP4格式，兼容性好</li>
            <li><strong>预览播放：</strong>合成后可直接在预览区播放</li>
          </ul>
        </div>
      </el-card>

      <!-- 界面功能说明 -->
      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><Monitor /></el-icon>
            <span>界面功能说明</span>
          </div>
        </template>

        <div class="ui-section">
          <h4>📋 字幕编辑表格</h4>
          <ul>
            <li><strong>序号：</strong>字幕段落编号</li>
            <li><strong>起止时间：</strong>字幕显示的时间范围（格式：HH:MM:SS,mmm）</li>
            <li><strong>原文：</strong>原始语言文本，支持内联编辑</li>
            <li><strong>译文：</strong>翻译后的文本，支持内联编辑</li>
            <li><strong>说话人：</strong>指定该段落的说话人（用于音色映射）</li>
            <li><strong>情感：</strong>TTS语音情感设置</li>
            <li><strong>操作：</strong>翻译、生成TTS、缩短、加长、删除等</li>
          </ul>
        </div>

        <div class="ui-section">
          <h4>🎮 工具栏功能</h4>
          <ul>
            <li><strong>上传视频：</strong>上传原始视频文件</li>
            <li><strong>上传字幕：</strong>上传SRT字幕文件</li>
            <li><strong>人声分离：</strong>分离人声和背景音</li>
            <li><strong>ASR识别：</strong>自动语音识别生成字幕</li>
            <li><strong>批量翻译：</strong>批量翻译选中或全部段落</li>
            <li><strong>批量TTS：</strong>批量生成语音</li>
            <li><strong>自动分配说话人：</strong>使用AI自动识别说话人</li>
            <li><strong>批量设置说话人：</strong>批量修改选中段落的说话人</li>
            <li><strong>拼接音频：</strong>合并所有段落音频</li>
            <li><strong>合成视频：</strong>生成最终翻译视频</li>
            <li><strong>导出字幕：</strong>导出SRT字幕文件</li>
          </ul>
        </div>

        <div class="ui-section">
          <h4>📺 预览区</h4>
          <ul>
            <li><strong>媒体切换：</strong>下拉菜单切换不同媒体（原始视频、翻译视频、各类音频）</li>
            <li><strong>视频播放：</strong>支持播放原始视频和翻译视频</li>
            <li><strong>音频播放：</strong>支持播放原始音频、翻译音频、背景音、混合音频</li>
            <li><strong>波形可视化：</strong>所有音频都显示波形图和播放进度</li>
            <li><strong>下载功能：</strong>点击下载按钮保存当前媒体文件</li>
          </ul>
        </div>
      </el-card>

      <!-- 音色管理 -->
      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><Microphone /></el-icon>
            <span>音色管理与克隆</span>
          </div>
        </template>

        <div class="voice-section">
          <h4>🎤 预设音色</h4>
          <ul>
            <li>系统内置20+种不同风格的音色</li>
            <li>包含男声、女声、不同年龄段和风格</li>
            <li>在"音色管理"页面可查看和试听所有预设音色</li>
          </ul>
        </div>

        <div class="voice-section">
          <h4>🎙️ 音色克隆</h4>
          <ul>
            <li>上传3-10分钟的纯净音频样本</li>
            <li>系统自动训练克隆模型</li>
            <li>克隆后的音色可用于TTS生成</li>
            <li>支持为不同项目使用不同的克隆音色</li>
          </ul>
        </div>

        <div class="voice-section">
          <h4>👥 音色映射</h4>
          <ul>
            <li>在项目配置中为每个说话人分配音色</li>
            <li>支持说话人：SPEAKER_00, SPEAKER_01, ...</li>
            <li>可以为不同角色使用不同音色</li>
            <li>批量TTS时自动根据说话人应用对应音色</li>
          </ul>
        </div>
      </el-card>

      <!-- 常见问题 -->
      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><QuestionFilled /></el-icon>
            <span>常见问题 FAQ</span>
          </div>
        </template>

        <div class="faq-item">
          <h4>Q: 批量TTS失败怎么办？</h4>
          <p>A: 确保已完成以下步骤：</p>
          <ul>
            <li>所有段落都有译文</li>
            <li>已配置音色映射</li>
            <li>检查MiniMax API配置是否正确</li>
            <li>查看系统监控确认错误信息</li>
          </ul>
        </div>

        <div class="faq-item">
          <h4>Q: 拼接音频提示"没有可拼接的音频"？</h4>
          <p>A: 需要先完成批量TTS，确保有段落生成了音频文件。</p>
        </div>

        <div class="faq-item">
          <h4>Q: 合成视频提示缺少文件？</h4>
          <p>A: 合成视频需要以下文件：</p>
          <ul>
            <li>翻译音频（批量TTS + 拼接音频）</li>
            <li>背景音（人声分离）</li>
            <li>原始视频</li>
          </ul>
        </div>

        <div class="faq-item">
          <h4>Q: ASR识别不准确？</h4>
          <p>A: 建议：</p>
          <ul>
            <li>确保人声分离质量良好</li>
            <li>检查项目源语言设置是否正确</li>
            <li>可以手动编辑识别结果</li>
          </ul>
        </div>

        <div class="faq-item">
          <h4>Q: 如何调整TTS语速？</h4>
          <p>A: 系统自动根据原字幕时长调整语速。可以在项目配置中设置最大语速限制（默认1.3倍）。</p>
        </div>

        <div class="faq-item">
          <h4>Q: 视频合成时音量如何调整？</h4>
          <p>A: 点击"合成视频"时可设置：</p>
          <ul>
            <li>翻译音频音量：默认1.0（100%）</li>
            <li>背景音音量：默认0.3（30%）</li>
          </ul>
        </div>
      </el-card>

      <!-- 技术规格 -->
      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><Setting /></el-icon>
            <span>技术规格</span>
          </div>
        </template>

        <div class="spec-section">
          <h4>支持的文件格式</h4>
          <ul>
            <li><strong>视频：</strong>MP4, AVI, MOV, MKV 等常见格式</li>
            <li><strong>音频：</strong>MP3, WAV, AAC, M4A 等</li>
            <li><strong>字幕：</strong>SRT格式</li>
          </ul>
        </div>

        <div class="spec-section">
          <h4>性能参数</h4>
          <ul>
            <li><strong>批量翻译速度：</strong>约1-2段/秒（取决于API响应）</li>
            <li><strong>批量TTS速度：</strong>约0.5-1段/秒（自动控制频率）</li>
            <li><strong>人声分离：</strong>约实时的0.1-0.2倍（取决于视频长度）</li>
            <li><strong>视频合成：</strong>约实时的0.3-0.5倍</li>
          </ul>
        </div>

        <div class="spec-section">
          <h4>系统要求</h4>
          <ul>
            <li><strong>后端：</strong>Python 3.8+, Django 5.2+</li>
            <li><strong>前端：</strong>现代浏览器（Chrome, Firefox, Edge, Safari）</li>
            <li><strong>依赖：</strong>ffmpeg（视频处理）, Demucs（人声分离）</li>
            <li><strong>API：</strong>MiniMax API（翻译和TTS）, 阿里云ASR（语音识别）</li>
          </ul>
        </div>
      </el-card>

      <!-- 快捷键 -->
      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><Pointer /></el-icon>
            <span>快捷操作</span>
          </div>
        </template>

        <div class="shortcut-section">
          <h4>表格编辑快捷键</h4>
          <ul>
            <li><strong>双击单元格：</strong>进入编辑模式</li>
            <li><strong>Tab：</strong>保存并移动到下一个可编辑单元格</li>
            <li><strong>Shift + Tab：</strong>保存并移动到上一个单元格</li>
            <li><strong>Enter：</strong>保存并移动到下一行相同列</li>
            <li><strong>Esc：</strong>取消编辑</li>
          </ul>
        </div>

        <div class="shortcut-section">
          <h4>批量操作</h4>
          <ul>
            <li><strong>勾选多行：</strong>点击表格左侧复选框</li>
            <li><strong>全选：</strong>点击表头复选框</li>
            <li><strong>不选择：</strong>批量操作默认应用到所有段落</li>
          </ul>
        </div>
      </el-card>

      <!-- 提示和建议 -->
      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><MagicStick /></el-icon>
            <span>最佳实践</span>
          </div>
        </template>

        <div class="tip-section">
          <h4>💡 提高翻译质量</h4>
          <ul>
            <li>人工检查并修正机器翻译的结果</li>
            <li>使用内联编辑快速调整不准确的翻译</li>
            <li>善用"缩短"和"加长"功能调整译文长度</li>
          </ul>
        </div>

        <div class="tip-section">
          <h4>💡 提高TTS效果</h4>
          <ul>
            <li>选择合适的音色匹配角色特征</li>
            <li>使用音色克隆获得更自然的效果</li>
            <li>适当调整情感参数增强表现力</li>
          </ul>
        </div>

        <div class="tip-section">
          <h4>💡 优化工作流程</h4>
          <ul>
            <li>先完成所有翻译，再进行批量TTS（避免重复生成）</li>
            <li>使用ASR识别可以省去手动制作字幕的时间</li>
            <li>人声分离质量直接影响后续所有步骤，确保质量</li>
            <li>定期查看系统监控了解任务进度</li>
          </ul>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { VideoCamera, Tools, Monitor, Microphone, QuestionFilled, Setting, Pointer, MagicStick } from '@element-plus/icons-vue'
</script>

<style scoped>
.user-guide-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.guide-header {
  text-align: center;
  margin-bottom: 40px;
  padding: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
}

.guide-header h1 {
  margin: 0 0 15px 0;
  font-size: 32px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  font-size: 16px;
  opacity: 0.95;
}

.guide-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.card-header .el-icon {
  font-size: 22px;
  color: #409eff;
}

/* 工作流程步骤 */
.workflow-steps {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.workflow-step {
  display: flex;
  gap: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.step-number {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #409eff;
  color: white;
  font-size: 20px;
  font-weight: 600;
  border-radius: 50%;
}

.step-content {
  flex: 1;
}

.step-content h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
}

.step-content p {
  margin: 8px 0;
  color: #606266;
}

.step-content ul {
  margin: 8px 0;
  padding-left: 20px;
}

.step-content li {
  margin: 6px 0;
  color: #606266;
  line-height: 1.6;
}

.step-content li.sub-step {
  margin-left: 20px;
  list-style-type: circle;
}

/* 功能详解 */
.feature-section {
  padding: 20px 0;
  border-bottom: 1px solid #ebeef5;
}

.feature-section:last-child {
  border-bottom: none;
}

.feature-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
}

.feature-section ul {
  margin: 0;
  padding-left: 20px;
}

.feature-section li {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
}

/* 界面说明 */
.ui-section {
  padding: 20px 0;
  border-bottom: 1px solid #ebeef5;
}

.ui-section:last-child {
  border-bottom: none;
}

.ui-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
}

.ui-section ul {
  margin: 0;
  padding-left: 20px;
}

.ui-section li {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
}

/* 音色管理 */
.voice-section {
  padding: 20px 0;
  border-bottom: 1px solid #ebeef5;
}

.voice-section:last-child {
  border-bottom: none;
}

.voice-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
}

.voice-section ul {
  margin: 0;
  padding-left: 20px;
}

.voice-section li {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
}

/* FAQ */
.faq-item {
  padding: 20px 0;
  border-bottom: 1px solid #ebeef5;
}

.faq-item:last-child {
  border-bottom: none;
}

.faq-item h4 {
  margin: 0 0 8px 0;
  color: #409eff;
  font-size: 15px;
}

.faq-item p {
  margin: 8px 0;
  color: #303133;
  font-weight: 500;
}

.faq-item ul {
  margin: 8px 0;
  padding-left: 20px;
}

.faq-item li {
  margin: 6px 0;
  color: #606266;
  line-height: 1.6;
}

/* 技术规格 */
.spec-section {
  padding: 20px 0;
  border-bottom: 1px solid #ebeef5;
}

.spec-section:last-child {
  border-bottom: none;
}

.spec-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
}

.spec-section ul {
  margin: 0;
  padding-left: 20px;
}

.spec-section li {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
}

/* 快捷键 */
.shortcut-section {
  padding: 20px 0;
  border-bottom: 1px solid #ebeef5;
}

.shortcut-section:last-child {
  border-bottom: none;
}

.shortcut-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
}

.shortcut-section ul {
  margin: 0;
  padding-left: 20px;
}

.shortcut-section li {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
}

/* 提示建议 */
.tip-section {
  padding: 20px 0;
  border-bottom: 1px solid #ebeef5;
}

.tip-section:last-child {
  border-bottom: none;
}

.tip-section h4 {
  margin: 0 0 12px 0;
  color: #67c23a;
  font-size: 16px;
}

.tip-section ul {
  margin: 0;
  padding-left: 20px;
}

.tip-section li {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
}

/* 强调文本 */
strong {
  color: #303133;
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 768px) {
  .user-guide-container {
    padding: 10px;
  }

  .guide-header {
    padding: 20px;
  }

  .guide-header h1 {
    font-size: 24px;
  }

  .workflow-step {
    flex-direction: column;
    gap: 12px;
  }

  .step-number {
    width: 32px;
    height: 32px;
    font-size: 16px;
  }
}
</style>
