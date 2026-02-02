from cryptography.fernet import Fernet
import base64

def converter(sigma_string, key):
    key_fixed = str(key).ljust(32)[:32] 
    b64_key = base64.b64encode(key_fixed.encode("utf-8"))
    
    try:
        sigma_fernet = Fernet(b64_key)

        clean_string = sigma_string.strip('\r\n') 

        token = sigma_fernet.encrypt(clean_string.encode("utf-8"))

        bits = ''.join(format(byte, '08b') for byte in token)
        
        return bits
    except Exception as e:
        return f"Ошибка при подготовке бит: {str(e)}"
