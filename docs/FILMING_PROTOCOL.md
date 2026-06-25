# Kịch bản quay video (4 cử chỉ)

Lưu file vào `data/raw_videos/`:

| File video | Class |
|------------|-------|
| `binh_thuong.mp4` | Binh_Thuong |
| `nam_tay.mp4` | Nam_Tay |
| `chi_ngon.mp4` | Chi_Ngon_Tro |
| `xoe_tay.mp4` | Xoe_Tay |

## Thiết lập camera

- Gắn cố định, ngang tầm ngực–mặt (mô phỏng webcam trước giường bệnh).
- Khoảng cách tay–ống kính: **0.8–1.2 m**.
- Ánh sáng đủ, nền đơn giản, tránh ngược sáng.
- Mỗi video **2–4 phút**.

## Quy trình trong mỗi video

1. Làm cử chỉ rõ ràng.
2. Giữ **3–5 giây**.
3. Về tư thế nghỉ 2–3 giây.
4. Đổi nhẹ: tay trái/phải, cao/thấp trong khung, nghiêng 15–30°.
5. Lặp **15–25 lần** / video (trừ Binh_Thuong: nhiều cảnh tay tự nhiên).

## Mô tả từng cử chỉ

### Binh_Thuong

- Tay thả lỏng trên chăn/đùi.
- Có thể di chuyển nhẹ nhưng **không** nắm tay / chỉ ngón / xòe tay.

### Nam_Tay

- Nắm chặt, lòng bàn tay có thể hướng hoặc nghiêng camera.

### Chi_Ngon_Tro

- Chỉ **ngón trỏ** duỗi thẳng, các ngón khác co.
- Tránh cử chỉ “OK” hoặc “số 2”.

### Xoe_Tay

- Xòe đủ 5 ngón, bàn tay mở rộng rõ.

## Sau khi quay

Chạy: `python training/01_extract_frames.py`

Mục tiêu: **400–800 ảnh / class** sau khi trích frame.
