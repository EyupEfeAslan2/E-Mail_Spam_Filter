"""
Model Eğitim (Fine-Tuning) Modülü

Bu betik, Hugging Face kütüphanesinden hafif ve hızlı DistilBERT modelini indirir
ve temizlenmiş e-posta veri setimiz üzerinde (Spam tespiti için) yeniden eğitir.
"""

import pandas as pd
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from sklearn.model_selection import train_test_split

def load_data(filepath="data/processed/dataset.csv"):
    """Temizlenmiş veri setini yükler ve eğitim/test olarak böler."""
    print("Veri seti yükleniyor...")
    try:
        df = pd.read_csv(filepath)
        # Veriyi %80 eğitim, %20 test olacak şekilde ayırıyoruz
        train_texts, test_texts, train_labels, test_labels = train_test_split(
            df['text'].tolist(), df['label'].tolist(), test_size=0.2, random_state=42
        )
        return train_texts, test_texts, train_labels, test_labels
    except FileNotFoundError:
        print(f"HATA: {filepath} bulunamadı! Önce veri ön işleme adımını tamamlayın.")
        return None, None, None, None

def initialize_model():
    """DistilBERT modelini ve kelime parçalayıcıyı (tokenizer) indirip hazırlar."""
    print("DistilBERT modeli ve Tokenizer indiriliyor...")
    
    # Kelimeleri modelin anlayacağı sayılara çeviren araç
    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
    
    # İki sınıflı (Spam=1, Ham=0) sınıflandırma yapacak şekilde ayarlanmış model
    model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=2)
    
    return tokenizer, model

if __name__ == "__main__":
    print("--- Hibrit Spam Filtresi: Model Eğitim Süreci Başlıyor ---")
    
    # 1. Veriyi yükle (Veri ön işleme görevi bitince burası çalışacak)
    # train_texts, test_texts, train_labels, test_labels = load_data()
    
    # 2. Modeli hazırla
    tokenizer, model = initialize_model()
    
    print("Altyapı hazır. Model eğitime (fine-tuning) başlanabilir!")