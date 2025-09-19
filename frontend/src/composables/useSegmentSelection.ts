import { ref, computed } from 'vue'

interface Segment {
  id: number
  status: string
  [key: string]: any
}

export function useSegmentSelection() {
  const selectedSegments = ref<Segment[]>([])

  // 计算属性
  const selectedCount = computed(() => selectedSegments.value.length)
  const hasSelection = computed(() => selectedSegments.value.length > 0)

  // 选择单个段落
  const selectSegment = (segment: Segment, selected: boolean) => {
    if (selected) {
      if (!selectedSegments.value.find(s => s.id === segment.id)) {
        selectedSegments.value.push(segment)
      }
    } else {
      selectedSegments.value = selectedSegments.value.filter(s => s.id !== segment.id)
    }
  }

  // 批量选择
  const selectSegments = (segments: Segment[]) => {
    segments.forEach(segment => {
      if (!selectedSegments.value.find(s => s.id === segment.id)) {
        selectedSegments.value.push(segment)
      }
    })
  }

  // 清除选择
  const clearSelection = () => {
    selectedSegments.value = []
  }

  // 全选/取消全选
  const toggleSelectAll = (segments: Segment[], selectAll: boolean) => {
    if (selectAll) {
      selectedSegments.value = [...segments]
    } else {
      clearSelection()
    }
  }

  // 反选
  const invertSelection = (allSegments: Segment[]) => {
    const currentSelectedIds = new Set(selectedSegments.value.map(s => s.id))
    selectedSegments.value = allSegments.filter(s => !currentSelectedIds.has(s.id))
  }

  // 按条件选择
  const selectByCondition = (allSegments: Segment[], condition: (segment: Segment) => boolean) => {
    const matchingSegments = allSegments.filter(condition)
    selectSegments(matchingSegments)
  }

  // 选择指定状态的段落
  const selectByStatus = (allSegments: Segment[], status: string) => {
    selectByCondition(allSegments, segment => segment.status === status)
  }

  // 检查段落是否被选中
  const isSelected = (segment: Segment) => {
    return selectedSegments.value.some(s => s.id === segment.id)
  }

  // 获取选中段落的ID列表
  const getSelectedIds = () => {
    return selectedSegments.value.map(s => s.id)
  }

  // 获取选中段落的统计信息
  const getSelectionStats = () => {
    const stats = {
      total: selectedSegments.value.length,
      pending: 0,
      translated: 0,
      completed: 0,
      failed: 0
    }

    selectedSegments.value.forEach(segment => {
      if (segment.status in stats) {
        stats[segment.status as keyof typeof stats]++
      }
    })

    return stats
  }

  return {
    selectedSegments,
    selectedCount,
    hasSelection,
    selectSegment,
    selectSegments,
    clearSelection,
    toggleSelectAll,
    invertSelection,
    selectByCondition,
    selectByStatus,
    isSelected,
    getSelectedIds,
    getSelectionStats
  }
}