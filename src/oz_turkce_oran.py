# -*- coding: utf-8 -*-
"""
Öz Türkçe yoğunluğu hesaplama.
Metni kelimelere böler, sözlükteki kelime sayısına göre oran döner.
Doğruluk artırıcılar: stopword çıkarımı, kök eşleme (sonek düşürme), min kelime uzunluğu.
Sözlük: data/oz_turkce_sozluk.txt (tek dosya; # ile başlayan satırlar yok sayılır).
"""
from __future__ import annotations

import os
import re

# Proje köküne göre varsayılan sözlük yolu
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SOZLUK = os.path.join(BASE, "data", "oz_turkce_sozluk.txt")

# Türkçe harfler (kelime içinde kabul)
TR_LETTERS = set("abcçdefgğhıijklmnoöprsştuüvyz")

# Yaygın işlev kelimeleri (stopword) – oranı sadece içerik kelimeleri üzerinden vermek için
# Kaynak: NLTK/stopwords benzeri + Türkçe ekleme
STOPWORDS = frozenset({
    "ve", "veya", "ile", "için", "bir", "bu", "şu", "o", "da", "de", "ta", "te",
    "mi", "mı", "mu", "mü", "ki", "kadar", "gibi", "üzere", "dolayı", "göre",
    "kendi", "hep", "her", "hiç", "daha", "en", "çok", "az", "şey", "var", "yok",
    "olmak", "etmek", "demek", "bilmek", "istemek", "durmak", "gelmek", "gitmek",
    "ise", "ama", "fakat", "ancak", "lakin", "yani", "zaten", "belki", "nitekim",
    "önce", "sonra", "şimdi", "böyle", "şöyle", "öyle", "niçin", "neden", "nasıl",
    "ne", "kim", "nere", "hangi", "kaç", "kimi", "nereye", "nerede", "nereden",
})

# Kök eşlemesi için denenecek sonekler (uzun önce; kök en az 2 karakter kalmalı)
# Türkçe ünlü uyumuna göre çeşitler
SONEK_LISTESI = [
    "ler", "lar", "lik", "lık", "luk", "lük", "ci", "cı", "cu", "cü",
    "li", "lı", "lu", "lü", "siz", "sız", "suz", "süz",
    "im", "ım", "um", "üm", "in", "ın", "un", "ün",
    "de", "da", "te", "ta", "den", "dan", "ten", "tan",
    "i", "ı", "u", "ü", "e", "a",  # belirtme/yonelme (kısa)
    "me", "ma", "ış", "iş", "uş", "üş",
    "mak", "mek", "acak", "ecek", "an", "en",
    "di", "dı", "du", "dü", "ti", "tı", "tu", "tü",
    "miş", "mış", "muş", "müş", "yor", "ki",
]


def _kelimelere_bol(metin: str, min_uzunluk: int = 2) -> list[str]:
    """Metni küçük harfe çevirir ve anlamlı kelimelere böler (noktalama ayrılır)."""
    metin = (metin or "").lower().strip()
    parcalar = re.split(r"[^\wçğıöşü]+", metin, flags=re.IGNORECASE)
    kelimeler = []
    for p in parcalar:
        p = p.strip()
        if not p or len(p) < min_uzunluk:
            continue
        if all(c.isalpha() or c in "çğıöşü" for c in p):
            kelimeler.append(p.lower())
    return kelimeler


def _sozluk_yukle(sozluk_yolu: str) -> set[str]:
    """Sözlük dosyasından kelimeleri yükler. # ve boş satırları atlar."""
    path = os.path.abspath(sozluk_yolu)
    if not os.path.isfile(path):
        return set()
    sozluk = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            w = line.strip().lower()
            if w and not w.startswith("#"):
                sozluk.add(w)
    return sozluk


