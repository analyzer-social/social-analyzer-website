# -*- coding: utf-8 -*-
from flask import Flask, render_template, send_from_directory, request, jsonify
from supabase import create_client, Client
import os
from functools import wraps

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'bio_social_analyzer_secret_key_2024_secure_9xK7mP2qR5tW8zL1')

# =====================================================
# متغيرات البيئة - دعم لعدة أسماء ممكنة
# =====================================================

# محاولة الحصول على URL من عدة أسماء ممكنة
SUPABASE_BIO_URL = (
    os.environ.get('SUPABASE_BIO_URL') or 
    os.environ.get('SUPABASE_URL') or
    os.environ.get('NEXT_PUBLIC_SUPABASE_URL') or
    'https://riojthitssmmsdmsqzyc.supabase.co'  # القيمة الافتراضية
)

# محاولة الحصول على ANON KEY من عدة أسماء ممكنة
SUPABASE_BIO_ANON_KEY = (
    os.environ.get('SUPABASE_BIO_ANON_KEY') or
    os.environ.get('SUPABASE_ANON_KEY') or
    os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY') or
    ''  # سيتم التحقق منها بعد
)

# طباعة معلومات debug (للتأكد من وجود المتغيرات)
print(f"🔍 Checking environment variables:")
print(f"   SUPABASE_BIO_URL: {'✅ Found' if SUPABASE_BIO_URL else '❌ Missing'}")
print(f"   SUPABASE_BIO_ANON_KEY: {'✅ Found' if SUPABASE_BIO_ANON_KEY else '❌ Missing'}")
print(f"   SECRET_KEY: {'✅ Found' if app.secret_key else '❌ Missing'}")

# التحقق من وجود ANON KEY (بدون إيقاف التشغيل)
if not SUPABASE_BIO_ANON_KEY:
    print("⚠️ WARNING: SUPABASE_BIO_ANON_KEY is not set! Some features may not work.")
    # لا نوقف التشغيل، نعطي قيمة افتراضية فارغة

# تهيئة Supabase للخلفية (حتى لو كان المفتاح فارغاً، سنتعامل معه لاحقاً)
try:
    if SUPABASE_BIO_URL and SUPABASE_BIO_ANON_KEY:
        supabase: Client = create_client(SUPABASE_BIO_URL, SUPABASE_BIO_ANON_KEY)
        print("✅ Supabase client initialized successfully")
    else:
        supabase = None
        print("⚠️ Supabase client not initialized (missing credentials)")
except Exception as e:
    print(f"⚠️ Supabase initialization error: {e}")
    supabase = None

# =====================================================
# دوال المصادقة (Decorators)
# =====================================================

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# واجهات برمجة التطبيقات (API)
# =====================================================

@app.route('/api/bio/save', methods=['POST'])
@require_auth
def save_bio():
    """حفظ بيانات صفحة البايو"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    try:
        data = request.json
        user_id = request.headers.get('X-User-Id')
        page_url = data.get('page_url')
        
        bio_data = {
            'avatar_url': data.get('avatar_url'),
            'display_name': data.get('display_name'),
            'bio': data.get('bio'),
            'theme_name': data.get('theme_name'),
            'accounts': data.get('accounts', {}),
            'custom_links': data.get('custom_links', []),
            'updated_at': 'now()'
        }
        
        if page_url:
            # تحديث صفحة موجودة
            result = supabase.table('bio_pages')\
                .update(bio_data)\
                .eq('user_id', int(user_id))\
                .execute()
            
            if result.data:
                return jsonify({'success': True, 'data': result.data[0]})
            else:
                return jsonify({'error': 'No data updated'}), 400
        else:
            # إنشاء صفحة جديدة
            name = data.get('display_name', 'user')
            import random
            import string
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            new_page_url = f"{name.replace(' ', '_').lower()}_{random_str}"
            
            new_data = {
                'user_id': int(user_id),
                'page_url': new_page_url,
                **bio_data,
                'is_active': True,
                'views_count': 0,
                'created_at': 'now()'
            }
            
            result = supabase.table('bio_pages')\
                .insert(new_data)\
                .execute()
            
            if result.data:
                return jsonify({'success': True, 'page_url': new_page_url, 'data': result.data[0]})
            else:
                return jsonify({'error': 'Failed to create'}), 400
                
    except Exception as e:
        print(f"Error in save_bio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bio/load', methods=['GET'])
@require_auth
def load_bio():
    """تحميل بيانات صفحة البايو"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    try:
        user_id = request.headers.get('X-User-Id')
        
        result = supabase.table('bio_pages')\
            .select('*')\
            .eq('user_id', int(user_id))\
            .maybe_single()\
            .execute()
        
        if result.data:
            return jsonify({'success': True, 'data': result.data})
        else:
            return jsonify({'success': True, 'data': None})
            
    except Exception as e:
        print(f"Error in load_bio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/create', methods=['POST'])
def create_user():
    """إنشاء مستخدم جديد"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    try:
        data = request.json
        telegram_id = data.get('telegram_id')
        
        if not telegram_id:
            return jsonify({'success': False, 'error': 'telegram_id required'}), 400
        
        # التحقق من وجود المستخدم
        result = supabase.table('app_users')\
            .select('*')\
            .eq('id', int(telegram_id))\
            .execute()
        
        if not result.data:
            # إنشاء مستخدم جديد
            new_user = {
                'id': int(telegram_id),
                'username': data.get('username', f'user_{telegram_id}'),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'created_at': 'now()',
                'updated_at': 'now()'
            }
            
            result = supabase.table('app_users')\
                .insert(new_user)\
                .execute()
            
            return jsonify({'success': True, 'user': result.data[0] if result.data else None})
        else:
            return jsonify({'success': True, 'user': result.data[0], 'exists': True})
        
    except Exception as e:
        print(f"Error in create_user: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/verify', methods=['GET'])
@require_auth
def verify_user():
    """التحقق من صحة المستخدم"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    try:
        user_id = request.headers.get('X-User-Id')
        
        result = supabase.table('app_users')\
            .select('id, username, first_name')\
            .eq('id', int(user_id))\
            .maybe_single()\
            .execute()
        
        if result.data:
            return jsonify({'success': True, 'user': result.data})
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
# نقطة نهاية فحص الصحة (لـ Render)
# =====================================================

@app.route('/health')
@app.route('/healthcheck')
def health():
    return {"status": "ok", "supabase_configured": supabase is not None}, 200

# =====================================================
# الملفات الثابتة
# =====================================================

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)
# =====================================================    
@app.route('/static/assets/icons/<path:filename>')
def serve_icon(filename):
    return send_from_directory('static/assets/icons', filename)
# =====================================================
# تشغيل التطبيق
# =====================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)