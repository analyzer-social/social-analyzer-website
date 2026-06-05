// ========================================
// المتغيرات العامة
// ========================================
let currentToken = null;
let currentUser = null;
let userPermissions = null;

// ========================================
// دوال المصادقة
// ========================================

// محاكاة تسجيل الدخول عبر تلغرام (للتجربة المحلية)
function simulateTelegramLogin() {
    showToast('🔄 جاري محاكاة تسجيل الدخول عبر تلغرام...');
    
    // توليد بيانات تجريبية
    const testUser = {
        id: Math.floor(Math.random() * 1000000000),
        username: 'test_user_' + Math.floor(Math.random() * 1000),
        first_name: 'مستخدم',
        last_name: 'تجريبي',
        is_premium: false
    };
    
    localStorage.setItem('social_analyzer_token', 'dev_token_' + testUser.id);
    localStorage.setItem('user_data', JSON.stringify(testUser));
    
    setTimeout(() => {
        showToast('✅ تم تسجيل الدخول بنجاح! جاري التوجيه...');
        window.location.href = '/dashboard.html';
    }, 1000);
}

// محاكاة تسجيل الدخول عبر جوجل (للتجربة المحلية)
function simulateGoogleLogin() {
    showToast('🔄 جاري محاكاة تسجيل الدخول عبر جوجل...');
    
    const testUser = {
        id: 'google_' + Math.floor(Math.random() * 1000000),
        email: 'user' + Math.floor(Math.random() * 1000) + '@example.com',
        name: 'مستخدم جوجل',
        is_premium: false
    };
    
    localStorage.setItem('social_analyzer_token', 'google_dev_token_' + testUser.id);
    localStorage.setItem('user_data', JSON.stringify(testUser));
    
    setTimeout(() => {
        showToast('✅ تم تسجيل الدخول بنجاح!');
        window.location.href = '/dashboard.html';
    }, 1000);
}

// تهيئة المصادقة عبر جوجل (للإنتاج)
function initGoogleLogin() {
    showToast('🚧 ميزة تسجيل الدخول عبر جوجل قيد التطوير حالياً');
    // هنا ستضيف كود OAuth الحقيقي لاحقاً
}

// تسجيل الخروج
function logout() {
    localStorage.removeItem('social_analyzer_token');
    localStorage.removeItem('user_data');
    showToast('👋 تم تسجيل الخروج بنجاح');
    setTimeout(() => {
        window.location.href = '/index.html';
    }, 1000);
}

// التحقق من حالة تسجيل الدخول
function checkAuth() {
    const token = localStorage.getItem('social_analyzer_token');
    const user = localStorage.getItem('user_data');
    
    if (!token || !user) {
        window.location.href = '/index.html';
        return false;
    }
    
    currentToken = token;
    currentUser = JSON.parse(user);
    
    // عرض اسم المستخدم في الـ Sidebar
    const userNameSpan = document.getElementById('userName');
    if (userNameSpan) {
        userNameSpan.textContent = currentUser.username || currentUser.first_name || currentUser.email || 'مستخدم';
    }
    
    return true;
}

