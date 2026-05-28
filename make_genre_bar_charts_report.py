import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(".matplotlib-cache").resolve()))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages


OUT_PDF = Path("all_movies_genre_bar_charts_report.pdf")
OUT_PNG = Path("all_movies_genre_avg_rating_bar.png")
OUT_CSV = Path("all_movies_genre_metrics.csv")

FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
if FONT_PATH.exists():
    font_manager.fontManager.addfont(str(FONT_PATH))
    plt.rcParams["font.family"] = "Arial Unicode MS"
plt.rcParams["axes.unicode_minus"] = False

MOVIES = [
    {
        "movie": "KPop Demon Hunters",
        "rating_csv": "kpop_demon_hunters_rating_counts.csv",
        "genres": ["Kids & Family", "Musical", "Comedy", "Action", "Fantasy", "Animation", "Adventure"],
    },
    {
        "movie": "Whiplash",
        "rating_csv": "whiplash_2014_rating_counts.csv",
        "genres": ["Drama", "Music", "Mystery & Thriller"],
    },
    {
        "movie": "Everything Everywhere All at Once",
        "rating_csv": "everything_everywhere_all_at_once_rating_counts.csv",
        "genres": ["Comedy", "Adventure", "Sci-Fi", "Fantasy"],
    },
    {
        "movie": "Apex",
        "rating_csv": "apex_2026_rating_counts.csv",
        "genres": ["Action", "Mystery & Thriller"],
    },
    {
        "movie": "F1 The Movie",
        "rating_csv": "f1_the_movie_rating_counts.csv",
        "genres": ["Action", "Drama", "Sports"],
    },
    {
        "movie": "GOAT",
        "rating_csv": "goat_2026_rating_counts.csv",
        "genres": ["Kids & Family", "Comedy", "Animation", "Adventure", "Sports"],
    },
    {
        "movie": "Red Notice",
        "rating_csv": "red_notice_rating_counts.csv",
        "genres": ["Action", "Comedy"],
    },
    {
        "movie": "Don't Look Up",
        "rating_csv": "dont_look_up_2021_rating_counts.csv",
        "genres": ["Comedy"],
    },
]


def movie_metrics(path):
    ratings = pd.read_csv(path)
    total = ratings["count"].sum()
    return {
        "reviews": int(total),
        "avg_rating": (ratings["rating_numeric"] * ratings["count"]).sum() / total,
        "5star_pct": ratings.loc[ratings["rating_numeric"] == 5, "count"].sum() / total * 100,
        "4plus_pct": ratings.loc[ratings["rating_numeric"] >= 4, "count"].sum() / total * 100,
        "2low_pct": ratings.loc[ratings["rating_numeric"] <= 2, "count"].sum() / total * 100,
    }


def build_genre_metrics():
    rows = []
    for item in MOVIES:
        metrics = movie_metrics(item["rating_csv"])
        for genre in item["genres"]:
            rows.append({"genre": genre, "movie": item["movie"], **metrics})
    exploded = pd.DataFrame(rows)
    genre_rows = []
    for genre, group in exploded.groupby("genre"):
        genre_rows.append(
            {
                "genre": genre,
                "movie_count": group["movie"].nunique(),
                "movies": ", ".join(sorted(group["movie"].unique())),
                "avg_rating": group["avg_rating"].mean(),
                "5star_pct": group["5star_pct"].mean(),
                "4plus_pct": group["4plus_pct"].mean(),
                "2low_pct": group["2low_pct"].mean(),
            }
        )
    out = pd.DataFrame(genre_rows).sort_values(["movie_count", "avg_rating"], ascending=[False, False])
    out.to_csv(OUT_CSV, index=False)
    return out


def add_bar_page(pdf, df, metric, title, xlabel, color, output_png=None):
    ordered = df.sort_values(metric, ascending=True)
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    ax.barh(ordered["genre"], ordered[metric], color=color, alpha=0.88)
    ax.set_title(title, fontsize=18, fontweight="bold", loc="left")
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", alpha=0.25)
    for idx, (_row_idx, row) in enumerate(ordered.iterrows()):
        value = row[metric]
        label = f"{value:.1f}" if metric != "movie_count" else f"{int(value)}"
        ax.text(value + max(ordered[metric]) * 0.01, idx, label, va="center", fontsize=9)
    if metric == "avg_rating":
        ax.set_xlim(0, 5)
    pdf.savefig(fig, bbox_inches="tight")
    if output_png:
        fig.savefig(output_png, dpi=180, bbox_inches="tight")
    plt.close(fig)


def add_grouped_page(pdf, df):
    ordered = df.sort_values("avg_rating", ascending=False)
    fig, ax = plt.subplots(figsize=(13, 8))
    fig.patch.set_facecolor("white")
    x = range(len(ordered))
    width = 0.24
    ax.bar([i - width for i in x], ordered["5star_pct"], width, label="5점 비중", color="#2c7a6b")
    ax.bar(x, ordered["4plus_pct"], width, label="4점 이상", color="#4f8fb8")
    ax.bar([i + width for i in x], ordered["2low_pct"], width, label="2점 이하", color="#c65b4b")
    ax.set_xticks(list(x))
    ax.set_xticklabels(ordered["genre"], rotation=35, ha="right", fontsize=9)
    ax.set_ylabel("평균 비중 (%)")
    ax.set_title("장르별 호평/혹평 비중 비교", fontsize=18, fontweight="bold", loc="left")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_table_page(pdf, df):
    fig, ax = plt.subplots(figsize=(13, 8))
    fig.patch.set_facecolor("white")
    ax.axis("off")
    ax.set_title("장르별 수치 요약", fontsize=18, fontweight="bold", loc="left", pad=14)
    display = df[["genre", "movie_count", "avg_rating", "5star_pct", "4plus_pct", "2low_pct", "movies"]].copy()
    for col in ["avg_rating", "5star_pct", "4plus_pct", "2low_pct"]:
        display[col] = display[col].map(lambda value: f"{value:.1f}")
    table = ax.table(
        cellText=display.values,
        colLabels=["장르", "영화 수", "평균 별점", "5점%", "4점 이상%", "2점 이하%", "포함 영화"],
        cellLoc="left",
        colLoc="left",
        loc="upper left",
        bbox=[0, 0, 1, 0.92],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.scale(1, 1.2)
    for (row, _col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#eeeeee")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def main():
    df = build_genre_metrics()
    with PdfPages(OUT_PDF) as pdf:
        add_bar_page(pdf, df, "movie_count", "장르별 포함 영화 수", "영화 수", "#6f7f95")
        add_bar_page(pdf, df, "avg_rating", "장르별 평균 별점", "평균 별점", "#2c7a6b", OUT_PNG)
        add_bar_page(pdf, df, "5star_pct", "장르별 5점 비중", "5점 비중 (%)", "#4f8fb8")
        add_bar_page(pdf, df, "2low_pct", "장르별 2점 이하 비중", "2점 이하 비중 (%)", "#c65b4b")
        add_grouped_page(pdf, df)
        add_table_page(pdf, df)
    print(f"Wrote {OUT_PDF}")
    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
