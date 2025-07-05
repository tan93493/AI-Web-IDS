# train_model.py
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import tensorflow as tf
import joblib
import os

MODEL_DIR = 'model'
TRAINING_FILE = 'training_data_labeled.csv'
PREPROCESSOR_FILE = os.path.join(MODEL_DIR, 'preprocessor.pkl')
MODEL_FILE = os.path.join(MODEL_DIR, 'ai_ids_model.h5')

def load_and_preprocess():
    print(f"Đang đọc dữ liệu từ file '{TRAINING_FILE}'...")
    try:
        df = pd.read_csv(TRAINING_FILE)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file '{TRAINING_FILE}'.")
        return None, None, None
    df['payload'] = df['payload'].fillna('')
    df['path'] = df['path'].fillna('unknown')
    df['method'] = df['method'].fillna('unknown')
    df.dropna(subset=['label'], inplace=True)
    y = df['label'].astype(int)
    X = df[['method', 'path', 'payload']]
    preprocessor = ColumnTransformer(
        transformers=[
            ('payload_tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2)), 'payload'),
            ('path_onehot', OneHotEncoder(handle_unknown='ignore'), ['path']),
            ('method_onehot', OneHotEncoder(handle_unknown='ignore'), ['method'])
        ],
        remainder='drop'
    )
    print("Bắt đầu tiền xử lý và huấn luyện bộ preprocessor...")
    X_processed = preprocessor.fit_transform(X)
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(preprocessor, PREPROCESSOR_FILE)
    print(f"Đã lưu preprocessor vào file {PREPROCESSOR_FILE}")
    return X_processed, y, preprocessor.get_feature_names_out().shape[0]

def train_model():
    X, y, num_features = load_and_preprocess()
    if X is None:
        return
    if len(y.unique()) < 2:
        print("Lỗi: Dữ liệu huấn luyện cần có cả nhãn 0 và 1.")
        return
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    X_train_dense = X_train.toarray()
    X_test_dense = X_test.toarray()
    class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
    class_weights_dict = dict(enumerate(class_weights))
    print(f"Trọng số lớp được áp dụng: {class_weights_dict}")
    model = tf.keras.models.Sequential([
        tf.keras.layers.Input(shape=(num_features,)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ]) 
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    print("\nBắt đầu quá trình huấn luyện mô hình cuối cùng...")
    model.fit(X_train_dense, y_train,
              epochs=20,
              batch_size=32,
              validation_data=(X_test_dense, y_test),
              class_weight=class_weights_dict,
              verbose=2)           
    model.save(MODEL_FILE)
    print(f"\n✅ Mô hình CUỐI CÙNG đã được huấn luyện và lưu vào file {MODEL_FILE}")

if __name__ == '__main__':
    train_model()