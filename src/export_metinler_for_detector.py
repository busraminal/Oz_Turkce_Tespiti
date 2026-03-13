# -*- coding: utf-8 -*-
"""
GPTZero vb. dedektöre elle yapıştırmak için metinleri ayrı .txt dosyası olarak çıkarır.
Çıktı: data/annotated/metinler_for_gptzero/*.txt ve manifest.csv (dosya, model, prompt_id, versiyon).
"""
from __future__ import annotations

import csv
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_JSON = os.path.join(BASE, "data", "raw", "raw_outputs.json")
RAW_DIR = os.path.join(BASE, "data", "raw")
OUT_DIR = os.path.join(BASE, "data", "annotated", "metinler_for_gptzero")
MANIFEST_CSV = os.path.join(BASE, "data", "annotated", "manifest_detector.csv")


def main():
    if os.path.isfile(RAW_JSON):
        with open(RAW_JSON, "r", encoding="utf-8") as f:
            items = json.load(f)
    else:
        items = []
        if os.path.isdir(RAW_DIR):
            pattern = re.compile(r"^(.+?)_([a-z0-9_]+)_(standart|oz_turkce)\.txt$", re.IGNORECASE)
            for name in sorted(os.listdir(RAW_DIR)):
                if not name.endswith(".txt"):
                    continue
                path = os.path.join(RAW_DIR, name)
                with open(path, "r", encoding="utf-8") as f:
                    metin = f.read()
                m = pattern.match(name)
                model = m.group(1).replace("_", "-") if m else ""
                prompt_id = m.group(2) if m else ""
                versiyon = m.group(3).lower() if m else ""
                items.append({"dosya": name, "metin": metin, "model": model, "prompt_id": prompt_id, "versiyon": versiyon})
    if not items:
        print("data/raw/ veya raw_outputs.json boş. Önce generate.py çalıştırın.")
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    manifest = []
    for i, item in enumerate(items):
        metin = item.get("metin", "")
        dosya = item.get("dosya", f"metin_{i}.txt")
        # Dedektör için kısa ad: prompt_id_versiyon.txt
        pid = item.get("prompt_id", f"p{i}")
        ver = item.get("versiyon", "standart")
        kisa_ad = f"{pid}_{ver}.txt"
        out_path = os.path.join(OUT_DIR, kisa_ad)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(metin)
        manifest.append({
            "dosya": kisa_ad,
            "model": item.get("model", ""),
            "prompt_id": pid,
            "versiyon": ver,
        })
    with open(MANIFEST_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dosya", "model", "prompt_id", "versiyon"])
        w.writeheader()
        w.writerows(manifest)
    print(f"{len(manifest)} metin: {OUT_DIR}")
    print(f"Manifest: {MANIFEST_CSV}")


if __name__ == "__main__":
    main()
