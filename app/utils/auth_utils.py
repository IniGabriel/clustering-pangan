import bcrypt
import random
import string

def hash_password(plain_password):
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))
