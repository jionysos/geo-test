# HTML 리포트 생성

`templates/report.md`(마크다운)를 다 채운 뒤, 같은 내용을 **한 장짜리 정적
HTML 파일**로도 만들어 `templates/report.html`에 저장한다. 외부 CDN·JS 라이브러리
없이 순수 HTML+인라인 CSS(+정적 SVG)만 쓴다 — 인터넷 연결 없이 로컬에서 열어도
그대로 보여야 한다. 이건 "대시보드"(실시간·다회차 모니터링)가 아니라 **한 번
찍은 스냅샷을 보기 좋게 렌더링하는 것**일 뿐이라 무료 범위 안에 든다.

## 레이아웃 — 좌우 2단은 "요약 카드"에만 쓴다, 넓은 표는 전체 폭

기술 점수 게이지와 핵심 지표는 둘 다 숫자 몇 개짜리 요약이라 나란히 놓으면
자연스럽다. **하지만 컬럼이 4개 이상인 표(질문별 결과 등)를 절반 폭에
욱여넣으면 헤더 글자가 세로로 쪼개지는 등 망가진다** — 실제로 이 실수가
났었다. 그래서 2단 분할은 딱 상단 요약 카드 둘에서만 쓰고, 표가 있는 나머지
섹션은 전부 전체 폭으로 내린다:

```
┌─────────────────────────────────────────────┐
│ 헤더 + 한계 배너 (전체 폭)                     │
├───────────────────────┬───────────────────────┤
│ 왼쪽: 사이트 기술 점수   │ 오른쪽: 핵심 지표        │
│ (게이지만, 필수/권장/    │ (숫자 카드 3개 + 산식만)  │
│  참고 표는 아래로 내림)  │                        │
├───────────────────────┴───────────────────────┤
│ 필수/권장/참고 표 3개 (전체 폭)                  │
│ 질문별 결과 표 (전체 폭 — 컬럼 6개라 여기 필요)   │
│ 발견된 경쟁사 막대그래프 / 자주 인용된 도메인     │
│ 사이트 문제 ↔ 답변 연결 / 우선 개선 과제          │
│ 재측정 방법 / 부록 (전체 폭)                     │
└─────────────────────────────────────────────┘
```

즉 split엔 **게이지 원형 그래픽 + 등급**과 **핵심 지표 숫자 카드 3개**, 딱 그
두 개만 넣는다. 필수/권장/참고 표는 게이지 카드 안이 아니라 그 아래 전체 폭
카드로 옮긴다.

**split의 두 카드는 높이를 맞춘다** — 게이지 카드가 자연히 더 크고 핵심지표
카드가 짧으면 나란히 놓았을 때 삐뚤빼뚤해 보인다. `align-items:stretch`(기본값,
따로 안 써도 됨 — `align-items:start`를 절대 쓰지 않는다)로 두면 그리드가 둘을
같은 높이로 늘려준다.

**높이만 맞추고 끝내지 않는다 — 늘어난 공간 안에서 내용물도 채운다.** 카드
높이를 억지로 늘려도 내용이 위쪽에만 뭉쳐있으면 아래쪽에 휑한 빈 공간이 남는다.
제목(`h2`)은 항상 카드 맨 위에 고정하되, **제목 아래 본문을 `.card-body`로
감싸서 남은 높이 안에서 세로 중앙 정렬**한다:

```html
<section class="card split-card">
  <h2>사이트 기술 점수</h2>
  <div class="card-body">
    <div class="gauge">...</div>
  </div>
</section>
<section class="card split-card">
  <h2>핵심 지표</h2>
  <div class="card-body">
    <div class="metrics">...</div>
    <ul class="formula-list">...</ul>
  </div>
</section>
```

```css
.split-card{display:flex;flex-direction:column}
.split-card .card-body{flex:1;display:flex;flex-direction:column;justify-content:center}
```

`.card-body`는 split의 두 카드에만 쓴다(`.split-card` 클래스로 한정) — 다른
전체 폭 카드(표·리스트가 있는 카드)까지 세로 중앙 정렬하면 오히려 어색해진다.

CSS: `.split{display:grid;grid-template-columns:1fr 1fr;gap:20px}` (align-items
지정 안 함 = 기본 stretch), `@media(max-width:760px){.split{grid-template-columns:1fr}}`로
좁은 화면에선 세로로 자연스럽게 접히게 한다. 표가 있는 카드엔 `overflow-x:auto`를
유지해서 그래도 화면이 좁으면 표 자체가 가로 스크롤되게 한다(레이아웃이 깨지는 대신).

## 기술 점수 게이지 (SVG, 그대로 쓰고 각도만 계산해서 채운다)

