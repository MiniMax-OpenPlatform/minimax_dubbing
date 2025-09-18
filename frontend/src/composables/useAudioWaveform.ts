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
        // 生成随机波形数据用于预览
        const amplitude = Math.random() * 0.8 + 0.2
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
        // 计算平均振幅并标准化到0-1范围
        const amplitude = (sum / blockSize)
        samples.push(Math.min(amplitude * 2, 1)) // 放大2倍但限制在1以内
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
        const amplitude = Math.random() * 0.4 + 0.1 // 更低的默认波形
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