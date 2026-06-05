# -*- coding: utf-8 -*-
from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

# =====================================================
# متغيرات البيئة
# =====================================================

SUPABASE_BIO_URL = os.environ.get('SUPABASE_BIO_URL', 'https://riojthitssmmsdmsqzyc.supabase.co')
SUPABASE_BIO_ANON_KEY = os.environ.get('SUPABASE_BIO_ANON_KEY', '')

# =====================================================
# الصفحات الرئيسية
# =====================================================

@app.route('/')
def index():
    """الصفحة الرئيسية (تسجيل الدخول)"""
    return render_template('index.html', 
                         SUPABASE_URL=SUPABASE_BIO_URL, 
                         SUPABASE_ANON_KEY=SUPABASE_BIO_ANON_KEY)

@app.route('/dashboard')
def dashboard():
    """لوحة تحكم المستخدم"""
    return render_template('dashboard.html', 
                         SUPABASE_URL=SUPABASE_BIO_URL, 
                         SUPABASE_ANON_KEY=SUPABASE_BIO_ANON_KEY)

@app.route('/auth')
def auth():
    """معالج مصادقة تلغرام"""
    return render_template('auth.html', 
                         SUPABASE_URL=SUPABASE_BIO_URL, 
                         SUPABASE_ANON_KEY=SUPABASE_BIO_ANON_KEY)

@app.route('/bio/<page_url>')
def bio_page(page_url):
    """صفحة عرض البايو العامة"""
    return render_template('bio.html', 
                         SUPABASE_URL=SUPABASE_BIO_URL, 
                         SUPABASE_ANON_KEY=SUPABASE_BIO_ANON_KEY,
                         page_url=page_url)

# =====================================================
# الملفات الثابتة
# =====================================================

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# =====================================================
# تشغيل التطبيق
# =====================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)