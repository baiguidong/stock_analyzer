from passlib.context import CryptContext

# 模拟原来的密码哈希函数
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def old_get_password_hash(password: str) -> str:
    """原来的密码哈希函数"""
    return pwd_context.hash(password)

def new_get_password_hash(password: str) -> str:
    """修复后的密码哈希函数"""
    # 限制密码长度不超过72字节，防止bcrypt库报错
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

# 测试
print("Testing old function with long password (should fail)...")
try:
    long_password = 'a' * 100
    old_hashed = old_get_password_hash(long_password)
    print("Old function succeeded (unexpected)")
except Exception as e:
    print(f"Old function failed as expected: {type(e).__name__}")

print("\nTesting new function with long password...")
try:
    long_password = 'a' * 100
    new_hashed = new_get_password_hash(long_password)
    print("New function succeeded!")
except Exception as e:
    print(f"New function failed: {type(e).__name__}: {e}")

print("\nTesting new function with exactly 72-byte password...")
try:
    exact_password = 'b' * 72
    exact_hashed = new_get_password_hash(exact_password)
    print("72-byte password function succeeded!")
except Exception as e:
    print(f"72-byte password function failed: {type(e).__name__}: {e}")
