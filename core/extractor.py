import os
import numpy as np
import base64
from PIL import Image
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Загружаем .env на случай, если ключ не передан из GUI
load_dotenv()

# Вспомогательная функция конвертации битов в байты
def bits_to_bytes(bits):
    all_bytes = b""
    for i in range(0, len(bits), 8):
        byte_str = bits[i:i+8]
        if len(byte_str) < 8:
            break
        byte_val = int(byte_str, 2)
        all_bytes += bytes([byte_val])
    return all_bytes

# Функционал декриптора для гуишки
def start_decryption(image_path, key_text=None):
    try:
        if not key_text:
            key_text = os.getenv("FERNET_KEY")
        
        if not key_text:
            return "Ошибка: Ключ не найден ни в GUI, ни в .env"

        
        b64_key = base64.b64encode(key_text.encode("utf-8")[:32])
        sigma_fernet = Fernet(b64_key)

        if not os.path.exists(image_path):
            return f"Ошибка: Файл {image_path} не найден"

        img = Image.open(image_path).convert("RGB")
        img_array = np.array(img)

        extracted_bits_array = img_array[:, :, 0] & 1
        
        extracted_bits = "".join(extracted_bits_array.flatten().astype(str))

        token = bits_to_bytes(extracted_bits)

        decrypted_bytes = sigma_fernet.decrypt(token)
        
        return decrypted_bytes.decode("utf-8")

    except Exception as e:
        error_msg = str(e)
        if "InvalidToken" in error_msg:
            return "Ошибка: Неверный ключ или данные в картинке повреждены."
        return f"Произошла ошибка: {error_msg}"

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(__file__))
    test_path = os.path.join(project_root, "encoded_secret.png")
    
    result = start_decryption(test_path)
    print(f"Результат: {result}")
