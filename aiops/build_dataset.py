import pandas as pd
import glob
import os

# Tìm tất cả các file CSV thu thập được trong thư mục data/
files = sorted(glob.glob("data/dataset_label*.csv"))
print(f"Tìm thấy {len(files)} file dữ liệu thành phần:")

dfs = []
for f in files:
    df = pd.read_csv(f)
    
    # Quy trình làm sạch dữ liệu (Data Cleaning):
    # 1. Bỏ dòng đầu tiên của mỗi file (tránh nhiễu cho thuộc tính delta)
    # 2. Loại bỏ hoàn toàn 3 cột rỗng không có data để tránh gây nhiễu cho mô hình AI
    cols_to_drop = ['http_error_rate', 'p99_latency_ms', 'rabbitmq_queue']
    df_cleaned = df.iloc[1:].drop(columns=[c for c in cols_to_drop if c in df.columns], errors='ignore').copy()
    
    print(f"  -> {os.path.basename(f):55s} | Kích thước: {len(df_cleaned):3d} dòng | Nhãn: {sorted(df_cleaned['label'].unique())}")
    dfs.append(df_cleaned)

# Gộp tất cả các hiệp dữ liệu lại thành một tập duy nhất
combined = pd.concat(dfs, ignore_index=True)

print(f"\n=======================================================")
print(f"TỔNG KẾT TIỀN XỬ LÝ DỮ LIỆU")
print(f"=======================================================")
print(f"Tổng số mẫu thu hái được: {len(combined)} dòng dữ liệu.")
print(f"Số lượng thuộc tính sử dụng để huấn luyện AI: {len(combined.columns)} cột.")

print("\n[Phân phối số lượng mẫu theo từng Nhãn]:")
label_mapping = {0: "Nhãn 0 (Bình thường)", 1: "Nhãn 1 (Bão Traffic)", 2: "Nhãn 2 (Lỗi Hệ Thống)"}
distribution = combined['label'].value_counts().sort_index()
for lbl, count in distribution.items():
    print(f"  + {label_mapping.get(lbl, f'Nhãn {lbl}')}: {count} mẫu")

# Kiểm tra giá trị rỗng (Missing values) phòng hờ hệ thống gặp lỗi khi trích xuất
missing_summary = combined.isnull().sum()
if missing_summary.any():
    print(f"\n[Cảnh báo] Phát hiện dữ liệu trống tại các cột:\n{missing_summary[missing_summary > 0]}")
else:
    print("\n[OK] Kiểm tra tính toàn vẹn: Dữ liệu sạch, không có giá trị trống (Missing values).")

# Xuất ra file dataset cuối cùng
output_filename = "data/dataset_final.csv"  
combined.to_csv(output_filename, index=False)
print(f"\n[THÀNH CÔNG] Đã đóng gói tập dữ liệu chuẩn: {output_filename}")
print(f"Danh sách các đặc trưng (Features): {list(combined.columns)}")