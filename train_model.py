import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import tensorflow as tf
import joblib
import os
from app import create_app 
from models import Log

MODEL_DIR = 'model'

def load_data_from_db():
    print("Đang kết nối tới database qua SQLAlchemy...")
    app = create_app()
    with app.app_context():
        all_logs = Log.query.all()
        if not all_logs:
            print("Cảnh báo: Database log đang trống. Không có dữ liệu để huấn luyện.")
            return pd.DataFrame()
        logs_data = [
            {'ip': log.ip, 'method': log.method, 'path': log.path}
            for log in all_logs
        ]
        df = pd.DataFrame(logs_data)
    df['label'] = df.apply(
        lambda row: 1 if row['method'] not in ['GET', 'POST'] or '/admin' in row['path'] else 0,
        axis=1
    )
    print(f"Đã tải thành công {len(df)} bản ghi từ database.")
    return df

def preprocess(df):
    enc_ip = LabelEncoder()
    enc_method = LabelEncoder()
    enc_path = LabelEncoder()
    df['ip'] = enc_ip.fit_transform(df['ip'])
    df['method'] = enc_method.fit_transform(df['method'])
    df['path'] = enc_path.fit_transform(df['path'])
    X = df[['ip', 'method', 'path']]
    y = df['label']
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(enc_ip, os.path.join(MODEL_DIR, 'ip_encoder.pkl'))
    joblib.dump(enc_method, os.path.join(MODEL_DIR, 'method_encoder.pkl'))
    joblib.dump(enc_path, os.path.join(MODEL_DIR, 'path_encoder.pkl'))
    print("Đã lưu các bộ encoder.")
    min_class_count = y.value_counts().min()
    if min_class_count < 2:
        print("\nCảnh báo: Số lượng mẫu của lớp ít nhất là 1. Không thể chia stratify.")
        return train_test_split(X, y, test_size=0.2, random_state=42)
    else:
        return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

def train_model():
    df = load_data_from_db()
    if df.empty:
        return
    if len(df['label'].unique()) < 2:
        print("Lỗi: Dữ liệu huấn luyện chỉ chứa một loại nhãn.")
        return
    X_train, X_test, y_train, y_test = preprocess(df)
    model = tf.keras.models.Sequential([
        tf.keras.layers.Input(shape=(3,)),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(8, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])
    print("\nBắt đầu quá trình huấn luyện mô hình...")
    model.fit(X_train, y_train,
              epochs=15,
              batch_size=8,
              validation_data=(X_test, y_test),
              verbose=2)
    model.save(os.path.join(MODEL_DIR, 'ai_ids_model.h5'))
    print("\n Mô hình đã được huấn luyện và lưu thành công!")

if __name__ == '__main__':
    train_model()