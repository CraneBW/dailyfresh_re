# exceptions.py - 自定义异常类

class ConfigError(Exception):
    """配置错误异常"""
    pass

class APIError(Exception):
    """API调用错误异常"""
    def __init__(self, message, status_code=None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ModelError(Exception):
    """模型错误异常"""
    pass

class DataError(Exception):
    """数据处理错误异常"""
    pass

class RecommendationError(Exception):
    """推荐系统错误异常"""
    pass

class AuthenticationError(Exception):
    """认证错误异常"""
    pass
