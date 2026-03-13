from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE = Path(__file__).resolve().parents[1]
SKORLAR_CSV = BASE / "data" / "annotated" / "skorlar.csv"
ASSETS_DIR = BASE / "assets"


def load_scores() -> pd.DataFrame:
    df = pd.read_csv(SKORLAR_CSV, encoding="utf-8")
    df["ai_skoru"] = pd.to_numeric(df["ai_skoru"], errors="coerce")
    return df.dropna(subset=["ai_skoru"]).copy()


def make_mean_chart(df: pd.DataFrame) -> None:
    summary = (
        df.groupby("versiyon", as_index=False)["ai_skoru"]
        .mean()
        .sort_values("versiyon")
    )
    labels = ["Oz Turkce" if v == "oz_turkce" else "Standart" for v in summary["versiyon"]]
    colors = ["#F28E2B" if v == "oz_turkce" else "#4E79A7" for v in summary["versiyon"]]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(labels, summary["ai_skoru"], color=colors, width=0.6)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Ortalama AI skoru")
    ax.set_title("Versiyona gore ortalama AI skoru")
    ax.grid(axis="y", linestyle="--", alpha=0.25)

    for bar, value in zip(bars, summary["ai_skoru"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.02,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    fig.tight_layout()
    fig.savefig(ASSETS_DIR / "mean_ai_score.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def make_prompt_delta_chart(df: pd.DataFrame) -> None:
    pivot = (
        df.pivot_table(
            index="prompt_id",
            columns="versiyon",
            values="ai_skoru",
            aggfunc="first",
        )
        .dropna(subset=["standart", "oz_turkce"])
        .sort_index()
    )
    delta = (pivot["oz_turkce"] - pivot["standart"]).sort_values()

    fig, ax = plt.subplots(figsize=(10, 5.2))
    x = range(len(delta))
    colors = ["#59A14F" if value >= 0 else "#E15759" for value in delta]
    bars = ax.bar(x, delta.values, color=colors)
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set_xticks(list(x))
    ax.set_xticklabels(delta.index, rotation=45, ha="right")
    ax.set_ylabel("Oz Turkce - Standart")
    ax.set_title("Prompt bazli AI skor farki")
    ax.grid(axis="y", linestyle="--", alpha=0.25)

    for bar, value in zip(bars, delta.values):
        y = value + 0.01 if value >= 0 else value - 0.03
        va = "bottom" if value >= 0 else "top"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y,
            f"{value:.2f}",
            ha="center",
            va=va,
            fontsize=8,
        )

    fig.tight_layout()
    fig.savefig(ASSETS_DIR / "prompt_level_delta.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ASSETS_DIR.mkdir(exist_ok=True)
    df = load_scores()
    if df.empty:
        raise SystemExit("ai_skoru iceren satir bulunamadi.")
    make_mean_chart(df)
    make_prompt_delta_chart(df)
    print(f"README gorselleri hazirlandi: {ASSETS_DIR}")


if __name__ == "__main__":
    main()
