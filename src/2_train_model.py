import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os

# =====================================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN
# =====================================================================
TRAIN_CSV = 'data/train.csv'
VAL_CSV = 'data/val.csv'
TEST_CSV = 'data/test.csv'
MODEL_DIR = 'models'
MODEL_PATH = os.path.join(MODEL_DIR, 'random_forest.pkl')

print("--- BẮT ĐẦU GIAI ĐOẠN 2: HUẤN LUYỆN NÃO BỘ AI ---")

# =====================================================================
# 2. NẠP DỮ LIỆU TỪ 3 TỆP CSV
# =====================================================================
print(">> Đang nạp ma trận dữ liệu vào RAM...")
try:
    train_df = pd.read_csv(TRAIN_CSV)
    val_df = pd.read_csv(VAL_CSV)
    test_df = pd.read_csv(TEST_CSV)
except FileNotFoundError as e:
    print(f"[LỖI] Không tìm thấy file CSV. Hãy chắc chắn bạn đã chạy file 1_collect_data.py trước. Chi tiết: {e}")
    exit()

# Tách Features (Tọa độ X, Y) và Label (Nhãn hành động)
X_train = train_df.iloc[:, :-1]
y_train = train_df.iloc[:, -1]

X_val = val_df.iloc[:, :-1]
y_val = val_df.iloc[:, -1]

X_test = test_df.iloc[:, :-1]
y_test = test_df.iloc[:, -1]

# =====================================================================
# 3. KHỞI TẠO VÀ DẠY THUẬT TOÁN RANDOM FOREST
# =====================================================================
print(f">> Bắt đầu huấn luyện Random Forest với {len(X_train)} mẫu dữ liệu...")
# n_estimators=100: Trồng 100 cây quyết định
# n_jobs=-1: Vắt kiệt sức mạnh của CPU để train cho nhanh
# class_weight='balanced': Vũ khí tối thượng xử lý việc thiếu hụt data nhãn Binh_Thuong
rf_model = RandomForestClassifier(
    n_estimators=100, 
    random_state=42, 
    n_jobs=-1,
    class_weight='balanced'
)

# Ép AI học bài
rf_model.fit(X_train, y_train)
print("   -> Quá trình học hoàn tất!")

# =====================================================================
# 4. CHẤM ĐIỂM NGHIỆM THU (EVALUATION)
# =====================================================================
print("\n--- BẢNG ĐIỂM NGHIỆM THU AI ---")

# 4.1. Thi thử trên tập Validation
y_val_pred = rf_model.predict(X_val)
val_acc = accuracy_score(y_val, y_val_pred)
print(f">> Độ chính xác trên tập kiểm định (Validation - 15%): {val_acc * 100:.2f}%")

# 4.2. Thi thật trên tập Test (Tập dữ liệu lạ 100%)
y_test_pred = rf_model.predict(X_test)
test_acc = accuracy_score(y_test, y_test_pred)
print(f">> Độ chính xác trên tập kiểm tra thực tế (Test - 15%): {test_acc * 100:.2f}%")

# 4.3. Xuất báo cáo chi tiết từng nhãn
print("\n>> Chi tiết báo cáo phân loại (Classification Report) trên tập Test:")
print(classification_report(y_test, y_test_pred))

# =====================================================================
# 5. ĐÓNG GÓI VÀ XUẤT BẢN NÃO BỘ (.pkl)
# =====================================================================
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

with open(MODEL_PATH, 'wb') as f:
    pickle.dump(rf_model, f)

print(f"\n[THÀNH CÔNG] Não bộ AI đã được đóng gói và lưu tại: {MODEL_PATH}")
print("--- HOÀN TẤT BƯỚC 2: SẴN SÀNG LẮP VÀO APP THỰC TẾ ---")