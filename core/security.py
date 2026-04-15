import os
from cryptography.fernet import Fernet

# 为了生产安全，密钥应由环境变量提供或存储在安全的地方
# 这里我们在本地生成一个 key 文件，模拟生产中的密钥存储
KEY_FILE = "anyops.key"

def load_or_generate_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key

FERNET = Fernet(load_or_generate_key())

def encrypt(text: str) -> str:
    """加密文本为字符串"""
    if not text:
        return ""
    return FERNET.encrypt(text.encode()).decode()

def decrypt(token: str) -> str:
    """解密 token 字符串为原文"""
    if not token:
        return ""
    try:
        return FERNET.decrypt(token.encode()).decode()
    except Exception:
        # 如果解密失败（可能是未加密的旧数据），原样返回以便过渡
        return token
