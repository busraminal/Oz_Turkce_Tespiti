# -*- coding: utf-8 -*-
"""Mevcut sözlük ile data/oz_turkce_ek_*.txt dosyalarını birleştirir, tekrarsız sıralar."""
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOZLUK = os.path.join(BASE, "data", "oz_turkce_sozluk.txt")
DATA_DIR = os.path.join(BASE, "data")

def main():
    seen = set()
    words = []
    # Mevcut sözlük
    if os.path.isfile(SOZLUK):
        with open(SOZLUK, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w and w not in seen:
                    seen.add(w)
                    words.append(w)
    # Ek dosyalar: oz_turkce_ek_1.txt, oz_turkce_ek_2.txt, ...
    for i in range(1, 20):
        path = os.path.join(DATA_DIR, f"oz_turkce_ek_{i}.txt")
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w and not w.startswith("#") and w not in seen:
                    seen.add(w)
                    words.append(w)
    # Üretilen kelimeler (generate_oz_turkce_words.py çıktısı)
    uretilen = os.path.join(DATA_DIR, "oz_turkce_ek_uretilen.txt")
    if os.path.isfile(uretilen):
        with open(uretilen, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w and w not in seen:
                    seen.add(w)
                    words.append(w)
    words.sort(key=lambda x: (x.replace("ı", "i").replace("ö", "o").replace("ü", "u").replace("ş", "s").replace("ğ", "g").replace("ç", "c"), x))
    with open(SOZLUK, "w", encoding="utf-8") as f:
        f.write("\n".join(words) + "\n")
    print(f"Toplam benzersiz kelime: {len(words)}")

if __name__ == "__main__":
    main()
