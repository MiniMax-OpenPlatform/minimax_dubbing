import { ref, computed } from 'vue'
import type { UploadProgress } from '../components/progress/UploadProgressBar.vue'

export function useUploadProgress() {
  // 上传进度状态
  const uploadProgress = ref<UploadProgress>({
    fileName: '',
    fileSize: 0,
    uploadedSize: 0,
    percentage: 0,
    speed: 0,
    remainingTime: 0,
    status: 'uploading',
    statusMessage: '',
    visible: false
  })

  // 上传开始时间，用于计算速度
  const uploadStartTime = ref<number>(0)
  const lastUpdateTime = ref<number>(0)
  const lastUploadedSize = ref<number>(0)

  // XMLHttpRequest 引用，用于取消上传
  const currentXhr = ref<XMLHttpRequest | null>(null)

  // 计算属性：是否有活跃的上传任务
  const hasActiveUpload = computed(() => uploadProgress.value.visible)

  /**
   * 开始上传进度跟踪
   */
  const startUpload = (fileName: string, fileSize: number) => {
    const now = Date.now()
    uploadStartTime.value = now
    lastUpdateTime.value = now
    lastUploadedSize.value = 0

    uploadProgress.value = {
      fileName,
      fileSize,
      uploadedSize: 0,
      percentage: 0,
      speed: 0,
      remainingTime: 0,
      status: 'uploading',
      statusMessage: '',
      visible: true
    }
  }

  /**
   * 更新上传进度
   */
  const updateProgress = (uploadedSize: number) => {
    if (!uploadProgress.value.visible) return

    const now = Date.now()
    const timeDiff = (now - lastUpdateTime.value) / 1000 // 秒
    const sizeDiff = uploadedSize - lastUploadedSize.value

    // 计算上传速度（字节/秒）
    let speed = 0
    if (timeDiff > 0.5) { // 每0.5秒更新一次速度
      speed = sizeDiff / timeDiff
      lastUpdateTime.value = now
      lastUploadedSize.value = uploadedSize
    } else {
      speed = uploadProgress.value.speed // 保持之前的速度
    }

    // 计算进度百分比
    const percentage = Math.round((uploadedSize / uploadProgress.value.fileSize) * 100)

    // 计算剩余时间
    let remainingTime = 0
    if (speed > 0) {
      const remainingBytes = uploadProgress.value.fileSize - uploadedSize
      remainingTime = remainingBytes / speed
    }

    uploadProgress.value = {
      ...uploadProgress.value,
      uploadedSize,
      percentage,
      speed,
      remainingTime
    }
  }

  /**
   * 上传成功
   */
  const uploadSuccess = (message?: string) => {
    uploadProgress.value = {
      ...uploadProgress.value,
      percentage: 100,
      status: 'success',
      statusMessage: message || '上传成功',
      speed: 0,
      remainingTime: 0
    }
  }

  /**
   * 上传失败
   */
  const uploadError = (errorMessage: string) => {
    uploadProgress.value = {
      ...uploadProgress.value,
      status: 'error',
      statusMessage: errorMessage,
      speed: 0,
      remainingTime: 0
    }
  }

  /**
   * 上传取消
   */
  const uploadCancelled = () => {
    uploadProgress.value = {
      ...uploadProgress.value,
      status: 'cancelled',
      statusMessage: '上传已取消',
      speed: 0,
      remainingTime: 0
    }
  }

  /**
   * 关闭进度条
   */
  const dismissProgress = () => {
    uploadProgress.value.visible = false
    currentXhr.value = null
  }

  /**
   * 取消上传
   */
  const cancelUpload = () => {
    if (currentXhr.value && uploadProgress.value.status === 'uploading') {
      currentXhr.value.abort()
      uploadCancelled()
    }
  }

  /**
   * 创建带进度监控的上传方法
   */
  const createUploadRequest = (
    url: string,
    formData: FormData,
    options: {
      headers?: Record<string, string>
      onSuccess?: (response: any) => void
      onError?: (error: any) => void
    } = {}
  ) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      currentXhr.value = xhr

      // 上传进度监听
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          updateProgress(event.loaded)
        }
      })

      // 上传完成监听
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText)
            uploadSuccess()
            options.onSuccess?.(response)
            resolve(response)
          } catch (error) {
            uploadError('响应解析失败')
            options.onError?.(error)
            reject(error)
          }
        } else {
          try {
            const errorResponse = JSON.parse(xhr.responseText)
            uploadError(errorResponse.message || `上传失败: ${xhr.status}`)
            options.onError?.(errorResponse)
            reject(errorResponse)
          } catch {
            uploadError(`上传失败: ${xhr.status}`)
            options.onError?.(new Error(`Upload failed: ${xhr.status}`))
            reject(new Error(`Upload failed: ${xhr.status}`))
          }
        }
      })

      // 上传错误监听
      xhr.addEventListener('error', () => {
        uploadError('网络错误，上传失败')
        const error = new Error('Network error')
        options.onError?.(error)
        reject(error)
      })

      // 上传取消监听
      xhr.addEventListener('abort', () => {
        uploadCancelled()
        const error = new Error('Upload cancelled')
        options.onError?.(error)
        reject(error)
      })

      // 设置请求
      xhr.open('POST', url)

      // 设置头部
      if (options.headers) {
        Object.entries(options.headers).forEach(([key, value]) => {
          xhr.setRequestHeader(key, value)
        })
      }

      // 发送请求
      xhr.send(formData)
    })
  }

  /**
   * 上传文件的便捷方法
   */
  const uploadFile = async (
    file: File,
    url: string,
    fieldName: string = 'file',
    additionalData: Record<string, string> = {},
    options: {
      headers?: Record<string, string>
      onSuccess?: (response: any) => void
      onError?: (error: any) => void
    } = {}
  ) => {
    // 开始上传跟踪
    startUpload(file.name, file.size)

    // 创建FormData
    const formData = new FormData()
    formData.append(fieldName, file)

    // 添加额外数据
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, value)
    })

    try {
      return await createUploadRequest(url, formData, options)
    } catch (error) {
      throw error
    }
  }

  return {
    // 状态
    uploadProgress: computed(() => uploadProgress.value),
    hasActiveUpload,

    // 方法
    startUpload,
    updateProgress,
    uploadSuccess,
    uploadError,
    uploadCancelled,
    dismissProgress,
    cancelUpload,
    createUploadRequest,
    uploadFile
  }
}

export type UseUploadProgress = ReturnType<typeof useUploadProgress>