점수(0~100)를 바늘 회전각으로 바꾸는 공식: **회전각(deg) = -90 + 점수 × 1.8**
(0점=-90°=왼쪽 수평, 50점=0°=정수직, 100점=90°=오른쪽 수평). 계산한 숫자를
`transform="rotate(...)"`에 그대로 넣는다.

```html
<div class="gauge">
  <svg viewBox="0 0 200 120" width="220" height="132">
    <!-- 시급 0-49 -->
    <path d="M 20 100 A 80 80 0 0 1 43.43 43.43" fill="none" stroke="#e74c3c" stroke-width="18"/>
    <!-- 보완필요 50-69 -->
    <path d="M 43.43 43.43 A 80 80 0 0 1 100 20" fill="none" stroke="#f39c12" stroke-width="18"/>
    <!-- 양호 70-89 -->
    <path d="M 100 20 A 80 80 0 0 1 156.57 43.43" fill="none" stroke="#f1c40f" stroke-width="18"/>
    <!-- 우수 90-100 -->
    <path d="M 156.57 43.43 A 80 80 0 0 1 180 100" fill="none" stroke="#2ecc71" stroke-width="18"/>
    <!-- 바늘: rotate()의 첫 숫자만 "-90 + 점수*1.8" 계산값으로 교체 -->
    <line x1="100" y1="100" x2="100" y2="30" stroke="#222" stroke-width="4"
          transform="rotate(0 100 100)"/>
    <circle cx="100" cy="100" r="8" fill="#222"/>
  </svg>
  <div class="gauge-score">68<span class="gauge-max">/100</span></div>
  <div class="gauge-grade">보완 필요</div>
</div>
```

예시(68점): 회전각 = -90 + 68×1.8 = 32.4 → `transform="rotate(32.4 100 100)"`.

**`.gauge-grade`엔 등급만 적는다 — "필수 항목 전부 통과" 같은 부연은 붙이지
않는다.** 아래 필수/권장/참고 표가 색으로 이미 다 보여주는 내용을 문장으로
반복할 필요가 없다. 등급 하나로 충분하다: "양호", "보완 필요" 같은 단어만.

## 필수/권장/참고 — 표 3개로 나누고, 색으로도 확실히 구분한다

소제목만으로는 구분이 약하다. **테두리 색 + 칩 배지**를 같이 쓰되, **둘 다
셋이 똑같은 강조색(파랑)으로 통일한다** — 필수·권장·참고 전부 같은 파랑
테두리·같은 파랑 칩으로, 핵심 지표 같은 다른 섹션 제목과 같은 "탭"으로
읽히게 한다. 색을 tier마다 다르게 나누면 권장·참고가 낮은 우선순위처럼
보여서 오히려 "이것도 똑같이 구분된 섹션"이라는 느낌이 약해진다 — tier
구분은 색이 아니라 **칩 안 텍스트("필수"/"권장"/"참고 · 점수 미포함")** 하나로
충분히 한다:

```html
<div class="tier-block required">
  <span class="tier-chip required">필수</span>
  <table class="tier-table">...HTTP 200, noindex 없음 등 4개...</table>
</div>

<div class="tier-block recommended">
  <span class="tier-chip recommended">권장</span>
  <table class="tier-table">...sitemap, AI 크롤러별 정책 등...</table>
</div>

<div class="tier-block optional">
  <span class="tier-chip optional">참고 · 점수 미포함</span>
  <table class="tier-table">...llms.txt...</table>
</div>
```

CSS (아래 전체 골격에 포함돼 있음):

```css
.tier-block{border-left:3px solid var(--line);padding-left:14px;margin-bottom:18px}
.tier-block:last-child{margin-bottom:0}
.tier-block.required{border-left-color:var(--accent)}
.tier-block.recommended{border-left-color:var(--accent)}
.tier-block.optional{border-left-color:var(--accent)}
.tier-chip{display:inline-block;font-size:.72rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.05em;padding:3px 9px;border-radius:5px;margin-bottom:10px}
.tier-chip.required{background:#16264a;color:var(--accent)}
.tier-chip.recommended{background:#16264a;color:var(--accent)}
.tier-chip.optional{background:#16264a;color:var(--accent)}
```

이렇게 하면 소제목 텍스트만 있을 때보다 "여기서부터 필수, 여기서부터 권장,
여기서부터 참고"가 스캔하듯 봐도 셋 다 바로 들어온다.

