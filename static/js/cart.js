// static/cart.js 

document.addEventListener('DOMContentLoaded', function() {
    var updateBtns = document.getElementsByClassName('update-cart');

    for (var i = 0; i < updateBtns.length; i++) {
        updateBtns[i].addEventListener('click', function() {
            // Bây giờ, chúng ta truyền cả 'this' (chính là cái nút được bấm) vào hàm
            updateUserOrder(this); 
        });
    }

    // THAY ĐỔI LỚN NẰM Ở ĐÂY
    // Hàm bây giờ nhận vào nguyên cả 'button' thay vì chỉ productId và action
    function updateUserOrder(buttonElement) {
        var productId = buttonElement.dataset.product;
        var action = buttonElement.dataset.action;
        
        // **SỬA LỖI: Lấy URL từ thuộc tính data-url của nút bấm**
        var url = buttonElement.dataset.url; 

        console.log('Đang gửi dữ liệu đến URL:', url); // Log ra URL đúng để kiểm tra
        
        // Lấy CSRF token từ thẻ meta trong HTML
        var csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ 'productId': productId, 'action': action })
        })
        .then((response) => {
            if (response.status === 401) {
                window.location.href = '/auth/login';
                // Dùng return để ngăn code chạy tiếp sau khi chuyển hướng
                return Promise.reject('Chưa đăng nhập, đang chuyển hướng...');
            }
            if (!response.ok) {
                // Nếu có lỗi khác 401 (ví dụ 404, 500), cũng báo lỗi
                return Promise.reject('Server trả về lỗi: ' + response.status);
            }
            return response.json();
        })
        .then((data) => {
            console.log('Phản hồi từ server:', data);
            // Tải lại trang để cập nhật giỏ hàng và các thông tin khác
            location.reload(); 
        })
        .catch((error) => {
            console.error('Lỗi khi cập nhật giỏ hàng:', error);
        });
    }
});