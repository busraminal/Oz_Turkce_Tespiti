# -*- coding: utf-8 -*-
"""
prompts.json'daki her konu için standart ve Öz Türkçe metin üretir.
- OpenAI API (bulut) veya
- PC'de kurulu model (Ollama / LM Studio vb. OpenAI-uyumlu sunucu)
Çıktı: data/raw/ altında .txt dosyaları + data/raw/raw_outputs.json
"""
from __future__ import annotations

import json
import os
import sys

# Proje kökü (src bir üst = kök)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE, ".env"))
except ImportError:
    pass

PROMPTS_PATH = os.path.join(BASE, "data", "prompts.json")
RAW_DIR = os.path.join(BASE, "data", "raw")
RAW_JSON = os.path.join(BASE, "data", "raw", "raw_outputs.json")

DEFAULT_MODEL_OPENAI = "gpt-4o-mini"
# Yerel: Ollama varsayılan adres; LM Studio için .env'de LOCAL_BASE_URL=http://localhost:1234/v1
DEFAULT_LOCAL_BASE = "http://localhost:11434/v1"
DEFAULT_LOCAL_MODEL = "qwen2.5:7b"


def _openai_uret(prompt: str, model: str) -> str:
    """OpenAI (bulut) Chat Completions ile tek metin üretir."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai paketi yok. pip install openai çalıştırın.")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY .env dosyasında tanımlı değil.")
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024,
    )
    text = (resp.choices[0].message.content or "").strip()
    return text


def _local_uret(prompt: str, model: str, base_url: str) -> str:
    """PC'de çalışan OpenAI-uyumlu sunucudan (Ollama, LM Studio vb.) metin üretir."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai paketi yok. pip install openai çalıştırın.")
    # Ollama/LM Studio genelde API key istemez; isterse .env'de LOCAL_API_KEY
    api_key = os.environ.get("LOCAL_API_KEY", "ollama")
    client = OpenAI(base_url=base_url, api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024,
    )
    text = (resp.choices[0].message.content or "").strip()
    return text


def main(model: str = None, limit: int = None, local: bool = None, append: bool = False):
    """
    prompts.json okuyup her konu için standart + öz türkçe metin üretir.
    local=True veya BACKEND=local/ollama ise PC'deki model kullanılır.
    append=True ise mevcut raw_outputs.json'a bu modelin çıktıları eklenir (ikinci model için).
    """
    use_local = local
    if use_local is None:
        backend = (os.environ.get("BACKEND") or "").lower()
        use_local = backend in ("local", "ollama", "yerel")
    if use_local:
        base_url = os.environ.get("LOCAL_BASE_URL", DEFAULT_LOCAL_BASE)
        model = model or os.environ.get("LOCAL_MODEL", DEFAULT_LOCAL_MODEL)
        print(f"Yerel model: {model} @ {base_url}")
        uret = lambda p: _local_uret(p, model, base_url)
    else:
        model = model or os.environ.get("OZ_TURKCE_MODEL", DEFAULT_MODEL_OPENAI)
        print(f"OpenAI (bulut): {model}")
        uret = lambda p: _openai_uret(p, model)
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        prompts = json.load(f)
    if limit is not None:
        prompts = prompts[:limit]
    os.makedirs(RAW_DIR, exist_ok=True)
    outputs = []
    if append and os.path.isfile(RAW_JSON):
        try:
            with open(RAW_JSON, "r", encoding="utf-8") as f:
                existing = json.load(f)
            # Sadece diğer modellerin çıktılarını tut; bu modeli yeniden üreteceğiz
            current_model = model.replace("-", "_")
            for item in existing:
                if (item.get("model") or "").replace("-", "_") != current_model:
                    outputs.append(item)
            print(f"Append: mevcut {len(outputs)} kayıt korunuyor, {model} eklenecek.")
        except Exception as e:
            print(f"Uyarı: mevcut JSON okunamadı ({e}), sıfırdan başlanıyor.")
    for i, p in enumerate(prompts):
        pid = p.get("id", f"prompt_{i}")
        konu = p.get("konu", "")
        for versiyon, key in [("standart", "prompt_standart"), ("oz_turkce", "prompt_oz_turkce")]:
            prompt_metin = p.get(key)
            if not prompt_metin:
                continue
            print(f"[{pid}] {versiyon} üretiliyor...")
            try:
                metin = uret(prompt_metin)
                if not (metin and metin.strip()):
                    print(f"  Uyarı: Boş yanıt (Ollama/model yanıt vermedi olabilir)")
                    metin = ""
            except Exception as e:
                print(f"  Hata: {e}")
                metin = ""
            dosya_ad = f"{model.replace('-', '_')}_{pid}_{versiyon}.txt"
            txt_path = os.path.join(RAW_DIR, dosya_ad)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(metin)
            outputs.append({
                "model": model,
                "prompt_id": pid,
                "konu": konu,
                "versiyon": versiyon,
                "metin": metin,
                "dosya": dosya_ad,
            })
    with open(RAW_JSON, "w", encoding="utf-8") as f:
        json.dump(outputs, f, ensure_ascii=False, indent=2)
    print(f"Toplam {len(outputs)} metin kaydedildi. Özet: {RAW_JSON}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Öz Türkçe deneyi için LLM metinleri üretir.")
    parser.add_argument("--model", default=None, help="Model adı (yerel veya OpenAI)")
    parser.add_argument("--limit", type=int, default=None, help="İlk N konu (test için)")
    parser.add_argument("--local", action="store_true", help="PC'deki modeli kullan (Ollama/LM Studio)")
    parser.add_argument("--append", action="store_true", help="Mevcut raw_outputs.json'a ekle (ikinci model için)")
    args = parser.parse_args()
    main(model=args.model, limit=args.limit, local=args.local, append=args.append)
