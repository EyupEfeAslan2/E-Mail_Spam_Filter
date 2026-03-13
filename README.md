Kullanılacak verisetinin Kaggle bağlantısı:
[text](https://www.kaggle.com/datasets/alihossary/enron1-spamassasin-raw-dataset)

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları sırasıyla izleyin:

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