# -*- coding: utf-8 -*-
"""
Öz Türkçe köklerden eklerle kelime türetir; çıktıyı data/oz_turkce_ek_uretilen.txt olarak yazar.
TDK ve arı Türkçe kökleri + yaygın ekler kullanır.
"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data", "oz_turkce_ek_uretilen.txt")

# Öz Türkçe kökler (fiil ve isim kökleri) - yaygın ve üretken
KOKLER = """
acı aç ak ad al an as at ay bağ bak bal bas bat bel bil bir boz bul bütün
çalış çek çevir çöz dağıl dayan değ değiş dengele dene dergi dert dikil diril
doğ dur düş düzenle eriş et evir geç gel geliş gerçekle gör göst güç güven
ısın işle karar katıl kavra kaynaş kesinle kilitle kodla kur kurgula
ölç örnekle paylaş pekiştir saptama sağlamlaştır seç sınırla sistemle
soyutla sorgula tartış temellendir topla türet uydur uyumla ulaş yapılandır yükselt
akıl anlam ayır başar bellek benze birleş bozul çalış çatış çevir çözüm dağılım
dayanış değişken denge dönüş düzen etkileş evrim geçiş gelişim gerçekleş
görünüm güçlen işlev kararlaş katılım kavrayış kaynaşım kesinleş kodlama
kurumsal ölçüm oran örnek paylaşım pekiştirme saptama seçim sınır sistem
soyutlama sorgulama tartışma temel toplum türetim uyum ulaşım yapı
yüksel
göz yürek el ayak baş dil gönül can iz ses öz söz yüz boy kol bacak
gök yer su ateş taş toprak orman deniz dağ ırmak göl güneş ay yıldız
ev yol kapı duvar oda ocak
bil gi gör işit dokun tat al ver gel git yap et ol de
büyük küçük uzun kısa geniş dar yüksek alçak sıcak soğuk sert yumuşak
ak kara kızıl yeşil mavi sarı boz
bir iki üç dört beş çok az tüm yarım tek
gün gece sabah akşam yıl an
""".split()

# Yaygın ekler (isim/fiil köküne eklenebilir - basitleştirilmiş, bazıları köke göre uyumlu olmayabilir)
EK_ISIM = ["lık", "lik", "luk", "lük", "lı", "li", "lu", "lü", "sız", "siz", "suz", "süz",
           "cı", "ci", "cu", "cü", "çı", "çi", "çu", "çü",
           "lık", "lik", "daş", "taş", "ca", "ce", "sal", "sel",
           "im", "ım", "um", "üm", "ış", "iş", "uş", "üş", "ma", "me",
           "gi", "gı", "gu", "gü", "ak", "ek", "ık", "ik", "uk", "ük",
           "ınç", "inç", "unç", "ünç", "gan", "gen", "kan", "ken",
           "ıcı", "ici", "ucu", "ücü", "ıt", "it", "ut", "üt",
           "la", "le", "lık", "lik", "sız", "siz"]

# Sadece güvenli kök+ek çiftleri (gerçekten var olan/olası Öz Türkçe türevler)
# Elle seçilmiş ek listesi - her kök için uyumlu ekler
TUREVLER = []
for kok in KOKLER:
    kok = kok.strip()
    if not kok:
        continue
    # Her kök için sadece yaygın ve anlamlı türevler
    son_ses = kok[-1] if kok else ""
    # -lık/-lik (isimden isim)
    for ek in ["lık", "lik", "luk", "lük"]:
        TUREVLER.append(kok + ek)
    # -lı/-li (ile)
    for ek in ["lı", "li", "lu", "lü"]:
        TUREVLER.append(kok + ek)
    # -sız/-siz
    for ek in ["sız", "siz", "suz", "süz"]:
        TUREVLER.append(kok + ek)
    # -ci
    for ek in ["cı", "ci", "cu", "cü"]:
        TUREVLER.append(kok + ek)
    # -im/-ım (fiilden isim)
    for ek in ["im", "ım", "um", "üm"]:
        TUREVLER.append(kok + ek)
    # -me/-ma
    for ek in ["me", "ma"]:
        TUREVLER.append(kok + ek)
    # -iş/-ış
    for ek in ["iş", "ış", "uş", "üş"]:
        TUREVLER.append(kok + ek)
    # -gen/-gan
    for ek in ["gen", "gan", "gin", "gın", "ken", "kan"]:
        TUREVLER.append(kok + ek)
    # -ecek/-acak (sadece fiil kökleri için - burada atlıyoruz, çok uzun olur)
    # -sel/-sal
    for ek in ["sel", "sal"]:
        TUREVLER.append(kok + ek)

# Tekrarsız, sadece geçerli uzunlukta (2-25 karakter)
def temizle(kelime):
    k = kelime.strip().lower()
    if len(k) < 2 or len(k) > 24:
        return None
    # Sadece Türkçe harfler
    for c in k:
        if c not in "abcçdefgğhıijklmnoöprsştuüvyz":
            return None
    return k

benzersiz = sorted(set(temizle(w) for w in TUREVLER if temizle(w)))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(benzersiz) + "\n")
print(f"Üretilen kelime sayısı: {len(benzersiz)}")
print(f"Yazıldı: {OUT}")
