import pywt
import numpy as np
from PIL import Image

def bytes_to_bits(data_bytes):
    return ''.join(format(byte, '08b') for byte in data_bytes)

def encode_message(image_path, message_file_path, output_path, wavelet='haar', subband='LH'):
    img = Image.open(image_path)
    img_array = np.array(img, dtype=np.float64)

    if img_array.shape[2] == 4:
        has_alpha = True
        alpha_channel = img_array[:, :, 3]
    else:
        has_alpha = False

    red_channel = img_array[:, :, 0]
    green_channel = img_array[:, :, 1]
    blue_channel = img_array[:, :, 2]

    if red_channel.shape[0] % 2 != 0 or red_channel.shape[1] % 2 != 0:
        raise ValueError("Kích thước ảnh phải chẵn để thực hiện DWT.")

    with open(message_file_path, 'rb') as file:
        message_bytes = file.read()

    message_bits = bytes_to_bits(message_bytes)
    message_length = len(message_bits)
    if message_length > (2**32 - 1):
        raise ValueError("Tin nhắn quá dài.")

    length_bits = format(message_length, '032b')
    all_bits = length_bits + message_bits

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
    if len(all_bits) > len(flat_subband):
        raise ValueError("Dữ liệu quá lớn để nhúng vào ảnh.")

    for i, bit in enumerate(all_bits):
        coeff = flat_subband[i]
        integer_part = int(coeff)
        fractional_part = coeff - integer_part
        new_integer = (integer_part & ~1) | int(bit)
        flat_subband[i] = new_integer + fractional_part

    modified_subband = flat_subband.reshape(selected_subband.shape)

    if subband == 'LH':
        modified_coeffs_red = (cA_red, (modified_subband, cV_red, cD_red))
    elif subband == 'HL':
        modified_coeffs_red = (cA_red, (cH_red, modified_subband, cD_red))
    else:
        modified_coeffs_red = (cA_red, (cH_red, cV_red, modified_subband))

    stego_red = pywt.idwt2(modified_coeffs_red, wavelet)

    if has_alpha:
        stego_array = np.stack([stego_red, green_channel, blue_channel, alpha_channel], axis=-1)
    else:
        stego_array = np.stack([stego_red, green_channel, blue_channel], axis=-1)

    stego_array = np.clip(stego_array, 0, 255).astype(np.uint8)
    Image.fromarray(stego_array).save(output_path)
    print("✅ Mã hóa thành công.")

encode_message("input.png", "encrypted.bin", "stego_output.png")