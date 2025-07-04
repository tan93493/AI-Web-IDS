# admin_site/views.py
from flask_admin.contrib.sqla import ModelView
from models import Category, Log
from flask import session, redirect, url_for, flash, render_template, request, send_file
from wtforms.fields import PasswordField
from flask_admin import AdminIndexView, expose
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

class ProtectedModelView(ModelView):
    def is_accessible(self):
        return session.get('is_admin') is True

    def inaccessible_callback(self, name, **kwargs):
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('main.home'))
    
class UserAdminView(ProtectedModelView):
    column_exclude_list = ('password_hash',)
    form_excluded_columns = ('password_hash',)
    form_extra_fields = {
        'password_new': PasswordField('Mật khẩu mới (để trống nếu không đổi)')
    }

    def on_model_change(self, form, model, is_created):
        if 'password_new' in form and form.password_new.data:
            model.set_password(form.password_new.data)
    
class ProductAdminView(ModelView):
    column_list = ('id', 'name', 'price', 'stock', 'categories')
    form_columns = [
        'name',
        'price',
        'detail',
        'stock',
        'is_available',
        'image_url',
        'categories'
    ]
    form_args = {
        'categories': {
            'label': 'Danh mục sản phẩm',
            'query_factory': lambda: Category.query.all() 
        }
    }
    
class OrderAdminView(ModelView):
    column_editable_list = ['status']
    column_list = ['id', 'order_number', 'customer', 'status', 'date_ordered', 'get_cart_total']
    column_filters = ['status', 'date_ordered']
    column_default_sort = ('date_ordered', True)
    
def parse_log_data():
    all_logs = Log.query.all()
    if not all_logs:
        return pd.DataFrame()
    logs_data = [{'timestamp': log.timestamp, 'ip': log.ip, 'method': log.method, 'path': log.path} for log in all_logs]
    return pd.DataFrame(logs_data)
    
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        """Kiểm tra xem người dùng có phải là admin không."""
        return session.get('is_admin') is True

    def inaccessible_callback(self, name, **kwargs):
        """Nếu không phải admin, chuyển hướng về trang chủ."""
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('main.home'))
    @expose('/')
    def index(self):
        try:
            model = load_model('model/ai_ids_model.h5')
            enc_ip = joblib.load('model/ip_encoder.pkl')
            enc_method = joblib.load('model/method_encoder.pkl')
            enc_path = joblib.load('model/path_encoder.pkl')
        except FileNotFoundError:
            model = None
            return self.render('admin/admin_dashboard.html', total_requests=0, chart_url='', log_table='<p>Lỗi: Không tìm thấy tệp model hoặc encoder.</p>')
        all_logs = Log.query.order_by(Log.timestamp.desc()).limit(1000).all()
        if not all_logs:
            return self.render('admin/admin_dashboard.html', total_requests=Log.query.count(), chart_url='', log_table='<p>Không có dữ liệu log để phân tích.</p>')
        all_logs.reverse()
        df = pd.DataFrame([{'timestamp': log.timestamp, 'ip': log.ip, 'method': log.method, 'path': log.path} for log in all_logs])
        df_encoded = df.copy()

        def safe_transform(encoder, series):
            known_values = encoder.classes_
            return series.apply(lambda x: encoder.transform([x])[0] if x in known_values else np.nan)
        df_encoded['ip'] = safe_transform(enc_ip, df_encoded['ip'])
        df_encoded['method'] = safe_transform(enc_method, df_encoded['method'])
        df_encoded['path'] = safe_transform(enc_path, df_encoded['path'])
        df['AI_Phân_Tích'] = np.where(df_encoded.isnull().any(axis=1), '❓ Mới', '')
        df_to_predict = df_encoded.dropna()
        if not df_to_predict.empty:
            input_data = df_to_predict[['ip', 'method', 'path']].to_numpy()
            predictions = model.predict(input_data, verbose=0)
            predicted_labels = np.where(predictions.flatten() > 0.5, '❌ Bất thường', '✅ Bình thường')
            df.loc[df_to_predict.index, 'AI_Phân_Tích'] = predicted_labels
        total_requests = Log.query.count()
        requests_by_method = df['method'].value_counts()
        plt.figure(figsize=(8, 4))
        requests_by_method.plot(kind='bar', color='skyblue')
        plt.title('Phân tích 1000 truy cập gần nhất')
        plt.ylabel('Số lượng')
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        chart_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        columns = ['timestamp', 'ip', 'method', 'path', 'AI_Phân_Tích']
        log_table_html = df.tail(10)[columns].to_html(classes='table table-striped', index=False, border=0)
        return self.render('admin/admin_dashboard.html',
                           total_requests=total_requests,
                           chart_url=chart_url,
                           log_table=log_table_html) 
    @expose('/export-logs')
    def export_logs(self):
        if not session.get('is_admin'):
            return "Access Denied!", 403
        df = parse_log_data()
        if df.empty:
            return "Không có dữ liệu để xuất."
        filetype = request.args.get('filetype', 'csv').lower()
        output = io.BytesIO()
        if filetype == 'excel':
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Logs')
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            download_name = 'logs.xlsx'
        else:
            df.to_csv(output, index=False, encoding='utf-8')
            mimetype = 'text/csv; charset=utf-8'
            download_name = 'logs.csv'
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=download_name, mimetype=mimetype)