**세 표의 항목/상태/근거 컬럼 너비도 통일한다.** 표 세 개가 각자 자기 내용
길이에 맞춰 컬럼 폭을 정하면(브라우저 기본 동작), 필수 표의 "항목" 폭과 권장
표의 "항목" 폭이 서로 달라져서 세로로 훑을 때 삐뚤빼뚤해 보인다. 세 표 모두
같은 `.tier-table`에 `table-layout:fixed`와 `<colgroup>`으로 고정 비율을
줘서 폭을 강제로 맞춘다:

```html
<table class="tier-table">
  <colgroup><col style="width:26%"><col style="width:14%"><col></colgroup>
  <thead>...</thead><tbody>...</tbody>
</table>
```

`.tier-table{table-layout:fixed}`를 CSS에 추가하고, 모든 tier 표에 이
colgroup(항목 26% · 상태 14% · 근거 나머지)을 그대로 반복해서 쓴다.

## 핵심 지표 아래 산식

**한 줄에 "·"로 이어붙이지 않는다** — 길어지면 줄바꿈이 어중간한 데서 끊겨
읽기 어렵다. 지표마다 줄을 나눠서 리스트로 보여준다:

```html
<ul class="formula-list">
  <li>언급률 = 언급된 답변 수 / 전체 질문 수</li>
  <li>추천률 = 추천된 답변 수 / 추천이 성립할 수 있는 질문 수</li>
</ul>
```

인용률은 넣지 않는다 — `references/scoring.md` 참고("+N" 묶음 맹점 때문에
계산하지 않기로 함). 경쟁사가 있으면 이 아래에 Mention SoV·Recommendation
SoV도 같이 보여준다.

`.formula-list`는 아래 전체 골격 CSS에 포함돼 있다(불릿 없이, 작고 흐린
텍스트로, 줄 사이 여백을 좀 준다).

## 질문별 결과 — O/X 표 + 등장 브랜드 배지 + AI 응답 원문(접기)

"자사가 빠진 질문"처럼 따로 뽑아 요약하지 않는다 — 이 표 하나로 다 보인다.
O/X는 색으로도 구분한다(`.ox-good`=초록 O, `.ox-bad`=회색 X, 회색인 이유는
"실패"가 아니라 "여기선 없었다"는 중립적 사실이라서 빨간색을 안 쓴다):

```html
<table><thead><tr><th>ID</th><th>질문</th><th>언급</th><th>추천</th><th>등장 브랜드</th></tr></thead>
<tbody>
<tr>
  <td>Q1</td><td>강아지 종합영양제 선택 기준</td>
  <td class="ox-bad">X</td><td class="ox-bad">X</td>
  <td>—</td>
</tr>
<tr>
  <td>Q2</td><td>국내 종합영양제 추천</td>
  <td class="ox-bad">X</td><td class="ox-bad">X</td>
  <td><span class="tag">한아름펫</span><span class="tag">라이프펫</span></td>
</tr>
</tbody></table>

<details><summary>Q1 응답 전문 보기</summary>
<p>(붙여넣은 원문 그대로 — 요약하지 말고 판정에 쓴 만큼 남긴다)</p>
</details>
<details><summary>Q2 응답 전문 보기</summary>
<p>...</p>
</details>
```

각 질문 표 아래에 `<details>`를 질문 개수만큼 나열한다(질문당 하나). CSS는
아래 전체 골격에 `.ox-good`/`.ox-bad`/`.tag`/`details`로 이미 포함돼 있다.
`<details>`는 JS 없이 브라우저 기본 기능으로 접고 펼쳐진다 — 이 스킬의
"외부 JS 없음" 원칙에 안 걸린다.

**표 아래 보조 설명도 한 줄로 이어붙이지 않는다.** `.formula-list`로 분리한다:

```html
<ul class="formula-list">
  <li>추천 "—" = 그 질문 유형이 추천률 분모에서 제외됨</li>
</ul>
```

