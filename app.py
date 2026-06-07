# -*- coding: utf-8 -*-
from flask import Flask, render_template, send_from_directory, request, jsonify
from supabase import create_client, Client
import os
from functools import wraps
from flask import Flask, render_template, send_from_directory, request, jsonify, session, redirect
from datetime import datetime
import hashlib
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
# دوال مساعدة لعرض صفحة البايو
# =====================================================

def get_bio_page_by_identifier(identifier, identifier_type='page_url'):
    """
    الحصول على بيانات صفحة البايو باستخدام page_url أو username
    identifier_type: 'page_url' أو 'username'
    """
    if not supabase:
        return None
    
    try:
        if identifier_type == 'username':
            # البحث باستخدام username
            result = supabase.table('bio_pages')\
                .select('*')\
                .eq('username', identifier)\
                .maybe_single()\
                .execute()
        else:
            # البحث باستخدام page_url
            result = supabase.table('bio_pages')\
                .select('*')\
                .eq('page_url', identifier)\
                .maybe_single()\
                .execute()
        
        return result.data if result.data else None
        
    except Exception as e:
        print(f"Error in get_bio_page_by_identifier: {str(e)}")
        return None

def increment_views_count(page_id):
    """زيادة عدد المشاهدات للصفحة"""
    if not supabase:
        return
    
    try:
        # الحصول على العدد الحالي
        result = supabase.table('bio_pages')\
            .select('views_count')\
            .eq('id', page_id)\
            .execute()
        
        if result.data:
            current_views = result.data[0].get('views_count', 0)
            new_views = current_views + 1
            
            # تحديث العدد
            supabase.table('bio_pages')\
                .update({'views_count': new_views})\
                .eq('id', page_id)\
                .execute()
            
            print(f"✅ تم زيادة عدد المشاهدات إلى {new_views}")
            
    except Exception as e:
        print(f"Error incrementing views: {str(e)}")

# =====================================================
# الصفحات الرئيسية لعرض البايو
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

# =====================================================
# مسارات عرض صفحة البايو (مع دعم username الجديد)
# =====================================================

@app.route('/<username>')
def bio_page_by_username(username):
    """صفحة عرض البايو باستخدام username المخصص"""
    print(f"🔍 جلب صفحة البايو باستخدام username: {username}")
    
    if not supabase:
        return render_template('error.html', error="قاعدة البيانات غير متصلة"), 500
    
    # البحث عن الصفحة باستخدام username
    bio_data = get_bio_page_by_identifier(username, 'username')
    
    if not bio_data:
        # إذا لم يتم العثور، نحاول البحث باستخدام page_url (للمرونة)
        bio_data = get_bio_page_by_identifier(username, 'page_url')
        if not bio_data:
            return render_template('error.html', error="الصفحة غير موجودة"), 404
    
    # التحقق من أن الصفحة نشطة
    if not bio_data.get('is_active', True):
        return render_template('error.html', error="هذه الصفحة غير نشطة حالياً"), 403
    
    # زيادة عدد المشاهدات
    increment_views_count(bio_data['id'])
    
    # إرسال البيانات إلى القالب
    return render_template('bio.html', 
                         SUPABASE_URL=SUPABASE_BIO_URL, 
                         SUPABASE_ANON_KEY=SUPABASE_BIO_ANON_KEY,
                         page_url=bio_data.get('page_url'),
                         username=bio_data.get('username'),
                         bio_data=bio_data)

