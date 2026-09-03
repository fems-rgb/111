"""智研星枢 - 全局异常定义"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class AppException(Exception):
    """应用基础异常"""
    def __init__(self, message: str, status_code: int = 400, error_code: str = "UNKNOWN"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class AuthException(AppException):
    """认证异常"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "AUTH_ERROR")


class ForbiddenException(AppException):
    """权限不足"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "FORBIDDEN")


class NotFoundException(AppException):
    """资源不存在"""
    def __init__(self, resource: str = "资源"):
        super().__init__(f"{resource}不存在", status.HTTP_404_NOT_FOUND, "NOT_FOUND")


class RateLimitException(AppException):
    """速率限制"""
    def __init__(self, retry_after: int = 60):
        super().__init__(f"请求过于频繁，请{retry_after}秒后重试", status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMIT")
        self.retry_after = retry_after


class AgentException(AppException):
    """Agent执行异常"""
    def __init__(self, message: str = "Agent执行失败", agent_name: str = ""):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, "AGENT_ERROR")
        self.agent_name = agent_name


class PromptGuardException(AppException):
    """提示注入检测异常"""
    def __init__(self, reason: str = ""):
        super().__init__(f"安全检测未通过: {reason}", status.HTTP_400_BAD_REQUEST, "PROMPT_GUARD")



class ProjectAlreadyRunningError(AppException):
    """项目已在运行中"""
    def __init__(self, project_id: int = 0):
        super().__init__(
            f"项目 {project_id} 正在运行中，请先暂停或等待完成后再重新启动",
            status.HTTP_409_CONFLICT,
            "PROJECT_ALREADY_RUNNING"
        )
        self.project_id = project_id


class ProjectNotReadyError(AppException):
    """项目状态不允许当前操作"""
    def __init__(self, message: str = "项目当前状态不允许此操作"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, "PROJECT_NOT_READY")


async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    if isinstance(exc, AppException):
        logger.warning(f"[{exc.error_code}] {exc.message} | {request.method} {request.url.path}")
        headers = {}
        if isinstance(exc, RateLimitException):
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error_code": exc.error_code, "message": exc.message, "detail": None},
            headers=headers
        )

    # 未预期的异常
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error_code": "INTERNAL_ERROR", "message": "服务器内部错误", "detail": None}
    )