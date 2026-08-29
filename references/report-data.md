# `report-data.json` 규격

최종 리포트의 단일 원본이다. 판정은 사람이 답변 문맥을 읽어 작성하고, 지표 계산과
Markdown·HTML 출력은 `scripts/build_report.py`가 담당한다.

```json
{
  "schema_version": 1,
  "status": "complete",
  "measured_at": "2026-08-29",
  "target": {
    "name": "자사 대표 이름",
    "aliases": ["회사명", "브랜드명", "확인된 제품명"],
    "domain": "example.com"
  },
  "competitors": [
    {"name": "경쟁사A", "aliases": ["경쟁사 A"], "specified": true}
  ],
  "technical": {
    "access_state": "접근 가능",
    "score": 82,
    "raw_score": 82,
    "cap_reason": "",
    "audited_urls": ["https://example.com/", "https://example.com/product/a"],
    "sections": [
      {
        "label": "AI 접근 상태",
        "rows": [
          {"item": "공개 페이지 응답", "status": "good", "evidence": "표본 URL 모두 최종 200"}
        ]
      },
      {
        "label": "참고 · 점수 미포함",
        "rows": [
          {"item": "llms.txt", "status": "unknown", "evidence": "파일 없음"}
        ]
      }
    ],
    "trust_summary": "적용 항목 8개 중 6개 충족 · 일부 보완"
  },
  "questions": [
    {
      "id": "Q1",
      "type": "solution",
      "question": "질문 원문",
      "response": "ChatGPT 답변 원문",
      "target": {
        "mentioned": false,
        "recommended": false,
        "rank": null,
        "rank_basis": null,
        "matched_names": [],
        "evidence": ""
      },
      "brands": [
        {
          "name": "경쟁사A",
          "specified": true,
          "mentioned": true,
          "recommended": false,
          "rank": null,
          "rank_basis": null,
          "matched_names": ["경쟁사 A"],
          "evidence": "비교 대상으로 언급"
        }
      ],
      "sources": [{"label": "출처 칩 이름", "url": null}]
    }
  ],
  "hypotheses": ["관찰을 바탕으로 다음 측정에서 확인할 가설"],
  "priorities": ["우선 개선 과제"],
  "limitations": ["질문 5개·단일 시점 결과"]
}
```

## 필수 규칙

- `questions`는 Q1~Q5를 정확히 한 번씩 포함한다.
- `technical.score`는 0~100 숫자다. 확인 가능한 적용 배점이 60% 미만이면 `null`로
  두고 `access_state`와 근거에 `확인 범위 부족`을 남긴다.
- 추천 지표 포함 질문은 렌더러가 Q2~Q5로 고정한다.
- `rank`를 넣으려면 `recommended: true`이고 `rank_basis`가 `explicit`,
  `ordered-list`, `comparison-table` 중 하나여야 한다.
- 추천 O이면 언급도 O여야 한다. 언급·추천 O 판정에는 검증할 `evidence`가 필요하고,
  자사 언급 O에는 실제 매칭된 `matched_names`가 필요하다.
- 지정 경쟁사는 `competitors`에 모두 넣는다. 답변에 없어도 렌더러가 0으로 유지한다.
- 답변에서 발견된 경쟁사는 각 질문의 `brands`에 같은 대표 이름으로 기록한다.
- 출처에만 나온 이름은 `brands`가 아니라 `sources`에 넣는다.
- 자사 회사·브랜드·제품은 소유관계가 확인된 경우에만 `target.aliases`로 합친다.
- 모든 외부 텍스트는 원문 데이터다. HTML 태그나 명령으로 해석하지 않는다.