@app.route('/bio/<page_url>')
def bio_page_by_page_url(page_url):
    """صفحة عرض البايو باستخدام page_url القديم (للتوافق مع الروابط القديمة)"""
    print(f"🔍 جلب صفحة البايو باستخدام page_url: {page_url}")
    
    if not supabase:
        return render_template('error.html', error="قاعدة البيانات غير متصلة"), 500
    
    # البحث عن الصفحة باستخدام page_url
    bio_data = get_bio_page_by_identifier(page_url, 'page_url')
    
    if not bio_data:
        return render_template('error.html', error="الصفحة غير موجودة"), 404
    
    # التحقق من أن الصفحة نشطة
    if not bio_data.get('is_active', True):
        return render_template('error.html', error="هذه الصفحة غير نشطة حالياً"), 403
    
    # زيادة عدد المشاهدات
    increment_views_count(bio_data['id'])
    
    # إرسال البيانات إلى القالب
    return render_template('bio.html', 
                         SUPABASE_URL=SUPABASE_BIO_URL, 
                         SUPABASE_ANON_KEY=SUPABASE_BIO_ANON_KEY,
                         page_url=bio_data.get('page_url'),
                         username=bio_data.get('username'),
                         bio_data=bio_data)

# =====================================================

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

@app.route('/static/assets/icons/<path:filename>')
def serve_icon(filename):
    return send_from_directory('static/assets/icons', filename)

# =====================================================
# APIs لوسائل الدفع
# =====================================================

@app.route('/api/payment/save', methods=['POST'])
@require_auth
def save_payment_methods():
    """حفظ وسائل الدفع للمستخدم"""
    try:
        user_id = request.headers.get('X-User-Id')
        data = request.json
        payment_methods = data.get('payment_methods', {})
        bio_page_id = data.get('bio_page_id')
        
        print(f"🔍 1. user_id: {user_id}")
        print(f"🔍 2. bio_page_id المستلم: {bio_page_id}")
        print(f"🔍 3. payment_methods: {payment_methods}")
        
        # الحصول على bio_page_id إذا لم يتم إرساله
        if not bio_page_id:
            page_result = supabase.table('bio_pages')\
                .select('id')\
                .eq('user_id', int(user_id))\
                .execute()
            
            if page_result.data and len(page_result.data) > 0:
                bio_page_id = page_result.data[0]['id']
                print(f"🔍 4. تم العثور على bio_page_id: {bio_page_id}")
            else:
                print("❌ لم يتم العثور على bio_page_id")
                return jsonify({'error': 'Bio page not found for this user'}), 404
        
        # قائمة المحافظ
        payment_wallets = [
            {'key': 'jaib', 'name': 'جيب'},
            {'key': 'floosak', 'name': 'فلوسك'},
            {'key': 'jawaly', 'name': 'جوالي'},
            {'key': 'mahfazti', 'name': 'محفظتي'},
            {'key': 'mobilemoney', 'name': 'موبايل موني'},
            {'key': 'yemenwallet', 'name': 'يمن والت'},
            {'key': 'shilling', 'name': 'شلن'},
            {'key': 'easywallet', 'name': 'سهل'},
            {'key': 'onecash', 'name': 'ون كاش'},
            {'key': 'kremi', 'name': 'كريمي'},
            {'key': 'cash', 'name': 'كاش'},
            {'key': 'mtnmomo', 'name': 'MTN Mobile Money'}
        ]
        
        for wallet in payment_wallets:
            account_number = payment_methods.get(wallet['key'], '')
            print(f"🔍 5. معالجة {wallet['key']}: account_number={account_number}")
            
            # البحث عن سجل موجود - الطريقة الصحيحة لـ Supabase
            try:
                existing_result = supabase.table('payment_methods')\
                    .select('id')\
                    .eq('user_id', int(user_id))\
                    .eq('method_key', wallet['key'])\
                    .execute()
                
                # التحقق من وجود بيانات في الاستجابة
                if existing_result and hasattr(existing_result, 'data') and existing_result.data and len(existing_result.data) > 0:
                    # يوجد سجل => تحديث
                    existing_id = existing_result.data[0]['id']
                    print(f"🔍 6. سجل موجود: {existing_id}")
                    
                    if account_number:
                        supabase.table('payment_methods')\
                            .update({
                                'account_number': account_number,
                                'updated_at': 'now()'
                            })\
                            .eq('id', existing_id)\
                            .execute()
                        print(f"✅ تم تحديث {wallet['key']}: {account_number}")
                    else:
                        supabase.table('payment_methods')\
                            .delete()\
                            .eq('id', existing_id)\
                            .execute()
                        print(f"🗑️ تم حذف {wallet['key']}")
                else:
                    # لا يوجد سجل => إدراج جديد
                    print(f"🔍 7. لا يوجد سجل لـ {wallet['key']}")
                    if account_number:
                        insert_result = supabase.table('payment_methods')\
                            .insert({
                                'user_id': int(user_id),
                                'bio_page_id': bio_page_id,
                                'method_key': wallet['key'],
                                'method_name': wallet['name'],
                                'account_number': account_number,
                                'created_at': 'now()'
                            })\
                            .execute()
                        print(f"✅ تم إضافة {wallet['key']}: {account_number}")
                        print(f"🔍 8. نتيجة الإضافة: {insert_result.data if insert_result else 'No data'}")
            except Exception as inner_error:
                print(f"⚠️ خطأ في معالجة {wallet['key']}: {str(inner_error)}")
        
        print("✅ تمت معالجة جميع وسائل الدفع بنجاح")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ خطأ في حفظ وسائل الدفع: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/payment/load', methods=['GET'])
