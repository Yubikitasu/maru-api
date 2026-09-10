import requests
from io import BytesIO
from colorthief import ColorThief
import colorsys

def extract_vibrant_colors(image_url):
    # 1. Tải hình ảnh từ URL
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi tải ảnh: {e}")
        return None

    # Load dữ liệu ảnh vào ColorThief
    image_stream = BytesIO(response.content)
    color_thief = ColorThief(image_stream)

    # 2. Lấy bảng 10 màu chủ đạo nhất từ hình ảnh (RGB)
    palette = color_thief.get_palette(color_count=10)

    vibrant = [0.0, 0.0]
    light_vibrant = [0.0, 0.0]
    
    max_vibrant_sat = -1
    max_light_sat = -1

    # 3. Phân tích các màu để tìm HSLVibrant và HSLLightVibrant
    for r, g, b in palette:
        # Chuyển đổi RGB (0-255) sang HLS (0-1) bằng colorsys chuẩn của Python
        h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)

        # Lọc màu Vibrant: Độ sáng (Lightness) vừa phải (0.3 - 0.7), ưu tiên độ bão hòa (Saturation) cao nhất
        if 0.3 <= l <= 0.7 and s > max_vibrant_sat:
            max_vibrant_sat = s
            vibrant = [round(h, 2), round(s, 2)] # Giữ lại 2 số thập phân

        # Lọc màu Light Vibrant: Độ sáng cao (> 0.7), ưu tiên độ bão hòa cao nhất
        if l > 0.7 and s > max_light_sat:
            max_light_sat = s
            light_vibrant = [round(h, 2), round(s, 2)]

    # 4. Xuất ra dictionary theo định dạng yêu cầu
    user_data = {
        "HSLVibrant": vibrant,
        "HSLLightVibrant": light_vibrant
    }
    
    return user_data

