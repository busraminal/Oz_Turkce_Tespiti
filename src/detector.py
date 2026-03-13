# -*- coding: utf-8 -*-
"""
Adım 7 - Seçenek B (API): Genel bir AI dedektör API'sine metin gönderir,
dönen skorları skorlar.csv'e ekler.

.env:
  DETECTOR_API_URL=https://...
  DETECTOR_API_KEY=...

API yanıtı: JSON, içinde "ai_score", "score" veya "ai_skoru" (0–1 arası).

Kullanım: python src/detector.py
"""
from __future__ import annotations

import csv
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE, ".env"))
except ImportError:
    pass

SKORLAR_CSV = os.path.join(BASE, "data", "annotated", "skorlar.csv")
MANIFEST_CSV = os.path.join(BASE, "data", "annotated", "manifest_detector.csv")
METINLER_DIR = os.path.join(BASE, "data", "annotated", "metinler_for_gptzero")


def _api_skor_al(metin: str, url: str, api_key: str) -> float | None:
    """Metni API'ye POST eder; yanıttan ai skorunu (0-1) döndürür."""
    try:
        import requests
    except ImportError:
        print("requests gerekli: pip install requests")
        return None
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {"text": metin}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        for key in ("ai_score", "score", "ai_skoru", "completely_generated_prob"):
            if key in data:
                v = data[key]
                if isinstance(v, (int, float)):
                    if v > 1:
                        v = v / 100.0
                    return float(v)
                if isinstance(v, str):
                    try:
                        return float(v.replace(",", "."))
                    except ValueError:
                        pass
        return None
    except Exception as e:
        print(f"API hatası: {e}")
        return None


def main():
    url = os.environ.get("DETECTOR_API_URL", "").strip()
    api_key = os.environ.get("DETECTOR_API_KEY", "").strip()
    if not url:
        print("DETECTOR_API_URL .env'de tanımlı değil. Seçenek B için .env'e ekleyin.")
        print("Manuel skorları birleştirmek için: python src/merge_ai_skorlari.py <sonuc.csv>")
        sys.exit(1)
    if not os.path.isfile(MANIFEST_CSV):
        print("Önce: python src/export_metinler_for_detector.py")
        sys.exit(1)
    if not os.path.isfile(SKORLAR_CSV):
        print("Önce: python src/annotate.py")
        sys.exit(1)

    with open(MANIFEST_CSV, "r", encoding="utf-8") as f:
        manifest = list(csv.DictReader(f))
    with open(SKORLAR_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        skor_sutunlari = list(reader.fieldnames)
        skorlar = list(reader)

    if "ai_skoru" not in skor_sutunlari:
        skor_sutunlari.append("ai_skoru")

    key_to_ai = {}
    for row in manifest:
        kisa = row.get("dosya", "")
        path = os.path.join(METINLER_DIR, kisa)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            metin = f.read()
        skor = _api_skor_al(metin, url, api_key)
        if skor is not None:
            key = (row.get("model", ""), row.get("prompt_id", ""), row.get("versiyon", ""))
            key_to_ai[key] = skor
            print(f"  {kisa} -> {skor:.3f}")

    for s in skorlar:
        key = (s.get("model", ""), s.get("prompt_id", ""), s.get("versiyon", ""))
        s["ai_skoru"] = key_to_ai.get(key, "")

    with open(SKORLAR_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=skor_sutunlari, extrasaction="ignore")
        w.writeheader()
        w.writerows(skorlar)
    print(f"ai_skoru yazıldı: {SKORLAR_CSV}. Analiz: python src/analyze.py")


if __name__ == "__main__":
    main()
