"""
Bloom Filter Veri Yapısı İmplementasyonu (Core Module)

Bu modül, e-posta filtreleme sistemimizin ilk ve en hızlı katmanını oluşturur. 
Bilinen spam göndericilerini ve zararlı URL'leri O(k) zaman karmaşıklığında, 
düşük bellek tüketimiyle tespit etmek amacıyla tasarlanmıştır.

Kısıt: Ders projesi gereksinimleri doğrultusunda, harici hiçbir Bloom Filter 
kütüphanesi (örn. pybloom) kullanılmayacaktır. Tüm yapı sıfırdan inşa edilmelidir.

GÖREV TANIMI VE GEREKSİNİMLER:
1. 'BloomFilter' adında, nesne yönelimli (OOP) prensiplere uygun bir sınıf tanımlayın.
2. Sınıfın yapıcı metodu (__init__), aşağıdaki parametreleri almalıdır:
   - m: Bit dizisinin boyutu (Bit array size).
   - k: Kullanılacak hash fonksiyonu sayısı (Number of hash functions).
3. Sınıf başlatıldığında, boyutu 'm' olan ve tüm elemanları 0 (veya False) 
   olarak atanan bir veri yapısı (örn. bytearray veya list) oluşturulmalıdır.
4. Python'un standart 'hashlib' (MD5, SHA-1 vb.) kütüphanesini kullanarak, 
   gelen string ifadeleri k farklı benzersiz indeks değerine dönüştürecek 
   deterministik bir hash mekanizması kurun.
5. Sınıf aşağıdaki iki temel operasyonu O(k) karmaşıklığında gerçekleştirmelidir:
   - add(item): Gelen girdiyi hash'leyerek hesaplanan indekslerdeki değerleri 1 (True) yapar.
   - check(item): Gelen girdiyi hash'ler ve ilgili indeksleri kontrol eder. 
     Eğer tüm indeksler 1 ise 'True' (Olası Spam), içlerinden herhangi biri 
     bile 0 ise kesinlikle 'False' (Temiz) değeri döndürür (False-positive doğası gereği).
"""

import hashlib

class BloomFilter:
    def __init__(self, size: int, hash_count: int):
        # TODO: Bit dizisi ve konfigürasyon tanımlamaları buraya yazılacak.
        pass

    def add(self, item: str) -> None:
        # TODO: Eleman ekleme mantığı buraya yazılacak.
        pass

    def check(self, item: str) -> bool:
        # TODO: Eleman sorgulama mantığı buraya yazılacak.
        return False