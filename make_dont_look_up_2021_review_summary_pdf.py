import os
import textwrap
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(".matplotlib-cache").resolve()))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import Normalizer


IN_CSV = Path("dont_look_up_2021_all_audience_reviews_latest_500.csv")
OUT_PDF = Path("dont_look_up_2021_review_rating_word_topics.pdf")
OUT_STAR_COUNTS = Path("dont_look_up_2021_rating_counts.csv")
OUT_CLUSTERS = Path("dont_look_up_2021_tfidf_word_topic_clusters.csv")

FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
if FONT_PATH.exists():
    font_manager.fontManager.addfont(str(FONT_PATH))
    plt.rcParams["font.family"] = "Arial Unicode MS"
plt.rcParams["axes.unicode_minus"] = False


TOPIC_RULES = {
    "정치/미디어 풍자": {
        "satire",
        "satirical",
        "political",
        "politics",
        "media",
        "news",
        "society",
        "social",
        "commentary",
        "message",
        "metaphor",
        "allegory",
        "trump",
        "government",
    },
    "코미디/블랙유머": {
        "comedy",
        "funny",
        "fun",
        "humor",
        "humour",
        "laugh",
        "jokes",
        "dark",
        "absurd",
        "ridiculous",
        "cynical",
        "tone",
    },
    "기후/재난/현실성": {
        "climate",
        "comet",
        "asteroid",
        "planet",
        "earth",
        "science",
        "scientists",
        "scientist",
        "disaster",
        "catastrophic",
        "world",
        "real",
        "relevant",
    },
    "스타 캐스팅/연기": {
        "cast",
        "actors",
        "actor",
        "acting",
        "performance",
        "performances",
        "leo",
        "leonardo",
        "dicaprio",
        "jennifer",
        "lawrence",
        "streep",
        "meryl",
        "stars",
    },
    "스토리/연출/메시지 전달": {
        "story",
        "plot",
        "script",
        "writing",
        "directing",
        "direction",
        "mckay",
        "adam",
        "heavy",
        "handed",
        "blunt",
        "subtle",
        "point",
        "premise",
    },
    "평가/추천/명작 반응": {
        "best",
        "great",
        "amazing",
        "perfect",
        "masterpiece",
        "excellent",
        "favorite",
        "incredible",
        "brilliant",
        "recommend",
        "loved",
        "awesome",
    },
    "부정평/비판": {
        "bad",
        "boring",
        "overrated",
        "hate",
        "weak",
        "terrible",
        "worse",
        "problem",
        "annoying",
        "predictable",
        "disappointing",
        "mediocre",
        "mess",
        "preachy",
        "heavy",
        "handed",
        "loud",
        "annoying",
        "awful",
        "waste",
    },
    "관람 경험/재미": {
        "fun",
        "entertaining",
        "enjoyed",
        "enjoyable",
        "watch",
        "watching",
        "rewatch",
        "experience",
        "worth",
        "solid",
        "decent",
        "okay",
    },
    "다국어 리뷰": {
        "pelicula",
        "película",
        "excelente",
        "historia",
        "musica",
        "música",
        "filme",
        "muito",
        "obra",
        "cine",
        "que",
        "una",
        "la",
    },
}


def choose_cluster_count(vectors, candidates):
    best_k = None
    best_score = -1
    scores = []
    for k in candidates:
        if k >= len(vectors):
            continue
        labels = KMeans(n_clusters=k, random_state=42, n_init=30).fit_predict(vectors)
        score = silhouette_score(vectors, labels)
        scores.append((k, score))
        if score > best_score:
            best_k = k
            best_score = score
    return best_k or 6, scores


def infer_topic(terms):
    term_set = {str(term).lower() for term in terms}
    scores = {label: len(term_set & keywords) for label, keywords in TOPIC_RULES.items()}
    label, score = max(scores.items(), key=lambda item: item[1])
    return label if score else "기타 반응/표현"


