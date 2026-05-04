"""
Model Eğitim (Fine-Tuning) Modülü

Bu betik, DistilBERT modelini indirir ve verisetimizin küçük bir kısmı üzerinde 
(CPU optimizasyonlu) hızlıca eğitir.
"""

import os
import json
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset as TorchDataset
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from core.config import settings

# Parametreler (CPU/Hızlı Deneme için Düşük Tutuldu)
MODEL_NAME = settings.model_name
SAMPLE_SIZE = int(os.getenv("SPAM_TRAIN_SAMPLE_SIZE", "2000"))
EPOCHS = int(os.getenv("SPAM_TRAIN_EPOCHS", "1"))
BATCH_SIZE = int(os.getenv("SPAM_TRAIN_BATCH_SIZE", "8"))


class EmailDataset(TorchDataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return {
            "input_ids": torch.tensor(self.encodings["input_ids"][idx]),
            "attention_mask": torch.tensor(self.encodings["attention_mask"][idx]),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long),
        }

def load_data(filepath="data/processed/dataset.csv"):
    """Temizlenmiş veri setini yükler ve eğitim/test olarak böler."""
    print("Veri seti yükleniyor...")
    try:
        df = pd.read_csv(filepath)
        feedback = load_feedback()
        if not feedback.empty:
            df = pd.concat([df, feedback], ignore_index=True)
        text_column = "text_cleaned" if "text_cleaned" in df.columns else "text"
        df = df.dropna(subset=[text_column, "label"])
        # CPU Eğitimi için rastgele küçük bir alt küme (sample) alıyoruz
        df = df.sample(n=min(SAMPLE_SIZE, len(df)), random_state=42)
        
        train_texts, test_texts, train_labels, test_labels = train_test_split(
            df[text_column].astype(str).tolist(),
            df['label'].astype(int).tolist(),
            test_size=0.2,
            random_state=42,
            stratify=df['label'].astype(int) if df['label'].nunique() == 2 else None,
        )
        return train_texts, test_texts, train_labels, test_labels
    except FileNotFoundError:
        print(f"HATA: {filepath} bulunamadı! Önce veri ön işleme adımını tamamlayın.")
        return None, None, None, None


def load_feedback() -> pd.DataFrame:
    """Load privacy-redacted feedback rows for future training."""
    try:
        feedback = pd.read_csv(settings.reports_file)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()
    if "text_redacted" not in feedback.columns or "label" not in feedback.columns:
        return pd.DataFrame()
    feedback = feedback.rename(columns={"text_redacted": "text_cleaned"})
    return feedback[["text_cleaned", "label"]].dropna()

def initialize_model():
    """DistilBERT modelini ve kelime parçalayıcıyı (tokenizer) indirip hazırlar."""
    print("DistilBERT modeli ve Tokenizer indiriliyor...")
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
    return tokenizer, model


def compute_metrics(labels, predictions, prefix="eval"):
    """Precision/recall/F1 ölçümü yüksek doğruluk gereksinimini görünür kılar."""
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )
    return {
        f"{prefix}_accuracy": accuracy_score(labels, predictions),
        f"{prefix}_precision": precision,
        f"{prefix}_recall": recall,
        f"{prefix}_f1": f1,
    }


def evaluate_model(model, data_loader, device):
    model.eval()
    predictions = []
    spam_probs = []
    labels = []
    total_loss = 0.0
    with torch.no_grad():
        for batch in data_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch)
            total_loss += outputs.loss.item()
            probs = torch.nn.functional.softmax(outputs.logits, dim=1)[:, 1]
            preds = (probs >= 0.5).long()
            predictions.extend(preds.cpu().tolist())
            spam_probs.extend(probs.cpu().tolist())
            labels.extend(batch["labels"].cpu().tolist())
    metrics = compute_metrics(labels, predictions)
    metrics["eval_loss"] = total_loss / max(1, len(data_loader))
    best = find_best_threshold(labels, spam_probs)
    metrics.update(best)
    return metrics


def find_best_threshold(labels, spam_probs):
    """Find validation threshold that balances precision and recall."""
    best_metrics = None
    best_threshold = 0.5
    for step in range(5, 96):
        threshold = step / 100
        predictions = [1 if prob >= threshold else 0 for prob in spam_probs]
        candidate = compute_metrics(labels, predictions, prefix="threshold")
        if best_metrics is None or candidate["threshold_f1"] > best_metrics["threshold_f1"]:
            best_metrics = candidate
            best_threshold = threshold
    return {
        "recommended_threshold": best_threshold,
        "eval_precision": best_metrics["threshold_precision"],
        "eval_recall": best_metrics["threshold_recall"],
        "eval_f1": best_metrics["threshold_f1"],
        "eval_accuracy": best_metrics["threshold_accuracy"],
    }


def save_recommended_threshold(metrics):
    if "recommended_threshold" not in metrics:
        return
    os.makedirs(os.path.dirname(settings.threshold_path), exist_ok=True)
    with open(settings.threshold_path, "w", encoding="utf-8") as f:
        json.dump({"threshold": metrics["recommended_threshold"]}, f, indent=2)

def train_model():
    print("--- Hibrit Spam Filtresi: Model Eğitim Süreci Başlıyor ---")
    
    train_texts, test_texts, train_labels, test_labels = load_data()
    if train_texts is None:
        return
    
    tokenizer, model = initialize_model()
    
    print("Veriler Tokenizer'dan geçiriliyor (Tokenization)...")
    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=settings.model_max_length)
    test_encodings = tokenizer(test_texts, truncation=True, padding=True, max_length=settings.model_max_length)

    train_dataset = EmailDataset(train_encodings, train_labels)
    test_dataset = EmailDataset(test_encodings, test_labels)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)

    device = torch.device("cpu")
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(os.getenv("SPAM_TRAIN_LR", "2e-5")))

    print("Model eğitiliyor (Bu işlem CPU üzerinde biraz zaman alabilir)...")
    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0.0
        for batch in train_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            optimizer.zero_grad()
            outputs = model(**batch)
            outputs.loss.backward()
            optimizer.step()
            total_loss += outputs.loss.item()
        avg_loss = total_loss / max(1, len(train_loader))
        print(f"Epoch {epoch + 1}/{EPOCHS} - train_loss={avg_loss:.4f}")
    metrics = evaluate_model(model, test_loader, device)
    
    print("Eğitim tamamlandı. Model kaydediliyor...")
    os.makedirs(settings.model_path, exist_ok=True)
    model.save_pretrained(settings.model_path)
    tokenizer.save_pretrained(settings.model_path)
    with open(os.path.join(settings.model_path, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    save_recommended_threshold(metrics)
    print(f"Model başarıyla '{settings.model_path}' dizinine kaydedildi!")

if __name__ == "__main__":
    train_model()
