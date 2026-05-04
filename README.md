Kullanılacak verisetinin Kaggle bağlantısı:
[text](https://www.kaggle.com/datasets/alihossary/enron1-spamassasin-raw-dataset)

# Adaptive Deep Learning Email Spam Filter

Bu proje Bloom Filter ve DistilBERT tabanlı derin öğrenme modelini birlikte
kullanan, kullanıcı geri bildirimiyle kendini geliştirmeye hazırlanan bir
e-posta spam filtreleme sistemidir.

## Mimari

- **Bloom Filter / Bit Array / Hash:** Bilinen spam imzaları düşük bellekle ve
  hızlı şekilde yakalanır.
- **Set:** Yanlış pozitif bildirilen e-postalar ham allowlist içinde tutulur.
- **Transformer Model:** DistilBERT ile anlamsal spam sınıflandırması yapılır.
- **CSV Feedback Queue:** Kullanıcı geri bildirimleri yeniden eğitim için
  kuyruk mantığıyla saklanır.
- **JSON Retrain Queue:** Feedback eşiği veya admin isteği modeli yeniden
  eğitmek için kalıcı kuyruk işareti oluşturur.
- **Stack:** Web arayüzünde sayfalar arası geçiş geçmişi LIFO yığın yapısıyla
  yönetilir.
- **Sliding Window Queue:** API kötüye kullanımını azaltmak için feedback ve
  admin isteklerinde rate limit uygulanır.
- **Salted SHA-256 Hash:** Feedback kayıtlarında kişisel veri yerine gizlilik
  odaklı imza saklanır.

## Ortam Değişkenleri

```bash
export SPAM_ADMIN_TOKEN="guclu-bir-admin-token"
export SPAM_PRIVACY_SALT="uzun-rastgele-bir-salt"
export SPAM_MODEL_PATH="data/model"
export SPAM_DEFAULT_THRESHOLD="0.5"
export SPAM_MIN_PRECISION="0.9"
export SPAM_MIN_RECALL="0.9"
export SPAM_MIN_F1="0.9"
```

IMAP entegrasyonu için:

```bash
export SPAM_EMAIL_ACCOUNT="mail@example.com"
export SPAM_EMAIL_APP_PASSWORD="uygulama-sifresi"
export SPAM_IMAP_SERVER="imap.gmail.com"
export SPAM_IMAP_SPAM_FOLDER="Spam"
```

SMTP pipe entegrasyonu için `scripts/smtp_pipe.py` Postfix/Exim transport
komutundan stdin üzerinden ham RFC822 mesaj alacak şekilde kullanılabilir.

## Çalıştırma

En kolay yol:

```bash
python start_app.py
```

Bu komut uygun bir port bulur, backend'i başlatır ve tarayıcıda arayüzü açar.

1. Repoyu Klonlayın:

Bash

git clone <github-repo-linkiniz>
cd spam-filter-project
2. Sanal Ortam (Virtual Environment) Oluşturun:

Bash

# Linux/macOS için:
python3 -m venv venv
source venv/bin/activate

# Windows için:
python -m venv venv
.\venv\Scripts\activate
3. Gerekli Kütüphaneleri Yükleyin:
(Not: requirements.txt dosyası güncellendikçe bu adımı tekrarlayın)

Bash

pip install -r requirements.txt

4. Veri hazırlama:

```bash
python notebooks/data_prep.py
```

5. Model eğitimi:

```bash
python -m core.train
```

6. Model kalite kapısı:

```bash
python scripts/validate_model.py
```

7. API ve UI:

```bash
uvicorn api.main:app --reload
```

Admin paneli için tarayıcıdaki token alanına `SPAM_ADMIN_TOKEN` değerini girin.

## İşletim Uçları

- `GET /health/live`: proses ayakta mı?
- `GET /health/ready`: eğitilmiş model ve precision/recall/F1 kapıları hazır mı?
- `GET /admin/health`: model, Bloom Filter, allowlist ve retrain durumu
- `POST /admin/retrain`: feedback verileriyle yeniden eğitim işini kuyruğa alır
- `POST /predict/batch`: yüksek hacimli sınıflandırma için toplu tahmin

## Doğrulama

```bash
python -m compileall api core scripts notebooks
python -m unittest discover
python scripts/load_test.py
```
