import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import tensorflow as tf
import joblib
import os
import sqlite3

# Đường dẫn tới file database SQLite
LOG_DB = 'logs/access.db'
MODEL_DIR = 'model'

# 1. Tải và xử lý dữ liệu từ SQLite
def load_data_from_db():
    """
    Kết nối tới database SQLite, đọc dữ liệu log và chuyển thành DataFrame.
    Áp dụng logic gán nhãn tương tự phiên bản cũ.
    """
    # Kiểm tra xem file database có tồn tại không
    if not os.path.exists(LOG_DB):
        print(f"Lỗi: Không tìm thấy tệp cơ sở dữ liệu tại '{LOG_DB}'.")
        print("Vui lòng chạy app.py để tạo một vài log trước khi huấn luyện.")
        return pd.DataFrame() # Trả về DataFrame rỗng nếu không có file

    # Kết nối tới database và đọc dữ liệu bằng pandas
    try:
        conn = sqlite3.connect(LOG_DB)
        # Lấy tất cả các bản ghi từ bảng 'logs'
        df = pd.read_sql_query("SELECT ip, method, path FROM logs", conn)
        conn.close()
    except Exception as e:
        print(f"Đã xảy ra lỗi khi đọc database: {e}")
        return pd.DataFrame()

    if df.empty:
        print("Cảnh báo: Database log đang trống. Không có dữ liệu để huấn luyện.")
        return df

    # Áp dụng logic gán nhãn: 1 = bất thường, 0 = bình thường
    # Một yêu cầu được coi là bất thường nếu phương thức khác GET/POST hoặc truy cập vào đường dẫn chứa '/admin'
    df['label'] = df.apply(
        lambda row: 1 if row['method'] not in ['GET', 'POST'] or '/admin' in row['path'] else 0,
        axis=1
    )
    print(f"Đã tải thành công {len(df)} bản ghi từ database.")
    return df

# 2. Tiền xử lý và encode dữ liệu
def preprocess(df):
    """
    Encode các cột dạng chữ thành số để mô hình có thể học.
    Lưu lại các bộ encoder để sử dụng trong lúc dự đoán.
    """
    enc_ip = LabelEncoder()
    enc_method = LabelEncoder()
    enc_path = LabelEncoder()

    # Fit và transform dữ liệu
    df['ip'] = enc_ip.fit_transform(df['ip'])
    df['method'] = enc_method.fit_transform(df['method'])
    df['path'] = enc_path.fit_transform(df['path'])

    X = df[['ip', 'method', 'path']]
    y = df['label']

    # Tạo thư mục model nếu chưa tồn tại
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Lưu các bộ encoder
    joblib.dump(enc_ip, os.path.join(MODEL_DIR, 'ip_encoder.pkl'))
    joblib.dump(enc_method, os.path.join(MODEL_DIR, 'method_encoder.pkl'))
    joblib.dump(enc_path, os.path.join(MODEL_DIR, 'path_encoder.pkl'))
    print("Đã lưu các bộ encoder.")

    # [FIX] Kiểm tra xem có thể chia dữ liệu theo tỷ lệ (stratify) được không
    min_class_count = y.value_counts().min()
    if min_class_count < 2:
        print("\nCảnh báo: Số lượng mẫu của lớp ít nhất chỉ là 1.")
        print("Không thể thực hiện chia dữ liệu theo tỷ lệ (stratify).")
        print("Tiến hành chia dữ liệu thông thường. Kết quả mô hình có thể không tối ưu.")
        print("Gợi ý: Hãy tạo thêm dữ liệu, đặc biệt là các truy cập 'bất thường' (ví dụ: vào trang /admin).\n")
        return train_test_split(X, y, test_size=0.2, random_state=42)
    else:
        # Nếu đủ dữ liệu, chia theo tỷ lệ để đảm bảo cân bằng
        return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


# 3. Huấn luyện và lưu model
def train_model():
    """
    Hàm chính điều phối toàn bộ quá trình: tải dữ liệu, tiền xử lý và huấn luyện.
    """
    df = load_data_from_db()

    # Dừng lại nếu không có dữ liệu để huấn luyện
    if df.empty:
        return

    # Kiểm tra xem có đủ cả hai loại nhãn không
    if len(df['label'].unique()) < 2:
        print("Lỗi: Dữ liệu huấn luyện chỉ chứa một loại nhãn. Cần cả log 'bình thường' và 'bất thường'.")
        print("Hãy thử tạo thêm các truy cập vào trang '/admin' để tạo log bất thường.")
        return

    # Thực hiện tiền xử lý và chia dữ liệu
    X_train, X_test, y_train, y_test = preprocess(df)

    # Xây dựng mô hình mạng nơ-ron
    model = tf.keras.models.Sequential([
        tf.keras.layers.Input(shape=(3,)),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dropout(0.2), # Thêm dropout để giảm overfitting
        tf.keras.layers.Dense(8, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid') # Output layer cho bài toán phân loại nhị phân
    ])

    # Biên dịch mô hình
    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])
    
    print("\nBắt đầu quá trình huấn luyện mô hình...")
    # Huấn luyện mô hình
    model.fit(X_train, y_train,
              epochs=15,  # Tăng số epochs để mô hình học tốt hơn
              batch_size=8,
              validation_data=(X_test, y_test),
              verbose=2)

    # Lưu mô hình đã huấn luyện
    model.save(os.path.join(MODEL_DIR, 'ai_ids_model.h5'))
    print("\n✅ Mô hình đã được huấn luyện và lưu thành công!")

if __name__ == '__main__':
    train_model()
