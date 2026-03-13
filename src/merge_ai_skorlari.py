# -*- coding: utf-8 -*-
"""
Adım 7 - Seçenek A (Manuel): GPTZero vb. dedektörden aldığınız AI skorlarını
skorlar.csv ile eşleştirip tek dosyada birleştirir.

Kullanım:
  1. Önce: python src/export_metinler_for_detector.py
  2. Metinleri GPTZero'ya elle yapıştırıp skorları alın.
  3. Sonuçları bir CSV'ye kaydedin (örnek: data/annotated/gptzero_sonuclar.csv)
     Sütunlar: dosya, ai_skoru  (dosya = dil_devrimi_standart.txt gibi kısa ad)
     veya: model, prompt_id, versiyon, ai_skoru
  4. Birleştir: python src/merge_ai_skorlari.py data/annotated/gptzero_sonuclar.csv
  5. İkinci dedektör için: python src/merge_ai_skorlari.py gptzero2.csv --column ai_skoru_gptzero
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKORLAR_CSV = os.path.join(BASE, "data", "annotated", "skorlar.csv")
MANIFEST_CSV = os.path.join(BASE, "data", "annotated", "manifest_detector.csv")


def main():
    parser = argparse.ArgumentParser(description="Dedektör skorlarını skorlar.csv'e birleştirir.")
    parser.add_argument("sonuc_csv", nargs="?", help="Sonuç CSV (dosya, ai_skoru veya model, prompt_id, versiyon, ai_skoru)")
    parser.add_argument("--column", default="ai_skoru", help="Hedef sütun adı (varsayılan: ai_skoru; ikinci dedektör için: ai_skoru_gptzero)")
    args = parser.parse_args()
    if not args.sonuc_csv:
        print("Kullanım: python src/merge_ai_skorlari.py <gptzero_sonuclar.csv> [--column ai_skoru_gptzero]")
        print("  CSV sütunları: dosya, ai_skoru  (dosya = prompt_id_versiyon.txt)")
        print("  veya: model, prompt_id, versiyon, ai_skoru")
        sys.exit(1)
    sonuc_csv = os.path.abspath(args.sonuc_csv)
    target_column = (args.column or "ai_skoru").strip()
    if not os.path.isfile(sonuc_csv):
        print(f"Dosya bulunamadı: {sonuc_csv}")
        sys.exit(1)
    if not os.path.isfile(SKORLAR_CSV):
        print(f"{SKORLAR_CSV} bulunamadı. Önce annotate.py çalıştırın.")
        sys.exit(1)

    # skorlar.csv oku
    with open(SKORLAR_CSV, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        skor_sutunlari = r.fieldnames
        skorlar = list(r)
    if not skorlar:
        print("skorlar.csv boş.")
        sys.exit(1)

    # Kullanıcı CSV'sini oku
    with open(sonuc_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        print("Sonuç CSV'si boş.")
        sys.exit(1)
    fieldnames = list(rows[0].keys())
    if "ai_skoru" not in fieldnames:
        # ai_score veya score da kabul et
        for alt in ("ai_score", "score", "ai_skoru"):
            if alt in fieldnames:
                for row in rows:
                    row["ai_skoru"] = row.get(alt, "")
                break
        else:
            print("Sonuç CSV'sinde 'ai_skoru', 'ai_score' veya 'score' sütunu gerekli.")
            sys.exit(1)

    # dosya (kısa ad) -> (model, prompt_id, versiyon) eşlemesi için manifest
    manifest_map = {}
    if os.path.isfile(MANIFEST_CSV):
        with open(MANIFEST_CSV, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                kisa = row.get("dosya", "").strip()
                if kisa:
                    manifest_map[kisa] = (row.get("model", ""), row.get("prompt_id", ""), row.get("versiyon", ""))

    # (model, prompt_id, versiyon) -> ai_skoru
    key_to_ai = {}
    for row in rows:
        ai = row.get("ai_skoru", "").strip()
        if "dosya" in row and row["dosya"].strip():
            kisa = row["dosya"].strip()
            key = manifest_map.get(kisa)
            if key:
                key_to_ai[key] = ai
            else:
                # dosya = tam raw ad olabilir (qwen2.5:7b_dil_devrimi_standart.txt)
                for s in skorlar:
                    if s.get("dosya") == kisa:
                        key = (s.get("model", ""), s.get("prompt_id", ""), s.get("versiyon", ""))
                        key_to_ai[key] = ai
                        break
        elif "model" in row and "prompt_id" in row and "versiyon" in row:
            key = (row["model"].strip(), row["prompt_id"].strip(), row["versiyon"].strip())
            key_to_ai[key] = ai

    # skorlar.csv'e hedef sütunu ekle
    skor_sutunlari = list(skor_sutunlari) if skor_sutunlari else []
    if target_column not in skor_sutunlari:
        skor_sutunlari = skor_sutunlari + [target_column]
    for s in skorlar:
        key = (s.get("model", ""), s.get("prompt_id", ""), s.get("versiyon", ""))
        s[target_column] = key_to_ai.get(key, "")

    with open(SKORLAR_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=skor_sutunlari, extrasaction="ignore")
        w.writeheader()
        w.writerows(skorlar)
    print(f"{target_column} eklendi: {SKORLAR_CSV}")
    dolu = sum(1 for s in skorlar if str(s.get(target_column, "")).strip())
    print(f"  {dolu}/{len(skorlar)} satırda {target_column} dolu. Analiz: python src/analyze.py")


if __name__ == "__main__":
    main()
