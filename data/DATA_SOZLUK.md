# Öz Türkçe sözlük — Methodology (makale için)

Bu dosya, Öz Türkçe oranı hesaplamasında kullanılan kelime listesinin nasıl oluşturulduğunu özetler (makale Methodology bölümünde atıf için).

## Dosya

- **Konum:** `data/oz_turkce_sozluk.txt`
- **Biçim:** Her satırda bir kelime (küçük harf); `#` ile başlayan satırlar yorum (okunmaz).
- **Kelime sayısı:** Yaklaşık 10.600+ madde (proje anındaki satır sayısına göre güncellenebilir).

## Kaynaklar ve oluşturma

1. **TDK ve arı Türkçe kökleri**  
   `scripts/generate_oz_turkce_words.py` betiği, Öz Türkçe kökler (isim/fiil) ve yaygın eklerle türetilmiş kelimeleri üretir; çıktı `data/oz_turkce_ek_uretilen.txt` vb. dosyalara yazılır.

2. **Genişletilmiş liste**  
   `scripts/expand_sozluk.py` betiği, mevcut `oz_turkce_sozluk.txt` ile `data/oz_turkce_ek_*.txt` dosyalarını birleştirip tekrarsız ve sıralı tek sözlük üretir.

3. **İçerik**  
   Sözlük, vücut/doğa/renkler, temel kavramlar, fiil kökleri ve türemiş biçimler gibi alanları kapsar; TDK’nın öz Türkçe karşılık önerileri ve alan literatüründeki arı Türkçe listelerle uyumlu tutulmuştur.

## Hesaplamada kullanım

- **Modül:** `src/oz_turkce_oran.py`
- **Oran:** (Sözlükte geçen içerik kelimesi sayısı) / (toplam içerik kelimesi). Stopword’ler ve isteğe bağlı kök eşleme (sonek düşürme) uygulanır; detay için `MAKALE_NOTLARI.md` Bölüm 2–3.

## Makalede atıf

Methodology’de şu ifade kullanılabilir:  
*“Öz Türkçe yoğunluğu, proje sözlüğü (data/oz_turkce_sozluk.txt) ile hesaplandı; sözlük TDK ve arı Türkçe köklerinden türetilmiş kelimeler ile genişletilmiş listelerden oluşturuldu (scripts/generate_oz_turkce_words.py, expand_sozluk.py).”*
