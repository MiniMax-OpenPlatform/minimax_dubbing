import { ref, nextTick } from 'vue'

// 全局波形缓存（跨组件共享）
const globalWaveformCache = new Map<string, number[]>()

export function useAudioWaveform() {
  const waveformData = ref<number[]>([])
  const isAnalyzingWaveform = ref(false)

  // 生成波形数据（使用Web Audio API分析真实音频）
  const generateWaveform = async (audioUrl?: string) => {
    // 设置加载状态
    isAnalyzingWaveform.value = true

    // 如果没有音频URL，生成默认波形用于展示
    if (!audioUrl) {
      const sampleCount = 200
      const samples: number[] = []

      for (let i = 0; i < sampleCount; i++) {
        // 生成更真实的波形：有静音区域和活跃区域
        const progress = i / sampleCount
        let amplitude = 0.05 // 基础静音值

        // 创建几个活跃区域
        if ((progress > 0.1 && progress < 0.3) ||
            (progress > 0.5 && progress < 0.8) ||
            (progress > 0.85 && progress < 0.95)) {
          // 活跃区域：使用正弦波 + 随机变化
          const wave = Math.sin(i * 0.2) * 0.4 + 0.4
          const noise = (Math.random() - 0.5) * 0.3
          amplitude = Math.max(0.1, Math.min(0.8, wave + noise))
        } else {
          // 静音区域：很小的随机波动
          amplitude = Math.random() * 0.15 + 0.02
        }

        samples.push(amplitude)
      }

      waveformData.value = samples
      isAnalyzingWaveform.value = false
      return samples
    }

    // 检查缓存
    if (globalWaveformCache.has(audioUrl)) {
      waveformData.value = globalWaveformCache.get(audioUrl)!
      isAnalyzingWaveform.value = false
      return waveformData.value
    }

    // 使用Web Audio API分析真实音频文件
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const response = await fetch(audioUrl)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const arrayBuffer = await response.arrayBuffer()
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

      // 获取音频数据（使用第一个声道）
      const rawData = audioBuffer.getChannelData(0)
      const sampleCount = 200 // 波形条数
      const blockSize = Math.floor(rawData.length / sampleCount)
      const samples: number[] = []

      for (let i = 0; i < sampleCount; i++) {
        let sum = 0
        for (let j = 0; j < blockSize; j++) {
          sum += Math.abs(rawData[i * blockSize + j])
        }
        // 计算平均振幅并标准化到0-1范围，增强可见性
        const amplitude = (sum / blockSize)

        // 动态增强：小音量大幅放大，大音量适度放大
        let enhancedAmplitude
        if (amplitude < 0.1) {
          // 小音量：放大5倍，确保静音区域可见
          enhancedAmplitude = Math.min(amplitude * 5, 0.2)
        } else if (amplitude < 0.3) {
          // 中音量：放大3倍
          enhancedAmplitude = Math.min(amplitude * 3, 0.6)
        } else {
          // 大音量：放大2倍，保持动态范围
          enhancedAmplitude = Math.min(amplitude * 2, 0.9)
        }

        // 确保最小可见高度
        enhancedAmplitude = Math.max(enhancedAmplitude, 0.03)
        samples.push(enhancedAmplitude)
      }

      waveformData.value = samples

      // 缓存波形数据
      globalWaveformCache.set(audioUrl, samples)

      // 关闭音频上下文以释放资源
      audioContext.close()

      isAnalyzingWaveform.value = false
      return samples

    } catch (error) {
      console.error('[useAudioWaveform] 音频波形分析失败:', error)

      // 分析失败时使用默认波形
      const sampleCount = 200
      const samples: number[] = []

      for (let i = 0; i < sampleCount; i++) {
        // 生成更明显的错误状态波形
        const amplitude = Math.random() * 0.6 + 0.2 // 提高默认波形的可见性
        samples.push(amplitude)
      }

      waveformData.value = samples
      isAnalyzingWaveform.value = false
      return samples
    }
  }

  return {
    waveformData,
    isAnalyzingWaveform,
    generateWaveform
  }
}