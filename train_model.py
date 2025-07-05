import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from scipy.sparse import hstack
import tensorflow as tf
import joblib
import os

MODEL_DIR = 'model'
TRAINING_FILE = 'training_data_labeled.csv'

def load_and_preprocess():
    print(f"Đang đọc dữ liệu từ file '{TRAINING_FILE}'...")
    try:
        df = pd.read_csv(TRAINING_FILE)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file '{TRAINING_FILE}'.")
        return None, None
    df['text_features'] = df['path'].fillna('') + ' ' + df['payload'].fillna('')
    vectorizer = TfidfVectorizer(max_features=1500, ngram_range=(1, 2))
    X_text = vectorizer.fit_transform(df['text_features'])
    y = df['label'].astype(int)
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(vectorizer, os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl'))
    print("Đã lưu TF-IDF vectorizer.")
    return X_text, y

def train_model():
    X, y = load_and_preprocess()
    if X is None:
        return
    if len(y.unique()) < 2:
        print("Lỗi: Dữ liệu huấn luyện cần có cả nhãn 0 và 1.")
        return
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    X_train_dense = X_train.toarray()
    X_test_dense = X_test.toarray()
    class_weights = compute_class_weight(
        class_weight='balanced',
        classes=np.unique(y_train),
        y=y_train
    )
    class_weights_dict = dict(enumerate(class_weights))
    print(f"Trọng số lớp được áp dụng: {class_weights_dict}")
    input_shape = (X_train_dense.shape[1],)
    model = tf.keras.models.Sequential([
        tf.keras.layers.Input(shape=input_shape),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.4),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.4),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])
    print("\nBắt đầu quá trình huấn luyện cuối cùng với Class Weighting...")
    model.fit(X_train_dense, y_train,
              epochs=20,
              batch_size=16,
              validation_data=(X_test_dense, y_test),
              class_weight=class_weights_dict,
              verbose=2)
              
    model.save(os.path.join(MODEL_DIR, 'ai_ids_model.h5'))
    print("\n✅ Mô hình CUỐI CÙNG đã được huấn luyện và lưu thành công!")

if __name__ == '__main__':
    train_model()