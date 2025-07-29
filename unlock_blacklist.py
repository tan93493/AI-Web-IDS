from app import create_app
from models import db, BlacklistedIP

# Tạo ứng dụng để có ngữ cảnh truy cập database
app = create_app()

with app.app_context():
    # Lấy tất cả các IP đang bị chặn
    blocked_ips = BlacklistedIP.query.all()
        
    if not blocked_ips:
        print("✅ Không tìm thấy IP nào trong danh sách đen.")
    else:
        print(f"🔎 Tìm thấy {len(blocked_ips)} IP đang bị chặn. Đang tiến hành xóa...")
            
        # Xóa tất cả các bản ghi trong bảng BlacklistedIP
        BlacklistedIP.query.delete()
            
        # Lưu thay đổi vào database
        db.session.commit()
            
        print("🚀 Đã xóa thành công tất cả các IP khỏi danh sách đen!")