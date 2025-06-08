import pywt
import numpy as np
from PIL import Image

def bits_to_bytes(binary_str):
    byte_array = bytearray()
    for i in range(0, len(binary_str), 8):
        byte_str = binary_str[i:i+8]
        if len(byte_str) < 8:
            byte_str = byte_str.ljust(8, '0')
        byte_array.append(int(byte_str, 2))
    return bytes(byte_array)

def decode_message(image_path, output_file_path, wavelet='haar', subband='LH'):
    img = Image.open(image_path)
    img_array = np.array(img, dtype=np.float64)

    if img_array.shape[0] % 2 != 0 or img_array.shape[1] % 2 != 0:
        raise ValueError("Kích thước ảnh phải chẵn để thực hiện DWT.")

    red_channel = img_array[:, :, 0]
    coeffs_red = pywt.dwt2(red_channel, wavelet)
    cA_red, (cH_red, cV_red, cD_red) = coeffs_red

    if subband == 'LH':
        selected_subband = cH_red
    elif subband == 'HL':
        selected_subband = cV_red
    elif subband == 'HH':
        selected_subband = cD_red
    else:
        raise ValueError("Subband không hợp lệ.")

    flat_subband = selected_subband.flatten()
    length_bits = ''.join(str(int(coeff) & 1) for coeff in flat_subband[:32])
    message_length = int(length_bits, 2)

    if message_length < 0 or message_length > len(flat_subband) - 32:
        raise ValueError("Độ dài tin nhắn không hợp lệ.")

    message_bits = ''.join(str(int(flat_subband[i]) & 1) for i in range(32, 32 + message_length))
    decoded_bytes = bits_to_bytes(message_bits)

    with open(output_file_path, 'wb') as file:
        file.write(decoded_bytes)

    print(f"✅ Giải mã thành công. Đã lưu vào {output_file_path}")
    return decoded_bytes

decode_message("stego_output.png", "recovered_secret.bin")