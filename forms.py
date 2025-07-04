from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class CheckoutForm(FlaskForm):
    name = StringField('Họ và Tên', validators=[DataRequired(), Length(min=2, max=100)])
    address = StringField('Địa chỉ nhận hàng', validators=[DataRequired(), Length(min=10, max=250)])
    phone = StringField('Số điện thoại', validators=[DataRequired(), Length(min=9, max=15)])
    note = TextAreaField('Ghi chú')
    submit = SubmitField('Hoàn tất đơn hàng')
    
class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired()])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    remember = BooleanField('Ghi nhớ đăng nhập') # Thêm tùy chọn "Remember Me"
    submit = SubmitField('Đăng nhập')
    
class RegistrationForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(min=4, max=25)]) 
    email = StringField('Email', validators=[DataRequired(), Email()]) 
    password = PasswordField('Mật khẩu', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[DataRequired(), EqualTo('password', message='Mật khẩu xác nhận phải khớp.')])
    submit = SubmitField('Đăng ký')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Tên đăng nhập này đã có người sử dụng. Vui lòng chọn tên khác.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email này đã có người sử dụng. Vui lòng chọn email khác.')
