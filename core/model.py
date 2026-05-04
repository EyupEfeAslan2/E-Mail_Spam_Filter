"""
Hibrit Çıkarım (Inference) Modülü

Bu modül, gelen e-postaları O(1) hızındaki Bloom Filter ve
eğitilmiş DistilBERT modelinden geçirerek tahmin oluşturur.
"""

import os
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from core.bloom_filter import BloomFilter
from core.text_utils import clean_text

class HybridSpamFilter:
    def __init__(self, model_path="data/model"):
        """Modeli ve Bloom Filtresini yükler."""
        self.bloom = BloomFilter(size=100000, hash_count=5)
        self.tokenizer = None
        self.model = None
        self.threshold = 0.5  # Admin sensitivity threshold
        
        print("Model yükleniyor...")
        try:
            if os.path.exists(model_path):
                self.tokenizer = DistilBertTokenizer.from_pretrained(model_path)
                self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
                print(f"Eğitilmiş model {model_path} dizininden yüklendi.")
            else:
                print("Eğitilmiş model bulunamadı! Lokal cache'de DistilBERT aranıyor.")
                self.tokenizer = DistilBertTokenizer.from_pretrained(
                    'distilbert-base-uncased', local_files_only=True
                )
                self.model = DistilBertForSequenceClassification.from_pretrained(
                    'distilbert-base-uncased', num_labels=2, local_files_only=True
                )
        except Exception as e:
            print(f"Model yüklenirken hata oluştu: {e}")
        
        if self.model is not None:
            self.model.eval() # Çıkarım (prediction) moduna al

    def _predict_fallback(self, cleaned_text: str):
        """
        DistilBERT yüklenemezse çevrimdışı basit bir yedek tahmin çalıştırır.
        Bu yol sadece servis sürekliliği içindir; model kadar doğru değildir.
        """
        spam_keywords = (
            "free", "winner", "win", "prize", "urgent", "click", "offer",
            "lottery", "credit", "money", "bonus", "discount", "viagra"
        )
        lowered = cleaned_text.lower()
        keyword_hits = sum(1 for k in spam_keywords if k in lowered)
        url_hit = "[url]" in lowered
        score = min(0.99, 0.25 + 0.15 * keyword_hits + (0.2 if url_hit else 0.0))
        if keyword_hits >= 2 or (keyword_hits >= 1 and url_hit):
            return {"prediction": "Spam", "confidence": score, "layer": "Rule-based Fallback"}
        return {"prediction": "Ham", "confidence": max(0.51, 1 - score), "layer": "Rule-based Fallback"}
    
    def predict(self, email_text: str):
        """E-postanın spam olup olmadığını tahmin eder."""
        # 1. Metni Temizle
        cleaned_text = clean_text(email_text)
        
        # 2. Bloom Filter (Hızlı Katman)
        if self.bloom.check(cleaned_text):
            return {
                "prediction": "Spam",
                "confidence": 1.0,
                "layer": "Bloom Filter (Fast)"
            }
        
        # 3. DistilBERT (Derin Katman)
        if self.model is None or self.tokenizer is None:
            return self._predict_fallback(cleaned_text)

        with torch.no_grad():
            inputs = self.tokenizer(
                cleaned_text, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=128
            )
            outputs = self.model(**inputs)
            scores = torch.nn.functional.softmax(outputs.logits, dim=1)
            
            # Spam=1, Ham=0 varsayımı
            # scores[0][1] Spam olasılığı, scores[0][0] Ham olasılığı
            spam_prob = scores[0][1].item()
            ham_prob = scores[0][0].item()
            
            if spam_prob > self.threshold:
                return {
                    "prediction": "Spam",
                    "confidence": spam_prob,
                    "layer": "DistilBERT (Deep)"
                }
            else:
                return {
                    "prediction": "Ham",
                    "confidence": ham_prob,
                    "layer": "DistilBERT (Deep)"
                }

    def set_threshold(self, value: float):
        """Spam hassasiyet eşiğini günceller."""
        if 0.0 <= value <= 1.0:
            self.threshold = value
        else:
            raise ValueError("Threshold 0 ile 1 arasında olmalıdır.")
