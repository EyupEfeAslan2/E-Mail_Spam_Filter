"""
Adaptif Öğrenme (Sürekli Öğrenme) Modülü

Bu modül, kullanıcı bildirimlerini (False Positive / False Negative) alarak
sistemin canlı olarak kendini güncellemesini sağlar.
"""

import os
import pandas as pd
from core.text_utils import clean_text
from core.model import HybridSpamFilter

class AdaptiveSystem:
    def __init__(self, filter_system: HybridSpamFilter):
        self.filter_system = filter_system
        self.reports_file = "data/processed/user_reports.csv"
        
        # Eğer rapor dosyası yoksa başlıkları (header) ile oluştur
        if not os.path.exists(self.reports_file):
            os.makedirs(os.path.dirname(self.reports_file), exist_ok=True)
            pd.DataFrame(columns=['text', 'label', 'text_cleaned']).to_csv(self.reports_file, index=False)
            
    def report_spam(self, email_text: str):
        """Kullanıcının gözden kaçan bir spam'i anında engellemesi için kullanılır."""
        cleaned_text = clean_text(email_text)
        
        # 1. Anında Engelleme: Bloom Filter'a ekle
        self.filter_system.bloom.add(cleaned_text)
        
        # 2. Gelecek Eğitim İçin Kaydet: CSV'ye ekle
        self._save_report(email_text, cleaned_text, label=1)
        
        return {"status": "success", "message": "Spam Bloom Filter'a anında eklendi ve periyodik eğitim kuyruğuna alındı."}

    def report_ham(self, email_text: str):
        """Kullanıcının yanlışlıkla Spam klasörüne düşmüş bir e-postayı (False Positive) Ham olarak bildirmesi."""
        cleaned_text = clean_text(email_text)
        
        # Gelecek Eğitim İçin Kaydet: CSV'ye ekle (1: Spam, 0: Ham)
        self._save_report(email_text, cleaned_text, label=0)
        
        return {"status": "success", "message": "False Positive bildirimi alındı. Model sonraki eğitimde bunu dikkate alacak."}

    def _save_report(self, raw_text, cleaned_text, label):
        """Bildirimi CSV dosyasına kaydeder."""
        df = pd.DataFrame([{
            'text': raw_text,
            'label': label,
            'text_cleaned': cleaned_text
        }])
        
        # Dosyanın sonuna (append mode) ekleyelim
        df.to_csv(self.reports_file, mode='a', header=False, index=False, encoding='utf-8')
        
        # Retrain tetikleyici kontrol (Örn: 100 girdi olursa)
        self._check_retrain_threshold()
        
    def _check_retrain_threshold(self):
        """Belirli bir eşiğe ulaşılınca (örn 50 rapor) modeli yeniden eğitmek için sinyal verebiliriz."""
        try:
            df = pd.read_csv(self.reports_file)
            if len(df) >= 50:
                print("Eğitim Eşiğine Ulaşıldı! Yeni veriler var olan datasete eklenip model yeniden eğitilmelidir.")
                # Gerçek senaryoda burada `core/train.py` bir subprocess (celery veya background task) ile çağrılır
                # Ancak şimdilik sadece uyarı veriyoruz. 
        except Exception:
            pass
