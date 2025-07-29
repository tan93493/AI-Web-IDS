# ai_blocker.py
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import joblib
from models import IPAttackTracker, BlacklistedIP, db
import datetime
import os

# --- Cấu hình ---
# Chặn IP sau khi phát hiện số lần tấn công bất thường này
ATTACK_THRESHOLD = 5 
# Thời gian chặn IP (tính bằng phút)
BLOCK_DURATION_MINUTES = 60 

MODEL_DIR = 'model'
MODEL_FILE = os.path.join(MODEL_DIR, 'ai_ids_model.h5')
PREPROCESSOR_FILE = os.path.join(MODEL_DIR, 'preprocessor.pkl')

# Sử dụng cache để không phải load model mỗi lần request
_model = None
_preprocessor = None

def get_model_and_preprocessor():
    """Tải model và preprocessor, chỉ tải lần đầu tiên."""
    global _model, _preprocessor
    if _model is None:
        try:
            _model = load_model(MODEL_FILE)
            _preprocessor = joblib.load(PREPROCESSOR_FILE)
            print("✅ AI model và preprocessor đã được tải thành công.")
        except (FileNotFoundError, IOError) as e:
            print(f"⚠️ Lỗi: Không thể tải model hoặc preprocessor. Chức năng chặn tự động sẽ không hoạt động. Chi tiết: {e}")
            _model = "not_found" # Đánh dấu là không tìm thấy để không thử lại
    return _model, _preprocessor

def analyze_and_block(log_entry):
    """
    Phân tích một entry log, cập nhật bộ đếm tấn công và chặn IP nếu cần.
    """
    model, preprocessor = get_model_and_preprocessor()
    if model == "not_found":
        return

    # Chuẩn bị dữ liệu từ log để đưa vào model
    df = pd.DataFrame([{
        'method': log_entry.method,
        'path': log_entry.path,
        'payload': log_entry.payload or ''
    }])
    df['payload'] = df['payload'].fillna('')
    df['path'] = df['path'].fillna('unknown')
    df['method'] = df['method'].fillna('unknown')
    
    X_processed = preprocessor.transform(df[['method', 'path', 'payload']])
    X_dense = X_processed.toarray()

    # Dự đoán
    prediction = model.predict(X_dense, verbose=0).flatten()[0]

    # Nếu phát hiện bất thường (label=1)
    if prediction > 0.5:
        ip = log_entry.ip
        print(f"🚨 AI phát hiện hành vi bất thường từ IP: {ip}")

        # Cập nhật bộ đếm tấn công
        tracker = IPAttackTracker.query.filter_by(ip_address=ip).first()
        if not tracker:
            tracker = IPAttackTracker(ip_address=ip, attack_count=1)
            db.session.add(tracker)
        else:
            tracker.attack_count += 1
        
        db.session.commit()

        # Kiểm tra nếu vượt ngưỡng
        if tracker.attack_count >= ATTACK_THRESHOLD:
            # Chỉ chặn nếu IP chưa bị chặn
            existing_block = BlacklistedIP.query.filter_by(ip_address=ip).first()
            if not existing_block:
                print(f"🚫 VƯỢT NGƯỠNG! Chặn IP: {ip} trong {BLOCK_DURATION_MINUTES} phút.")
                expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=BLOCK_DURATION_MINUTES)
                new_blacklist_entry = BlacklistedIP(
                    ip_address=ip,
                    expires_at=expires,
                    reason=f"Tự động chặn sau khi phát hiện {tracker.attack_count} hành vi bất thường."
                )
                db.session.add(new_blacklist_entry)
                db.session.commit()