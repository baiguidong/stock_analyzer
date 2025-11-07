"""
配置管理模块
"""
import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """数据库配置"""
    url: str = "sqlite:///./stock_data.db"


class TushareConfig(BaseModel):
    """Tushare配置"""
    token: str = ""


class LLMConfig(BaseModel):
    """大模型配置"""
    provider: str = "openai"
    api_key: str = ""
    base_url: Optional[str] = None
    model: str = "gpt-4-turbo-preview"


class UpdateScheduleConfig(BaseModel):
    """更新调度配置"""
    daily_update_time: str = "07:00"
    auto_update: bool = True
    update_on_start: bool = False


class JWTConfig(BaseModel):
    """JWT认证配置"""
    secret_key: str = "your-secret-key-change-this-in-production"
    access_token_expire_minutes: int = 1440  # 24小时


class APIConfig(BaseModel):
    """API服务配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False


class WebConfig(BaseModel):
    """Web配置"""
    title: str = "A股数据分析助手"
    port: int = 8501


class Config(BaseSettings):
    """全局配置"""
    database: DatabaseConfig = DatabaseConfig()
    tushare: TushareConfig = TushareConfig()
    llm: LLMConfig = LLMConfig()
    update_schedule: UpdateScheduleConfig = UpdateScheduleConfig()
    jwt: JWTConfig = JWTConfig()
    api: APIConfig = APIConfig()
    web: WebConfig = WebConfig()

    @classmethod
    def load_from_yaml(cls, config_path: str = "config.yaml") -> "Config":
        """从YAML文件加载配置"""
        config_file = Path(config_path)

        if not config_file.exists():
            # 如果配置文件不存在，尝试复制example文件
            example_file = Path("config.yaml.example")
            if example_file.exists():
                print(f"配置文件不存在，请复制 {example_file} 为 config.yaml 并修改配置")
            else:
                print("配置文件不存在，使用默认配置")
            return cls()

        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)


# 全局配置实例
config = Config.load_from_yaml()
