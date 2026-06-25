import pandas as pd
import os

files = {
    'Huấn luyện (Train)': 'data/train.csv',
    'Kiểm định (Val)': 'data/val.csv',
    'Thử nghiệm (Test)': 'data/test.csv'
}

print("--- BÁO CÁO THỐNG KÊ DATASET NHÓM 11 ---")
total_samples = 0

for name, path in files.items():
    if os.path.exists(path):
        df = pd.read_csv(path)
        count = len(df)
        total_samples += count
        print(f"\n[+] {name}:")
        print(f"   - Tổng số mẫu: {count}")
        
        label_col = df.columns[-1] 
        print(f"   - Tên cột nhãn đang dùng: '{label_col}'")
        print("   - Phân bổ dữ liệu:")
        print(df[label_col].value_counts())
    else:
        print(f"[!] Không tìm thấy file {path}")

print(f"\n==> TỔNG CỘNG TOÀN BỘ DATASET: {total_samples} mẫu")