# -*- coding: utf-8 -*-
"""
Sırayla: generate → annotate → analyze.
Yerel model için: --local, test için: --limit 2
"""
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

def run(cmd, desc):
    print(f"\n--- {desc} ---")
    r = subprocess.run(cmd, shell=True)
    if r.returncode != 0:
        print(f"Hata: {desc} çıkış kodu {r.returncode}")
        sys.exit(r.returncode)

# Yerel Ollama (Qwen2.5:7b); tüm prompt'lar. Test için: --limit 2 ekle
RUN_GENERATE = "python src/generate.py --local"

run(RUN_GENERATE, "Metin üretimi (generate)")
run("python src/annotate.py", "Öz Türkçe oranı (annotate)")
run("python src/analyze.py", "Özet tablo ve grafik (analyze)")
print("\nBitti.")
