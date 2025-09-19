"""
Base service class for business logic
"""
import logging
from typing import Any, Dict, Optional
from django.db import transaction
from backend.exceptions import ValidationError, BusinessLogicError

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class providing common functionality"""

    def __init__(self, user=None):
        self.user = user
        self.logger = logger

    def validate_user_permission(self, obj) -> bool:
        """Validate user has permission to access object"""
        if hasattr(obj, 'user'):
            return obj.user == self.user
        return True

    def log_operation(self, operation: str, details: Dict[str, Any]):
        """Log business operation"""
        self.logger.info(f"[{self.__class__.__name__}] {operation}", extra=details)

    @transaction.atomic
    def execute_transaction(self, operation_func, *args, **kwargs):
        """Execute operation in database transaction"""
        try:
            return operation_func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Transaction failed: {str(e)}")
            raise BusinessLogicError(f"Operation failed: {str(e)}")