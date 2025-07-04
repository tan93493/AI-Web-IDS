# auth_site/routes.py
from flask import render_template, request, redirect, url_for, session, flash
from . import auth_bp 
from models import User
from forms import RegistrationForm, LoginForm
from extensions import db
from werkzeug.security import check_password_hash

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['username'] = user.username
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin           
            flash('Đăng nhập thành công!', 'success')
            if user.is_admin:
                return redirect(url_for('admin.index'))
            else:
                return redirect(url_for('main.home'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'username' in session:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Tài khoản {form.username.data} đã được tạo thành công!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)


@auth_bp.route('/logout')
def logout():
    session.pop('username', None)
    flash('Bạn đã đăng xuất thành công.', 'success')
    return redirect(url_for('main.home'))