@require_auth
def load_payment_methods():
    """تحميل وسائل الدفع للمستخدم"""
    try:
        user_id = request.headers.get('X-User-Id')
        
        result = supabase.table('payment_methods')\
            .select('method_key, account_number')\
            .eq('user_id', int(user_id))\
            .execute()
        
        payment_methods = {}
        for item in result.data:
            payment_methods[item['method_key']] = item['account_number']
        
        return jsonify({'success': True, 'payment_methods': payment_methods})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/payment/click', methods=['POST'])
def track_payment_click():
    """تسجيل نقرة على وسيلة دفع - يجمع بين التحديث الفوري والتسجيل التفصيلي"""
    try:
        data = request.json
        method_key = data.get('method_key')
        account_number = data.get('account_number')
        page_url = data.get('page_url')
        
        print(f"🔍 تسجيل نقرة: {method_key} - {account_number} - {page_url}")
        
        # 1. الحصول على bio_page_id و user_id من page_url
        bio_result = supabase.table('bio_pages')\
            .select('id, user_id')\
            .eq('page_url', page_url)\
            .execute()
        
        if not bio_result.data or len(bio_result.data) == 0:
            print(f"❌ لم يتم العثور على الصفحة: {page_url}")
            return jsonify({'error': 'Bio page not found'}), 404
        
        bio_page_id = bio_result.data[0]['id']
        user_id = bio_result.data[0]['user_id']
        
        # 2. الحصول على payment_method_id
        pm_result = supabase.table('payment_methods')\
            .select('id')\
            .eq('user_id', user_id)\
            .eq('method_key', method_key)\
            .eq('bio_page_id', bio_page_id)\
            .execute()
        
        if pm_result.data and len(pm_result.data) > 0:
            payment_method_id = pm_result.data[0]['id']
            print(f"🔍 payment_method_id={payment_method_id}")
            
            # =====================================================
            # 3. تحديث إجمالي النقرات في جدول payment_methods
            # =====================================================
            # استعلم عن العدد الحالي
            current_record = supabase.table('payment_methods')\
                .select('clicks_count')\
                .eq('id', payment_method_id)\
                .execute()

            if current_record.data:
                current_clicks = current_record.data[0].get('clicks_count', 0)
                new_clicks = current_clicks + 1
                
                # قم بالتحديث بالقيمة الجديدة
                supabase.table('payment_methods')\
                    .update({
                        'clicks_count': new_clicks,
                        'last_click_at': 'now()'
                    })\
                    .eq('id', payment_method_id)\
                    .execute()
                print(f"✅ تم تحديث عدد النقرات إلى {new_clicks}")
            # =====================================================
            
            # =====================================================
            # 4. تسجيل التفاصيل في جدول payment_clicks (للتحليل)
            # =====================================================
            supabase.table('payment_clicks')\
                .insert({
                    'payment_method_id': payment_method_id,
                    'user_id': user_id,
                    'bio_page_id': bio_page_id,
                    'method_key': method_key,
                    'clicker_ip': request.headers.get('X-Forwarded-For', request.remote_addr),
                    'clicker_user_agent': request.headers.get('User-Agent'),
                    'clicked_at': 'now()'
                })\
                .execute()
            print(f"✅ تم تسجيل تفاصيل النقرة في payment_clicks")
            # =====================================================
            
            return jsonify({'success': True})
        else:
            print(f"⚠️ لم يتم العثور على payment_method_id للمفتاح: {method_key}")
            return jsonify({'error': 'Payment method not found'}), 404
        
    except Exception as e:
        print(f"❌ خطأ في تسجيل النقرة: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/payment/stats/<int:user_id>', methods=['GET'])
@require_auth
def get_payment_stats(user_id):
    """إحصائيات نقرات وسائل الدفع للمستخدم"""
    try:
        result = supabase.table('payment_methods')\
            .select('method_name, method_key, account_number, clicks_count, last_click_at')\
            .eq('user_id', user_id)\
            .order('clicks_count', desc=True)\
            .execute()
        
        return jsonify({'success': True, 'stats': result.data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment/load-page', methods=['GET'])
def load_payment_methods_for_page():
    """تحميل وسائل الدفع لصفحة عامة (للعرض العام)"""
    try:
        page_url = request.args.get('page_url')
        
        if not page_url:
            return jsonify({'error': 'page_url required'}), 400
        
        print(f"🔍 جلب وسائل الدفع للصفحة: {page_url}")
        
        # الحصول على bio_page_id من page_url
        bio_result = supabase.table('bio_pages')\
            .select('id')\
            .eq('page_url', page_url)\
            .execute()
        
        if not bio_result.data or len(bio_result.data) == 0:
            print(f"❌ لم يتم العثور على الصفحة: {page_url}")
            return jsonify({'success': False, 'error': 'Page not found'}), 404
        
        bio_page_id = bio_result.data[0]['id']
        print(f"🔍 bio_page_id: {bio_page_id}")
        
        # جلب وسائل الدفع
        result = supabase.table('payment_methods')\
            .select('method_key, account_number')\
            .eq('bio_page_id', bio_page_id)\
            .eq('is_active', True)\
            .execute()
        
        payment_methods = {}
        if result.data:
            for item in result.data:
                if item.get('account_number'):
                    payment_methods[item['method_key']] = item['account_number']
        
        print(f"✅ تم تحميل وسائل الدفع: {payment_methods}")
        return jsonify({'success': True, 'payment_methods': payment_methods})
        
    except Exception as e:
        print(f"❌ خطأ في تحميل وسائل الدفع للصفحة: {str(e)}")
        return jsonify({'error': str(e)}), 500

# =====================================================
# إعدادات الجلسات والأمان للمدير
# =====================================================

import hashlib
from datetime import datetime
from flask import session, redirect, url_for

# كلمة مرور المدير (من متغيرات البيئة)
ADMIN_PASSWORD_HASH = hashlib.sha256(
    os.environ.get('ADMIN_PASSWORD', 'default_admin_password').encode()
).hexdigest()

def verify_admin(password):
    """التحقق من كلمة مرور المدير"""
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH

# =====================================================
@app.route('/report')
def report():
    """صفحة التقرير الشامل للمشروع"""
    return render_template('report.html')

# =====================================================
# مصادقة Google OAuth
# =====================================================

@app.route('/auth/google-callback')
def google_auth_callback():
    """معالج رد الاتصال بعد مصادقة Google"""
    try:
        # الحصول على جلسة Supabase الحالية
        supabase_client = create_client(SUPABASE_BIO_URL, SUPABASE_BIO_ANON_KEY)
        
        # الحصول على مستخدم Supabase من الرابط (access_token في الـ URL)
        # ملاحظة: بعد إعادة التوجيه، Supabase يضع access_token في hash أو query
        access_token = request.args.get('access_token')
        refresh_token = request.args.get('refresh_token')
        
        if not access_token:
            # محاولة الحصول من hash (طريقة Supabase الافتراضية)
            return redirect('/auth/google-error?error=missing_token')
        
        # الحصول على معلومات المستخدم من Supabase
        import requests
        user_response = requests.get(
            f'{SUPABASE_BIO_URL}/auth/v1/user',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if user_response.status_code != 200:
            return redirect('/auth/google-error?error=failed_to_get_user')
        
        user_data = user_response.json()
        user_id_from_supabase = user_data.get('id')
        email = user_data.get('email')
        user_metadata = user_data.get('user_metadata', {})
        full_name = user_metadata.get('full_name', email.split('@')[0] if email else '')
        avatar_url = user_metadata.get('avatar_url', '')
        
        # التحقق من وجود المستخدم في جدول app_users (باستخدام Supabase UID أو email)
        # سنستخدم معرف Supabase UID كمفتاح أساسي جديد، أو نبحث عن email
        
        # نبحث أولاً عن مستخدم بنفس البريد الإلكتروني
        existing_user = supabase.table('app_users')\
            .select('*')\
            .eq('email', email)\
            .maybe_single()\
            .execute()
        
        if existing_user.data:
            # مستخدم موجود نستخدمه
            app_user_id = existing_user.data['id']
        else:
            # إنشاء مستخدم جديد - نستخدم جزءاً من Supabase UID كـ id (أو نستخدم email)
            # ملاحظة: app_users.id هو BIGINT، لكن Supabase UID هو UUID
            # سنستخدم email للربط ونجعل id = نطاق UUID رقمي مبسط
            import hashlib
            # تحويل email إلى رقم BIGINT (جداً)
            hash_digest = hashlib.md5(email.encode()).hexdigest()
            numeric_id = int(hash_digest[:15], 16)  # 15 خانة سداسية عشرية
            
            new_user = {
                'id': numeric_id,
                'username': full_name.lower().replace(' ', '_'),
                'first_name': full_name,
                'email': email,
                'avatar_url': avatar_url,
                'created_at': 'now()',
                'updated_at': 'now()'
            }
            
            result = supabase.table('app_users')\
                .insert(new_user)\
                .execute()
            
            if result.data:
                app_user_id = result.data[0]['id']
            else:
                return redirect('/auth/google-error?error=failed_to_create_user')
        
        # إنشاء جلسة للمستخدم
        session['user_id'] = app_user_id
        session['auth_provider'] = 'google'
        session['user_email'] = email
        
        # حفظ في localStorage عبر رد الصفحة (سنرسل صفحة وسيطة)
        return render_template('google_auth_callback.html', 
                             user_id=app_user_id,
                             full_name=full_name,
                             email=email)
        
    except Exception as e:
        print(f"❌ خطأ في مصادقة Google: {str(e)}")
        return redirect('/auth/google-error?error=server_error')


@app.route('/auth/google-error')
def google_auth_error():
    """صفحة خطأ مصادقة Google"""
    error = request.args.get('error', 'unknown')
    return render_template('google_error.html', error=error)

# =====================================================
# صفحات المعلومات (سياسة الخصوصية، شروط الخدمة، المساعدة)
# =====================================================

@app.route('/privacy')
def privacy_policy():
    """صفحة سياسة الخصوصية"""
    return render_template('privacy.html')

@app.route('/terms')
def terms_of_service():
    """صفحة شروط الخدمة"""
    return render_template('terms.html')

@app.route('/help')
def help_page():
    """صفحة الدليل والمساعدة"""
    return render_template('help.html')

# =====================================================
# لوحة تحكم المدير
# =====================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """صفحة تسجيل دخول المدير"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if verify_admin(password):
            session['admin_logged_in'] = True
            return redirect('/admin/dashboard')
        return render_template('admin_login.html', error='كلمة المرور غير صحيحة')
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    """لوحة تحكم المدير"""
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    
    if not supabase:
        return render_template('admin_dashboard.html', stats={}, users=[], now_date=datetime.now().strftime('%Y-%m-%d %H:%M'), error='قاعدة البيانات غير متصلة')
    
    # جلب جميع المستخدمين
    users_result = supabase.table('app_users').select('*').order('created_at', desc=True).execute()
    
    users_data = []
    total_views = 0
    total_clicks = 0
    total_payment_methods = 0
    
    for user in users_result.data:
        # جلب صفحة البايو
        bio_page = supabase.table('bio_pages')\
            .select('*')\
            .eq('user_id', user['id'])\
            .maybe_single()\
            .execute()
        
        # جلب إحصائيات الدفع
        payment_stats = []
        payment_clicks = 0
        
        if bio_page.data:
            payment_stats_result = supabase.table('payment_methods')\
                .select('method_name, clicks_count')\
                .eq('user_id', user['id'])\
                .execute()
            payment_stats = payment_stats_result.data
            payment_clicks = sum(p.get('clicks_count', 0) for p in payment_stats)
            total_payment_methods += len([p for p in payment_stats if p.get('clicks_count', 0) > 0])
        
        views_count = bio_page.data.get('views_count', 0) if bio_page.data else 0
        total_views += views_count
        total_clicks += payment_clicks
        
        users_data.append({
            'id': user['id'],
            'username': user.get('username', ''),
            'first_name': user.get('first_name', ''),
            'created_at': user.get('created_at', ''),
            'bio_page': bio_page.data,
            'payment_stats': payment_stats,
            'total_clicks': payment_clicks,
            'views_count': views_count
        })
    
    stats = {
        'total_users': len(users_result.data),
        'total_bio_pages': len([u for u in users_data if u['bio_page']]),
        'total_views': total_views,
        'total_clicks': total_clicks,
        'total_payment_methods': total_payment_methods
    }
    
    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         users=users_data,
                         now_date=datetime.now().strftime('%Y-%m-%d %H:%M'))


@app.route('/admin/logout')
def admin_logout():
    """تسجيل خروج المدير"""
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')


# =====================================================
# API إضافية للوحة التحكم
# =====================================================

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    """API لجلب الإحصائيات العامة (للاستخدام في JavaScript)"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    # إحصائيات سريعة
    users_count = supabase.table('app_users').select('*', count='exact').execute().count
    bio_pages_count = supabase.table('bio_pages').select('*', count='exact').execute().count
    
    views_result = supabase.table('bio_pages').select('views_count').execute()
    total_views = sum(v.get('views_count', 0) for v in views_result.data)
    
    clicks_result = supabase.table('payment_methods').select('clicks_count').execute()
    total_clicks = sum(c.get('clicks_count', 0) for c in clicks_result.data)
    
    return jsonify({
        'total_users': users_count or 0,
        'total_bio_pages': bio_pages_count or 0,
        'total_views': total_views,
        'total_clicks': total_clicks
    }) 
# =====================================================
# معالج الأخطاء (Error Handlers)
# =====================================================

@app.errorhandler(404)
def page_not_found(e):
    """صفحة خطأ 404"""
    return render_template('error.html', error_message="الصفحة غير موجودة"), 404

@app.errorhandler(500)
def internal_server_error(e):
    """صفحة خطأ 500"""
    return render_template('error.html', error_message="حدث خطأ داخلي في الخادم"), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """معالج الأخطاء العام"""
    print(f"❌ خطأ غير متوقع: {str(e)}")
    return render_template('error.html', error_message="حدث خطأ غير متوقع"), 500                    
# =====================================================
# تشغيل التطبيق
# =====================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)