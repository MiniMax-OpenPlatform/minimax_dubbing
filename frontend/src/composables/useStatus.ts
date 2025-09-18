import { PROJECT_STATUS_MAP, SEGMENT_STATUS_MAP } from '../constants/status'
import type { ProjectStatus, SegmentStatus } from '../types/project'

// 获取项目状态标签
export const useProjectStatus = () => {
  const getStatusTag = (status: ProjectStatus) => {
    return PROJECT_STATUS_MAP[status] || { type: 'info', text: status }
  }

  return { getStatusTag }
}

// 获取段落状态标签
export const useSegmentStatus = () => {
  const getStatusTag = (status: SegmentStatus) => {
    return SEGMENT_STATUS_MAP[status] || { type: 'info', text: status }
  }

  return { getStatusTag }
}