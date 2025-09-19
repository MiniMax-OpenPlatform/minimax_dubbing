#!/bin/bash

# 批处理过程监控脚本
echo "🔍 批处理算法监控启动..."
echo "监控以下关键过程："
echo "  - 批量翻译算法执行"
echo "  - 批量TTS生成过程"
echo "  - 时间戳对齐算法步骤"
echo "  - MiniMax API调用"
echo "  - 错误和异常处理"
echo ""
echo "按 Ctrl+C 停止监控"
echo "===================="

# 实时监控Django日志中的批处理相关内容
tail -f django.log | grep -E "(批量|batch|TTS|align|MiniMax|optimize|algorithm|timestamp|第[一二三四五]步)" --line-buffered --color=always