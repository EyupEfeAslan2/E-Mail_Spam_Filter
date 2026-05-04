"""
Model Eğitim (Fine-Tuning) Modülü

Bu betik, DistilBERT modelini indirir ve verisetimizin küçük bir kısmı üzerinde 
(CPU optimizasyonlu) hızlıca eğitir.
"""

import os
import pandas as pd
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from datasets import Dataset

# Parametreler (CPU/Hızlı Deneme için Düşük Tutuldu)
MODEL_NAME = 'distilbert-base-uncased'
SAMPLE_SIZE = 2000  # CPU'da çok uzun sürmemesi için verinin küçük kısmını alıyoruz
EPOCHS = 1
BATCH_SIZE = 8

def load_data(filepath="data/processed/dataset.csv"):
    """Temizlenmiş veri setini yükler ve eğitim/test olarak böler."""
    print("Veri seti yükleniyor...")
    try:
        df = pd.read_csv(filepath)
        # CPU Eğitimi için rastgele küçük bir alt küme (sample) alıyoruz
        df = df.sample(n=min(SAMPLE_SIZE, len(df)), random_state=42)
        
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
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
    return tokenizer, model

def train_model():
    print("--- Hibrit Spam Filtresi: Model Eğitim Süreci Başlıyor ---")
    
    train_texts, test_texts, train_labels, test_labels = load_data()
    if train_texts is None:
        return
    
    tokenizer, model = initialize_model()
    
    print("Veriler Tokenizer'dan geçiriliyor (Tokenization)...")
    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=128)
    test_encodings = tokenizer(test_texts, truncation=True, padding=True, max_length=128)

    # Dataset formatına çeviriyoruz
    train_dataset = Dataset.from_dict({
        'labels': train_labels,
        'input_ids': train_encodings['input_ids'],
        'attention_mask': train_encodings['attention_mask']
    })
    
    test_dataset = Dataset.from_dict({
        'labels': test_labels,
        'input_ids': test_encodings['input_ids'],
        'attention_mask': test_encodings['attention_mask']
    })

    print("Eğitim ayarları (CPU optimizasyonlu) yapılandırılıyor...")
    training_args = TrainingArguments(
        output_dir='./runs',
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_dir='./logs',
        logging_steps=10,
        no_cuda=True, # GPU YOK zorlaması
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset
    )

    print("Model eğitiliyor (Bu işlem CPU üzerinde biraz zaman alabilir)...")
    trainer.train()
    
    print("Eğitim tamamlandı. Model kaydediliyor...")
    os.makedirs('data/model', exist_ok=True)
    model.save_pretrained('data/model')
    tokenizer.save_pretrained('data/model')
    print("Model başarıyla 'data/model' dizinine kaydedildi!")

if __name__ == "__main__":
    train_model()