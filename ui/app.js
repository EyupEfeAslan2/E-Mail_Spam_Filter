/**
 * Stack Veri Yapısı (Data Structure)
 * Sayfa geçişlerini yönetmek için kullanılır (LIFO prensibi).
 */
class NavigationStack {
    constructor() {
        this.items = [];
    }

    push(pageId) {
        this.items.push(pageId);
    }

    pop() {
        if (this.isEmpty()) return null;
        return this.items.pop();
    }

    peek() {
        if (this.isEmpty()) return null;
        return this.items[this.items.length - 1];
    }

    isEmpty() {
        return this.items.length === 0;
    }

    size() {
        return this.items.length;
    }
}

// Global Uygulama Durumu
const appState = {
    navStack: new NavigationStack(),
    currentPage: 'page-home',
    currentEmailText: '',
    // Getter/Setter ile localStorage ve state yönetimini senkronize ettik
    get adminToken() {
        return localStorage.getItem('spamguard_admin_token') || '';
    },
    set adminToken(value) {
        localStorage.setItem('spamguard_admin_token', value.trim());
    }
};

/**
 * API İstekleri için Temel URL Yapılandırması
 * Eğer UI dosyalarını Live Server ile (örn: 5500) açıyorsan, Docker backend'ine (8000 veya 9000) erişebilmesi için
 * backend URL'ini dinamik olarak ayarlar. UI ve API aynı porttaysa direkt relative path (göreceli yol) kullanır.
 */
const getApiUrl = (endpoint) => {
    const BACKEND_PORT = "9000"; 
    
    // Eğer UI live server (5500 vb.) ile açıldıysa istekleri Docker backend portuna yönlendirir
    if (window.location.port && window.location.port !== BACKEND_PORT && window.location.port !== "") {
        return `http://${window.location.hostname}:${BACKEND_PORT}${endpoint}`;
    }
    return endpoint; // Aynı porttaysa veya production ortamındaysa direkt relative path kullanır
};

// İsteklerde tekrarı önlemek için merkezi Header oluşturucu
function getRequestHeaders(extraHeaders = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...extraHeaders
    };
    if (appState.adminToken) {
        headers['X-Admin-Token'] = appState.adminToken;
    }
    return headers;
}

// Sayfa Yönlendirme Fonksiyonu
function navigateTo(pageId) {
    if (appState.currentPage === pageId) return;

    // Mevcut sayfayı yığına ekle (Stack Push)
    appState.navStack.push(appState.currentPage);

    // Animasyonla geçiş yap
    transitionPages(appState.currentPage, pageId, 'forward');
    
    appState.currentPage = pageId;
    updateBackButton();
}

// Geri Dönme Fonksiyonu
function navigateBack() {
    if (appState.navStack.isEmpty()) return;

    // Yığından önceki sayfayı al (Stack Pop)
    const previousPage = appState.navStack.pop();

    // Animasyonla geçiş yap
    transitionPages(appState.currentPage, previousPage, 'backward');
    
    appState.currentPage = previousPage;
    updateBackButton();
}

// Sayfa Geçiş Animasyonları
function transitionPages(oldPageId, newPageId, direction) {
    const oldPage = document.getElementById(oldPageId);
    const newPage = document.getElementById(newPageId);

    if (direction === 'forward') {
        oldPage.classList.remove('active');
        oldPage.classList.add('exiting');
        
        newPage.classList.remove('exiting', 'entering-back');
        // Kısa bir gecikme ile yeni sayfayı getir
        setTimeout(() => {
            oldPage.classList.remove('exiting');
            newPage.classList.add('active');
        }, 50);
    } else {
        oldPage.classList.remove('active');
        oldPage.classList.add('entering-back'); // sağa doğru çıkar
        
        newPage.classList.remove('exiting', 'entering-back');
        setTimeout(() => {
            oldPage.classList.remove('entering-back');
            newPage.classList.add('active');
        }, 50);
    }
}

function updateBackButton() {
    const backBtn = document.getElementById('back-btn');
    if (appState.navStack.isEmpty()) {
        backBtn.classList.add('hidden');
    } else {
        backBtn.classList.remove('hidden');
    }
}

// Toast Bildirimi
function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.remove('hidden');
    
    // Trigger reflow
    void toast.offsetWidth;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.classList.add('hidden'), 300);
    }, 3000);
}

