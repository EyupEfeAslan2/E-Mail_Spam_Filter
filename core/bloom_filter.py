import hashlib

class BloomFilter:
    def __init__(self, size: int, hash_count: int):
        """
        m (size): Bit dizisinin boyutu.
        k (hash_count): Kullanılacak hash fonksiyonu sayısı.
        """
        self.size = size
        self.hash_count = hash_count
        # Başlangıçta tüm elemanları False (0) olan bit dizisini oluşturuyoruz
        self.bit_array = [False] * self.size

    def _hash_item(self, item: str, i: int) -> int:
        """
        Yardımcı Fonksiyon: Girdiyi k farklı deterministik hash'e dönüştürür.
        Farklı indeksler üretmek için girdinin sonuna döngü numarasını (i) ekleriz.
        """
        # MD5 algoritması ile girdiyi ve döngü sayısını birleştirip hash'liyoruz
        hash_object = hashlib.md5(f"{item}{i}".encode('utf-8'))
        # Üretilen hexadecimal yapıyı tam sayıya (base 16) çevirip, dizi boyutuna göre mod alıyoruz
        return int(hash_object.hexdigest(), 16) % self.size

    def add(self, item: str) -> None:
        """Elemanı filtreye ekler. Zaman karmaşıklığı: O(k)"""
        for i in range(self.hash_count):
            index = self._hash_item(item, i)
            # İlgili indekslerdeki değerleri 1 (True) yapıyoruz
            self.bit_array[index] = True

    def check(self, item: str) -> bool:
        """Elemanın filtrede olup olmadığını kontrol eder. Zaman karmaşıklığı: O(k)"""
        for i in range(self.hash_count):
            index = self._hash_item(item, i)
            # Eğer hesaplanan indekslerden herhangi biri bile 0 (False) ise kesinlikle 'False' (Temiz) döner
            if not self.bit_array[index]:
                return False
        # Eğer tüm indeksler 1 (True) ise, 'True' (Olası Spam) döner
        return True