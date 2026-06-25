import os
import shutil
from pathlib import Path

# Thư mục gốc
NEW_DATA_DIR = Path(r"d:\DEV_AI\nhan_nam_tay_va_chi_ngon_moi\train")
TARGET_DATA_DIR = Path(r"d:\DEV_AI\dataset_3class\train")  # Theo cấu trúc thư mục dataset_3class (wait, dataset_3class/images/train or dataset_3class/train?)
# Let's check dataset_3class structure. data.yaml says:
# train: images/train
# val: images/val
TARGET_IMAGES = Path(r"d:\DEV_AI\dataset_3class\images\train")
TARGET_LABELS = Path(r"d:\DEV_AI\dataset_3class\labels\train")

# Map class từ bộ mới sang bộ cũ (dataset_3class)
# Mới: 0 (Chi_Ngon_Tro), 1 (Nam_Tay)
# Cũ: 0 (Nam_Tay), 1 (Chi_Ngon_Tro), 2 (Xoe_Tay)
CLASS_MAP = {
    0: 1,  # Chi_Ngon_Tro -> Chi_Ngon_Tro
    1: 0,  # Nam_Tay -> Nam_Tay
}

def main():
    new_images_dir = NEW_DATA_DIR / "images"
    new_labels_dir = NEW_DATA_DIR / "labels"
    
    if not new_images_dir.exists() or not new_labels_dir.exists():
        print("Không tìm thấy thư mục images hoặc labels trong dataset mới.")
        return
        
    TARGET_IMAGES.mkdir(parents=True, exist_ok=True)
    TARGET_LABELS.mkdir(parents=True, exist_ok=True)
    
    copied_count = 0
    modified_labels_count = 0
    
    for label_file in new_labels_dir.glob("*.txt"):
        # Đọc nội dung file label
        with open(label_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        new_lines = []
        for line in lines:
            line = line.strip()
            if not line: continue
            parts = line.split()
            old_class = int(float(parts[0]))
            
            if old_class in CLASS_MAP:
                new_class = CLASS_MAP[old_class]
                new_lines.append(f"{new_class} " + " ".join(parts[1:]))
                modified_labels_count += 1
            else:
                # Nếu có class lạ, giữ nguyên hoặc bỏ qua
                print(f"Warning: Unknown class {old_class} in {label_file.name}")
                
        # Lưu vào thư mục target
        target_label_path = TARGET_LABELS / label_file.name
        with open(target_label_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
            
        # Copy ảnh tương ứng
        image_name = label_file.stem + ".jpg" # Roboflow thường dùng .jpg
        source_image = new_images_dir / image_name
        
        if not source_image.exists():
            # Thử các extension khác nếu không phải jpg
            for ext in [".jpeg", ".png", ".webp", ".bmp"]:
                alt_image = new_images_dir / (label_file.stem + ext)
                if alt_image.exists():
                    source_image = alt_image
                    break
                    
        if source_image.exists():
            target_image_path = TARGET_IMAGES / source_image.name
            shutil.copy2(source_image, target_image_path)
            copied_count += 1
        else:
            print(f"Không tìm thấy ảnh cho label {label_file.name}")
            
    print(f"Hoàn thành! Đã copy {copied_count} ảnh và xử lý {modified_labels_count} bounding boxes.")

if __name__ == "__main__":
    main()
