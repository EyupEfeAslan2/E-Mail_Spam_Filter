"""
Adaptif Öğrenme (Sürekli Öğrenme) Modülü

Bu modül, kullanıcı bildirimlerini (False Positive / False Negative) alarak
sistemin canlı olarak kendini güncellemesini sağlar.
"""

import os
from datetime import datetime, timezone
import pandas as pd
from core.config import settings
from core.retrain import retrain_queue
from core.security import privacy_hash, redact_email_text
from core.text_utils import clean_text
from core.model import HybridSpamFilter

class AdaptiveSystem:
    def __init__(self, filter_system: HybridSpamFilter):
        self.filter_system = filter_system
        self.reports_file = settings.reports_file
        
        # Eğer rapor dosyası yoksa başlıkları (header) ile oluştur
        if not os.path.exists(self.reports_file):
            os.makedirs(os.path.dirname(self.reports_file), exist_ok=True)
            pd.DataFrame(
                columns=[
                    'created_at',
                    'label',
                    'text_redacted',
                    'text_hash',
                    'text_cleaned_hash',
                    'feedback_type',
                ]
            ).to_csv(self.reports_file, index=False)
            
    def report_spam(self, email_text: str):
        """Kullanıcının gözden kaçan bir spam'i anında engellemesi için kullanılır."""
        cleaned_text = clean_text(email_text)
        
        # 1. Anında Engelleme: Bloom Filter'a ekle
        self.filter_system.add_spam_signature(cleaned_text)
        
        # 2. Gelecek Eğitim İçin Kaydet: CSV'ye ekle
        self._save_report(email_text, cleaned_text, label=1, feedback_type="false_negative")
        
        return {"status": "success", "message": "Spam Bloom Filter'a anında eklendi ve periyodik eğitim kuyruğuna alındı."}

    def report_ham(self, email_text: str):
        """Kullanıcının yanlışlıkla Spam klasörüne düşmüş bir e-postayı (False Positive) Ham olarak bildirmesi."""
        cleaned_text = clean_text(email_text)
        self.filter_system.allow_ham_signature(cleaned_text)
        
        # Gelecek Eğitim İçin Kaydet: CSV'ye ekle (1: Spam, 0: Ham)
        self._save_report(email_text, cleaned_text, label=0, feedback_type="false_positive")
        
        return {"status": "success", "message": "False Positive bildirimi alındı. Model sonraki eğitimde bunu dikkate alacak."}

    def _save_report(self, raw_text, cleaned_text, label, feedback_type):
        """Bildirimi CSV dosyasına kaydeder."""
        # Veri yapısı: Hash. Ham e-posta saklamadan tekil feedback takibi sağlar.
        df = pd.DataFrame([{
            'created_at': datetime.now(timezone.utc).isoformat(),
            'label': label,
            'text_redacted': redact_email_text(raw_text),
            'text_hash': privacy_hash(raw_text),
            'text_cleaned_hash': privacy_hash(cleaned_text),
            'feedback_type': feedback_type,
        }])
        
        # Dosyanın sonuna (append mode) ekleyelim
        df.to_csv(self.reports_file, mode='a', header=False, index=False, encoding='utf-8')
        
        # Retrain tetikleyici kontrol (Örn: 100 girdi olursa)
        self._check_retrain_threshold()
        
    def _check_retrain_threshold(self):
        """Belirli bir eşiğe ulaşılınca (örn 50 rapor) modeli yeniden eğitmek için sinyal verebiliriz."""
        try:
            df = pd.read_csv(self.reports_file)
            if len(df) >= settings.feedback_retrain_threshold:
                retrain_queue.enqueue(
                    reason=f"feedback_threshold_reached:{len(df)}"
                )
        except Exception:
            pass
