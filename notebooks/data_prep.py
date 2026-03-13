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