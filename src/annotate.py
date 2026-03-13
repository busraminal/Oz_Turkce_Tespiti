# -*- coding: utf-8 -*-
"""
data/raw/ içindeki metinlerin Öz Türkçe oranını hesaplar.
Önce raw_outputs.json okunur; yoksa data/raw/*.txt dosyaları taranır.
Çıktı: data/annotated/skorlar.csv
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import oz_turkce_oran

RAW_DIR = os.path.join(BASE, "data", "raw")
RAW_JSON = os.path.join(BASE, "data", "raw", "raw_outputs.json")
ANNOTATED_DIR = os.path.join(BASE, "data", "annotated")
SKORLAR_CSV = os.path.join(BASE, "data", "annotated", "skorlar.csv")


def _raw_outputs_oku():
    """raw_outputs.json varsa list of dict döner; yoksa None."""
    if not os.path.isfile(RAW_JSON):
        return None
    with open(RAW_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _txt_dosyalarini_tara():
    """data/raw/*.txt dosyalarını tara; her biri için {dosya, metin, model?, prompt_id?, versiyon?}."""
    if not os.path.isdir(RAW_DIR):
        return []
    # Örnek: gpt_4o_mini_dil_devrimi_standart.txt -> model, prompt_id, versiyon
    pattern = re.compile(r"^(.+?)_([a-z0-9_]+)_(standart|oz_turkce)\.txt$", re.IGNORECASE)
    rows = []
    for name in sorted(os.listdir(RAW_DIR)):
        if not name.endswith(".txt"):
            continue
        path = os.path.join(RAW_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                metin = f.read()
        except Exception:
            metin = ""
        m = pattern.match(name)
        if m:
            model = m.group(1).replace("_", "-")
            prompt_id = m.group(2)
            versiyon = m.group(3).lower()
        else:
            model = ""
            prompt_id = ""
            versiyon = ""
        rows.append({
            "dosya": name,
            "metin": metin,
            "model": model,
            "prompt_id": prompt_id,
            "versiyon": versiyon,
        })
    return rows


def main():
    os.makedirs(ANNOTATED_DIR, exist_ok=True)
    # Kaynak: önce JSON, yoksa .txt taraması
    kaynak = _raw_outputs_oku()
    if kaynak:
        # JSON'daki her öğe: model, prompt_id, konu, versiyon, metin, dosya
        rows = [
            {
                "dosya": item.get("dosya", ""),
                "metin": item.get("metin", ""),
                "model": item.get("model", ""),
                "prompt_id": item.get("prompt_id", ""),
                "konu": item.get("konu", ""),
                "versiyon": item.get("versiyon", ""),
            }
            for item in kaynak
        ]
    else:
        rows = _txt_dosyalarini_tara()
        for r in rows:
            r["konu"] = ""

    if not rows:
        print("data/raw/ içinde metin bulunamadı. Önce python src/generate.py çalıştırın.")
        return

    # Her metin için Öz Türkçe oranı hesapla
    sonuclar = []
    for r in rows:
        detay = oz_turkce_oran.hesapla_detay(r["metin"])
        sonuclar.append({
            "dosya": r["dosya"],
            "model": r["model"],
            "prompt_id": r["prompt_id"],
            "konu": r.get("konu", ""),
            "versiyon": r["versiyon"],
            "oz_turkce_oran": detay["oran"],
            "oz_turkce_sayisi": detay["oz_turkce_sayisi"],
            "toplam_kelime": detay["toplam_kelime"],
            "stopword_sayisi": detay.get("stopword_sayisi", ""),
        })

    # Mevcut skorlar.csv'teki ek sütunları (ai_skoru vb.) koru
    base_alanlar = ["dosya", "model", "prompt_id", "konu", "versiyon", "oz_turkce_oran", "oz_turkce_sayisi", "toplam_kelime", "stopword_sayisi"]
    extra_alanlar = []
    eski_satirlar = {}  # (model, prompt_id, versiyon) -> dict
    if os.path.isfile(SKORLAR_CSV):
        try:
            with open(SKORLAR_CSV, "r", encoding="utf-8") as f:
                r = csv.DictReader(f)
                old_fieldnames = list(r.fieldnames) if r.fieldnames else []
                for row in r:
                    key = (row.get("model", ""), row.get("prompt_id", ""), row.get("versiyon", ""))
                    eski_satirlar[key] = row
                extra_alanlar = [c for c in old_fieldnames if c not in base_alanlar]
        except Exception:
            pass
    for s in sonuclar:
        key = (s.get("model", ""), s.get("prompt_id", ""), s.get("versiyon", ""))
        if key in eski_satirlar:
            for c in extra_alanlar:
                if c in eski_satirlar[key] and eski_satirlar[key][c]:
                    s[c] = eski_satirlar[key][c]
    alanlar = base_alanlar + extra_alanlar
    with open(SKORLAR_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=alanlar, extrasaction="ignore")
        w.writeheader()
        w.writerows(sonuclar)
    print(f"{len(sonuclar)} satır yazıldı: {SKORLAR_CSV}" + (f" ({len(extra_alanlar)} ek sütun korundu)" if extra_alanlar else ""))


if __name__ == "__main__":
    main()
