#!/usr/bin/env python3
"""Build deterministic Markdown and HTML GEO reports from report-data.json."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from collections import OrderedDict
from pathlib import Path
from typing import Any


QUESTION_IDS = ["Q1", "Q2", "Q3", "Q4", "Q5"]
RECOMMENDATION_IDS = {"Q2", "Q3", "Q4", "Q5"}
RANK_BASES = {"explicit", "ordered-list", "comparison-table"}
STATUS_LABELS = {
    "good": ("충족", "b-good"),
    "warn": ("일부", "b-warn"),
    "bad": ("미충족", "b-bad"),
    "unknown": ("확인 불가", "b-unknown"),
    "na": ("해당 없음", "b-unknown"),
}
BAR_COLORS = ["#6ea0ff", "#f39c12", "#9b59b6", "#1abc9c", "#e91e8c"]


class ReportDataError(ValueError):
    """Raised when report data would produce an ambiguous or invalid report."""


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _key(value: str) -> str:
    return "".join(value.casefold().split())


def _percent(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "N/A"
    return f"{round(numerator / denominator * 100)}%"


def _grade(score: int) -> str:
    if score >= 90:
        return "우수"
    if score >= 70:
        return "양호"
    if score >= 50:
        return "보완 필요"
    return "시급"


def _md_cell(value: Any) -> str:
    return html.escape(_text(value), quote=False).replace("|", "\\|").replace("\n", "<br>")


def _html(value: Any) -> str:
    return html.escape(_text(value), quote=True)


def load_data(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    validate_data(data)
    return data


def validate_data(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise ReportDataError("schema_version은 1이어야 합니다.")
    if data.get("status") != "complete":
        raise ReportDataError("완료된 실행만 렌더링할 수 있습니다: status=complete 필요")
    target = data.get("target") or {}
    if not _text(target.get("name")).strip():
        raise ReportDataError("target.name이 필요합니다.")

    questions = data.get("questions")
    if not isinstance(questions, list):
        raise ReportDataError("questions는 목록이어야 합니다.")
    ids = [_text(question.get("id")) for question in questions]
    if sorted(ids) != QUESTION_IDS or len(ids) != len(set(ids)):
        raise ReportDataError("questions는 Q1~Q5를 정확히 한 번씩 포함해야 합니다.")

    technical = data.get("technical") or {}
    score = technical.get("score")
    if score is not None and (
        not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 100
    ):
        raise ReportDataError("technical.score는 null 또는 0~100 숫자여야 합니다.")

    target_key = _key(_text(target.get("name")))
    competitor_keys: set[str] = set()
    for competitor in data.get("competitors", []):
        name = _text(competitor.get("name")).strip()
        if not name:
            raise ReportDataError("competitors의 모든 항목에 name이 필요합니다.")
        key = _key(name)
        if key == target_key:
            raise ReportDataError("자사 이름을 경쟁사 목록에 넣을 수 없습니다.")
        if key in competitor_keys:
            raise ReportDataError(f"중복 경쟁사 이름: {name}")
        competitor_keys.add(key)

    for question in questions:
        if not _text(question.get("question")).strip():
            raise ReportDataError(f"{question['id']} question이 비어 있습니다.")
        if not isinstance(question.get("response", ""), str):
            raise ReportDataError(f"{question['id']} response는 문자열이어야 합니다.")
        if not question.get("response", "").strip():
            raise ReportDataError(f"{question['id']} response가 비어 있습니다.")
        judgments = [("target", question.get("target") or {})]
        judgments.extend(("brand", item) for item in question.get("brands", []))
        for kind, judgment in judgments:
            if kind == "brand" and not _text(judgment.get("name")).strip():
                raise ReportDataError(f"{question['id']}: brands의 모든 항목에 name이 필요합니다.")
            if judgment.get("recommended") and not judgment.get("mentioned"):
                raise ReportDataError(f"{question['id']} {kind}: 추천 O이면 언급도 O여야 합니다.")
            if (judgment.get("mentioned") or judgment.get("recommended")) and not _text(judgment.get("evidence")).strip():
                raise ReportDataError(f"{question['id']} {kind}: O 판정에는 evidence가 필요합니다.")
            if kind == "target" and judgment.get("mentioned") and not judgment.get("matched_names"):
                raise ReportDataError(f"{question['id']} target: 언급 O이면 matched_names가 필요합니다.")
            rank = judgment.get("rank")
            basis = judgment.get("rank_basis")
            if rank is None:
                if basis not in (None, ""):
                    raise ReportDataError(f"{question['id']} {kind}: rank 없이 rank_basis를 둘 수 없습니다.")
                continue
            if not judgment.get("recommended"):
                raise ReportDataError(f"{question['id']} {kind}: 추천 X에는 순위를 둘 수 없습니다.")
            if basis not in RANK_BASES:
                raise ReportDataError(f"{question['id']} {kind}: 허용되지 않은 순위 근거 {basis!r}")
            if not isinstance(rank, (int, float)) or isinstance(rank, bool) or rank <= 0:
                raise ReportDataError(f"{question['id']} {kind}: rank는 0보다 큰 숫자여야 합니다.")


def calculate_metrics(data: dict[str, Any]) -> dict[str, Any]:
    questions = sorted(data["questions"], key=lambda item: QUESTION_IDS.index(item["id"]))
    target_name = _text(data["target"]["name"])
    brands: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def ensure_brand(name: str, kind: str, specified: bool) -> dict[str, Any]:
        key = _key(name)
        if not key:
            raise ReportDataError("빈 브랜드 이름을 집계할 수 없습니다.")
        if key not in brands:
            brands[key] = {
                "name": name,
                "kind": kind,
                "specified": specified,
                "mentions": 0,
                "recommendations": 0,
                "ranks": [],
                "recommended_with_rank": 0,
                "mentioned_questions": [],
            }
        elif specified:
            brands[key]["specified"] = True
            if brands[key]["kind"] != "target":
                brands[key]["kind"] = "specified"
        return brands[key]

    target = ensure_brand(target_name, "target", True)
    for competitor in data.get("competitors", []):
        ensure_brand(_text(competitor["name"]), "specified", True)

    for question in questions:
        qid = question["id"]
        target_judgment = question.get("target") or {}
        if bool(target_judgment.get("mentioned")):
            target["mentions"] += 1
            target["mentioned_questions"].append(qid)
        if qid in RECOMMENDATION_IDS and bool(target_judgment.get("recommended")):
            target["recommendations"] += 1
            if target_judgment.get("rank") is not None:
                target["ranks"].append(float(target_judgment["rank"]))
                target["recommended_with_rank"] += 1

        seen: set[str] = set()
        for judgment in question.get("brands", []):
            name = _text(judgment.get("name")).strip()
            key = _key(name)
            if key == _key(target_name):
                raise ReportDataError(f"{qid}: 자사 판정은 brands가 아니라 target에 넣어야 합니다.")
            if key in seen:
                raise ReportDataError(f"{qid}: 같은 브랜드가 중복 기록됐습니다: {name}")
            seen.add(key)
            brand = ensure_brand(name, "specified" if judgment.get("specified") else "discovered", bool(judgment.get("specified")))
            if bool(judgment.get("mentioned")):
                brand["mentions"] += 1
                brand["mentioned_questions"].append(qid)
            if qid in RECOMMENDATION_IDS and bool(judgment.get("recommended")):
                brand["recommendations"] += 1
                if judgment.get("rank") is not None:
                    brand["ranks"].append(float(judgment["rank"]))
                    brand["recommended_with_rank"] += 1

    total_recommendations = sum(brand["recommendations"] for brand in brands.values())
    for brand in brands.values():
        brand["mention_rate"] = _percent(brand["mentions"], 5)
        brand["recommendation_rate"] = _percent(brand["recommendations"], 4)
        brand["sov"] = _percent(brand["recommendations"], total_recommendations)
        if brand["ranks"]:
            brand["average_rank"] = sum(brand["ranks"]) / len(brand["ranks"])
        else:
            brand["average_rank"] = None

    return {
        "questions": questions,
        "brands": list(brands.values()),
        "target": target,
        "total_recommendations": total_recommendations,
    }


def _rate_label(count: int, denominator: int) -> str:
    return f"{count}/{denominator} · {_percent(count, denominator)}"


def _sov_label(brand: dict[str, Any], total: int) -> str:
    if total == 0:
        return "N/A"
    return f"{brand['recommendations']}/{total} · {_percent(brand['recommendations'], total)}"


def _rank_label(brand: dict[str, Any]) -> str:
    average = brand["average_rank"]
    if average is None:
        return "-"
    ranked = len(brand["ranks"])
    recommended = brand["recommendations"]
    return f"{average:.1f}위 ({ranked}/{recommended}건 순위 확인)"


def _source_counts(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for question in questions:
        for source in question.get("sources", []):
            label = _text(source.get("label")).strip()
            url = _text(source.get("url")).strip()
            if not label and not url:
                continue
            key = (url or label).casefold()
            if key not in sources:
                sources[key] = {"label": label or url, "url": url, "count": 0, "questions": []}
            sources[key]["count"] += 1
            sources[key]["questions"].append(question["id"])
    return list(sources.values())


def render_markdown(data: dict[str, Any], metrics: dict[str, Any]) -> str:
    target = metrics["target"]
    technical = data["technical"]
    score = None if technical.get("score") is None else round(float(technical["score"]))
    lines = [
        f"# {_md_cell(data['target']['name'])} ChatGPT GEO 스냅샷 — {_md_cell(data.get('measured_at', ''))}",
        "",
        "> 질문 5개, 단일 시점, 반복 측정 없음의 스냅샷입니다. 추세가 아니라 현재 한 장의 사진으로 읽어주세요.",
        "> 사이트 기술 진단은 AI가 사이트를 접근·발견·해석하기 좋은 상태인지 확인한 별도 결과이며 실제 추천을 보장하지 않습니다.",
        "",
        "## 사이트 기술 진단",
        "",
        f"- AI 접근 상태: **{_md_cell(technical.get('access_state', '확인 불가'))}**",
        (
            f"- 사이트 기술 점수: **{score}/100 ({_grade(score)})**"
            if score is not None
            else "- 사이트 기술 점수: **- (확인 범위 부족)**"
        ),
    ]
    if technical.get("cap_reason"):
        lines.append(f"- 점수 상한 근거: {_md_cell(technical['cap_reason'])}")
    urls = technical.get("audited_urls", [])
    if urls:
        lines.extend(["- 확인 URL:"] + [f"  - {_md_cell(url)}" for url in urls])
    for section in technical.get("sections", []):
        lines.extend(["", f"### {_md_cell(section.get('label'))}", "", "| 항목 | 상태 | 근거 |", "|---|---|---|"])
        for row in section.get("rows", []):
            label = STATUS_LABELS.get(row.get("status"), (row.get("status", ""), ""))[0]
            lines.append(f"| {_md_cell(row.get('item'))} | {_md_cell(label)} | {_md_cell(row.get('evidence'))} |")
    if technical.get("trust_summary"):
        lines.extend(["", f"**콘텐츠 신뢰성 요약:** {_md_cell(technical['trust_summary'])}"])

    lines.extend([
        "",
        "## 핵심 지표",
        "",
        f"- 언급률: **{_rate_label(target['mentions'], 5)}**",
        f"- 추천률: **{_rate_label(target['recommendations'], 4)}**",
        f"- 추천 SoV: **{_sov_label(target, metrics['total_recommendations'])}**",
        f"- 평균 추천순위: **{_rank_label(target)}**",
        "",
        "언급률 = Q1~Q5 자사 언급 수 / 5  ",
        "추천률 = Q2~Q5 자사 추천 수 / 4  ",
        "추천 SoV = Q2~Q5 자사 추천 수 / 자사·지정 경쟁사·자동 발견 경쟁사 전체 추천 수  ",
        "평균 추천순위 = Q2~Q5에서 신뢰 가능한 자사 추천순위 평균",
        "",
        "## 전체 브랜드 비교",
        "",
        "| 브랜드 | 구분 | 언급률 | 추천률 | 추천 SoV | 평균 추천순위 |",
        "|---|---|---|---|---|---|",
    ])
    kind_labels = {"target": "자사", "specified": "지정 경쟁사", "discovered": "자동 발견"}
    for brand in metrics["brands"]:
        lines.append(
            f"| {_md_cell(brand['name'])} | {kind_labels[brand['kind']]} | "
            f"{_rate_label(brand['mentions'], 5)} | {_rate_label(brand['recommendations'], 4)} | "
            f"{_sov_label(brand, metrics['total_recommendations'])} | {_rank_label(brand)} |"
        )

    lines.extend(["", "## 질문별 결과", "", "| ID | 질문 | 자사 언급 | 자사 추천 | 답변 본문 등장 경쟁사 |", "|---|---|---:|---:|---|"])
    for question in metrics["questions"]:
        body_brands = [item["name"] for item in question.get("brands", []) if item.get("mentioned")]
        tj = question.get("target") or {}
        rec = "O" if tj.get("recommended") else "X"
        if question["id"] == "Q1":
            rec += " (지표 제외)"
        lines.append(
            f"| {question['id']} | {_md_cell(question.get('question'))} | "
            f"{'O' if tj.get('mentioned') else 'X'} | {rec} | {_md_cell(', '.join(body_brands) or '—')} |"
        )
    lines.extend(["", "Q1은 해결책 탐색 질문이므로 추천 O/X를 보여주되 추천 지표에서는 제외합니다."])
    for question in metrics["questions"]:
        tj = question.get("target") or {}
        matched = ", ".join(_text(item) for item in tj.get("matched_names", [])) or "없음"
        lines.extend([
            "",
            f"<details><summary>{question['id']} 응답 전문 보기</summary>",
            "",
            f"자사 판정 근거: {_html(tj.get('evidence') or '해당 없음')}  ",
            f"실제 매칭 이름: {_html(matched)}",
            "",
            f"<pre>{_html(question.get('response'))}</pre>",
            "",
            "</details>",
        ])

    discovered = [brand for brand in metrics["brands"] if brand["kind"] != "target" and brand["mentions"]]
    lines.extend(["", "## 답변에서 발견된 경쟁사", "", "| 브랜드 | 구분 | 등장 질문 | 등장 답변 수 |", "|---|---|---|---:|"])
    if discovered:
        for brand in discovered:
            lines.append(f"| {_md_cell(brand['name'])} | {kind_labels[brand['kind']]} | {', '.join(brand['mentioned_questions'])} | {brand['mentions']} |")
    else:
        lines.append("| — | — | — | 0 |")

    strong_questions = []
    for question in metrics["questions"]:
        if question["id"] not in RECOMMENDATION_IDS or (question.get("target") or {}).get("recommended"):
            continue
        recommended = [item["name"] for item in question.get("brands", []) if item.get("recommended")]
        if recommended:
            strong_questions.append((question, recommended))
    lines.extend(["", "## 경쟁사가 강한 질문", ""])
    if strong_questions:
        lines.append("Q2~Q5 중 경쟁사는 추천됐지만 자사는 추천되지 않은 질문입니다.")
        lines.append("")
        for question, recommended in strong_questions:
            lines.append(f"- **{question['id']}** {_md_cell(question.get('question'))} — {_md_cell(', '.join(recommended))} 추천")
    else:
        lines.append("이 기준에 해당하는 질문이 없습니다.")

    sources = _source_counts(metrics["questions"])
    lines.extend(["", "## 확인된 출처 표기", "", "| 출처 라벨 | URL | 확인된 질문 |", "|---|---|---|"])
    if sources:
        for source in sources:
            lines.append(f"| {_md_cell(source['label'])} | {_md_cell(source['url'] or '—')} | {', '.join(source['questions'])} |")
    else:
        lines.append("| — | — | — |")
    lines.extend(["", "복사본에 보인 출처만 기록한 관찰 목록이며 완전한 출처 집계나 비율이 아닙니다."])

    lines.extend(["", "## 관찰 기반 개선 가설", ""])
    hypotheses = data.get("hypotheses", []) or ["현재 데이터만으로 기술 상태와 답변 결과의 인과관계를 단정할 수 없습니다."]
    lines.extend(f"- {_md_cell(item)}" for item in hypotheses)
    lines.extend(["", "## 우선 개선 과제", ""])
    priorities = data.get("priorities", []) or ["확인된 기술·콘텐츠 문제부터 수정하고 같은 질문으로 다시 측정합니다."]
    lines.extend(f"{index}. {_md_cell(item)}" for index, item in enumerate(priorities[:3], 1))
    lines.extend([
        "",
        "## 재측정 방법",
        "",
        "개선 반영과 재크롤링 시간을 고려해 보통 2~4주 후, 아래 동일 질문을 각각 새 ChatGPT 대화에서 다시 실행합니다. 변화는 보장되지 않으며 같은 기준으로 비교합니다.",
        "",
        "## 한계",
        "",
    ])
    limitations = data.get("limitations", []) or ["질문 5개·단일 시점 결과이며 ChatGPT 답변은 실행할 때마다 달라질 수 있습니다."]
    lines.extend(f"- {_md_cell(item)}" for item in limitations)
    lines.extend(["", "## 부록 · 측정 질문 5개", "", "| ID | 질문 |", "|---|---|"])
    for question in metrics["questions"]:
        lines.append(f"| {question['id']} | {_md_cell(question.get('question'))} |")
    lines.extend(["", "<!-- geo-test-run: complete -->", ""])
    return "\n".join(lines)


def _gauge_svg(score: int) -> str:
    angle = -90 + score * 1.8
    return f"""<svg viewBox="0 0 200 120" role="img" aria-label="사이트 기술 점수 {score}점">
