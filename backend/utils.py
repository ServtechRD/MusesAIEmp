from datetime import datetime

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


def log(message):
    # 獲取當前日期和時間
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 如果訊息是字串，直接打印
    if isinstance(message, str):
        print(f"{current_time}\t{message}")
    else:
        # 如果不是字串，使用 repr() 來轉換對象為字串
        print(f"{current_time}")
        print(repr(message))
