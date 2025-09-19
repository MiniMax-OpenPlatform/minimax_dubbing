import { ref, reactive } from 'vue'

interface ValidationError {
  field: string
  message: string
}

interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  custom?: (value: any) => string | null
}

interface ValidationRules {
  [field: string]: ValidationRule
}

export function useSegmentValidation() {
  const validationErrors = reactive<Record<number, Record<string, string>>>({})
  const isValidating = ref(false)

  // 验证规则定义
  const defaultRules: ValidationRules = {
    original_text: {
      required: true,
      minLength: 1,
      maxLength: 500
    },
    translated_text: {
      maxLength: 500
    },
    speaker: {
      maxLength: 50
    },
    voice_id: {
      pattern: /^[a-zA-Z0-9_-]+$/
    },
    emotion: {
      pattern: /^[a-zA-Z_]+$/
    },
    speed: {
      custom: (value: number) => {
        if (typeof value !== 'number') return '语速必须是数字'
        if (value < 0.5 || value > 2.0) return '语速必须在0.5-2.0之间'
        return null
      }
    }
  }

  // 验证单个字段
  const validateField = (field: string, value: any, rules: ValidationRule = defaultRules[field]): string | null => {
    if (!rules) return null

    // 必填验证
    if (rules.required && (!value || (typeof value === 'string' && value.trim() === ''))) {
      return `${getFieldLabel(field)}不能为空`
    }

    // 如果值为空且不是必填，跳过其他验证
    if (!value && !rules.required) return null

    const stringValue = String(value)

    // 最小长度验证
    if (rules.minLength && stringValue.length < rules.minLength) {
      return `${getFieldLabel(field)}长度不能少于${rules.minLength}个字符`
    }

    // 最大长度验证
    if (rules.maxLength && stringValue.length > rules.maxLength) {
      return `${getFieldLabel(field)}长度不能超过${rules.maxLength}个字符`
    }

    // 正则验证
    if (rules.pattern && !rules.pattern.test(stringValue)) {
      return `${getFieldLabel(field)}格式不正确`
    }

    // 自定义验证
    if (rules.custom) {
      const customError = rules.custom(value)
      if (customError) return customError
    }

    return null
  }

  // 验证整个段落
  const validateSegment = (segment: any, customRules?: ValidationRules): Record<string, string> => {
    const errors: Record<string, string> = {}
    const rulesToUse = { ...defaultRules, ...customRules }

    Object.keys(rulesToUse).forEach(field => {
      const error = validateField(field, segment[field], rulesToUse[field])
      if (error) {
        errors[field] = error
      }
    })

    return errors
  }

  // 批量验证段落
  const validateSegments = (segments: any[], customRules?: ValidationRules): boolean => {
    isValidating.value = true
    let isValid = true

    segments.forEach(segment => {
      const errors = validateSegment(segment, customRules)

      if (Object.keys(errors).length > 0) {
        validationErrors[segment.id] = errors
        isValid = false
      } else {
        delete validationErrors[segment.id]
      }
    })

    isValidating.value = false
    return isValid
  }

  // 设置字段错误
  const setFieldError = (segmentId: number, field: string, error: string) => {
    if (!validationErrors[segmentId]) {
      validationErrors[segmentId] = {}
    }
    validationErrors[segmentId][field] = error
  }

  // 清除字段错误
  const clearFieldError = (segmentId: number, field: string) => {
    if (validationErrors[segmentId]) {
      delete validationErrors[segmentId][field]
      if (Object.keys(validationErrors[segmentId]).length === 0) {
        delete validationErrors[segmentId]
      }
    }
  }

  // 清除段落所有错误
  const clearSegmentErrors = (segmentId: number) => {
    delete validationErrors[segmentId]
  }

  // 清除所有错误
  const clearAllErrors = () => {
    Object.keys(validationErrors).forEach(key => {
      delete validationErrors[Number(key)]
    })
  }

  // 检查段落是否有错误
  const hasSegmentErrors = (segmentId: number): boolean => {
    return Boolean(validationErrors[segmentId] && Object.keys(validationErrors[segmentId]).length > 0)
  }

  // 获取段落错误数量
  const getSegmentErrorCount = (segmentId: number): number => {
    return validationErrors[segmentId] ? Object.keys(validationErrors[segmentId]).length : 0
  }

  // 获取总错误数量
  const getTotalErrorCount = (): number => {
    return Object.values(validationErrors).reduce((total, errors) => total + Object.keys(errors).length, 0)
  }

  // 获取有错误的段落数量
  const getErrorSegmentCount = (): number => {
    return Object.keys(validationErrors).length
  }

  // 实时验证字段（防抖）
  let validateTimeout: number | null = null
  const validateFieldDebounced = (segmentId: number, field: string, value: any, delay = 500) => {
    if (validateTimeout) {
      clearTimeout(validateTimeout)
    }

    validateTimeout = window.setTimeout(() => {
      const error = validateField(field, value)
      if (error) {
        setFieldError(segmentId, field, error)
      } else {
        clearFieldError(segmentId, field)
      }
    }, delay)
  }

  // 获取字段标签
  const getFieldLabel = (field: string): string => {
    const labels: Record<string, string> = {
      original_text: '原文',
      translated_text: '译文',
      speaker: '说话人',
      voice_id: '音色ID',
      emotion: '情感',
      speed: '语速'
    }
    return labels[field] || field
  }

  // 翻译前验证
  const validateForTranslation = (segments: any[]): { valid: boolean; errors: string[] } => {
    const errors: string[] = []

    segments.forEach(segment => {
      if (!segment.original_text || segment.original_text.trim() === '') {
        errors.push(`段落${segment.index}: 原文不能为空`)
      }

      if (segment.original_text && segment.original_text.length > 500) {
        errors.push(`段落${segment.index}: 原文长度超过500字符`)
      }
    })

    return {
      valid: errors.length === 0,
      errors
    }
  }

  // TTS前验证
  const validateForTTS = (segments: any[]): { valid: boolean; errors: string[] } => {
    const errors: string[] = []

    segments.forEach(segment => {
      if (!segment.translated_text || segment.translated_text.trim() === '') {
        errors.push(`段落${segment.index}: 译文不能为空`)
      }

      if (segment.speed && (segment.speed < 0.5 || segment.speed > 2.0)) {
        errors.push(`段落${segment.index}: 语速设置不正确`)
      }
    })

    return {
      valid: errors.length === 0,
      errors
    }
  }

  return {
    validationErrors,
    isValidating,
    validateField,
    validateSegment,
    validateSegments,
    setFieldError,
    clearFieldError,
    clearSegmentErrors,
    clearAllErrors,
    hasSegmentErrors,
    getSegmentErrorCount,
    getTotalErrorCount,
    getErrorSegmentCount,
    validateFieldDebounced,
    validateForTranslation,
    validateForTTS
  }
}