"""
统一异常处理模块
"""
import logging
import traceback
import uuid
import functools
from django.http import JsonResponse
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response


logger = logging.getLogger(__name__)


class APIException(Exception):
    """API基础异常类"""
    def __init__(self, message: str, code: str = "API_ERROR", status_code: int = 500, details: dict = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIException):
    """数据验证异常"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class BusinessLogicError(APIException):
    """业务逻辑异常"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "BUSINESS_ERROR", 422, details)


class ExternalAPIError(APIException):
    """外部API调用异常"""
    def __init__(self, message: str, service: str = None, details: dict = None):
        details = details or {}
        if service:
            details['service'] = service
        super().__init__(message, "EXTERNAL_API_ERROR", 503, details)


class ResourceNotFoundError(APIException):
    """资源未找到异常"""
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None):
        details = {}
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
        super().__init__(message, "RESOURCE_NOT_FOUND", 404, details)


class PermissionError(APIException):
    """权限异常"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "PERMISSION_DENIED", 403, details)


def custom_exception_handler(exc, context):
    """
    自定义异常处理器
    """
    # 生成追踪ID
    trace_id = str(uuid.uuid4())[:8]

    # 获取请求信息
    request = context.get('request')
    view = context.get('view')

    # 记录请求信息
    request_info = {
        'path': request.path if request else 'unknown',
        'method': request.method if request else 'unknown',
        'user': str(request.user) if request and hasattr(request, 'user') else 'anonymous',
        'view': view.__class__.__name__ if view else 'unknown'
    }

    # 处理自定义API异常
    if isinstance(exc, APIException):
        logger.error(f"[{trace_id}] API异常: {exc.message}", extra={
            'trace_id': trace_id,
            'error_code': exc.code,
            'request_info': request_info,
            'details': exc.details
        })

        return Response({
            'success': False,
            'error': {
                'code': exc.code,
                'message': exc.message,
                'details': exc.details
            },
            'trace_id': trace_id
        }, status=exc.status_code)

    # 使用DRF默认异常处理器
    response = exception_handler(exc, context)

    if response is not None:
        # DRF异常
        error_code = "DRF_ERROR"
        error_message = "请求处理失败"

        # 根据状态码设置错误码和消息
        if response.status_code == 400:
            error_code = "VALIDATION_ERROR"
            error_message = "数据验证失败"
        elif response.status_code == 401:
            error_code = "AUTHENTICATION_ERROR"
            error_message = "身份验证失败"
        elif response.status_code == 403:
            error_code = "PERMISSION_DENIED"
            error_message = "权限不足"
        elif response.status_code == 404:
            error_code = "RESOURCE_NOT_FOUND"
            error_message = "资源未找到"
        elif response.status_code == 405:
            error_code = "METHOD_NOT_ALLOWED"
            error_message = "请求方法不允许"

        logger.warning(f"[{trace_id}] DRF异常: {error_message}", extra={
            'trace_id': trace_id,
            'error_code': error_code,
            'request_info': request_info,
            'response_data': response.data
        })

        # 统一格式化响应
        custom_response_data = {
            'success': False,
            'error': {
                'code': error_code,
                'message': error_message,
                'details': response.data
            },
            'trace_id': trace_id
        }
        response.data = custom_response_data
        return response

    # 未处理的异常（服务器错误）
    logger.error(f"[{trace_id}] 未处理异常: {str(exc)}", extra={
        'trace_id': trace_id,
        'error_code': 'INTERNAL_ERROR',
        'request_info': request_info,
        'traceback': traceback.format_exc()
    })

    return Response({
        'success': False,
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': '服务器内部错误',
            'details': {}
        },
        'trace_id': trace_id
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ErrorHandlerMiddleware:
    """
    错误处理中间件
    处理Django视图中未被异常处理器捕获的异常
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """处理Django视图异常"""
        trace_id = str(uuid.uuid4())[:8]

        request_info = {
            'path': request.path,
            'method': request.method,
            'user': str(request.user) if hasattr(request, 'user') else 'anonymous'
        }

        logger.error(f"[{trace_id}] Django视图异常: {str(exception)}", extra={
            'trace_id': trace_id,
            'error_code': 'VIEW_ERROR',
            'request_info': request_info,
            'traceback': traceback.format_exc()
        })

        return JsonResponse({
            'success': False,
            'error': {
                'code': 'VIEW_ERROR',
                'message': '视图处理异常',
                'details': {}
            },
            'trace_id': trace_id
        }, status=500)


def handle_external_api_error(func):
    """
    装饰器：处理外部API调用异常
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            service_name = kwargs.get('service_name', func.__name__)
            raise ExternalAPIError(
                f"外部服务调用失败: {str(e)}",
                service=service_name,
                details={'original_error': str(e)}
            )
    return wrapper


def handle_business_logic_error(func):
    """
    装饰器：处理业务逻辑异常
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIException:
            # 重新抛出API异常
            raise
        except Exception as e:
            raise BusinessLogicError(
                f"业务逻辑处理失败: {str(e)}",
                details={'original_error': str(e)}
            )
    return wrapper