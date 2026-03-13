# -*- coding: utf-8 -*-
"""
skorlar.csv okur; Model x Versiyon özet tablosu ve grafik üretir.
Çıktı: results/ozet_tablo.csv, results/oz_turkce_grafik.png
"""
from __future__ import annotations

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKORLAR_CSV = os.path.join(BASE, "data", "annotated", "skorlar.csv")
RESULTS_DIR = os.path.join(BASE, "results")
OZET_CSV = os.path.join(BASE, "results", "ozet_tablo.csv")
GRAFIK_PNG = os.path.join(BASE, "results", "oz_turkce_grafik.png")


def main():
    try:
        import pandas as pd
    except ImportError:
        print("pandas gerekli: pip install pandas")
        return
    if not os.path.isfile(SKORLAR_CSV):
        print(f"{SKORLAR_CSV} bulunamadı. Önce annotate.py çalıştırın.")
        return
    df = pd.read_csv(SKORLAR_CSV, encoding="utf-8")
    if df.empty:
        print("skorlar.csv boş.")
        return
    os.makedirs(RESULTS_DIR, exist_ok=True)
    # Özet: model x versiyon -> ortalama oz_turkce_oran, adet; ai_skoru varsa ortalama
    ozet = df.groupby(["model", "versiyon"], as_index=False).agg(
        ortalama_oz_turkce_oran=("oz_turkce_oran", "mean"),
        adet=("oz_turkce_oran", "count"),
    )
    ai_cols = [c for c in df.columns if c == "ai_skoru" or c.startswith("ai_skoru_")]
    for col in ai_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        ai_ort = df.groupby(["model", "versiyon"])[col].mean().reset_index()
        ai_ort = ai_ort.rename(columns={col: f"ortalama_{col}"})
        ozet = ozet.merge(ai_ort, on=["model", "versiyon"], how="left")
    ozet.to_csv(OZET_CSV, index=False, encoding="utf-8")
    print(f"Özet tablo: {OZET_CSV}")
    print(ozet.to_string(index=False))
    # Grafik
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib yok; grafik atlandı.")
        return
    n_extra = len(ai_cols)
    fig, axes = plt.subplots(1, 1 + n_extra, figsize=(4 + 4 * n_extra, 4))
    if n_extra == 0:
        axes = [axes]
    # Sol: Versiyon başına ortalama Öz Türkçe oranı (çubuk)
    ax = axes[0]
    versiyonlar = df["versiyon"].unique()
    ortalar = [df[df["versiyon"] == v]["oz_turkce_oran"].mean() for v in versiyonlar]
    ax.bar(range(len(versiyonlar)), ortalar, tick_label=versiyonlar, color=["#1f77b4", "#ff7f0e"])
    ax.set_ylabel("Ortalama Öz Türkçe oranı")
    ax.set_xlabel("Versiyon")
    ax.set_title("Öz Türkçe yoğunluğu (standart vs öz türkçe)")
    ax.set_ylim(0, 1)
    for i, col in enumerate(ai_cols):
        if i + 1 < len(axes):
            ax2 = axes[i + 1]
            ax2.scatter(df["oz_turkce_oran"], df[col], alpha=0.6)
            ax2.set_xlabel("Öz Türkçe oranı")
            ax2.set_ylabel(col)
            ax2.set_title(f"X: Öz Türkçe / Y: {col}")
    plt.tight_layout()
    plt.savefig(GRAFIK_PNG, dpi=150)
    plt.close()
    print(f"Grafik: {GRAFIK_PNG}")


if __name__ == "__main__":
    main()
