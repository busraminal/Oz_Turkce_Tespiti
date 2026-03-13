# -*- coding: utf-8 -*-
"""
Adım 7 - Seçenek C (Binoculars): Açık kaynak AI dedektör ile metinlere skor verir,
sonuçları skorlar.csv'e ekler.

İki mod:
  1) Binoculars kuruluysa (pip install binoculars): Binoculars skoru kullanılır.
  2) Değilse: Hugging Face'tan hafif bir "AI vs human" sınıflandırıcı denenir
     (transformers gerekir; Türkçe için tam optimize değil, deneme amaçlı).

Kullanım: python src/detector_binoculars.py
"""
from __future__ import annotations

import csv
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKORLAR_CSV = os.path.join(BASE, "data", "annotated", "skorlar.csv")
MANIFEST_CSV = os.path.join(BASE, "data", "annotated", "manifest_detector.csv")
METINLER_DIR = os.path.join(BASE, "data", "annotated", "metinler_for_gptzero")


def _score_binoculars(metin: str) -> float | None:
    """Binoculars paketi varsa skor döndürür (yüksek = AI olası)."""
    try:
        import binoculars
        # Paket API'si farklı olabilir; yaygın kullanım
        if hasattr(binoculars, "score"):
            return float(binoculars.score(metin))
        if hasattr(binoculars, "Binoculars"):
            b = binoculars.Binoculars()
            return float(b.score(metin))
    except ImportError:
        pass
    except Exception as e:
        print(f"Binoculars hatası: {e}")
    return None


def _load_transformers_pipeline():
    """HF pipeline'ı tek sefer yükler (ilk çalıştırmada model indirilir)."""
    try:
        from transformers import pipeline
    except ImportError:
        return None
    try:
        print("Hugging Face modeli yükleniyor (ilk seferde indirme 1–2 dk sürebilir)...", flush=True)
        pipe = pipeline(
            "text-classification",
            model="openai-community/roberta-base-openai-detector",
            top_k=None,
            truncation=True,
            max_length=512,
        )
        print("Model hazır.", flush=True)
        return pipe
    except Exception as e:
        print(f"Transformers model hatası: {e}", flush=True)
        return None


def _flatten_pipeline_out(obj):
    """İç içe listeyi recursive aç; sadece dict'leri topla. .get sadece dict üzerinde çağrılacak."""
    if isinstance(obj, dict):
        return [obj]
    if isinstance(obj, list):
        result = []
        for item in obj:
            result.extend(_flatten_pipeline_out(item))
        return result
    return []


def _score_transformers(metin: str, pipe) -> float | None:
    """Yüklü pipeline ile AI skoru döndürür."""
    if pipe is None or len(metin.strip()) < 20:
        return None
    try:
        raw = pipe(metin[:2000])
        out = _flatten_pipeline_out(raw)
        if not out:
            return None
        for d in out:
            if not isinstance(d, dict):
                continue
            label = str(d.get("label", "")).upper()
            score = d.get("score")
            if score is not None and ("AI" in label or "GENERATED" in label):
                return float(score)
        if out and isinstance(out[0], dict) and "score" in out[0]:
            return float(out[0]["score"])
    except Exception as e:
        print(f"  Uyarı: {e}", flush=True)
    return None


def main():
    if not os.path.isfile(MANIFEST_CSV):
        print("Önce: python src/export_metinler_for_detector.py", flush=True)
        sys.exit(1)
    if not os.path.isfile(SKORLAR_CSV):
        print("Önce: python src/annotate.py", flush=True)
        sys.exit(1)

    print("Manifest ve skorlar okunuyor...", flush=True)
    with open(MANIFEST_CSV, "r", encoding="utf-8") as f:
        manifest = list(csv.DictReader(f))
    with open(SKORLAR_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        skor_sutunlari = list(reader.fieldnames)
        skorlar = list(reader)

    if "ai_skoru" not in skor_sutunlari:
        skor_sutunlari.append("ai_skoru")

    key_to_ai = {}
    use_bino = _score_binoculars("test") is not None
    hf_pipe = None
    if use_bino:
        print("Binoculars kullanılıyor.", flush=True)
    else:
        print("Binoculars yok; Hugging Face (roberta-openai-detector) kullanılacak.", flush=True)
        hf_pipe = _load_transformers_pipeline()

    n = len(manifest)
    for i, row in enumerate(manifest, 1):
        kisa = row.get("dosya", "")
        path = os.path.join(METINLER_DIR, kisa)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            metin = f.read()
        skor = _score_binoculars(metin) if use_bino else _score_transformers(metin, hf_pipe)
        if skor is not None:
            key = (row.get("model", ""), row.get("prompt_id", ""), row.get("versiyon", ""))
            key_to_ai[key] = skor
            print(f"  [{i}/{n}] {kisa} -> {skor:.3f}", flush=True)

    if not key_to_ai and not use_bino:
        print("Transformers modeli yüklenemedi veya skor dönmedi.", flush=True)
        print("Manuel skorlar için: python src/merge_ai_skorlari.py <sonuc.csv>", flush=True)
        sys.exit(1)

    for s in skorlar:
        key = (s.get("model", ""), s.get("prompt_id", ""), s.get("versiyon", ""))
        s["ai_skoru"] = key_to_ai.get(key, "")

    with open(SKORLAR_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=skor_sutunlari, extrasaction="ignore")
        w.writeheader()
        w.writerows(skorlar)
    print(f"ai_skoru yazıldı: {SKORLAR_CSV}. Analiz: python src/analyze.py", flush=True)


if __name__ == "__main__":
    main()
