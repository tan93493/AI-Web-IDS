# admin_site/views.py
from flask_admin.contrib.sqla import ModelView
from models import Category, Log
from flask import session, redirect, url_for, render_template, request, send_file
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

def run_ai_predictions(logs):
    try:
        model = load_model('model/ai_ids_model.h5')
        preprocessor = joblib.load('model/preprocessor.pkl')
    except FileNotFoundError:
        return pd.DataFrame()
    if not logs:
        return pd.DataFrame()
    df = pd.DataFrame([
        {'id': log.id, 'method': log.method, 'path': log.path, 'payload': log.payload} 
        for log in logs
    ])
    df['payload'] = df['payload'].fillna('')
    df['path'] = df['path'].fillna('unknown')
    df['method'] = df['method'].fillna('unknown')
    X_new = df[['method', 'path', 'payload']]
    X_new_processed = preprocessor.transform(X_new)
    X_new_dense = X_new_processed.toarray()
    predictions = model.predict(X_new_dense, verbose=0)
    df['AI_Phân_Tích'] = np.where(predictions.flatten() > 0.5, '❌ Bất thường', '✅ Bình thường')
    return df[['id', 'AI_Phân_Tích']].set_index('id')

class ProtectedModelView(ModelView):
    def is_accessible(self):
        return session.get('is_admin') is True
    def inaccessible_callback(self, name, **kwargs):
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
    
class LogAdminView(ProtectedModelView):
    list_template = 'admin/custom_log_list.html'
    column_default_sort = ('timestamp', True)
    can_edit = False
    can_create = False
    can_delete = True
    column_list = ['timestamp', 'ip', 'method', 'path', 'payload', 'ai_analysis']
    column_labels = {'ai_analysis': 'AI Phân Tích'}

    def get_list(self, page, sort_column, sort_desc, search, filters, execute=True, page_size=10):
        count, data = super().get_list(page, sort_column, sort_desc, search, filters, execute, page_size)
        analysis_df = run_ai_predictions(data)
        if not analysis_df.empty:
            for item in data:
                item.ai_analysis = analysis_df.loc[item.id]['AI_Phân_Tích'] if item.id in analysis_df.index else 'N/A'
        else:
            for item in data:
                item.ai_analysis = 'Model not available'
        return count, data

def parse_log_data():
    all_logs = Log.query.all()
    if not all_logs:
        return pd.DataFrame()
    logs_data = [{'timestamp': log.timestamp, 'ip': log.ip, 'method': log.method, 'path': log.path, 'payload': log.payload} for log in all_logs]
    return pd.DataFrame(logs_data)

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('is_admin') is True
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.home'))

    @expose('/')
    def index(self):
        total_requests = Log.query.count()
        recent_logs = Log.query.order_by(Log.timestamp.desc()).limit(100).all()
        if not recent_logs:
            return self.render('admin/admin_dashboard.html', total_requests=total_requests, chart_url='', log_table='<p>Không có dữ liệu log để phân tích.</p>') 
        analysis_df = run_ai_predictions(recent_logs)
        df_display = pd.DataFrame([{'id': log.id, 'timestamp': log.timestamp, 'ip': log.ip, 'method': log.method, 'path': log.path, 'payload': log.payload} for log in recent_logs])       
        if not analysis_df.empty:
            df_display = df_display.merge(analysis_df, on='id', how='left').fillna('N/A')
        else:
            df_display['AI_Phân_Tích'] = 'Model not available'
        requests_by_method = df_display['method'].value_counts()
        plt.figure(figsize=(8, 4))
        requests_by_method.plot(kind='bar', color='skyblue')
        plt.title('Phân tích phương thức trong 100 truy cập gần nhất')
        plt.ylabel('Số lượng')
        plt.xticks(rotation=0)
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        chart_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        df_anomalous = df_display[df_display['AI_Phân_Tích'] == '❌ Bất thường']
        columns_to_display = ['timestamp', 'ip', 'method', 'path', 'payload', 'AI_Phân_Tích']
        if not df_anomalous.empty:
            log_table_html = df_anomalous[columns_to_display].to_html(classes='table table-striped table-sm', index=False, border=0, justify='left')
        else:
            log_table_html = "<p>✅ Không phát hiện hành vi bất thường nào trong các truy cập gần đây.</p>"
        return self.render('admin/admin_dashboard.html', total_requests=total_requests, chart_url=chart_url, log_table=log_table_html)
                           
    @expose('/export-logs')
    def export_logs(self):
        """Xử lý việc xuất toàn bộ log ra file CSV hoặc Excel."""
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