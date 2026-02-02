import os
from PIL import Image
import core.encrypter as encrypter

def start_injection(image_path, text_to_hide, key, custom_save_path):
    try:
        img = Image.open(image_path).convert("RGB")
        pixels = img.load()
        width, height = img.size

        bits = encrypter.converter(text_to_hide, key)
        
        bit_index = 0
        total_bits = len(bits)

        if total_bits > width * height:
            return "Too much text"

        for y in range(height):
            for x in range(width):
                if bit_index < total_bits:
                    r, g, b = pixels[x, y]
                    
                    # LSB Method ( Least Significant Bit )
                    r = (r & 0xFE) | int(bits[bit_index])
                    bit_index += 1
                    
                    pixels[x, y] = (r, g, b)
                else:
                    break
        
        img.save(custom_save_path)
        
        return f"Saved file: {custom_save_path}"

    except Exception as e:
        return f"Error: {str(e)}"
