# Dàn ý slide báo cáo nhận diện cử chỉ tay

## Trạng thái mới của bài

- Model chính: `D:/DEV_AI/best (1).pt`.
- `best.pt` cũ không còn được lệnh chạy mặc định sử dụng.
- Model online nhận diện chữ tay ASL 21 class. Hệ thống map sang cử chỉ:
  - `A/S` -> `Nam_Tay` -> bật/tắt đèn.
  - `D/G/L` -> `Chi_Ngon_Tro` -> điều chỉnh giường.
  - `B` -> `Xoe_Tay` -> SOS.
  - Class khác hoặc không có detection -> `Binh_Thuong`.

## Dataset

- Tổng ảnh: `1510`.
- Huấn luyện: `1208` ảnh.
- Thử nghiệm/Val: `302` ảnh.
- Chưa có thư mục test riêng.

Ảnh chèn:

- `docs/assets/dataset_summary_table.png`
- `docs/assets/class_distribution.png`
- `docs/assets/split_distribution.png`

## Visualize và phương pháp

- Visualize tạo bằng Matplotlib trong `scripts/generate_report_assets.py`.
- Phương pháp chính là YOLO object detection vì cần bbox + class theo thời gian thực.
- CNN 1D, CNN 2D, CNN 3D, Transformer được trình bày ở phần so sánh mô hình.
- CLIP được trình bày như hướng text + ảnh trong nghiên cứu liên quan, không dùng làm app realtime.

Ảnh chèn:

- `docs/assets/method_selection.png`
- `docs/assets/model_family_comparison.png`
- `docs/assets/clip_text_image.png`

## Mô hình và trích xuất đặc trưng

- YOLOv8x ASL trong `best (1).pt` trích xuất đặc trưng qua backbone.
- Detect head trả bbox, class ASL và confidence.
- Hệ thống map ASL sang cử chỉ, sau đó dùng buffer + dwell time để chống kích hoạt nhầm.

Ảnh chèn:

- `docs/assets/model_mapping_asl_to_gestures.png`
- `docs/assets/feature_extraction_pipeline.png`
- `docs/assets/architecture_diagram.png`

## Thử nghiệm và đánh giá

Các chỉ số được đo theo mapping ASL -> cử chỉ trên tập `dataset/images/val`; đây là proxy evaluation vì chưa có dataset ASL gốc đi kèm model online.

| Chỉ số | Giá trị |
|---|---:|
| Accuracy | 0.328 |
| F1-Score | 0.247 |
| IoU | 0.834 |
| mAP@0.5 | 0.081 |
| mAP@0.5:0.95 | 0.057 |
| FLOPs 320 | 64.56 GFLOPs |
| FLOPs 640 | 258.23 GFLOPs |
| Parameter | 68,172,831 |
| Inference time CPU | 480.8 ms @320 |

Ảnh chèn:

- `docs/assets/metrics_summary.png`
- `docs/assets/confusion_matrix_mapped.png`
- `docs/assets/confusion_matrix_mapped_normalized.png`
- `docs/assets/tsne_features.png`

## Thứ tự slide gợi ý

1. Tiêu đề đề tài.
2. Đặt vấn đề.
3. Phát biểu bài toán.
4. Dataset.
5. Thống kê nhãn.
6. Visualize dataset.
7. Lựa chọn phương pháp.
8. So sánh CNN 1D, CNN 2D, CNN 3D, Transformer.
9. CLIP text + ảnh.
10. Model YOLOv8x ASL và mapping cử chỉ.
11. Trích xuất đặc trưng.
12. Thử nghiệm và đánh giá.
13. Ma trận nhầm lẫn.
14. t-SNE.
15. Xây dựng hệ thống.
16. Demo.
17. Kết luận.
