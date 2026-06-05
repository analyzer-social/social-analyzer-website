// config.js - ملف تهيئة Supabase (سيتم استدعاؤه قبل استخدام supabaseClient)
// المتغيرات سيتم تمريرها من Flask عبر window

console.log('✅ config.js loaded');

// دالة مساعدة للتحقق من جاهزية Supabase
function isSupabaseReady() {
    return window.SUPABASE_URL && window.SUPABASE_ANON_KEY;
}

// يمكن إضافة دوال مساعدة أخرى هنا إذا لزم الأمر