브랜드 표기 재확인 같은 별개 내용(예: "OO·OO 및 관련 제품명을 원문에서 다시
확인했으나 실제로 없었다")은 이 리스트에 섞지 말고 별도 `<p class="note">`로
분리한다 — 컬럼 설명과 다른 종류의 정보라서 같이 나열하면 산식 목록인지
일반 코멘트인지 헷갈린다.

## 답변에서 발견된 경쟁사 — 막대그래프 (파이차트 대신)

원형 차트보다 막대그래프가 값을 비교하기 쉽고 카드 폭도 꽉 채울 수 있다.
**막대는 최댓값 기준으로 폭을 채운다**(전체 합 기준 아니다 — 합 기준으로
하면 브랜드가 여럿일 때 막대가 다 짧아져서 폭이 안 찬다). 막대 안에는 개수와
전체 대비 비율(%)을 같이 써넣는다:

```
폭% = (그 브랜드 등장 수 / 최댓값) × 100
막대 안 표시 텍스트 = "{등장 수} ({전체 합 대비 비율}%)"
```

```html
<div class="bars">
  <div class="bar-row">
    <span class="bar-label">라이프펫</span>
    <div class="bar-track"><div class="bar-fill" style="width:100%;background:#6ea0ff">2 (33%)</div></div>
  </div>
  <div class="bar-row">
    <span class="bar-label">한아름펫/페티널</span>
    <div class="bar-track"><div class="bar-fill" style="width:50%;background:#f39c12">1 (17%)</div></div>
  </div>
  <div class="bar-row">
    <span class="bar-label">펫생각</span>
    <div class="bar-track"><div class="bar-fill" style="width:50%;background:#9b59b6">1 (17%)</div></div>
  </div>
</div>
```

CSS(아래 전체 골격에 포함돼 있음):

```css
.bars{display:flex;flex-direction:column;gap:10px}
.bar-row{display:flex;align-items:center;gap:14px}
.bar-label{width:150px;flex-shrink:0;font-size:.88rem;text-align:right}
.bar-track{flex:1;background:#0e1319;border-radius:6px;height:30px;overflow:hidden}
.bar-fill{height:100%;display:flex;align-items:center;padding-left:10px;
  color:#0b0f14;font-weight:700;font-size:.82rem;border-radius:6px;white-space:nowrap}
```

색 팔레트는 고정 5색(`#6ea0ff #f39c12 #9b59b6 #1abc9c #e91e8c`)을 브랜드
등장 순서대로 배정하고, 5개보다 많으면 나머지는 "기타"로 묶어서 색 하나를
더 쓴다(무한정 늘리지 않는다). 브랜드가 1개뿐이면 막대그래프도 의미가 없으니
표만 쓴다.

## 전체 페이지 골격 (인라인 CSS)

배너에 문장이 두 개 이상 들어가면(예: 한계 고지 + 기술 점수는 별도 지표라는
설명) **한 문단으로 이어붙이지 않는다** — 브라우저가 아무 데서나 줄바꿈해서
단어 중간이 잘리기도 한다. 문장 사이에 `<br>`을 넣어 각자 한 줄로 시작하게
한다(위 골격의 `.banner` 예시 참고).

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>{브랜드명} GEO 스냅샷 — {측정일자}</title>
<style>
  :root{--bg:#0b0f14;--card:#141a22;--line:#232b36;--text:#e8edf3;--muted:#8a96a6;
        --accent:#4f8cff;--good:#2ecc71;--warn:#f1c40f;--bad:#e74c3c}
  *{box-sizing:border-box}
  body{margin:0;padding:32px;background:var(--bg);color:var(--text);
       font-family:-apple-system,"Pretendard","Malgun Gothic",sans-serif;line-height:1.6}
  .wrap{max-width:1040px;margin:0 auto}
  h1{font-size:1.6rem;margin-bottom:4px} .sub{color:var(--muted);margin-bottom:24px}
  .banner{background:#2a1f10;border:1px solid #5a3d10;color:#f1c40f;
          padding:10px 16px;border-radius:8px;margin-bottom:24px;font-size:.78rem}
  .split{display:grid;grid-template-columns:1fr 1fr;gap:20px}
  @media(max-width:760px){.split{grid-template-columns:1fr}}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;
        padding:20px;margin-bottom:20px}
  .split-card{display:flex;flex-direction:column}
  .split-card .card-body{flex:1;display:flex;flex-direction:column;justify-content:center}
  .gauge{display:flex;flex-direction:column;align-items:center;text-align:center;margin-bottom:12px}
  .gauge-score{font-size:2rem;font-weight:700;margin-top:-8px}
  .gauge-max{font-size:1rem;color:var(--muted);font-weight:400}
  .gauge-grade{color:var(--muted)}
  table{width:100%;border-collapse:collapse;font-size:.92rem}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
  th{color:var(--muted);font-weight:600;white-space:nowrap}
  .tier-table{table-layout:fixed}
  .badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.8rem}
  .b-good{background:#123a24;color:var(--good)} .b-warn{background:#3a2f0f;color:var(--warn)}
  .b-bad{background:#3a1414;color:var(--bad)}
  h2{font-size:1.05rem;margin:0 0 12px;color:var(--accent)}
  .tier-block{border-left:3px solid var(--line);padding-left:14px;margin-bottom:18px}
  .tier-block:last-child{margin-bottom:0}
  .tier-block.required{border-left-color:var(--accent)}
  .tier-block.recommended{border-left-color:var(--accent)}
  .tier-block.optional{border-left-color:var(--accent)}
  .tier-chip{display:inline-block;font-size:.72rem;font-weight:700;text-transform:uppercase;
    letter-spacing:.05em;padding:3px 9px;border-radius:5px;margin-bottom:10px}
  .tier-chip.required{background:#16264a;color:var(--accent)}
  .tier-chip.recommended{background:#16264a;color:var(--accent)}
  .tier-chip.optional{background:#16264a;color:var(--accent)}
  .note{color:var(--muted);font-size:.85rem;margin-top:10px}
  .formula-list{list-style:none;margin:10px 0 0;padding:0;color:var(--muted);
    font-size:.85rem;line-height:1.9}
  .ox-good{color:var(--good);font-weight:700} .ox-bad{color:var(--muted);font-weight:700}
  .tag{display:inline-block;background:#232b36;color:#aab4c2;font-size:.78rem;
    padding:2px 8px;border-radius:999px;margin:0 4px 4px 0}
  details{margin-bottom:8px;border:1px solid var(--line);border-radius:8px;padding:8px 12px}
  summary{cursor:pointer;color:var(--accent);font-size:.9rem}
  details p{margin:8px 0 2px;font-size:.88rem;color:var(--text);white-space:pre-wrap}
  .bars{display:flex;flex-direction:column;gap:10px}
  .bar-row{display:flex;align-items:center;gap:14px}
  .bar-label{width:150px;flex-shrink:0;font-size:.88rem;text-align:right}
  .bar-track{flex:1;background:#0e1319;border-radius:6px;height:30px;overflow:hidden}
  .bar-fill{height:100%;display:flex;align-items:center;padding-left:10px;
    color:#0b0f14;font-weight:700;font-size:.82rem;border-radius:6px;white-space:nowrap}
  ul{margin:0;padding-left:20px}
</style>
</head>
<body>
<div class="wrap">
  <h1>{브랜드명} GEO 스냅샷</h1>
  <div class="sub">측정일자: {날짜} · 질문 5개 · 단일 시점</div>
  <div class="banner">⚠ 질문 5개, 단일 시점, 반복 측정 없음의 스냅샷입니다. 추세가 아니라 현재 한 장의 사진으로 읽어주세요.
  <br>아래 사이트 기술 점수는 HTTP 응답·HTML·메타 태그 등 확인 가능한 사실 기준의 별도 지표입니다.</div>

  <div class="split">
    <section class="card split-card"><h2>사이트 기술 점수</h2><div class="card-body">(게이지 + 등급만 — 표는 아래로)</div></section>
    <section class="card split-card"><h2>핵심 지표</h2><div class="card-body">(숫자 카드 3개 + 산식 .formula-list만)</div></section>
  </div>

  <!-- 아래부터는 전체 폭 — 컬럼 많은 표·차트가 있는 섹션은 전부 여기 -->
  <div class="card"><h2>사이트 기술 진단 상세</h2>(필수/권장/참고 3표 삽입, 각 table.tier-table + colgroup)</div>
  <div class="card"><h2>질문별 결과</h2>(O/X표 + 등장브랜드 배지 + 질문별 details 삽입)</div>
  <div class="card"><h2>답변에서 발견된 경쟁사</h2>(막대그래프 삽입, 브랜드 1개뿐이면 표만)</div>
  <!-- 자주 인용된 도메인 카드도 여기 순서대로 추가 -->
  <div class="card"><h2>사이트 문제 ↔ 실제 AI 답변 연결</h2>(내용 삽입)</div>
  <div class="card"><h2>우선 개선 과제</h2>(내용 삽입)</div>
  <div class="card"><h2>재측정 방법</h2>(내용 삽입)</div>
  <div class="card"><h2>부록 · 측정 질문 5개</h2>(표 삽입)</div>
</div>
</body>
</html>
```

배지(`badge`) 클래스는 ✅→`b-good`, ⚠️→`b-warn`, ❌→`b-bad`로 매핑해서 표 안
상태 칸에 쓴다. 색상표는 라이트/다크 상관없이 이 다크 테마 하나로 고정한다 —
사용자 브라우저 설정에 맞출 필요 없는 정적 파일이라 단순하게 간다.

## 저장·안내

`templates/report.html`로 저장하고, 8단계 마지막에 "브라우저로 열어서
`templates/report.html`을 보시면 시각적으로 정리된 버전을 보실 수 있어요"라고
안내한다. 마크다운 리포트(`templates/report.md`)를 대체하는 게 아니라 같이
남긴다 — 마크다운은 재검증·diff용, HTML은 보여주기용으로 역할이 다르다.
