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
    adminToken: localStorage.getItem('spamguard_admin_token') || ''
};

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

// API İstekleri
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
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) throw new Error('API Hatası');
        
        const result = await response.json();
        appState.currentEmailText = text;
        displayResult(result);
    } catch (error) {
        showToast('Hata: Sunucuya ulaşılamadı.');
        console.error(error);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

async function reportFeedback(type) {
    if (!appState.currentEmailText) return;

    const endpoint = type === 'spam' ? '/report/spam' : '/report/ham';
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: appState.currentEmailText })
        });

        if (!response.ok) throw new Error('API Hatası');
        
        const result = await response.json();
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
    
    // Reset classes
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
    
    // Animate bar width
    setTimeout(() => {
        bar.style.width = `${percentage}%`;
    }, 100);
}

// Admin Ayarları
async function fetchSensitivity() {
    try {
        const response = await fetch('/admin/sensitivity', {
            headers: getAdminHeaders()
        });
        if (response.ok) {
            const data = await response.json();
            const slider = document.getElementById('sensitivity-slider');
            const valDisplay = document.getElementById('sensitivity-value');
            slider.value = data.threshold;
            valDisplay.textContent = data.threshold;
            await fetchAdminHealth();
        } else if (response.status === 401) {
            showToast('Yönetici token gerekli.');
        }
    } catch (e) {
        console.error('Hassasiyet ayarı alınamadı', e);
    }
}

function getAdminHeaders() {
    // Veri yapısı: Hash/token. Admin token API tarafında sabit-zamanlı karşılaştırılır.
    return appState.adminToken ? { 'X-Admin-Token': appState.adminToken } : {};
}

async function fetchAdminHealth() {
    const health = document.getElementById('admin-health');
    try {
        const response = await fetch('/admin/health', {
            headers: getAdminHeaders()
        });
        if (!response.ok) return;
        const data = await response.json();
        const readiness = data.ready ? 'Hazır' : 'Hazır Değil';
        health.textContent = `Model: ${data.model_status} | ${readiness} | Cihaz: ${data.device} | Bloom: ${data.bloom_size}/${data.bloom_hash_count}`;
    } catch (e) {
        console.error('Sistem durumu alınamadı', e);
    }
}

async function requestRetrain() {
    try {
        const response = await fetch('/admin/retrain', {
            method: 'POST',
            headers: getAdminHeaders()
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

async function saveSensitivity() {
    const slider = document.getElementById('sensitivity-slider');
    const threshold = parseFloat(slider.value);
    
    try {
        const response = await fetch('/admin/sensitivity', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getAdminHeaders() },
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

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Navigasyon Butonları
    document.getElementById('nav-to-check').addEventListener('click', () => navigateTo('page-check'));
    document.getElementById('nav-to-admin').addEventListener('click', () => {
        navigateTo('page-admin');
        fetchSensitivity(); // Admin sayfasına girince güncel değeri al
    });
    document.getElementById('nav-to-about').addEventListener('click', () => navigateTo('page-about'));
    document.getElementById('back-btn').addEventListener('click', navigateBack);

    // İşlem Butonları
    document.getElementById('analyze-btn').addEventListener('click', analyzeEmail);
    document.getElementById('report-spam-btn').addEventListener('click', () => reportFeedback('spam'));
    document.getElementById('report-ham-btn').addEventListener('click', () => reportFeedback('ham'));
    
    // Admin İşlemleri
    const slider = document.getElementById('sensitivity-slider');
    const valDisplay = document.getElementById('sensitivity-value');
    const adminToken = document.getElementById('admin-token');
    adminToken.value = appState.adminToken;
    adminToken.addEventListener('input', (e) => {
        appState.adminToken = e.target.value.trim();
        localStorage.setItem('spamguard_admin_token', appState.adminToken);
    });
    slider.addEventListener('input', (e) => {
        valDisplay.textContent = e.target.value;
    });
    document.getElementById('save-sensitivity-btn').addEventListener('click', saveSensitivity);
    document.getElementById('retrain-btn').addEventListener('click', requestRetrain);
});
