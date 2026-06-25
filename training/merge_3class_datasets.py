import os
import shutil
import sys
import yaml
import zipfile
from pathlib import Path

# Đảm bảo mã hóa console là utf-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Cấu hình class ID đích của dự án
TARGET_CLASSES = {
    "Nam_Tay": 0,
    "Chi_Ngon_Tro": 1,
    "Xoe_Tay": 2
}

def read_class_mapping(dataset_dir: Path):
    """Đọc cấu hình names từ file data.yaml của dataset nguồn"""
    yaml_path = dataset_dir / "data.yaml"
    if not yaml_path.exists():
        # Thử tìm ở thư mục cha
        yaml_path = dataset_dir.parent / "data.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"Khong tim thay data.yaml o {dataset_dir}")
            
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    names = data.get("names", {})
    # Chuẩn hóa key thành int và value thành tên chuẩn
    mapping = {}
    for k, v in names.items():
        # Chuẩn hóa tên class để so khớp (ví dụ: 'chi_ngon_tro' -> 'Chi_Ngon_Tro')
        normalized_name = v.strip()
        if normalized_name.lower() in ["nam_tay", "fist", "nam-tay"]:
            mapping[int(k)] = "Nam_Tay"
        elif normalized_name.lower() in ["chi_ngon_tro", "pointing", "chi_ngon", "chi-ngon-tro"]:
            mapping[int(k)] = "Chi_Ngon_Tro"
        elif normalized_name.lower() in ["xoe_tay", "open_hand", "xoe-tay"]:
            mapping[int(k)] = "Xoe_Tay"
        else:
            mapping[int(k)] = normalized_name
    return mapping

def remap_and_copy(src_dir: Path, dest_dir: Path, src_mapping: dict):
    """Di chuyển, sửa lại class ID trong file txt và copy vào thư mục đích"""
    print(f"\nDang xu ly dataset tu: {src_dir.name}")
    print(f"  -> Mapping goc phat hien: {src_mapping}")
    
    # Duyệt qua các tập train / val
    for split in ["train", "val", "valid"]:
        dest_split = "val" if split in ["val", "valid"] else "train"
        
        # Tìm thư mục images nguồn
        src_img_dir = src_dir / "images" / split
        if not src_img_dir.exists():
            src_img_dir = src_dir / split / "images"
        if not src_img_dir.exists():
            continue
            
        src_lbl_dir = src_img_dir.parent / "labels"
        if not src_lbl_dir.exists():
            src_lbl_dir = src_dir / "labels" / split
            
        dest_img_dir = dest_dir / "images" / dest_split
        dest_lbl_dir = dest_dir / "labels" / dest_split
        
        dest_img_dir.mkdir(parents=True, exist_ok=True)
        dest_lbl_dir.mkdir(parents=True, exist_ok=True)
        
        copied_count = 0
        for img_path in src_img_dir.glob("*"):
            if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp"]:
                continue
                
            # Copy ảnh sang thư mục đích
            dest_img_path = dest_img_dir / img_path.name
            shutil.copy2(img_path, dest_img_path)
            
            # Sửa đổi file nhãn tương ứng (.txt)
            lbl_path = src_lbl_dir / f"{img_path.stem}.txt"
            dest_lbl_path = dest_lbl_dir / f"{img_path.stem}.txt"
            
            if lbl_path.exists():
                lines = lbl_path.read_text(encoding="utf-8").splitlines()
                new_lines = []
                for line in lines:
                    parts = line.split()
                    if not parts:
                        continue
                    old_cls_id = int(parts[0])
                    class_name = src_mapping.get(old_cls_id)
                    
                    if class_name in TARGET_CLASSES:
                        new_cls_id = TARGET_CLASSES[class_name]
                        parts[0] = str(new_cls_id)
                        new_lines.append(" ".join(parts))
                
                dest_lbl_path.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
            else:
                # Nếu là ảnh background (không nhãn), tạo file txt trống
                dest_lbl_path.write_text("", encoding="utf-8")
                
            copied_count += 1
        print(f"  - {dest_split}: Da copy & remap {copied_count} anh/nhan.")

def main():
    # Nhập đường dẫn
    old_dir_str = input("Nhap duong dan den thu muc dataset CU (da giai nen): ").strip()
    new_dir_str = input("Nhap duong dan den thu muc dataset MOI (da giai nen): ").strip()
    
    old_dir = Path(old_dir_str)
    new_dir = Path(new_dir_str)
    output_dir = Path("D:/DEV_AI/dataset_3class")
    zip_output_path = Path("D:/DEV_AI/dataset_3class.zip")
    
    if not old_dir.exists():
        print(f"[-] Khong tim thay thu muc cu: {old_dir}")
        return
    if not new_dir.exists():
        print(f"[-] Khong tim thay thu muc moi: {new_dir}")
        return
        
    # Đọc mapping
    try:
        old_mapping = read_class_mapping(old_dir)
        new_mapping = read_class_mapping(new_dir)
    except Exception as e:
        print(f"[-] Loi doc data.yaml: {e}")
        return
        
    # Tạo sạch thư mục đầu ra
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Thực hiện copy và remap
    remap_and_copy(old_dir, output_dir, old_mapping)
    remap_and_copy(new_dir, output_dir, new_mapping)
    
    # Tạo file data.yaml đích
    data_yaml_content = f"""path: /content/dataset
train: images/train
val: images/val

names:
  0: Nam_Tay
  1: Chi_Ngon_Tro
  2: Xoe_Tay
"""
    (output_dir / "data.yaml").write_text(data_yaml_content, encoding="utf-8")
    print(f"\n[+] Da tao xong data.yaml tai: {output_dir / 'data.yaml'}")
    
    # Nén file zip cho Colab
    print("Dang nen dataset thanh file dataset_3class.zip...")
    if zip_output_path.exists():
        zip_output_path.unlink()
        
    with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = Path(root) / file
                # Giữ nguyên cấu trúc thư mục con từ dataset_3class
                arcname = Path("dataset") / file_path.relative_to(output_dir)
                zipf.write(file_path, arcname)
                
    print(f"\n🎉 HOÀN THÀNH GỘP DATASET!")
    print(f"-> Thư mục gộp: {output_dir}")
    print(f"-> File ZIP sẵn sàng cho Colab: {zip_output_path}")

if __name__ == "__main__":
    main()
