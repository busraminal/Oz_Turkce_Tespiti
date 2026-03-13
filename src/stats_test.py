# -*- coding: utf-8 -*-
"""
Eşleşmiş çiftlerde (aynı model, aynı prompt_id) standart vs öz türkçe AI skoru farkı
için Wilcoxon işaretli sıra testi (ve isteğe bağlı paired t-test) yapar.
Makale için anlamlılık raporu: results/stats_sonuc.txt
"""
from __future__ import annotations

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKORLAR_CSV = os.path.join(BASE, "data", "annotated", "skorlar.csv")
RESULTS_DIR = os.path.join(BASE, "results")
STATS_OUT = os.path.join(BASE, "results", "stats_sonuc.txt")


def main():
    if not os.path.isfile(SKORLAR_CSV):
        print("skorlar.csv bulunamadı. Önce annotate.py ve dedektör/merge çalıştırın.")
        sys.exit(1)
    try:
        import pandas as pd
    except ImportError:
        print("pandas gerekli.")
        sys.exit(1)
    df = pd.read_csv(SKORLAR_CSV, encoding="utf-8")
    if "ai_skoru" not in df.columns:
        print("ai_skoru sütunu yok. Adım 7 (dedektör veya merge) çalıştırın.")
        sys.exit(1)
    # Boş olmayan skorlar
    df = df.dropna(subset=["ai_skoru"])
    df["ai_skoru"] = pd.to_numeric(df["ai_skoru"], errors="coerce")
    df = df.dropna(subset=["ai_skoru"])
    if df.empty:
        print("Geçerli ai_skoru yok.")
        sys.exit(1)
    # Eşleşmiş çiftler: (model, prompt_id) başına standart ve oz_turkce
    pivot = df.pivot_table(
        index=["model", "prompt_id"],
        columns="versiyon",
        values="ai_skoru",
        aggfunc="first",
    )
    if "standart" not in pivot.columns or "oz_turkce" not in pivot.columns:
        print("standart ve oz_turkce versiyonları bulunamadı.")
        sys.exit(1)
    pivot = pivot.dropna(subset=["standart", "oz_turkce"])
    n_pairs = len(pivot)
    if n_pairs < 2:
        print("Yeterli eşleşmiş çift yok (en az 2).")
        sys.exit(1)
    standart = pivot["standart"].values
    oz_turkce = pivot["oz_turkce"].values
    diff = oz_turkce - standart  # Öz Türkçe - Standart (negatif = Öz Türkçe’de skor düşük)
    try:
        from scipy import stats
    except ImportError:
        print("scipy gerekli: pip install scipy")
        sys.exit(1)
    wilcoxon = stats.wilcoxon(standart, oz_turkce, alternative="two-sided")
    try:
        t_res = stats.ttest_rel(standart, oz_turkce)
    except Exception:
        t_res = None
    os.makedirs(RESULTS_DIR, exist_ok=True)
    lines = [
        "Öz Türkçe × AI Tespiti — İstatistik Raporu",
        "==========================================",
        "",
        f"Eşleşmiş çift sayısı (model × prompt_id): {n_pairs}",
        f"Standart ortalama AI skoru: {standart.mean():.4f}",
        f"Öz Türkçe ortalama AI skoru: {oz_turkce.mean():.4f}",
        f"Fark (öz_turkce - standart): {diff.mean():.4f}",
        "",
        "Wilcoxon işaretli sıra testi (standart vs öz_turkce, two-sided):",
        f"  istatistik = {wilcoxon.statistic:.4f}",
        f"  p-değeri   = {wilcoxon.pvalue:.4f}",
        "",
    ]
    if t_res is not None:
        lines.extend([
            "Paired t-test (standart vs öz_turkce):",
            f"  t = {t_res.statistic:.4f}, p = {t_res.pvalue:.4f}",
            "",
        ])
    lines.append("Yorum: p < 0,05 ise standart ile öz türkçe AI skorları arasında istatistiksel fark vardır.")
    lines.append("(Öz Türkçe’de skor daha düşükse dedektör Öz Türkçe metinleri daha az 'AI' olarak işaretliyor.)")
    text = "\n".join(lines)
    with open(STATS_OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print(f"\nRapor: {STATS_OUT}")


if __name__ == "__main__":
    main()
