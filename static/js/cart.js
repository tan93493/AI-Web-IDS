// static/cart.js 
document.addEventListener('DOMContentLoaded', function() {
    var updateBtns = document.getElementsByClassName('update-cart');

    for (var i = 0; i < updateBtns.length; i++) {
        updateBtns[i].addEventListener('click', function() {
            updateUserOrder(this); 
        });
    }
    function updateUserOrder(buttonElement) {
        var productId = buttonElement.dataset.product;
        var action = buttonElement.dataset.action;
        var url = buttonElement.dataset.url; 
        console.log('Đang gửi dữ liệu đến URL:', url);
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
                return Promise.reject('Chưa đăng nhập, đang chuyển hướng...');
            }
            if (!response.ok) {
                return Promise.reject('Server trả về lỗi: ' + response.status);
            }
            return response.json();
        })
        .then((data) => {
            console.log('Phản hồi từ server:', data);
            location.reload(); 
        })
        .catch((error) => {
            console.error('Lỗi khi cập nhật giỏ hàng:', error);
        });
    }
});