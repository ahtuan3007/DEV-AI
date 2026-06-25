# Overleaf Report - AFOSR ATC 2021 July

## Hướng dẫn sử dụng trên Overleaf

### Cách 1: Upload trực tiếp
1. Truy cập [Overleaf](https://www.overleaf.com)
2. Tạo **New Project** → **Blank Project**
3. Xóa nội dung file `main.tex` mặc định
4. Copy toàn bộ nội dung file `main.tex` trong thư mục này vào
5. Tạo thư mục `figures/` trên Overleaf
6. Upload tất cả ảnh trong thư mục `figures/` vào thư mục `figures/` trên Overleaf
7. Nhấn **Recompile** để xem kết quả

### Cách 2: Upload dạng ZIP
1. Nén toàn bộ thư mục `overleaf_report` thành file `.zip`
2. Truy cập Overleaf → **New Project** → **Upload Project**
3. Upload file `.zip`
4. Nhấn **Recompile**

## Cấu trúc thư mục

```
overleaf_report/
├── main.tex              # File LaTeX chính
├── README.md             # File hướng dẫn này
└── figures/              # Thư mục chứa ảnh
    ├── fig1_prototype.png
    ├── fig2_postures.png
    ├── fig3_datacollection.png
    ├── fig4_examples.png
    ├── fig6_framework.png
    ├── fig7_curves.png
    ├── fig8_confusion.png
    └── fig9_outputs.png
```

## Lưu ý
- Bài báo sử dụng format **IEEE Conference** (`IEEEtran`)
- Overleaf có sẵn class `IEEEtran`, không cần cài thêm
- Các ảnh được tạo bằng AI để minh họa, bạn có thể thay thế bằng ảnh gốc từ nghiên cứu