// ========================================
// دوال عرض الإشعارات (Toast)
// ========================================
function showToast(message, isError = false) {
    const toast = document.getElementById('toastMessage');
    if (!toast) return;
    
    toast.textContent = message;
    toast.style.background = isError ? '#f56565' : '#48bb78';
    toast.style.display = 'block';
    
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// ========================================
// دوال جلب البيانات من الـ API
// ========================================

// تحديد عنوان API الأساسي (من متغير البيئة أو الرابط المباشر)
const API_BASE_URL = '{{ API_BASE_URL|default("https://social-analyzer-flask-3.onrender.com") }}';
const API_BASE = API_BASE_URL.startsWith('http') ? API_BASE_URL : `https://${API_BASE_URL}`;

// جلب صلاحيات المستخدم والحسابات المسجلة
async function loadUserPermissions() {
    try {
        const response = await fetch(`${API_BASE}/api/user_permissions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: currentToken })
        });
        
        const result = await response.json();
        
        if (result.success) {
            userPermissions = result.data;
            return userPermissions;
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('Error loading permissions:', error);
        showToast('❌ فشل تحميل بيانات المستخدم', true);
        return null;
    }
}

// عرض الحسابات المسجلة
async function displayAccounts() {
    const accountsContainer = document.getElementById('accountsList');
    if (!accountsContainer) return;
    
    const permissions = await loadUserPermissions();
    if (!permissions) return;
    
    const platformInfo = {
        youtube: { name: 'يوتيوب', icon: 'fab fa-youtube', color: '#ff0000' },
        instagram: { name: 'انستقرام', icon: 'fab fa-instagram', color: '#e1306c' },
        tiktok: { name: 'تيك توك', icon: 'fab fa-tiktok', color: '#000000' },
        facebook: { name: 'فيسبوك', icon: 'fab fa-facebook-f', color: '#1877f2' },
        snapchat: { name: 'سناب شات', icon: 'fab fa-snapchat', color: '#fffc00' }
    };
    
    const accounts = permissions.accounts || {};
    const isPremium = permissions.is_premium || false;
    const dailyRemaining = permissions.daily_remaining || 0;
    const freeLimit = permissions.free_limit || 3;
    
    let html = '';
    let hasAny = false;
    
    // عرض الحصة المتبقية (للمستخدم المجاني)
    if (!isPremium) {
        html += `
            <div class="daily-limit-warning" style="background: #fef3c7; padding: 10px; border-radius: 12px; margin-bottom: 15px;">
                <i class="fas fa-info-circle"></i> 
                الحصة المتبقية اليوم: ${dailyRemaining} من ${freeLimit} تحليل
                ${dailyRemaining === 0 ? '<br><strong>⚠️ لقد وصلت للحد اليومي! قم بالترقية للمزيد.</strong>' : ''}
            </div>
        `;
    }
    
    for (const [platform, info] of Object.entries(platformInfo)) {
        const account = accounts[platform];
        if (account && account.account_identifier) {
            hasAny = true;
            const username = account.account_identifier.replace(/^@/, '');
            const isWorking = platform === 'youtube' || platform === 'tiktok';
            
            html += `
                <div class="account-item">
                    <div class="account-info">
                        <div class="account-icon" style="background: ${info.color}20;">
                            <i class="${info.icon}" style="color: ${info.color};"></i>
                        </div>
                        <div>
                            <strong>${info.name}</strong>
                            <div style="font-size: 12px; color: ${info.color};">@${username}</div>
                        </div>
                    </div>
                    <button class="btn-analyze ${!isWorking ? 'coming-soon' : ''}" 
                            onclick="analyzeAccount('${platform}', '${account.account_identifier}')"
                            ${!isWorking ? 'disabled' : ''}>
                        <i class="fas fa-chart-line"></i> ${isWorking ? 'تحليل' : 'قيد التطوير'}
                    </button>
                </div>
            `;
        }
    }
    
    if (!hasAny) {
        html = '<div style="text-align: center; padding: 40px; color: #a0aec0;"><i class="fas fa-info-circle" style="font-size: 48px; margin-bottom: 15px;"></i><p>لا توجد حسابات مسجلة</p><p style="font-size: 12px;">يمكنك إضافة حساباتك من تبويب "بياناتي"</p></div>';
    }
    
    accountsContainer.innerHTML = html;
}

// تحليل حساب
async function analyzeAccount(platform, identifier) {
    showToast(`⏳ جاري تحليل ${platform}...`);
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                token: currentToken, 
                platform: platform, 
                identifier: identifier.replace(/^@/, '')
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✅ تم التحليل بنجاح!');
            setTimeout(() => {
                loadRecentAnalyses();
                loadUserPermissions();
            }, 1500);
        } else {
            showToast(`❌ فشل التحليل: ${result.error || 'خطأ غير معروف'}`, true);
        }
    } catch (error) {
        showToast('❌ خطأ في الاتصال بالخادم', true);
    }
}

// جلب آخر التحليلات
async function loadRecentAnalyses() {
    const container = document.getElementById('recentAnalysesList');
    if (!container) return;
    
    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> جاري التحميل...</div>';
    
    try {
        const response = await fetch(`/api/analysis/history?token=${encodeURIComponent(currentToken)}&limit=10`);
        const result = await response.json();
        
        if (!result.success || !result.data || result.data.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: 40px; color: #a0aec0;"><i class="fas fa-chart-line" style="font-size: 48px; margin-bottom: 15px;"></i><p>لا توجد تحليلات سابقة</p></div>';
            return;
        }
        
        let html = '';
        for (const analysis of result.data.slice(0, 5)) {
            const analysisDate = new Date(analysis.analysis_date);
            const dateStr = analysisDate.toLocaleDateString('ar-EG');
            
            html += `
                <div class="analysis-card">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <strong>${analysis.platform === 'youtube' ? '📺 يوتيوب' : '🎵 تيك توك'}</strong>
                        <span style="font-size: 11px; color: #a0aec0;">${dateStr}</span>
                    </div>
                    <div style="margin-bottom: 8px;">@${analysis.account_name}</div>
                    <div class="analysis-stats">
                        <span class="stat-mini">👥 ${formatNumber(analysis.subscribers || analysis.followers)}</span>
                        <span class="stat-mini">👁️ ${formatNumber(analysis.total_views)}</span>
                    </div>
                    <div class="action-buttons">
                        <button class="btn-details" onclick="showFullReport(${analysis.id})">
                            <i class="fas fa-file-alt"></i> عرض التقرير
                        </button>
                        <button class="btn-download" onclick="downloadReport(${analysis.id})">
                            <i class="fas fa-download"></i> تنزيل
                        </button>
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading analyses:', error);
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #f56565;">❌ فشل تحميل التحليلات</div>';
    }
}

// تنسيق الأرقام
function formatNumber(num) {
    if (!num && num !== 0) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

// عرض التقرير الكامل
async function showFullReport(analysisId) {
    const modal = document.getElementById('reportModal');
    const modalText = document.getElementById('modalReportText');
    
    modal.style.display = 'flex';
    modalText.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> جاري تحميل التقرير...</div>';
    
    try {
        const response = await fetch('/api/send-report-to-bot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: currentToken, analysis_id: analysisId, return_report: true })
        });
        
        const result = await response.json();
        
        if (result.success && result.report_text) {
            modalText.innerHTML = result.report_text.replace(/\n/g, '<br>');
        } else {
            modalText.innerHTML = '<p style="color: #f56565;">❌ فشل تحميل التقرير</p>';
        }
    } catch (error) {
        modalText.innerHTML = '<p style="color: #f56565;">❌ حدث خطأ أثناء تحميل التقرير</p>';
    }
}

// تنزيل التقرير
async function downloadReport(analysisId) {
    showToast('⏳ جاري تجهيز التقرير...');
    
    try {
        const response = await fetch('/api/send-report-to-bot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: currentToken, analysis_id: analysisId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✅ تم إرسال التقرير إلى البوت!');
        } else {
            showToast('❌ فشل إرسال التقرير', true);
        }
    } catch (error) {
        showToast('❌ حدث خطأ', true);
    }
}

// إغلاق النافذة المنبثقة
function closeModal() {
    document.getElementById('reportModal').style.display = 'none';
}

// التبديل بين التبويبات
function initTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.getAttribute('data-tab');
            
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(tabId + 'Tab').classList.add('active');
        });
    });
}

// ========================================
// التهيئة الرئيسية عند تحميل الصفحة
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    // التحقق من الصفحة الحالية
    if (window.location.pathname.includes('dashboard.html')) {
        if (!checkAuth()) return;
        
        initTabs();
        displayAccounts();
        loadRecentAnalyses();
    }
});

// ربط الدوال للنطاق العام
window.simulateTelegramLogin = simulateTelegramLogin;
window.simulateGoogleLogin = simulateGoogleLogin;
window.initGoogleLogin = initGoogleLogin;
window.logout = logout;
window.analyzeAccount = analyzeAccount;
window.loadRecentAnalyses = loadRecentAnalyses;
window.showFullReport = showFullReport;
window.downloadReport = downloadReport;
window.closeModal = closeModal;