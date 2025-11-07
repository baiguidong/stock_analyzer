"""
用户认证模块 - JWT令牌和密码加密
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import hashlib
import secrets

from ..config import config

# OAuth2 密码bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None
    user_id: Optional[int] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码 (使用MD5)
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码 (格式: salt$hash)
    Returns:
        是否匹配
    """
    try:
        # 从存储的哈希中提取盐
        salt, hash_value = hashed_password.split('$')
        # 使用相同的盐计算密码哈希
        return get_password_hash_with_salt(plain_password, salt) == hashed_password
    except ValueError:
        # 如果格式不正确，可能是旧的未加盐哈希
        return get_password_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    """
    获取密码哈希 (使用MD5加盐)
    Args:
        password: 明文密码
    Returns:
        带盐的哈希密码 (格式: salt$hash)
    """
    # 生成随机盐
    salt = secrets.token_hex(16)
    return get_password_hash_with_salt(password, salt)


def get_password_hash_with_salt(password: str, salt: str) -> str:
    """
    使用指定盐获取密码哈希
    Args:
        password: 明文密码
        salt: 盐值
    Returns:
        带盐的哈希密码 (格式: salt$hash)
    """
    # 组合密码和盐，然后计算MD5哈希
    salted_password = salt + password
    hash_value = hashlib.md5(salted_password.encode('utf-8')).hexdigest()
    return f"{salt}${hash_value}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
    Returns:
        JWT令牌
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.jwt.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.jwt.secret_key, algorithm="HS256")

    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """
    解码访问令牌
    Args:
        token: JWT令牌
    Returns:
        令牌数据
    Raises:
        HTTPException: 令牌无效
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, config.jwt.secret_key, algorithms=["HS256"])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if username is None:
            raise credentials_exception

        return TokenData(username=username, user_id=user_id)

    except JWTError:
        raise credentials_exception


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """
    获取当前用户ID（依赖注入）
    Args:
        token: JWT令牌
    Returns:
        用户ID
    """
    token_data = decode_access_token(token)

    if token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data.user_id
