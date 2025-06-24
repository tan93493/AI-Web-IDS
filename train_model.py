import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import tensorflow as tf
import joblib
import os

LOG_FILE = 'logs/access.log'

# 1. Load và xử lý log
def load_data():
    data = []
    with open(LOG_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            timestamp = f"{parts[0]} {parts[1]}"
            ip = parts[2]
            method = parts[3]
            path = parts[4]
            label = 1 if method not in ['GET', 'POST'] or '/admin' in path else 0  # 1 = bất thường
            data.append([ip, method, path, label])
    df = pd.DataFrame(data, columns=['ip', 'method', 'path', 'label'])
    return df

# 2. Encode dữ liệu
def preprocess(df):
    enc_ip = LabelEncoder()
    enc_method = LabelEncoder()
    enc_path = LabelEncoder()

    df['ip'] = enc_ip.fit_transform(df['ip'])
    df['method'] = enc_method.fit_transform(df['method'])
    df['path'] = enc_path.fit_transform(df['path'])

    X = df[['ip', 'method', 'path']]
    y = df['label']

    os.makedirs('model', exist_ok=True)
    joblib.dump(enc_ip, 'model/ip_encoder.pkl')
    joblib.dump(enc_method, 'model/method_encoder.pkl')
    joblib.dump(enc_path, 'model/path_encoder.pkl')

    return train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Huấn luyện model
def train_model():
    df = load_data()
    X_train, X_test, y_train, y_test = preprocess(df)

    model = tf.keras.models.Sequential([
        tf.keras.layers.Input(shape=(3,)),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dense(8, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    model.fit(X_train, y_train, epochs=10, batch_size=8, validation_data=(X_test, y_test))
    model.save('model/ai_ids_model.h5')
    print("✅ Mô hình đã được huấn luyện và lưu.")

if __name__ == '__main__':
    train_model()
