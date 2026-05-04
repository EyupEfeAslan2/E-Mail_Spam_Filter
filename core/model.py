"""
Hibrit Çıkarım (Inference) Modülü

Bu modül, gelen e-postaları O(1) hızındaki Bloom Filter ve
eğitilmiş DistilBERT modelinden geçirerek tahmin oluşturur.
"""

import os
import json
import time
from threading import RLock
try:
    import torch
    from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
except ModuleNotFoundError:
    torch = None
    DistilBertTokenizer = None
    DistilBertForSequenceClassification = None
from core.bloom_filter import BloomFilter
from core.config import settings
from core.security import privacy_hash
from core.text_utils import clean_text

class HybridSpamFilter:
    def __init__(self, model_path=None):
        """Modeli ve Bloom Filtresini yükler."""
        self.model_path = model_path or settings.model_path
        # Veri yapısı: Bloom Filter. Bilinen spam imzalarını O(k) zamanda yakalar.
        self.bloom = BloomFilter(
            size=settings.bloom_size,
            hash_count=settings.bloom_hash_count,
            storage_path=settings.bloom_path,
        )
        # Veri yapısı: Set. Yanlış pozitif bildirilen içerikler Bloom sonucunu geçersiz kılar.
        self.ham_allowlist = set()
        self._lock = RLock()
        self.tokenizer = None
        self.model = None
        self.model_status = "unloaded"
        self.device = "cpu"
        if torch is not None:
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() and not settings.force_cpu else "cpu"
            )
        self.threshold = self._load_threshold()
        self._load_ham_allowlist()
        
        print("Model yükleniyor...")
        try:
            if torch is None or DistilBertTokenizer is None or DistilBertForSequenceClassification is None:
                raise RuntimeError("PyTorch/Transformers dependency unavailable")
            if os.path.exists(self.model_path):
                self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_path)
                self.model = DistilBertForSequenceClassification.from_pretrained(self.model_path)
                self.model_status = "fine_tuned"
                print(f"Eğitilmiş model {self.model_path} dizininden yüklendi.")
            else:
                print("Eğitilmiş model bulunamadı! Lokal cache'de DistilBERT aranıyor.")
                self.tokenizer = DistilBertTokenizer.from_pretrained(
                    settings.model_name, local_files_only=True
                )
                self.model = DistilBertForSequenceClassification.from_pretrained(
                    settings.model_name, num_labels=2, local_files_only=True
                )
                self.model_status = "base_model_untrained_for_project"
        except Exception as e:
            print(f"Model yüklenirken hata oluştu: {e}")
            self.model_status = "fallback_only"
        
        if self.model is not None and torch is not None:
            self.model.to(self.device)
            self.model.eval() # Çıkarım (prediction) moduna al

    def _load_threshold(self) -> float:
        try:
            with open(settings.threshold_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return float(data.get("threshold", settings.default_threshold))
        except (OSError, ValueError, json.JSONDecodeError):
            return settings.default_threshold

    def _save_threshold(self) -> None:
        os.makedirs(os.path.dirname(settings.threshold_path), exist_ok=True)
        with open(settings.threshold_path, "w", encoding="utf-8") as f:
            json.dump({"threshold": self.threshold}, f)

    def _load_ham_allowlist(self) -> None:
        try:
            with open(settings.ham_allowlist_path, "r", encoding="utf-8") as f:
                self.ham_allowlist = {line.strip() for line in f if line.strip()}
        except OSError:
            self.ham_allowlist = set()

    def _save_ham_allowlist(self) -> None:
        os.makedirs(os.path.dirname(settings.ham_allowlist_path), exist_ok=True)
        with open(settings.ham_allowlist_path, "w", encoding="utf-8") as f:
            for item in sorted(self.ham_allowlist):
                f.write(f"{item}\n")

    def add_spam_signature(self, cleaned_text: str) -> None:
        with self._lock:
            self.bloom.add(cleaned_text)
            self.bloom.save()

    def allow_ham_signature(self, cleaned_text: str) -> None:
        with self._lock:
            self.ham_allowlist.add(privacy_hash(cleaned_text))
            self._save_ham_allowlist()

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
        url_hit = "url" in lowered
        score = min(0.99, 0.25 + 0.15 * keyword_hits + (0.2 if url_hit else 0.0))
        if keyword_hits >= 2 or (keyword_hits >= 1 and url_hit):
            return {"prediction": "Spam", "confidence": score, "layer": "Rule-based Fallback"}
        return {"prediction": "Ham", "confidence": max(0.51, 1 - score), "layer": "Rule-based Fallback"}
    
    def predict(self, email_text: str):
        """E-postanın spam olup olmadığını tahmin eder."""
        start = time.perf_counter()
        # 1. Metni Temizle
        cleaned_text = clean_text(email_text)
        signature = privacy_hash(cleaned_text)
        
        # 2. Ham Allowlist (Yanlış pozitif düzeltme katmanı)
        if signature in self.ham_allowlist:
            return {
                "prediction": "Ham",
                "confidence": 1.0,
                "layer": "Ham Allowlist",
                "model_status": self.model_status,
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            }

        # 3. Bloom Filter (Hızlı Katman)
        with self._lock:
            bloom_hit = self.bloom.check(cleaned_text)
        if bloom_hit:
            return {
                "prediction": "Spam",
                "confidence": 1.0,
                "layer": "Bloom Filter (Fast)",
                "model_status": self.model_status,
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            }
        
        # 4. DistilBERT (Derin Katman)
        if self.model is None or self.tokenizer is None:
            result = self._predict_fallback(cleaned_text)
            result["model_status"] = self.model_status
            result["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
            return result

        with torch.no_grad():
            inputs = self.tokenizer(
                cleaned_text, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=settings.model_max_length
            )
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
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
                    "layer": "DistilBERT (Deep)",
                    "model_status": self.model_status,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                }
            else:
                return {
                    "prediction": "Ham",
                    "confidence": ham_prob,
                    "layer": "DistilBERT (Deep)",
                    "model_status": self.model_status,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                }

    def batch_predict(self, email_texts: list[str]) -> list[dict]:
        """Data structure: List. High-volume callers can process batches with stable ordering."""
        return [self.predict(text) for text in email_texts]

    def set_threshold(self, value: float):
        """Spam hassasiyet eşiğini günceller."""
        if 0.0 <= value <= 1.0:
            with self._lock:
                self.threshold = value
                self._save_threshold()
        else:
            raise ValueError("Threshold 0 ile 1 arasında olmalıdır.")

    def health(self) -> dict:
        metrics = self.metrics()
        ready = self.model_status == "fine_tuned" and self.metrics_pass(metrics)
        return {
            "model_status": self.model_status,
            "threshold": self.threshold,
            "device": str(self.device),
            "bloom_size": self.bloom.size,
            "bloom_hash_count": self.bloom.hash_count,
            "ham_allowlist_count": len(self.ham_allowlist),
            "metrics": metrics,
            "ready": ready,
        }

    def metrics(self) -> dict:
        metrics_path = os.path.join(self.model_path, "metrics.json")
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def metrics_pass(self, metrics: dict) -> bool:
        return (
            float(metrics.get("eval_precision", metrics.get("precision", 0.0))) >= settings.min_precision
            and float(metrics.get("eval_recall", metrics.get("recall", 0.0))) >= settings.min_recall
            and float(metrics.get("eval_f1", metrics.get("f1", 0.0))) >= settings.min_f1
        )
