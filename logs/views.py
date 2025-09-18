from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from backend.utils import memory_log_handler
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_system_logs(request):
    """
    获取系统日志

    Query Parameters:
    - limit: 限制返回的日志数量 (默认: 100)
    - level: 过滤日志级别 (DEBUG, INFO, WARNING, ERROR)
    - search: 搜索关键词
    """
    try:
        # 获取查询参数
        limit = request.GET.get('limit', 100)
        level_filter = request.GET.get('level')
        search = request.GET.get('search')

        try:
            limit = int(limit)
            if limit <= 0:
                limit = 100
        except (ValueError, TypeError):
            limit = 100

        # 限制最大返回数量
        limit = min(limit, 1000)

        # 调试信息
        logger.info(f"日志API调用: limit={limit}, level_filter={level_filter}, search={search}")
        logger.info(f"内存日志处理器状态: {len(memory_log_handler.logs)} 条日志")

        # 获取日志
        logs = memory_log_handler.get_logs(
            limit=limit,
            level_filter=level_filter,
            search=search
        )

        return Response({
            'success': True,
            'count': len(logs),
            'logs': logs
        })

    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'logs': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def clear_system_logs(request):
    """清空系统日志"""
    try:
        memory_log_handler.clear_logs()
        logger.info("系统日志已清空")

        return Response({
            'success': True,
            'message': '系统日志已清空'
        })

    except Exception as e:
        logger.error(f"清空系统日志失败: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_raw_logs(request):
    """获取原始日志文本"""
    try:
        # 获取所有日志
        logs = memory_log_handler.get_logs()

        # 格式化为原始日志文本
        raw_text_lines = []
        for log in logs:
            # 格式：时间戳 [级别] logger: 消息
            line = f"{log['timestamp']} [{log['level']}] {log['logger']}: {log['message']}"
            raw_text_lines.append(line)

        raw_text = '\n'.join(raw_text_lines)

        # 直接返回文本，不包装在JSON中
        from django.http import HttpResponse
        return HttpResponse(raw_text, content_type='text/plain; charset=utf-8')

    except Exception as e:
        logger.error(f"获取原始日志失败: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def clear_logs(request):
    """清空系统日志 - 新的简化接口"""
    try:
        memory_log_handler.clear_logs()
        logger.info("系统日志已清空")

        from django.http import HttpResponse
        return HttpResponse("日志已清空", content_type='text/plain; charset=utf-8')

    except Exception as e:
        logger.error(f"清空系统日志失败: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_log_stats(request):
    """获取日志统计信息"""
    try:
        logs = memory_log_handler.get_logs()

        # 统计各级别日志数量
        level_counts = {}
        for log in logs:
            level = log['level']
            level_counts[level] = level_counts.get(level, 0) + 1

        return Response({
            'success': True,
            'total_logs': len(logs),
            'level_counts': level_counts
        })

    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)