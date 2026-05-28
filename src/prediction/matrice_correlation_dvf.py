import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns


INPUT_CSV = Path("data/processed/dvf_paris_prediction_encode_normalise.csv")
OUTPUT_DIR = Path("data/visuals/correlation_dvf")


def creer_matrice_correlation(input_csv=INPUT_CSV, output_dir=OUTPUT_DIR):
    df = pd.read_csv(input_csv, low_memory=False)
    df = df.apply(pd.to_numeric, errors="coerce").dropna()

    matrice = df.corr()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "matrice_correlation_dvf_encode_normalise.csv"
    html_path = output_dir / "matrice_correlation_dvf_encode_normalise.html"
    png_path = output_dir / "matrice_correlation_dvf_encode_normalise.png"

    matrice.to_csv(csv_path)

    taille = max(12, len(matrice.columns) * 0.45)
    plt.figure(figsize=(taille, taille))
    sns.heatmap(
        matrice,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        linewidths=0.4,
        linecolor="white",
        square=True,
        cbar_kws={"label": "Correlation"},
        annot_kws={"size": 6},
    )
    plt.title("Matrice de correlation DVF encode et normalise", fontsize=14)
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()
    plt.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close()

    figure = go.Figure(
        data=go.Heatmap(
            z=matrice.values,
            x=matrice.columns,
            y=matrice.index,
            zmin=-1,
            zmax=1,
            colorscale="RdBu",
            reversescale=True,
            colorbar={"title": "Correlation"},
        )
    )
    figure.update_layout(
        title="Matrice de correlation DVF encode et normalise",
        width=1200,
        height=1000,
    )
    figure.write_html(html_path)

    return csv_path, html_path, png_path, matrice


def main():
    parser = argparse.ArgumentParser(
        description="Cree la matrice de correlation du CSV DVF encode et normalise.",
    )
    parser.add_argument("--input", default=INPUT_CSV, type=Path)
    parser.add_argument("--output-dir", default=OUTPUT_DIR, type=Path)
    args = parser.parse_args()

    csv_path, html_path, png_path, matrice = creer_matrice_correlation(
        args.input,
        args.output_dir,
    )

    print(f"Matrice CSV : {csv_path}")
    print(f"Matrice HTML : {html_path}")
    print(f"Matrice PNG : {png_path}")
    print(f"Lignes/colonnes : {matrice.shape[0]} x {matrice.shape[1]}")


if __name__ == "__main__":
    main()