<path d="M20 100 A80 80 0 0 1 100 20" class="arc urgent"/>
<path d="M100 20 A80 80 0 0 1 147.02 35.28" class="arc improve"/>
<path d="M147.02 35.28 A80 80 0 0 1 176.08 75.28" class="arc good"/>
<path d="M176.08 75.28 A80 80 0 0 1 180 100" class="arc excellent"/>
<line x1="100" y1="100" x2="100" y2="31" class="needle" transform="rotate({angle:.1f} 100 100)"/>
<circle cx="100" cy="100" r="7" class="hub"/></svg>"""


def render_html(data: dict[str, Any], metrics: dict[str, Any]) -> str:
    target = metrics["target"]
    technical = data["technical"]
    score = None if technical.get("score") is None else round(float(technical["score"]))
    title = f"{_html(data['target']['name'])} ChatGPT GEO 스냅샷"
    total = metrics["total_recommendations"]
    kind_labels = {"target": "자사", "specified": "지정 경쟁사", "discovered": "자동 발견"}

    metric_cards = "".join([
        f'<div class="metric-card"><span>언급률</span><strong>{_html(_rate_label(target["mentions"], 5))}</strong></div>',
        f'<div class="metric-card"><span>추천률</span><strong>{_html(_rate_label(target["recommendations"], 4))}</strong></div>',
        f'<div class="metric-card"><span>추천 SoV</span><strong>{_html(_sov_label(target, total))}</strong></div>',
        f'<div class="metric-card"><span>평균 추천순위</span><strong>{_html(_rank_label(target))}</strong></div>',
    ])

    tech_sections = []
    for section in technical.get("sections", []):
        rows = []
        for row in section.get("rows", []):
            status_label, status_class = STATUS_LABELS.get(row.get("status"), (_text(row.get("status")), "b-unknown"))
            rows.append(f'<tr><td>{_html(row.get("item"))}</td><td><span class="badge {status_class}">{_html(status_label)}</span></td><td>{_html(row.get("evidence"))}</td></tr>')
        tech_sections.append(
            f'<div class="tier"><span class="tier-chip">{_html(section.get("label"))}</span>'
            '<div class="table-wrap"><table class="tier-table"><colgroup><col style="width:26%"><col style="width:14%"><col></colgroup>'
            '<thead><tr><th>항목</th><th>상태</th><th>근거</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div></div>"
        )

    comparison_rows = []
    for brand in metrics["brands"]:
        comparison_rows.append(
            f'<tr><td>{_html(brand["name"])}</td><td>{kind_labels[brand["kind"]]}</td>'
            f'<td>{_html(_rate_label(brand["mentions"], 5))}</td>'
            f'<td>{_html(_rate_label(brand["recommendations"], 4))}</td>'
            f'<td>{_html(_sov_label(brand, total))}</td><td>{_html(_rank_label(brand))}</td></tr>'
        )

    question_rows = []
    response_details = []
    for question in metrics["questions"]:
        tj = question.get("target") or {}
        brands = [item["name"] for item in question.get("brands", []) if item.get("mentioned")]
        tags = "".join(f'<span class="tag">{_html(name)}</span>' for name in brands) or "—"
        rec = "O" if tj.get("recommended") else "X"
        rec_class = "ox-good" if tj.get("recommended") else "ox-bad"
        if question["id"] == "Q1":
            rec += "*"
        question_rows.append(
            f'<tr><td>{question["id"]}</td><td>{_html(question.get("question"))}</td>'
            f'<td class="{"ox-good" if tj.get("mentioned") else "ox-bad"}">{"O" if tj.get("mentioned") else "X"}</td>'
            f'<td class="{rec_class}">{rec}</td><td>{tags}</td></tr>'
        )
        matched = ", ".join(_text(item) for item in tj.get("matched_names", [])) or "없음"
        response_details.append(
            f'<details><summary>{question["id"]} 응답 전문 보기</summary>'
            f'<p class="evidence"><b>자사 판정 근거:</b> {_html(tj.get("evidence") or "해당 없음")}<br>'
            f'<b>실제 매칭 이름:</b> {_html(matched)}</p>'
            f'<pre>{_html(question.get("response"))}</pre></details>'
        )

    discovered = [brand for brand in metrics["brands"] if brand["kind"] != "target" and brand["mentions"]]
    max_mentions = max((brand["mentions"] for brand in discovered), default=0)
    total_mentions = sum(brand["mentions"] for brand in discovered)
    bars = []
    for index, brand in enumerate(discovered):
        width = brand["mentions"] / max_mentions * 100 if max_mentions else 0
        share = round(brand["mentions"] / total_mentions * 100) if total_mentions else 0
        bars.append(
            f'<div class="bar-row"><span class="bar-label">{_html(brand["name"])}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%;background:{BAR_COLORS[index % len(BAR_COLORS)]}">'
            f'{brand["mentions"]} ({share}%)</div></div></div>'
        )
    if not bars:
        bars.append('<p class="note">답변 본문에서 확인된 경쟁사가 없습니다.</p>')

    strong_items = []
    for question in metrics["questions"]:
        if question["id"] not in RECOMMENDATION_IDS or (question.get("target") or {}).get("recommended"):
            continue
        recommended = [item["name"] for item in question.get("brands", []) if item.get("recommended")]
        if recommended:
            strong_items.append(
                f'<li><b>{question["id"]}</b> {_html(question.get("question"))} — {_html(", ".join(recommended))} 추천</li>'
            )
    strong_content = (
        '<p class="note">Q2~Q5 중 경쟁사는 추천됐지만 자사는 추천되지 않은 질문입니다.</p><ul>'
        + "".join(strong_items)
        + "</ul>"
        if strong_items
        else '<p class="note">이 기준에 해당하는 질문이 없습니다.</p>'
    )

    source_rows = []
    for source in _source_counts(metrics["questions"]):
        source_rows.append(f'<tr><td>{_html(source["label"])}</td><td>{_html(source["url"] or "—")}</td><td>{_html(", ".join(source["questions"]))}</td></tr>')
    if not source_rows:
        source_rows.append('<tr><td colspan="3">복사본에서 확인된 출처 표기가 없습니다.</td></tr>')

    hypotheses = data.get("hypotheses", []) or ["현재 데이터만으로 기술 상태와 답변 결과의 인과관계를 단정할 수 없습니다."]
    priorities = data.get("priorities", []) or ["확인된 기술·콘텐츠 문제부터 수정하고 같은 질문으로 다시 측정합니다."]
    limitations = data.get("limitations", []) or ["질문 5개·단일 시점 결과이며 ChatGPT 답변은 실행할 때마다 달라질 수 있습니다."]
    audited_urls = "".join(f"<li>{_html(url)}</li>" for url in technical.get("audited_urls", []))
    cap_note = f'<p class="note">원점수 {_html(technical.get("raw_score", score))}점 · {_html(technical["cap_reason"])}</p>' if technical.get("cap_reason") else ""
    if score is None:
        gauge_content = '<div class="gauge-unavailable">-</div><div class="gauge-grade">확인 범위 부족</div>'
    else:
        gauge_content = f'{_gauge_svg(score)}<div class="gauge-score">{score}<small>/100</small></div><div class="gauge-grade">{_grade(score)}</div>'

    css = """
