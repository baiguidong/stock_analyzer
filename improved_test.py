from passlib.context import CryptContext

# 模拟原来的密码哈希函数
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_password_length():
    """测试密码长度处理"""
    # 测试不同长度的密码
    for length in [50, 72, 73, 100, 200]:
        password = 'a' * length
        utf8_length = len(password.encode('utf-8'))
        print(f"Password length: {length}, UTF-8 bytes: {utf8_length}")
        
        # 截断到72字节
        if utf8_length > 72:
            # 先编码为bytes再截断
            truncated_bytes = password.encode('utf-8')[:72]
            # 尝试解码，可能失败
            try:
                truncated_password = truncated_bytes.decode('utf-8')
                print(f"  Truncated to {len(truncated_password)} chars, {len(truncated_password.encode('utf-8'))} bytes")
                
                # 尝试哈希
                try:
                    hashed = pwd_context.hash(truncated_password)
                    print(f"  Hash success")
                except Exception as e:
                    print(f"  Hash failed: {e}")
                    
            except Exception as e:
                print(f"  Decode failed: {e}")
        else:
            print(f"  No truncation needed")
        print()

test_password_length()
