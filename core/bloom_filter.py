import hashlib
import os
import struct

class BloomFilter:
    HEADER = b"BSF1"

    def __init__(self, size: int, hash_count: int, storage_path: str | None = None):
        """
        m (size): Bit dizisinin boyutu.
        k (hash_count): Kullanılacak hash fonksiyonu sayısı.
        """
        self.size = size
        self.hash_count = hash_count
        self.storage_path = storage_path
        # Veri yapısı: Bit array. Bloom Filter eleman üyeliğini düşük bellekle takip eder.
        self.bit_array = bytearray((self.size + 7) // 8)
        if self.storage_path:
            self.load()

    def _hash_item(self, item: str, i: int) -> int:
        """
        Yardımcı Fonksiyon: Girdiyi k farklı deterministik hash'e dönüştürür.
        Farklı indeksler üretmek için girdinin sonuna döngü numarasını (i) ekleriz.
        """
        # Veri yapısı: Hash. SHA-256 tabanlı indeksler Bloom Filter bitlerini belirler.
        hash_object = hashlib.sha256(f"{i}:{item}".encode('utf-8'))
        # Üretilen hexadecimal yapıyı tam sayıya (base 16) çevirip, dizi boyutuna göre mod alıyoruz
        return int(hash_object.hexdigest(), 16) % self.size

    def _set_bit(self, index: int) -> None:
        self.bit_array[index // 8] |= 1 << (index % 8)

    def _get_bit(self, index: int) -> bool:
        return bool(self.bit_array[index // 8] & (1 << (index % 8)))

    def add(self, item: str) -> None:
        """Elemanı filtreye ekler. Zaman karmaşıklığı: O(k)"""
        for i in range(self.hash_count):
            index = self._hash_item(item, i)
            self._set_bit(index)

    def check(self, item: str) -> bool:
        """Elemanın filtrede olup olmadığını kontrol eder. Zaman karmaşıklığı: O(k)"""
        for i in range(self.hash_count):
            index = self._hash_item(item, i)
            # Eğer hesaplanan indekslerden herhangi biri bile 0 (False) ise kesinlikle 'False' (Temiz) döner
            if not self._get_bit(index):
                return False
        # Eğer tüm indeksler 1 (True) ise, 'True' (Olası Spam) döner
        return True

    def save(self) -> None:
        """Persist the bit array so adaptive spam reports survive restarts."""
        if not self.storage_path:
            return
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "wb") as f:
            f.write(self.HEADER)
            f.write(struct.pack(">II", self.size, self.hash_count))
            f.write(self.bit_array)

    def load(self) -> None:
        """Load a persisted Bloom Filter if compatible metadata is present."""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "rb") as f:
                header = f.read(4)
                size, hash_count = struct.unpack(">II", f.read(8))
                payload = f.read()
            if header != self.HEADER or size != self.size or hash_count != self.hash_count:
                return
            self.bit_array = bytearray(payload)
        except OSError:
            return