:root{--bg:#0b0f14;--card:#141a22;--line:#26303d;--text:#e8edf3;--muted:#96a2b2;--accent:#6ea0ff;--good:#2ecc71;--warn:#f1c40f;--bad:#e46b65}
*{box-sizing:border-box}body{margin:0;padding:28px;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Pretendard","Malgun Gothic",sans-serif;line-height:1.55}.wrap{max-width:1180px;margin:auto}h1{font-size:1.75rem;margin:0 0 3px}.sub,.note{color:var(--muted)}.sub{margin-bottom:20px}.banner{padding:11px 15px;border:1px solid #5a4214;background:#2b2112;color:#f4ca58;border-radius:9px;font-size:.82rem;margin-bottom:18px}.split{display:grid;grid-template-columns:2fr 3fr;gap:16px}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin-bottom:16px}.split-card{display:flex;flex-direction:column}.split-card .card-body{flex:1;display:flex;flex-direction:column;justify-content:center}h2{font-size:1.05rem;color:var(--accent);margin:0 0 12px}.access-state{align-self:center;background:#172746;color:var(--accent);padding:4px 10px;border-radius:99px;font-size:.78rem;font-weight:700}.gauge{text-align:center}.gauge svg{display:block;width:210px;max-width:100%;margin:auto}.gauge-unavailable{font-size:3rem;font-weight:800;margin:24px 0 4px}.arc{fill:none;stroke-width:18}.urgent{stroke:#e74c3c}.improve{stroke:#f39c12}.good{stroke:#f1c40f}.excellent{stroke:#2ecc71}.needle{stroke:#dfe7f2;stroke-width:4}.hub{fill:#dfe7f2}.gauge-score{font-size:2rem;font-weight:800;margin-top:-20px}.gauge-grade{color:var(--muted)}.metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.metric-card{background:#0f151d;border:1px solid var(--line);border-radius:9px;padding:12px}.metric-card span{display:block;color:var(--muted);font-size:.78rem}.metric-card strong{display:block;font-size:1.18rem;margin-top:3px}.formula-list{list-style:none;padding:0;margin:12px 0 0;color:var(--muted);font-size:.79rem;line-height:1.85}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:.88rem}th,td{text-align:left;padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);white-space:nowrap}.tier{border-left:3px solid var(--accent);padding-left:13px;margin-bottom:17px}.tier:last-child{margin-bottom:0}.tier-chip,.tag,.badge{display:inline-block;border-radius:6px;font-size:.76rem}.tier-chip{background:#172746;color:var(--accent);font-weight:700;padding:3px 9px;margin-bottom:9px}.tier-table{table-layout:fixed}.badge{padding:2px 7px;white-space:nowrap}.b-good{background:#123a24;color:var(--good)}.b-warn{background:#3a3011;color:var(--warn)}.b-bad{background:#3a1717;color:var(--bad)}.b-unknown{background:#27303b;color:#b6c0cc}.ox-good{color:var(--good);font-weight:800}.ox-bad{color:var(--muted);font-weight:800}.tag{background:#26303d;color:#c2ccd8;padding:2px 7px;margin:0 3px 3px 0}details{border:1px solid var(--line);border-radius:8px;padding:8px 11px;margin-top:8px}summary{cursor:pointer;color:var(--accent)}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;font-size:.86rem;background:#0e1319;padding:12px;border-radius:7px}.evidence{font-size:.84rem;color:var(--muted)}.bars{display:flex;flex-direction:column;gap:10px}.bar-row{display:flex;align-items:center;gap:12px}.bar-label{width:160px;text-align:right;flex:0 0 auto;font-size:.84rem}.bar-track{flex:1;background:#0e1319;border-radius:6px;height:30px;overflow:hidden}.bar-fill{height:100%;display:flex;align-items:center;padding-left:9px;color:#091017;font-weight:800;font-size:.79rem;white-space:nowrap;border-radius:6px}ul,ol{margin:0;padding-left:20px}.url-list{font-size:.82rem;color:var(--muted);overflow-wrap:anywhere}@media(max-width:760px){body{padding:14px}.split{grid-template-columns:1fr}.metrics{grid-template-columns:1fr 1fr}.bar-label{width:105px}.tier-table{min-width:650px}}
"""

    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — {_html(data.get('measured_at'))}</title><style>{css}</style></head><body><main class="wrap">
<h1>{title}</h1><div class="sub">측정일자: {_html(data.get('measured_at'))} · 질문 5개 · ChatGPT 단일 시점</div>
<div class="banner">⚠ 질문 5개, 단일 시점, 반복 측정 없음의 스냅샷입니다. 추세가 아니라 현재 한 장의 사진으로 읽어주세요.<br>아래 사이트 기술 점수는 AI가 사이트를 접근·발견·해석하기 좋은 상태인지 확인한 별도 지표이며 실제 추천을 보장하지 않습니다.</div>
<div class="split"><section class="card split-card"><h2>사이트 기술 점수</h2><div class="card-body"><div class="access-state">AI 접근 상태: {_html(technical.get('access_state', '확인 불가'))}</div><div class="gauge">{gauge_content}{cap_note}</div></div></section>
<section class="card split-card"><h2>핵심 지표</h2><div class="card-body"><div class="metrics">{metric_cards}</div><ul class="formula-list"><li>언급률 = Q1~Q5 자사 언급 수 / 5</li><li>추천률 = Q2~Q5 자사 추천 수 / 4</li><li>추천 SoV = Q2~Q5 자사 추천 수 / 자사·지정·자동 발견 경쟁사 전체 추천 수</li><li>평균 추천순위 = Q2~Q5의 신뢰 가능한 자사 추천순위 평균</li></ul></div></section></div>
<section class="card"><h2>사이트 기술 진단 상세</h2><p class="note">확인한 공개 핵심 페이지 표본</p><ul class="url-list">{audited_urls or '<li>기록 없음</li>'}</ul>{''.join(tech_sections)}<p class="note"><b>콘텐츠 신뢰성:</b> {_html(technical.get('trust_summary', '기록 없음'))}</p></section>
<section class="card"><h2>전체 브랜드 비교</h2><div class="table-wrap"><table><thead><tr><th>브랜드</th><th>구분</th><th>언급률</th><th>추천률</th><th>추천 SoV</th><th>평균 추천순위</th></tr></thead><tbody>{''.join(comparison_rows)}</tbody></table></div></section>
<section class="card"><h2>질문별 결과</h2><div class="table-wrap"><table><thead><tr><th>ID</th><th>질문</th><th>자사 언급</th><th>자사 추천</th><th>답변 본문 등장 경쟁사</th></tr></thead><tbody>{''.join(question_rows)}</tbody></table></div><p class="note">* Q1의 추천 판정은 보여주지만 추천률·추천 SoV·평균 추천순위에서는 제외합니다.</p>{''.join(response_details)}</section>
<section class="card"><h2>답변에서 발견된 경쟁사</h2><div class="bars">{''.join(bars)}</div></section>
<section class="card"><h2>경쟁사가 강한 질문</h2>{strong_content}</section>
<section class="card"><h2>확인된 출처 표기</h2><div class="table-wrap"><table><thead><tr><th>출처 라벨</th><th>URL</th><th>확인된 질문</th></tr></thead><tbody>{''.join(source_rows)}</tbody></table></div><p class="note">복사본에 보인 출처만 기록한 관찰 목록이며 완전한 출처 집계나 비율이 아닙니다.</p></section>
<section class="card"><h2>관찰 기반 개선 가설</h2><ul>{''.join(f'<li>{_html(item)}</li>' for item in hypotheses)}</ul></section>
<section class="card"><h2>우선 개선 과제</h2><ol>{''.join(f'<li>{_html(item)}</li>' for item in priorities[:3])}</ol></section>
<section class="card"><h2>재측정 방법</h2><p>개선 반영과 재크롤링 시간을 고려해 보통 2~4주 후, 아래 동일 질문을 각각 새 ChatGPT 대화에서 다시 실행합니다. 변화는 보장되지 않으며 같은 기준으로 비교합니다.</p></section>
<section class="card"><h2>한계</h2><ul>{''.join(f'<li>{_html(item)}</li>' for item in limitations)}</ul></section>
<section class="card"><h2>부록 · 측정 질문 5개</h2><div class="table-wrap"><table><thead><tr><th>ID</th><th>질문</th></tr></thead><tbody>{''.join(f'<tr><td>{q["id"]}</td><td>{_html(q.get("question"))}</td></tr>' for q in metrics['questions'])}</tbody></table></div></section>
</main></body></html>"""


def build(input_path: Path, run_dir: Path, download_copy: Path | None = None) -> tuple[Path, Path]:
    data = load_data(input_path)
    metrics = calculate_metrics(data)
    run_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = run_dir / "report.md"
    html_path = run_dir / "report.html"
    markdown_path.write_text(render_markdown(data, metrics), encoding="utf-8")
    html_path.write_text(render_html(data, metrics), encoding="utf-8")
    if download_copy is not None:
        download_copy = download_copy.expanduser()
        download_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(html_path, download_copy)
    return markdown_path, html_path


def main() -> int:
    parser = argparse.ArgumentParser(description="report-data.json에서 GEO 리포트를 생성합니다.")
    parser.add_argument("--input", type=Path, required=True, help="완료된 report-data.json")
    parser.add_argument("--run-dir", type=Path, help="report.md/report.html 저장 폴더(기본: 입력 파일 폴더)")
    parser.add_argument("--download-copy", type=Path, help="사용자용 HTML을 추가 복사할 경로")
    args = parser.parse_args()
    run_dir = args.run_dir or args.input.parent
    markdown_path, html_path = build(args.input, run_dir, args.download_copy)
    print(f"Markdown: {markdown_path.resolve()}")
    print(f"HTML: {html_path.resolve()}")
    if args.download_copy:
        print(f"Download copy: {args.download_copy.expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
