<template>
  <div class="about-container">
    <div class="about-header">
      <h1>关于本软件</h1>
      <p class="subtitle">MiniMax 翻译工具 - 基于AI的智能翻译解决方案</p>
    </div>

    <div class="about-content">
      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><cpu /></el-icon>
            <span>核心技术</span>
          </div>
        </template>
        <p>本翻译软件基于MiniMax的TTS和LLM模型API实现翻译功能，提供高质量的文本翻译和语音合成服务。</p>
      </el-card>

      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><document /></el-icon>
            <span>开源代码</span>
          </div>
        </template>
        <p>本软件全栈代码可以到GitHub获取，内部长期使用或定制化修改建议自行部署：</p>
        <el-link
          href="https://github.com/backearth1/minimax_translation"
          target="_blank"
          type="primary"
          class="github-link"
        >
          🔗 https://github.com/backearth1/minimax_translation
        </el-link>
      </el-card>

      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><timer /></el-icon>
            <span>时间戳自动对齐逻辑</span>
          </div>
        </template>
        <div class="timestamp-logic">
          <h4>批量TTS时的智能对齐算法：</h4>

          <div class="step-item">
            <div class="step-number">1</div>
            <div class="step-content">
              <h5>初始TTS生成</h5>
              <ul>
                <li>使用默认语速(1.0)生成TTS音频</li>
                <li>通过静音裁剪检测实际音频时长</li>
                <li>根据时间戳差值计算目标时长</li>
              </ul>
            </div>
          </div>

          <div class="step-item">
            <div class="step-number">2</div>
            <div class="step-content">
              <h5>LLM文本优化</h5>
              <ul>
                <li>当音频过长时，使用大语言模型创建更短的文本变体</li>
                <li>在保持语义的同时减少字数</li>
                <li>用优化后的文本重新生成TTS</li>
              </ul>
            </div>
          </div>

          <div class="step-item">
            <div class="step-number">3</div>
            <div class="step-content">
              <h5>语速调节（精细调优）</h5>
              <ul>
                <li>计算最优语速：目标时长 / 实际时长</li>
                <li>采用递增的语速提升（0.1-0.2步长）</li>
                <li>验证语速保持在合理范围内</li>
              </ul>
            </div>
          </div>

          <div class="step-item">
            <div class="step-number">4</div>
            <div class="step-content">
              <h5>语速加速重试</h5>
              <ul>
                <li>对仍然过长的音频，采用更大的语速增量（0.3-0.5）</li>
                <li>多次重试，逐步提升语速</li>
                <li>平衡音频质量与时间要求</li>
              </ul>
            </div>
          </div>

          <div class="step-item">
            <div class="step-number">5</div>
            <div class="step-content">
              <h5>最大语速尝试</h5>
              <ul>
                <li>使用配置的最大语速作为最后的备选方案</li>
                <li>使用项目的 max_speed 参数（范围：1.2-2.0）</li>
                <li>即使略微超出目标时长也接受结果</li>
              </ul>
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><edit /></el-icon>
            <span>人工调优</span>
          </div>
        </template>
        <p>软件也支持用户自己手动修改SRT段落的翻译/TTS等参数，人工修正更稳定。</p>
      </el-card>

      <el-card class="section-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><message /></el-icon>
            <span>联系支持</span>
          </div>
        </template>
        <p>在使用过程中遇到问题可以在GitHub提PR，也可以联系作者：</p>
        <el-link
          href="mailto:devin@minimaxi.com"
          type="primary"
          class="contact-link"
        >
          <el-icon><message /></el-icon>
          devin@minimaxi.com
        </el-link>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Cpu, Document, Timer, Edit, Message } from '@element-plus/icons-vue'
</script>

<style scoped>
.about-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.about-header {
  text-align: center;
  margin-bottom: 40px;
}

.about-header h1 {
  font-size: 32px;
  color: #303133;
  margin-bottom: 10px;
  font-weight: 600;
}

.subtitle {
  font-size: 16px;
  color: #909399;
  margin: 0;
}

.about-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-card {
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s ease;
}

.section-card:hover {
  border-color: #409eff;
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}

.card-header .el-icon {
  color: #409eff;
  font-size: 18px;
}

.github-link, .contact-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  font-size: 14px;
  text-decoration: none;
}

.timestamp-logic h4 {
  color: #303133;
  margin-bottom: 20px;
  font-size: 16px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.step-number {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.step-content {
  flex: 1;
}

.step-content h5 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.step-content ul {
  margin: 0;
  padding-left: 16px;
  color: #606266;
}

.step-content li {
  margin-bottom: 4px;
  font-size: 13px;
  line-height: 1.5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .about-container {
    padding: 15px;
  }

  .about-header h1 {
    font-size: 24px;
  }

  .subtitle {
    font-size: 14px;
  }

  .step-item {
    flex-direction: column;
    gap: 12px;
  }

  .step-number {
    align-self: flex-start;
  }
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .step-item {
    background: #1a1a1a;
  }
}
</style>