def _kok_bul(kelime: str, sozluk: set[str], max_derinlik: int = 2) -> bool:
    """Kelime veya sonek düşürülmüş hali sözlükte varsa True. En fazla max_derinlik adım sonek düşürülür."""
    if kelime in sozluk:
        return True
    if max_derinlik <= 0:
        return False
    for sonek in SONEK_LISTESI:
        if len(kelime) <= len(sonek) + 1:
            continue
        if kelime.endswith(sonek):
            kok = kelime[:-len(sonek)]
            if len(kok) >= 2:
                if kok in sozluk:
                    return True
                if max_derinlik > 1 and _kok_bul(kok, sozluk, max_derinlik - 1):
                    return True
    return False


def _sozlukte_var(kelime: str, sozluk: set[str], kok_esleme: bool) -> bool:
    """Kelime sözlükte varsa True. kok_esleme=True ise sonek düşürerek de dener (en fazla 2 adım)."""
    if kelime in sozluk:
        return True
    if not kok_esleme:
        return False
    return _kok_bul(kelime, sozluk, max_derinlik=2)


def hesapla(
    metin: str,
    sozluk_yolu: str = None,
    icerik_kelimesi_only: bool = True,
    kok_esleme: bool = True,
    min_uzunluk: int = 2,
) -> float:
    """
    Metindeki Öz Türkçe kelime oranını döner.

    Parametreler:
      sozluk_yolu: Sözlük dosyası (varsayılan: data/oz_turkce_sozluk.txt).
      icerik_kelimesi_only: True ise stopword'ler hem paydan hem paydadan çıkarılır;
        oran = (öz türkçe içerik kelimesi) / (içerik kelimesi). False ise tüm kelimeler sayılır.
      kok_esleme: True ise kelime sözlükte yoksa sonek düşürülüp kök sözlükte aranır (doğruluk artar).
      min_uzunluk: Bu uzunluktan kısa token'lar sayılmaz (1 harfli gürültü azalır).

    Kelime yoksa 0.0 döner.
    """
    sozluk = _sozluk_yukle(sozluk_yolu or DEFAULT_SOZLUK)
    kelimeler = _kelimelere_bol(metin, min_uzunluk=min_uzunluk)
    if not kelimeler:
        return 0.0
    if icerik_kelimesi_only:
        kelimeler = [k for k in kelimeler if k not in STOPWORDS]
    if not kelimeler:
        return 0.0
    eslesen = sum(1 for k in kelimeler if _sozlukte_var(k, sozluk, kok_esleme))
    return eslesen / len(kelimeler)


def hesapla_detay(
    metin: str,
    sozluk_yolu: str = None,
    icerik_kelimesi_only: bool = True,
    kok_esleme: bool = True,
    min_uzunluk: int = 2,
) -> dict:
    """
    Oran + kelime sayılarını döner.
    Keys: oz_turkce_sayisi, toplam_kelime, oran [, stopword_sayisi ]
    """
    sozluk = _sozluk_yukle(sozluk_yolu or DEFAULT_SOZLUK)
    tum = _kelimelere_bol(metin, min_uzunluk=min_uzunluk)
    if icerik_kelimesi_only:
        kelimeler = [k for k in tum if k not in STOPWORDS]
        stopword_sayisi = len(tum) - len(kelimeler)
    else:
        kelimeler = tum
        stopword_sayisi = 0
    toplam = len(kelimeler)
    eslesen = sum(1 for k in kelimeler if _sozlukte_var(k, sozluk, kok_esleme))
    oran = (eslesen / toplam) if toplam else 0.0
    out = {
        "oz_turkce_sayisi": eslesen,
        "toplam_kelime": toplam,
        "oran": round(oran, 6),
    }
    if icerik_kelimesi_only:
        out["stopword_sayisi"] = stopword_sayisi
    return out


if __name__ == "__main__":
    test_metin = "Dil devrimi eğitim sisteminde önemli bir olanak sağladı. Bellek ve anımsama güçlendi."
    print("Test metni:", test_metin[:60], "...")
    detay = hesapla_detay(test_metin)
    print("Detay (içerik kelimesi + kök eşleme):", detay)
    print("Oran:", hesapla(test_metin))
    # Eski davranış (stopword yok, kök eşleme yok) ile karşılaştırma
    detay_ham = hesapla_detay(test_metin, icerik_kelimesi_only=False, kok_esleme=False)
    print("Detay (tüm kelime, kök yok):", detay_ham)