def add_text_page(pdf, title, lines, fontsize=9):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    plt.axis("off")
    fig.text(0.06, 0.955, title, fontsize=16, fontweight="bold", va="top")

    y = 0.91
    for line in lines:
        wrapped = textwrap.wrap(str(line), width=92, replace_whitespace=False) or [""]
        for part in wrapped:
            if y < 0.06:
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)
                fig = plt.figure(figsize=(8.27, 11.69))
                fig.patch.set_facecolor("white")
                plt.axis("off")
                fig.text(0.06, 0.955, f"{title} (continued)", fontsize=16, fontweight="bold", va="top")
                y = 0.91
            fig.text(0.06, y, part, fontsize=fontsize, family=plt.rcParams["font.family"][0], va="top")
            y -= 0.019

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_rating_chart(pdf, rating_counts):
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    colors = ["#c7372f", "#d85a42", "#e28642", "#e5b84d", "#84a85a", "#3f8d63", "#25715f", "#1d5c6b", "#254a78", "#443d72"]
    ax.bar(rating_counts["rating_label"], rating_counts["count"], color=colors[: len(rating_counts)])
    ax.set_title("별점별 리뷰 갯수", loc="left", fontsize=18, fontweight="bold")
    ax.set_xlabel("별점")
    ax.set_ylabel("리뷰 수")
    ax.grid(axis="y", alpha=0.25)
    for i, row in rating_counts.iterrows():
        ax.text(i, row["count"] + max(rating_counts["count"]) * 0.01, str(row["count"]), ha="center", va="bottom", fontsize=11)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_table_page(pdf, title, table_df, fontsize=8):
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    ax.axis("off")
    ax.set_title(title, fontsize=15, fontweight="bold", loc="left", pad=16)

    display = table_df.copy()
    for col in display.columns:
        display[col] = display[col].map(lambda x: f"{x:.5f}" if isinstance(x, float) else x)

    table = ax.table(
        cellText=display.values,
        colLabels=display.columns,
        cellLoc="left",
        colLoc="left",
        loc="upper left",
        bbox=[0, 0, 1, 0.95],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)
    table.scale(1, 1.2)
    for (row, _col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#eeeeee")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_scatter_page(pdf, clustered):
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    for topic, group in clustered.groupby("topic"):
        ax.scatter(group["x"], group["y"], s=16, alpha=0.68, label=topic)

    for _, row in clustered.sort_values("mean_tfidf", ascending=False).head(32).iterrows():
        ax.annotate(row["term"], (row["x"], row["y"]), fontsize=7, alpha=0.85)

    ax.set_title("TF-IDF 단어 클러스터 2D 투영", loc="left", fontweight="bold", fontsize=16)
    ax.set_xlabel("SVD 1")
    ax.set_ylabel("SVD 2")
    ax.legend(fontsize=7, ncol=1, loc="best")
    ax.grid(True, alpha=0.2)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def build_clusters(df):
    reviews = df["review"].fillna("").astype(str)
    vectorizer = TfidfVectorizer(
        strip_accents="unicode",
        lowercase=True,
        stop_words="english",
        min_df=2,
        max_df=0.9,
        token_pattern=r"(?u)\b[^\W\d_][^\W\d_]{1,}\b",
    )
    doc_term = vectorizer.fit_transform(reviews)
    terms = vectorizer.get_feature_names_out()

    stats = pd.DataFrame(
        {
            "term": terms,
            "mean_tfidf": doc_term.mean(axis=0).A1,
            "max_tfidf": doc_term.max(axis=0).toarray().ravel(),
            "document_count": (doc_term > 0).sum(axis=0).A1,
        }
    ).sort_values(["mean_tfidf", "max_tfidf"], ascending=False)

    selected_terms = stats.head(min(450, len(stats))).copy()
    term_doc = doc_term.T[selected_terms.index.to_numpy()]

    reduced_dim = max(2, min(50, term_doc.shape[0] - 1, term_doc.shape[1] - 1))
    reduced = TruncatedSVD(n_components=reduced_dim, random_state=42).fit_transform(term_doc)
    normalized = Normalizer().fit_transform(reduced)
    best_k, scores = choose_cluster_count(normalized, range(6, 13))
    labels = KMeans(n_clusters=best_k, random_state=42, n_init=50).fit_predict(normalized)
    projection = TruncatedSVD(n_components=2, random_state=42).fit_transform(term_doc)

    clustered = selected_terms.reset_index(drop=True)
    clustered["cluster"] = labels
    clustered["x"] = projection[:, 0]
    clustered["y"] = projection[:, 1]

    topic_by_cluster = {}
    for cluster_id, group in clustered.groupby("cluster"):
        top_terms = group.sort_values(["mean_tfidf", "max_tfidf"], ascending=False).head(20)["term"]
        topic_by_cluster[cluster_id] = infer_topic(top_terms)
    clustered["topic"] = clustered["cluster"].map(topic_by_cluster)
    return clustered.sort_values(["topic", "mean_tfidf", "max_tfidf"], ascending=[True, False, False]), scores, len(terms), len(selected_terms)


def main():
    df = pd.read_csv(IN_CSV)
    df["rating_numeric"] = pd.to_numeric(df["rating_numeric"], errors="coerce")
    df["review"] = df["review"].fillna("").astype(str)

    rating_counts = (
        df.dropna(subset=["rating_numeric"])
        .groupby("rating_numeric", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("rating_numeric")
    )
    rating_counts["rating_label"] = rating_counts["rating_numeric"].map(lambda value: f"{value:g}★")
    rating_counts["share_pct"] = rating_counts["count"] / rating_counts["count"].sum() * 100
    rating_counts[["rating_numeric", "rating_label", "count", "share_pct"]].to_csv(OUT_STAR_COUNTS, index=False)

    clustered, scores, vocabulary_size, clustered_terms = build_clusters(df)
    clustered.to_csv(OUT_CLUSTERS, index=False)

    topic_summary = (
        clustered.sort_values(["topic", "mean_tfidf", "max_tfidf"], ascending=[True, False, False])
        .groupby("topic")
        .agg(
            terms=("term", "size"),
            top_terms=("term", lambda values: ", ".join(values.head(14).astype(str))),
        )
        .reset_index()
        .sort_values("terms", ascending=False)
    )

    with PdfPages(OUT_PDF) as pdf:
        add_text_page(
            pdf,
            "Don't Look Up 관객 리뷰 분석",
            [
                f"Source CSV: {IN_CSV}",
                f"Review records used: {len(df)}",
                f"Ratings counted: {int(rating_counts['count'].sum())}",
                f"TF-IDF vocabulary size after filtering: {vocabulary_size}",
                f"Clustered top terms: {clustered_terms}",
                "",
                "방법:",
                "1. rating_numeric 별점을 기준으로 리뷰 수를 집계했습니다.",
                "2. 리뷰 본문에서 TF-IDF 단어 가중치를 계산했습니다. 영어 불용어와 1회 등장 단어는 제외했습니다.",
                "3. 단어별 TF-IDF 패턴을 SVD로 축소한 뒤 KMeans로 클러스터링했습니다.",
                "4. 각 클러스터의 상위 단어를 기준으로 사람이 읽기 쉬운 주제명을 자동 부여했습니다.",
            ],
        )
        add_rating_chart(pdf, rating_counts)
        add_table_page(pdf, "별점별 리뷰 갯수 표", rating_counts[["rating_label", "count", "share_pct"]], fontsize=10)
        add_table_page(pdf, "단어 주제 클러스터 요약", topic_summary, fontsize=7)
        add_scatter_page(pdf, clustered)

        for topic, group in clustered.groupby("topic"):
            ordered = group.sort_values(["mean_tfidf", "max_tfidf"], ascending=False).head(55)
            add_table_page(
                pdf,
                f"주제: {topic}",
                ordered[["term", "mean_tfidf", "max_tfidf", "document_count", "cluster"]],
                fontsize=8,
            )

        add_text_page(pdf, "클러스터 수 선택 기준", ["Silhouette scores:"] + [f"k={k}: {score:.4f}" for k, score in scores])

    print(f"Wrote {OUT_PDF}")
    print(f"Wrote {OUT_STAR_COUNTS}")
    print(f"Wrote {OUT_CLUSTERS}")
    print(f"reviews={len(df)} clustered_terms={clustered_terms} topics={topic_summary.shape[0]}")


if __name__ == "__main__":
    main()
