# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    REAL_TIME_API_URL = "https://api.example.com/realtime/{}"
    
    # 添加基本配置
    API_TIMEOUT = 30  # API请求超时时间(秒)
    MAX_RETRIES = 3   # API请求最大重试次数
    
    # 推荐系统配置
    MAX_RECOMMENDATIONS = 5  # 最大推荐数量
    MIN_CONFIDENCE_SCORE = 0.7  # 最小置信度分数
    
    # 数据存储配置
    USER_HISTORY_PATH = "user_data/"  # 用户历史数据存储路径
    
    # 排序配置
    RANKING_WEIGHTS = {
        "relevance": 0.4,
        "recency": 0.3,
        "popularity": 0.2,
        "diversity": 0.1
    }
    
    # 模型配置
    USER_FEATURE_WEIGHTS = {
        "project_type": 0.4,
        "tech_stack": 0.3,
        "project_size": 0.2,
        "time_since_last_project": 0.1
    }
    
class DevelopmentConfig(Config):
    DEBUG = True
    MODEL_NAME = "gpt-3.5-turbo"
    # 开发环境特定配置
    LOG_LEVEL = "DEBUG"
    CACHE_ENABLED = True
    CACHE_TIMEOUT = 300  # 缓存超时时间(秒)
    
class ProductionConfig(Config):
    DEBUG = False
    MODEL_NAME = "gpt-4"
    # 生产环境特定配置
    LOG_LEVEL = "INFO"
    CACHE_ENABLED = True
    CACHE_TIMEOUT = 3600  # 缓存超时时间(秒)
    ENABLE_METRICS = True  # 启用指标收集
    
# 添加测试配置
class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    MODEL_NAME = "gpt-3.5-turbo"
    # 使用模拟数据
    USE_MOCK_DATA = True
    
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}

# 设置当前环境
current_env = os.getenv("APP_ENV", "development")
current_config = config[current_env]