// API İstekleri - E-posta Analizi
async function analyzeEmail() {
    const textArea = document.getElementById('email-input');
    const text = textArea.value.trim();
    
    if (!text) {
        showToast('Lütfen analiz edilecek metni girin.');
        return;
    }

    const btn = document.getElementById('analyze-btn');
    const originalText = btn.textContent;
    btn.textContent = 'Analiz Ediliyor...';
    btn.disabled = true;

    try {
        const response = await fetch(getApiUrl('/predict'), {
            method: 'POST',
            headers: getRequestHeaders(),
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) throw new Error('API Hatası');
        
        const result = await response.json();
        appState.currentEmailText = text;
        displayResult(result);
    } catch (error) {
        showToast('Hata: Sunucuya ulaşılamadı veya model yüklenemedi.');
        console.error(error);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// API İstekleri - Geri Bildirim Raporlama
async function reportFeedback(type) {
    if (!appState.currentEmailText) return;

    const endpoint = type === 'spam' ? '/report/spam' : '/report/ham';
    
    try {
        const response = await fetch(getApiUrl(endpoint), {
            method: 'POST',
            headers: getRequestHeaders(),
            body: JSON.stringify({ text: appState.currentEmailText })
        });

        if (!response.ok) throw new Error('API Hatası');
        
        await response.json();
        showToast('Geri bildiriminiz alındı. Teşekkürler!');
    } catch (error) {
        showToast('Hata: Bildirim gönderilemedi.');
        console.error(error);
    }
}

// Sonuçları Ekranda Gösterme
function displayResult(result) {
    const container = document.getElementById('result-container');
    const badge = document.getElementById('result-badge');
    const layer = document.getElementById('result-layer');
    const bar = document.getElementById('confidence-bar');
    const confText = document.getElementById('confidence-text');

    container.classList.remove('hidden');
    badge.className = 'badge';
    
    const percentage = Math.round(result.confidence * 100);
    
    if (result.prediction.toLowerCase() === 'spam') {
        badge.textContent = 'SPAM';
        badge.classList.add('spam');
        bar.style.backgroundColor = 'var(--danger)';
    } else {
        badge.textContent = 'GÜVENLİ (HAM)';
        badge.classList.add('ham');
        bar.style.backgroundColor = 'var(--success)';
    }

    layer.textContent = `Katman: ${result.layer}`;
    confText.textContent = `Güven Skoru: %${percentage}`;
    
    // Bar genişliğini animasyonla arttır
    setTimeout(() => {
        bar.style.width = `${percentage}%`;
    }, 100);
}

// Admin Ayarları - Hassasiyet Değerini Çekme
async function fetchSensitivity() {
    try {
        const response = await fetch(getApiUrl('/admin/sensitivity'), {
            headers: getRequestHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            const slider = document.getElementById('sensitivity-slider');
            const valDisplay = document.getElementById('sensitivity-value');
            slider.value = data.threshold;
            valDisplay.textContent = data.threshold;
            await fetchAdminHealth();
        } else if (response.status === 401) {
            showToast('Yönetici tokenı geçersiz veya gerekli.');
        }
    } catch (e) {
        console.error('Hassasiyet ayarı alınamadı', e);
        showToast('Hata: Admin ayarlarına erişilemedi.');
    }
}

// Admin Ayarları - Sistem Durumu (Health) Kontrolü
async function fetchAdminHealth() {
    const health = document.getElementById('admin-health');
    try {
        const response = await fetch(getApiUrl('/admin/health'), {
            headers: getRequestHeaders()
        });
        if (!response.ok) return;
        const data = await response.json();
        const readiness = data.ready ? 'Hazır' : 'Hazır Değil';
        health.textContent = `Model: ${data.model_status} | ${readiness} | Cihaz: ${data.device} | Bloom: ${data.bloom_size}/${data.bloom_hash_count}`;
    } catch (e) {
        console.error('Sistem durumu alınamadı', e);
        health.textContent = 'Sistem durumu: Sunucu bağlantısı yok.';
    }
}

// Admin İşlemleri - Yeniden Eğitimi Tetikleme
async function requestRetrain() {
    try {
        const response = await fetch(getApiUrl('/admin/retrain'), {
            method: 'POST',
            headers: getRequestHeaders()
        });
        if (response.ok) {
            showToast('Yeniden eğitim kuyruğa alındı.');
            await fetchAdminHealth();
        } else {
            showToast('Hata: Yeniden eğitim başlatılamadı.');
        }
    } catch (e) {
        showToast('Hata: Sunucuya ulaşılamadı.');
        console.error(e);
    }
}

// Admin İşlemleri - Hassasiyet Değerini Kaydetme
async function saveSensitivity() {
    const slider = document.getElementById('sensitivity-slider');
    const threshold = parseFloat(slider.value);
    
    try {
        const response = await fetch(getApiUrl('/admin/sensitivity'), {
            method: 'POST',
            headers: getRequestHeaders(),
            body: JSON.stringify({ threshold: threshold })
        });
        
        if (response.ok) {
            showToast('Hassasiyet ayarı başarıyla kaydedildi!');
        } else {
            showToast('Hata: Ayar kaydedilemedi.');
        }
    } catch (e) {
        showToast('Hata: Sunucuya ulaşılamadı.');
        console.error(e);
    }
}

// Event Listeners (Uygulama Yüklendiğinde Tetiklenen Yapılar)
document.addEventListener('DOMContentLoaded', () => {
    // Navigasyon Buton Dinleyicileri
    document.getElementById('nav-to-check').addEventListener('click', () => navigateTo('page-check'));
    document.getElementById('nav-to-admin').addEventListener('click', () => {
        navigateTo('page-admin');
        fetchSensitivity(); // Admin sayfasına geçildiğinde güncel veriyi çek
    });
    document.getElementById('nav-to-about').addEventListener('click', () => navigateTo('page-about'));
    document.getElementById('back-btn').addEventListener('click', navigateBack);

    // Ana İşlem Buton Dinleyicileri
    document.getElementById('analyze-btn').addEventListener('click', analyzeEmail);
    document.getElementById('report-spam-btn').addEventListener('click', () => reportFeedback('spam'));
    document.getElementById('report-ham-btn').addEventListener('click', () => reportFeedback('ham'));
    
    // Admin Arayüz Dinleyicileri
    const slider = document.getElementById('sensitivity-slider');
    const valDisplay = document.getElementById('sensitivity-value');
    const adminTokenInput = document.getElementById('admin-token');
    
    // Başlangıçta kayıtlı tokenı arayüze bas
    adminTokenInput.value = appState.adminToken;
    
    adminTokenInput.addEventListener('input', (e) => {
        appState.adminToken = e.target.value; // Setter otomatik tetiklenir ve localStorage'a yazar
    });
    
    slider.addEventListener('input', (e) => {
        valDisplay.textContent = e.target.value;
    });
    
    document.getElementById('save-sensitivity-btn').addEventListener('click', saveSensitivity);
    document.getElementById('retrain-btn').addEventListener('click', requestRetrain);
});
