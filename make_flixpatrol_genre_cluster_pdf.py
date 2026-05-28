from pathlib import Path
import textwrap

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages


MOVIES_CSV = Path("flixpatrol_uk_streaming_movies_2026-05-13.csv")
OVERALL_CSV = Path("flixpatrol_uk_genre_clusters_overall_2026-05-13.csv")
PLATFORM_CSV = Path("flixpatrol_uk_genre_clusters_by_platform_2026-05-13.csv")
MATRIX_CSV = Path("flixpatrol_uk_genre_platform_matrix_2026-05-13.csv")
OUT_PDF = Path("flixpatrol_uk_genre_cluster_report_2026-05-13.pdf")

PAGE = (11.69, 8.27)
INK = "#19212a"
MUTED = "#667085"
BLUE = "#2f6fbb"
TEAL = "#2a9d8f"
GOLD = "#d89b2b"
GRID = "#d8dde6"


def wrap(text, width):
    return "\n".join(textwrap.wrap(str(text), width=width, break_long_words=False))


def style_axis(ax):
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="x", colors=MUTED, labelsize=8)
    ax.tick_params(axis="y", colors=INK, labelsize=9, length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def add_footer(fig, page_label):
    fig.text(0.04, 0.035, page_label, color=MUTED, fontsize=8)
    fig.text(0.96, 0.035, "Source: FlixPatrol UK Streaming Top 10, 2026-05-13", color=MUTED, fontsize=8, ha="right")


def add_title(fig, title, subtitle=None):
    fig.text(0.04, 0.94, title, fontsize=19, fontweight="bold", color=INK, va="top")
    if subtitle:
        fig.text(0.04, 0.895, subtitle, fontsize=10, color=MUTED, va="top")


def draw_kpi(fig, x, y, label, value, color):
    fig.text(x, y, str(value), fontsize=26, fontweight="bold", color=color, va="top")
    fig.text(x, y - 0.055, label, fontsize=9, color=MUTED, va="top")


def cover_page(pdf, movies, overall, platform):
    fig = plt.figure(figsize=PAGE)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    add_title(
        fig,
        "UK Streaming Movies: Genre Cluster Report",
        "Grouped by genre tags across the full list, then broken down by streaming platform.",
    )

    draw_kpi(fig, 0.06, 0.77, "movie-platform listings", len(movies), BLUE)
    draw_kpi(fig, 0.31, 0.77, "genre clusters", len(overall), TEAL)
    draw_kpi(fig, 0.52, 0.77, "platforms", movies["streaming_platform"].nunique(), GOLD)
    draw_kpi(fig, 0.70, 0.77, "platform-genre clusters", len(platform), "#8a5fbf")

    top = overall.head(6).copy()
    summary_lines = [
        f"{row.genre_cluster}: {int(row.unique_movie_count)} unique movies across {int(row.platform_count)} platforms"
        for row in top.itertuples()
    ]
    fig.text(0.06, 0.57, "Top overall clusters", fontsize=13, fontweight="bold", color=INK)
    fig.text(0.06, 0.52, "\n".join(summary_lines), fontsize=10.5, color=INK, linespacing=1.45, va="top")

    note = (
        "Method: multi-tag clustering. A movie with two genre tags, such as Action; Superhero, "
        "is counted once in each relevant genre cluster. This preserves cross-genre patterns "
        "instead of forcing every movie into a single bucket."
    )
    fig.text(0.06, 0.27, wrap(note, 125), fontsize=10, color=MUTED, va="top", linespacing=1.35)

    add_footer(fig, "Overview")
    pdf.savefig(fig)
    plt.close(fig)


def overall_chart_page(pdf, overall):
    fig, ax = plt.subplots(figsize=PAGE)
    fig.patch.set_facecolor("white")
    add_title(fig, "Overall Genre Clusters", "Ranked by unique movie count. Bars show unique titles, labels show listing count.")

    top = overall.head(18).sort_values("unique_movie_count")
    bars = ax.barh(top["genre_cluster"], top["unique_movie_count"], color=BLUE, alpha=0.88)
    ax.set_xlabel("Unique movie count", fontsize=9, color=MUTED)
    style_axis(ax)
    ax.set_position([0.19, 0.12, 0.74, 0.72])
    for bar, listings in zip(bars, top["listing_count"]):
        ax.text(bar.get_width() + 0.25, bar.get_y() + bar.get_height() / 2, f"{int(listings)} listings", va="center", fontsize=8, color=MUTED)

    add_footer(fig, "Overall clusters")
    pdf.savefig(fig)
    plt.close(fig)


def heatmap_page(pdf, matrix):
    genre_cols = [c for c in matrix.columns if c not in ["streaming_platform", "total_genre_tags"]]
    totals = matrix[genre_cols].sum().sort_values(ascending=False)
    selected = list(totals.head(14).index)
    heat = matrix.set_index("streaming_platform")[selected]

    fig, ax = plt.subplots(figsize=PAGE)
    fig.patch.set_facecolor("white")
    add_title(fig, "Platform x Genre Density", "Top genre clusters by listing count. Darker cells indicate more movies tagged with that genre.")

    im = ax.imshow(heat.values, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(selected)), labels=selected, rotation=35, ha="right", fontsize=8, color=INK)
    ax.set_yticks(range(len(heat.index)), labels=heat.index, fontsize=9, color=INK)
    ax.set_position([0.16, 0.18, 0.72, 0.62])
    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            value = int(heat.iloc[i, j])
            if value:
                ax.text(j, i, value, ha="center", va="center", fontsize=8, color="white" if value >= 4 else INK)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.03)
    cbar.ax.tick_params(labelsize=8, colors=MUTED)

    add_footer(fig, "Platform matrix")
    pdf.savefig(fig)
    plt.close(fig)


