from passlib.context import CryptContext

# 模拟修改后的密码哈希函数
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def new_get_password_hash(password: str) -> str:
    """修复后的密码哈希函数"""
    # 限制密码长度不超过72个字符，防止bcrypt库报错
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

# 测试
print("Testing new function with long password...")
try:
    long_password = 'a' * 100
    print(f"Original password length: {len(long_password)}")
    new_hashed = new_get_password_hash(long_password)
    print("New function succeeded!")
except Exception as e:
    print(f"New function failed: {type(e).__name__}: {e}")

print("\nTesting new function with exactly 72-character password...")
try:
    exact_password = 'b' * 72
    print(f"Password length: {len(exact_password)}")
    exact_hashed = new_get_password_hash(exact_password)
    print("72-character password function succeeded!")
except Exception as e:
    print(f"72-character password function failed: {type(e).__name__}: {e}")

print("\nTesting new function with short password...")
try:
    short_password = 'c' * 10
    print(f"Password length: {len(short_password)}")
    short_hashed = new_get_password_hash(short_password)
    print("Short password function succeeded!")
except Exception as e:
    print(f"Short password function failed: {type(e).__name__}: {e}")
