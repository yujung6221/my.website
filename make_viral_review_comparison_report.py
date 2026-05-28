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


OUT_PDF = Path("rotten_tomatoes_viral_review_comparison_report.pdf")
OUT_CSV = Path("rotten_tomatoes_viral_review_comparison_summary.csv")

FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
if FONT_PATH.exists():
    font_manager.fontManager.addfont(str(FONT_PATH))
    plt.rcParams["font.family"] = "Arial Unicode MS"
plt.rcParams["axes.unicode_minus"] = False

MOVIES = [
    ("KPop Demon Hunters", "kpop_demon_hunters_rating_counts.csv", "kpop_demon_hunters_tfidf_word_topic_clusters.csv"),
    ("Whiplash", "whiplash_2014_rating_counts.csv", "whiplash_2014_tfidf_word_topic_clusters.csv"),
    ("Everything Everywhere All at Once", "everything_everywhere_all_at_once_rating_counts.csv", "everything_everywhere_all_at_once_tfidf_word_topic_clusters.csv"),
    ("Apex", "apex_2026_rating_counts.csv", "apex_2026_tfidf_word_topic_clusters.csv"),
    ("F1 The Movie", "f1_the_movie_rating_counts.csv", "f1_the_movie_tfidf_word_topic_clusters.csv"),
    ("GOAT", "goat_2026_rating_counts.csv", "goat_2026_tfidf_word_topic_clusters.csv"),
    ("Red Notice", "red_notice_rating_counts.csv", "red_notice_tfidf_word_topic_clusters.csv"),
    ("Don't Look Up", "dont_look_up_2021_rating_counts.csv", "dont_look_up_2021_tfidf_word_topic_clusters.csv"),
]

ARCHETYPES = {
    "Whiplash": {
        "type": "완성도/명작 입소문형",
        "hook": "연기, 긴장감, 재즈/드럼, 엔딩",
        "read": "혹평이 거의 없고 강한 5점이 많다. 논쟁형보다는 신뢰 기반 추천과 장기 입소문에 강하다.",
    },
    "GOAT": {
        "type": "가족/스포츠 호감 확산형",
        "hook": "농구, 동물 캐릭터, 가족영화, 귀여움/메시지",
        "read": "낮은 별점이 적고 5점 비중이 높다. 가족 관객과 스포츠/애니메이션 훅으로 넓게 퍼지는 구조다.",
    },
    "KPop Demon Hunters": {
        "type": "음악/팬덤/재관람형",
        "hook": "K-pop, 노래, 캐릭터, 애니메이션, 가족 관람",
        "read": "5점 비중이 높고 음악/캐릭터 단어가 강하다. 노래 클립, 팬아트, 재관람 담론에 유리하지만 cringe/overrated 반발도 있다.",
    },
    "Everything Everywhere All at Once": {
        "type": "감정/철학/논쟁형",
        "hook": "멀티버스, 가족, 삶의 의미, 이상한 상상력",
        "read": "사랑하는 층과 거부하는 층이 동시에 크다. 밈/해석/논쟁이 같이 도는 강한 담론형 바이럴이다.",
    },
    "F1 The Movie": {
        "type": "극장 체험/스펙터클형",
        "hook": "레이싱, 속도, Brad Pitt, 촬영/사운드",
        "read": "스토리 독창성보다 체험 가치가 바이럴 포인트다. IMAX/극장 관람 추천과 스포츠 팬 확산에 유리하다.",
    },
    "Don't Look Up": {
        "type": "이슈/풍자/문화논쟁형",
        "hook": "정치 풍자, 미디어 비판, 기후/재난, 스타 캐스팅",
        "read": "메시지와 현실성이 강한 대신 heavy-handed 반응도 있다. 찬반 공유와 사회 이슈 연결에 강하다.",
    },
    "Red Notice": {
        "type": "스타 캐스팅/캐주얼 스트리밍형",
        "hook": "Ryan Reynolds, Dwayne Johnson, Gal Gadot, 액션 코미디",
        "read": "스타 파워는 강하지만 generic/predictable 비판이 크다. 깊은 팬덤보다는 가벼운 시청/밈 소비형이다.",
    },
    "Apex": {
        "type": "혼합/부정 입소문형",
        "hook": "액션/스릴러, 배우명, 풍경/장면",
        "read": "저평 비중이 가장 높다. 긍정 바이럴보다 '생각보다 볼만함'과 '예측 가능/실망'이 섞인 논쟁형에 가깝다.",
    },
}


def wrap(text, width=88):
    lines = []
    for part in str(text).split("\n"):
        lines.extend(textwrap.wrap(part, width=width, replace_whitespace=False) or [""])
    return lines