def table_page(pdf, title, subtitle, df, columns, widths, footer):
    fig, ax = plt.subplots(figsize=PAGE)
    fig.patch.set_facecolor("white")
    ax.axis("off")
    add_title(fig, title, subtitle)
    ax.set_position([0.04, 0.08, 0.92, 0.76])

    display = df[columns].copy()
    for col, width in widths.items():
        if col in display.columns:
            display[col] = display[col].map(lambda x: wrap(x, width))

    table = ax.table(
        cellText=display.values,
        colLabels=display.columns,
        cellLoc="left",
        colLoc="left",
        loc="upper left",
        bbox=[0, 0, 1, 1],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.2)
    table.scale(1, 1.4)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#e5e8ef")
        cell.set_linewidth(0.4)
        if row == 0:
            cell.set_facecolor("#edf3fb")
            cell.set_text_props(weight="bold", color=INK)
        else:
            cell.set_facecolor("#ffffff" if row % 2 else "#fafbfc")
            cell.set_text_props(color=INK)
    add_footer(fig, footer)
    pdf.savefig(fig)
    plt.close(fig)


def platform_summary_page(pdf, platform):
    summary = []
    for platform_name, group in platform.groupby("streaming_platform"):
        top = group.sort_values(["unique_movie_count", "listing_count"], ascending=False).head(4)
        summary.append(
            {
                "streaming_platform": platform_name,
                "top_genre_clusters": "; ".join(
                    f"{r.genre_cluster} ({int(r.unique_movie_count)})" for r in top.itertuples()
                ),
            }
        )
    summary_df = pd.DataFrame(summary)
    table_page(
        pdf,
        "Platform Genre Fingerprints",
        "The strongest genre clusters per platform, using unique movie counts.",
        summary_df,
        ["streaming_platform", "top_genre_clusters"],
        {"top_genre_clusters": 95},
        "Platform summary",
    )


def main():
    movies = pd.read_csv(MOVIES_CSV)
    overall = pd.read_csv(OVERALL_CSV).sort_values(["unique_movie_count", "listing_count"], ascending=False)
    platform = pd.read_csv(PLATFORM_CSV)
    matrix = pd.read_csv(MATRIX_CSV)

    with PdfPages(OUT_PDF) as pdf:
        cover_page(pdf, movies, overall, platform)
        overall_chart_page(pdf, overall)
        heatmap_page(pdf, matrix)
        platform_summary_page(pdf, platform)

        table_page(
            pdf,
            "Overall Genre Cluster Detail",
            "Movies are shown with the platforms where they appear in the source list.",
            overall.head(18),
            ["genre_cluster", "listing_count", "unique_movie_count", "platform_count", "movies"],
            {"movies": 95},
            "Overall detail",
        )

        for platform_name, group in platform.groupby("streaming_platform"):
            top = group.sort_values(["unique_movie_count", "listing_count"], ascending=False).head(12)
            table_page(
                pdf,
                f"{platform_name}: Genre Clusters",
                "Cluster rows show the movies that belong to each genre tag on this platform.",
                top,
                ["genre_cluster", "listing_count", "unique_movie_count", "movies"],
                {"movies": 100},
                f"{platform_name} detail",
            )

    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
