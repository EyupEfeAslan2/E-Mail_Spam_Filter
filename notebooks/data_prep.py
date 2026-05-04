"""
Veri Ön İşleme (Data Preprocessing) Modülü

Bu modül, ham e-posta veri setinin derin öğrenme (Deep Learning) modelimizin 
eğitimi için uygun, temiz ve yapılandırılmış bir formata dönüştürülmesinden sorumludur.

GÖREV TANIMI VE GEREKSİNİMLER:
1. 'data/raw/' dizini altında yer alan 'spam' ve 'ham' klasörlerindeki tüm 
   .txt uzantılı e-posta metinlerini yinelemeli (recursive) olarak okuyacak bir yapı kurun.
2. Okunan e-posta metinleri üzerinde temel doğal dil işleme (NLP) temizliği yapın:
   - Gereksiz satır boşluklarını ve sekme (tab) karakterlerini silin.
   - Anlamsız özel sembolleri ve noktalama işaretlerini filtreleyin.
   - Metni standartlaştırmak adına tüm karakterleri küçük harfe (lowercase) çevirin.
3. Temizlenen verileri yapısal bir bütünlük içinde tutmak için bir Pandas DataFrame oluşturun.
   DataFrame yapısı kesinlikle şu iki sütunu içermelidir:
   - 'text': Temizlenmiş e-posta gövdesi.
   - 'label': İkili sınıflandırma (Binary Classification) etiketi (Spam = 1, Ham = 0).
4. Nihai DataFrame'i 'data/processed/dataset.csv' dizinine kaydedin.
   (Not: Repo güvenliği ve temizliği açısından .csv dosyaları .gitignore 
   ile izole edilmiştir, git push işlemine dahil edilmeyecektir.)
"""

import os
import pandas as pd

# TODO: Veri okuma ve temizleme işlemleri bu satırdan itibaren kodlanacaktır.
from pathlib import Path
from core.text_utils import clean_text

path_spam = Path("data/raw/Enron1+spamAssasin/spam")
path_ham = Path("data/raw/Enron1+spamAssasin/ham")
output_path = "data/processed/dataset.csv"

def mail(path, label):
    texts = []
    for file in Path(path).rglob("*"):
        if not file.is_file():
            continue

        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                if not text.strip():
                    continue
                texts.append({'text': text, 'label': label})
        except Exception as e:
            print(f"Error ({file}): {e}")
    return texts


def main():
    spam_list = mail(path_spam, 1)
    ham_list = mail(path_ham, 0)

    df = pd.DataFrame(spam_list + ham_list)
    if df.empty:
        raise ValueError(
            "Veri okunamadi: spam/ham klasor yollarini ve ham veri dosyalarini kontrol edin."
        )

    df = df.drop_duplicates(subset=['text']).reset_index(drop=True)
    df['text_cleaned'] = df['text'].apply(clean_text) # temizlenip text_cleaned olarak kaydediliyor

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8') # df kaydediliyor


if __name__ == "__main__":
    main()