def add_text_page(pdf, title, lines, fontsize=10):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    plt.axis("off")
    fig.text(0.06, 0.955, title, fontsize=18, fontweight="bold", va="top")
    y = 0.905
    for line in lines:
        for piece in wrap(line):
            if y < 0.06:
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)
                fig = plt.figure(figsize=(8.27, 11.69))
                fig.patch.set_facecolor("white")
                plt.axis("off")
                fig.text(0.06, 0.955, f"{title} (continued)", fontsize=18, fontweight="bold", va="top")
                y = 0.905
            fig.text(0.06, y, piece, fontsize=fontsize, va="top")
            y -= 0.023
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_table_page(pdf, title, table_df, fontsize=7):
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    ax.axis("off")
    ax.set_title(title, fontsize=17, fontweight="bold", loc="left", pad=14)
    display = table_df.copy()
    for col in display.columns:
        display[col] = display[col].map(lambda x: f"{x:.1f}" if isinstance(x, float) else x)
    tbl = ax.table(
        cellText=display.values,
        colLabels=display.columns,
        cellLoc="left",
        colLoc="left",
        loc="upper left",
        bbox=[0, 0, 1, 0.92],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(fontsize)
    tbl.scale(1, 1.2)
    for (row, _col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#eeeeee")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def load_summary():
    rows = []
    for title, rating_path, topic_path in MOVIES:
        ratings = pd.read_csv(rating_path)
        total = ratings["count"].sum()
        avg = (ratings["rating_numeric"] * ratings["count"]).sum() / total
        five = ratings.loc[ratings["rating_numeric"] == 5, "count"].sum() / total * 100
        high = ratings.loc[ratings["rating_numeric"] >= 4, "count"].sum() / total * 100
        low = ratings.loc[ratings["rating_numeric"] <= 2, "count"].sum() / total * 100
        mid = ratings.loc[(ratings["rating_numeric"] > 2) & (ratings["rating_numeric"] < 4), "count"].sum() / total * 100
        topics = pd.read_csv(topic_path)
        top_topics = topics.groupby("topic").size().sort_values(ascending=False).head(3)
        top_topic_text = " / ".join([f"{topic}({count})" for topic, count in top_topics.items()])
        archetype = ARCHETYPES[title]
        rows.append(
            {
                "movie": title,
                "reviews": int(total),
                "avg_rating": avg,
                "5star_pct": five,
                "4plus_pct": high,
                "2low_pct": low,
                "mid_pct": mid,
                "polar_signal": five + low,
                "viral_type": archetype["type"],
                "viral_hook": archetype["hook"],
                "top_topics": top_topic_text,
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    return df


def add_love_vs_controversy(pdf, summary):
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    colors = ["#d85a42", "#2c7a6b", "#7a5aa6", "#a55d3a", "#4f8fb8", "#6a9b52", "#b96a4b", "#5b6f96"]
    ax.scatter(summary["2low_pct"], summary["5star_pct"], s=summary["4plus_pct"] * 18, c=colors[: len(summary)], alpha=0.76)
    for _, row in summary.iterrows():
        ax.annotate(row["movie"], (row["2low_pct"], row["5star_pct"]), fontsize=8, xytext=(5, 4), textcoords="offset points")
    ax.set_xlabel("2점 이하 비중: 혹평/반발 (%)")
    ax.set_ylabel("5점 비중: 팬심/강한 애호 (%)")
    ax.set_title("바이럴 감정 지형: 사랑받는 강도 vs 논쟁성", fontsize=18, fontweight="bold", loc="left")
    ax.grid(True, alpha=0.25)
    ax.set_xlim(0, max(summary["2low_pct"]) + 8)
    ax.set_ylim(0, max(summary["5star_pct"]) + 8)
    fig.text(0.06, 0.03, "원 크기 = 4점 이상 비중. 오른쪽 위일수록 팬덤과 반발이 동시에 큰 담론형 바이럴 가능성이 높음.", fontsize=9)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_rank_bars(pdf, summary):
    fig, axes = plt.subplots(1, 2, figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    love = summary.sort_values("5star_pct", ascending=True)
    controversy = summary.sort_values("2low_pct", ascending=True)
    axes[0].barh(love["movie"], love["5star_pct"], color="#2c7a6b")
    axes[0].set_title("5점 비중: 팬심 강도", fontweight="bold")
    axes[0].set_xlabel("%")
    axes[0].grid(axis="x", alpha=0.25)
    axes[1].barh(controversy["movie"], controversy["2low_pct"], color="#c65b4b")
    axes[1].set_title("2점 이하 비중: 반발/논쟁성", fontweight="bold")
    axes[1].set_xlabel("%")
    axes[1].grid(axis="x", alpha=0.25)
    fig.suptitle("바이럴 동력의 양극: 팬심과 반발", fontsize=18, fontweight="bold", x=0.08, ha="left")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def topic_lines(title):
    topic_path = dict((movie, path) for movie, _rating, path in MOVIES)[title]
    topics = pd.read_csv(topic_path)
    lines = []
    for topic, count in topics.groupby("topic").size().sort_values(ascending=False).items():
        terms = ", ".join(
            topics[topics["topic"] == topic]
            .sort_values(["mean_tfidf", "max_tfidf"], ascending=False)
            .head(7)["term"]
            .astype(str)
        )
        lines.append(f"- {topic} ({count} terms): {terms}")
    return lines


def main():
    summary = load_summary()

    executive = [
        "분석 대상: Rotten Tomatoes all-audience 리뷰 각 500개, 총 4,000개 리뷰",
        "대상 영화: KPop Demon Hunters, Whiplash, Everything Everywhere All at Once, Apex, F1 The Movie, GOAT, Red Notice, Don't Look Up",
        "",
        "핵심 요약:",
        "1. 가장 강한 긍정 입소문형은 Whiplash와 GOAT다. 둘 다 4점 이상 비중이 높고 2점 이하 반발이 낮아 추천 저항이 적다.",
        "2. 가장 바이럴 담론성이 큰 영화는 Everything Everywhere All at Once와 KPop Demon Hunters다. 5점 팬심이 강하면서도 낮은 별점 반발이 적지 않아 사랑/반발이 함께 돈다.",
        "3. Don't Look Up은 영화 자체보다 메시지, 정치/미디어 풍자, 현실성 논쟁이 바이럴 동력이다. 공유될 때 감상평보다 입장 표명이 붙기 쉽다.",
        "4. F1 The Movie는 극장 체험/스펙터클형이다. 리뷰 언어가 레이싱, 속도, Brad Pitt, 촬영/사운드로 모이며 '어디서 봐야 하는가'가 확산 포인트다.",
        "5. Red Notice와 Apex는 스타/장르 훅은 있으나 공식적, 예측 가능, 지루함 같은 비판이 강하다. 긍정 바이럴보다는 '가볍게 볼 만함 vs 실망'의 혼합형이다.",
        "",
        "공통 바이럴 공식:",
        "- 한 문장으로 설명 가능한 훅이 있다: K-pop 노래, 재즈 드럼, 멀티버스, 레이싱 체험, 동물 농구, 정치 풍자, 스타 액션 코미디.",
        "- 공유 가능한 감정 단어가 반복된다: amazing, loved, best, funny, emotional, entertaining.",
        "- 반발 단어도 확산을 만든다: overrated, predictable, boring, generic, heavy-handed, cringe.",
        "- 스타/캐릭터/장면명이 검색 앵커가 된다: Simmons, Michelle Yeoh, Brad Pitt, Ryan Reynolds, Dwayne Johnson, GOAT/Jett, KPop songs.",
    ]

    viral_matrix = summary[
        [
            "movie",
            "avg_rating",
            "5star_pct",
            "4plus_pct",
            "2low_pct",
            "polar_signal",
            "viral_type",
            "viral_hook",
        ]
    ].copy()
    viral_matrix.columns = ["영화", "평균", "5점%", "4점이상%", "2점이하%", "강감정지수", "바이럴 유형", "핵심 훅"]

    with PdfPages(OUT_PDF) as pdf:
        add_text_page(pdf, "Rotten Tomatoes 리뷰 기반 바이럴 총집합 보고서", executive)
        add_table_page(pdf, "바이럴 지표 매트릭스", viral_matrix, fontsize=6.5)
        add_love_vs_controversy(pdf, summary)
        add_rank_bars(pdf, summary)

        for title in summary.sort_values("polar_signal", ascending=False)["movie"]:
            meta = ARCHETYPES[title]
            lines = [
                f"바이럴 유형: {meta['type']}",
                f"핵심 훅: {meta['hook']}",
                f"해석: {meta['read']}",
                "",
                "주요 단어 주제 클러스터:",
                *topic_lines(title),
            ]
            add_text_page(pdf, f"{title}: 바이럴 해석", lines, fontsize=9)

        closing = [
            "실무적 시사점:",
            "1. 긍정 입소문을 키우려면 Whiplash/GOAT처럼 명확한 만족 포인트와 낮은 반발률이 중요하다.",
            "2. 빠른 온라인 확산은 EEAAO/KPop처럼 팬심과 반발이 동시에 생기는 선명한 훅에서 잘 발생한다.",
            "3. F1처럼 체험형 영화는 '극장/IMAX/사운드' 같은 관람 조건을 메시지화할수록 유리하다.",
            "4. 정치/사회 풍자형은 Don't Look Up처럼 작품 평점보다 논점이 확산된다. 캠페인은 감상평보다 질문/입장/현실 연결을 중심으로 설계하는 편이 맞다.",
            "5. Red Notice/Apex류의 혼합형은 스타나 장르 장점을 짧게 밀되, 스토리 독창성 기대치를 낮추는 포지셔닝이 필요하다.",
            "",
            "주의:",
            "이 보고서는 최신 500개 관객 리뷰의 텍스트와 별점 분포를 기준으로 한 탐색적 분석이다. Rotten Tomatoes 전체 관객의 완전한 대표값이라기보다, 현재 리뷰 페이지에서 관찰되는 바이럴 신호로 읽는 것이 적절하다.",
        ]
        add_text_page(pdf, "종합 시사점", closing)

    print(f"Wrote {OUT_PDF}")
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
